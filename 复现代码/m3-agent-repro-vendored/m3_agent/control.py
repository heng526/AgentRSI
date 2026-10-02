# Copyright (2025) Bytedance Ltd. and/or its affiliates

# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at

#     http://www.apache.org/licenses/LICENSE-2.0

# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
import re
import os
import sys
import json
import time
import argparse
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import mmagent.videograph
from mmagent.retrieve import search
from vllm import LLM, SamplingParams
from transformers import AutoTokenizer
from mmagent.utils.general import load_video_graph
from mmagent.utils.chat_api import generate_messages, glm_client, glm_settings
from mmagent.prompts import prompt_agent_verify_answer_referencing
from repro.scripts.qa_selection import select_qa_pairs

sys.modules["videograph"] = mmagent.videograph
processing_config = json.load(open("configs/processing_config.json"))
model_name = "models/M3-Agent-Control"
gpt_model = os.environ.get("M3_AZURE_DEPLOYMENT", "gpt-4o-2024-11-20")
client = None

def get_client():
    """Create the Azure client only when scoring is explicitly enabled."""
    global client
    if client is None:
        import openai
        config_path = "configs/api_config.json"
        if not os.path.isfile(config_path):
            raise RuntimeError("Azure evaluation config is missing; use --skip-eval for local inference")
        with open(config_path, encoding="utf-8") as config_file:
            config = json.load(config_file)
        if gpt_model not in config:
            raise RuntimeError(f"Azure deployment '{gpt_model}' is missing from {config_path}")
        client = openai.AzureOpenAI(
            azure_endpoint=config[gpt_model]["azure_endpoint"],
            api_version=config[gpt_model]["api_version"],
            api_key=config[gpt_model]["api_key"],
        )
    return client

def get_response(messages, timeout=30):
    response = get_client().chat.completions.create(
        model=gpt_model, messages=messages, temperature=0, timeout=timeout, max_tokens=2048
    )
    return response.choices[0].message.content, response.usage.total_tokens

def get_response_with_retry(messages, timeout=30):
    for i in range(20):
        try:
            return get_response(messages, timeout)
        except Exception as e:
            time.sleep(20)
            print(f"Retry {i} times, exception: {e} from message {messages}")
            continue
    raise Exception(f"Failed to get response after 5 retries")

def eval_answer(question, predict, ground_truth):
    if predict == "":
        return False
    try:
        input = [
            {
                "type": "text",
                "content": prompt_agent_verify_answer_referencing.format(
                    question=question,
                    ground_truth_answer=ground_truth,
                    agent_answer=predict,
                ),
            }   
        ]
        messages = generate_messages(input)
        response = get_response_with_retry(messages)
        result = response[0].lower()
    except Exception as e:
        print(f"Error verifying qa: {question} | {str(e)}")
        return False
    return True if "yes" in result else False


def eval_answer_glm(question, predict, ground_truth):
    """Apply the paper's answer-comparison prompt with a GLM judge."""
    if not predict:
        return False
    prompt = prompt_agent_verify_answer_referencing.format(
        question=question,
        ground_truth_answer=ground_truth,
        agent_answer=predict,
    )
    settings = glm_settings()
    response = glm_client().chat.completions.create(
        model=settings["chat_model"],
        messages=[{"role": "user", "content": prompt}],
        temperature=0,
        max_tokens=512,
        timeout=60,
        extra_body={"reasoning_effort": "low"} if settings["provider"] == "bailian" else None,
    )
    verdict = (response.choices[0].message.content or "").strip().lower()
    match = re.search(r"\b(yes|no)\b", verdict)
    if not match:
        return None
    return match.group(1) == "yes"

system_prompt = "You are given a question and some relevant knowledge. Your task is to reason about whether the provided knowledge is sufficient to answer the question. If it is sufficient, output [Answer] followed by the answer. If it is not sufficient, output [Search] and generate a query that will be encoded into embeddings for a vector similarity search. The query will help retrieve additional information from a memory bank.\n\nQuestion: {question}"
instruction = f"""

Output the answer in the format:
Action: [Answer] or [Search]
Content: {{content}}

If the answer cannot be derived yet, the {{content}} should be a single search query that would help retrieve the missing information. The search {{content}} needs to be different from the previous.
You can get the mapping relationship between character ID and name by using search query such as: "What is the name of <character_{{i}}>" or "What is the character id of {{name}}".
After obtaining the mapping, it is best to use character ID instead of name for searching.
If the answer can be derived from the provided knowledge, the {{content}} is the specific answer to the question. Only name can appear in the answer, not character ID like <character_{{i}}>."""

sampling_params = SamplingParams(
    temperature=0.6,
    top_p=0.95,
    top_k=20,
    max_tokens=1024
)
pattern = r"Action: \[(.*)\].*Content: (.*)"

def consumer(data):
    if not data["finish"]:
        before_clip = data.get("before_clip", None)
        response = data["conversations"][-1]["content"]
        match_result = re.search(pattern, response.split("</think>")[-1], re.DOTALL)
        if match_result:
            action = match_result.group(1)
            content = match_result.group(2)
        else:
            action = "Search"
            content = None
        if action == "Answer":
            data["response"] = content
            data["finish"] = True
        else:
            new_memories = {}
            if content and not data.get("skip_retrieval"):
                mem_node = load_video_graph(data["mem_path"])
                if mem_node is None:
                    raise RuntimeError(f"Memory graph not found: {data['mem_path']}")
                if os.environ.get("M3_EMBEDDING_PROVIDER") == "glm":
                    settings = glm_settings()
                    if (getattr(mem_node, "text_embedding_model", None) != settings["embedding_model"] or
                            getattr(mem_node, "text_embedding_provider", None) != settings["provider"] or
                            getattr(mem_node, "text_embedding_dim", None) != settings["embedding_dim"]):
                        raise RuntimeError(f"Memory graph embedding metadata does not match the API settings: {data['mem_path']}")
                if before_clip is not None:
                    mem_node.truncate_memory_by_clip(before_clip, False)
                mem_node.refresh_equivalences()
                if "character id" in content:
                    memories, _, _ = search(mem_node, content, [], mem_wise=True, topk=20, before_clip=before_clip)
                    new_memories.update(memories)
                else:
                    memories, currenr_clips, _ = search(mem_node, content, data["currenr_clips"], threshold=0.5, topk=processing_config["topk"], before_clip=before_clip)
                    data["currenr_clips"] = currenr_clips
                    new_memories.update(memories)
            data["search_trace"].append({
                "round": data.get("rounds", 0),
                "query": content,
                "memories_returned": len(new_memories),
                "retrieval": "performed" if not data.get("skip_retrieval") else "skipped",
            })
            search_result = "Searched knowledge: " + json.dumps(new_memories, ensure_ascii=False).encode("utf-8", "ignore").decode("utf-8")
            if len(new_memories) == 0:
                search_result += "\n(The search result is empty. Please try searching from another perspective.)"
            data["conversations"].append({"role": "user", "content": search_result})
    return data


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--data_file", type=str, default="data/annotations/robot.json")
    parser.add_argument("--output_file", type=str, default=None,
                        help="Optional result JSONL path. Defaults to the upstream data/results location.")
    parser.add_argument("--tensor_parallel_size", type=int,
                        default=int(os.environ.get("M3_TENSOR_PARALLEL_SIZE", "2")))
    parser.add_argument("--skip-eval", action="store_true",
                        help="Run local inference only; do not initialize or call the Azure evaluator.")
    parser.add_argument("--eval-provider", choices=("azure", "glm"), default="azure")
    parser.add_argument("--skip-retrieval", action="store_true",
                        help="Generation-only diagnostic mode; skip memory search and embedding API calls.")
    parser.add_argument("--control-provider", choices=("qwen", "glm"), default="qwen",
                        help="Use the official local Qwen Control or GLM-5.3-Flash API as Control.")
    parser.add_argument("--max-qas", type=int, default=None,
                        help="Optional deterministic, type-diverse QA limit (used for smoke runs).")
    args = parser.parse_args()
    if args.max_qas is not None and args.max_qas < 1:
        parser.error("--max-qas must be positive")
    dataset_name = args.data_file.split("/")[-1].split(".")[0]
    output_path = args.output_file or os.path.join("data/results", f"{dataset_name}.jsonl")
    output_dir = os.path.dirname(output_path)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)
    with open(args.data_file, encoding="utf-8") as annotation_file:
        datas = json.load(annotation_file)

    all_items = []
    for video_id, qa in select_qa_pairs(datas, args.max_qas):
        video = datas[video_id]
        mem_path = video["mem_path"]
        if os.environ.get("M3_EMBEDDING_PROVIDER") == "glm":
            source_path = Path(mem_path)
            if source_path.parts[:2] != ("data", "memory_graphs"):
                raise RuntimeError(f"Unexpected official graph path: {mem_path}")
            mem_path = str(Path(f"data/memory_graphs_{glm_settings()['provider']}").joinpath(*source_path.parts[2:]))
        item = {
            "id": qa["question_id"],
            "video_id": video_id,
            "mem_path": mem_path,
            "question": qa["question"],
            "answer": qa["answer"],
            "types": qa.get("type", []),
        }
        if "before_clip" in qa:
            item["before_clip"] = qa["before_clip"]
        all_items.append(item)

    batched_datas = [
        all_items[index:index + processing_config["batch_size"]]
        for index in range(0, len(all_items), processing_config["batch_size"])
    ]
    model = None
    tokenizer = None
    glm_model = None
    if args.control_provider == "qwen":
        tokenizer = AutoTokenizer.from_pretrained(model_name)
        model = LLM(model=model_name, tensor_parallel_size=args.tensor_parallel_size)
    else:
        glm_model = glm_settings()["chat_model"]
        glm_client()

    with open(output_path, "w", encoding="utf-8") as output_file:
        for batched_data in batched_datas:
            for item in batched_data:
                item["conversations"] = [
                    {"role": "system", "content": system_prompt.format(question=item["question"])},
                    {"role": "user", "content": "Searched knowledge: {}"},
                ]
                item["finish"] = False
                item["rounds"] = 0
                item["search_trace"] = []
                item["generation_trace"] = []
                item["currenr_clips"] = []
                item["skip_retrieval"] = args.skip_retrieval

            for idx in range(processing_config["total_round"]):
                generation_inputs = []
                for item in batched_data:
                    if item["finish"]:
                        continue
                    item["rounds"] = idx + 1
                    item["conversations"][-1]["content"] += instruction
                    if idx == processing_config["total_round"] - 1:
                        item["conversations"][-1]["content"] += "\n(The Action of this round must be [Answer]. If there is insufficient information, you can make reasonable guesses.)"
                    if args.control_provider == "qwen":
                        token_ids = tokenizer.apply_chat_template(
                            item["conversations"],
                            tokenize=True,
                            add_generation_prompt=True,
                            enable_thinking=True,
                        )
                        generation_inputs.append({"prompt_token_ids": token_ids})
                    else:
                        generation_inputs.append(item["conversations"])

                if not generation_inputs:
                    break
                if args.control_provider == "qwen":
                    generated = model.generate(
                        prompts=generation_inputs,
                        sampling_params=sampling_params,
                        use_tqdm=False,
                    )
                    generation_results = [{
                        "text": output.outputs[0].text,
                        "finish_reason": output.outputs[0].finish_reason,
                        "completion_tokens": len(output.outputs[0].token_ids or []),
                    } for output in generated]
                else:
                    def call_glm(messages):
                        settings = glm_settings()
                        completion = glm_client().chat.completions.create(
                            model=glm_model,
                            messages=messages,
                            temperature=0.6,
                            top_p=0.95,
                            max_tokens=2048 if settings["provider"] == "bailian" else 1024,
                            timeout=90,
                            extra_body={"reasoning_effort": "low"} if settings["provider"] == "bailian" else None,
                        )
                        choice = completion.choices[0]
                        usage = completion.usage
                        details = getattr(usage, "completion_tokens_details", None)
                        return {
                            "text": choice.message.content or "",
                            "finish_reason": choice.finish_reason,
                            "completion_tokens": getattr(usage, "completion_tokens", None),
                            "reasoning_tokens": getattr(details, "reasoning_tokens", None),
                        }
                    with ThreadPoolExecutor(max_workers=min(4, len(generation_inputs))) as executor:
                        generation_results = list(executor.map(call_glm, generation_inputs))
                output_index = 0
                for item in batched_data:
                    if item["finish"]:
                        continue
                    generation = generation_results[output_index]
                    output_text = generation["text"]
                    item["conversations"].append({"role": "assistant", "content": output_text})
                    trace = {
                        "round": item["rounds"],
                        "finish_reason": generation["finish_reason"],
                        "completion_tokens": generation["completion_tokens"],
                        "reasoning_tokens": generation.get("reasoning_tokens"),
                        "output_chars": len(output_text),
                        "format_matched": bool(re.search(pattern, output_text.split("</think>")[-1], re.DOTALL)),
                    }
                    if not trace["format_matched"]:
                        trace["output_excerpt"] = output_text[-500:]
                    item["generation_trace"].append(trace)
                    output_index += 1
                if output_index != len(generation_results):
                    raise RuntimeError("Control returned a different number of outputs than prompts")

                consumer_workers = min(4, len(batched_data))
                with ThreadPoolExecutor(max_workers=consumer_workers) as executor:
                    batched_data = list(executor.map(consumer, batched_data))

            for item in batched_data:
                record = {
                    "id": item["id"],
                    "video_id": item["video_id"],
                    "question": item["question"],
                    "answer": item["answer"],
                    "types": item["types"],
                    "response": item.get("response"),
                    "status": "answered" if item.get("response") else "unanswered",
                    "rounds": item["rounds"],
                    "retrieval_mode": "skipped" if args.skip_retrieval else "embedding-search",
                    "embedding_provider": glm_settings()["provider"] if os.environ.get("M3_EMBEDDING_PROVIDER") == "glm" else "azure",
                    "embedding_model": glm_settings()["embedding_model"] if os.environ.get("M3_EMBEDDING_PROVIDER") == "glm" else "text-embedding-3-large",
                    "control_provider": args.control_provider,
                    "control_api_provider": glm_settings()["provider"] if args.control_provider == "glm" else "local",
                    "control_model": model_name if args.control_provider == "qwen" else glm_model,
                    "search_trace": item["search_trace"],
                    "generation_trace": item["generation_trace"],
                }
                if "before_clip" in item:
                    record["before_clip"] = item["before_clip"]
                if not args.skip_eval:
                    if args.eval_provider == "glm":
                        record["judge_provider"] = glm_settings()["provider"]
                        record["judge_model"] = glm_settings()["chat_model"]
                        record["judge_result"] = eval_answer_glm(
                            item["question"], item.get("response", ""), item["answer"]
                        )
                    else:
                        record["judge_provider"] = "azure"
                        record["judge_model"] = gpt_model
                        record["judge_result"] = eval_answer(
                            item["question"], item.get("response", ""), item["answer"]
                        )
                        time.sleep(0.5)
                output_file.write(json.dumps(record, ensure_ascii=False) + "\n")
            output_file.flush()
