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
import json
import os
import openai
from concurrent.futures import ThreadPoolExecutor
from functools import lru_cache
from pathlib import Path
from time import sleep
import logging
import re
from urllib.parse import urlparse

from dotenv import dotenv_values

# Configure logging
logger = logging.getLogger(__name__)

# Disable httpx logging
logging.getLogger("httpx").setLevel(logging.CRITICAL)
# Disable urllib3 logging (which httpx uses)
logging.getLogger("urllib3").setLevel(logging.CRITICAL)
# Disable httpcore logging (which httpx uses)
logging.getLogger("httpcore").setLevel(logging.CRITICAL)

# api utils

processing_config = json.load(open("configs/processing_config.json"))
temp = processing_config["temperature"]

config = {}
client = {}
try:
    with open("configs/api_config.json", encoding="utf-8") as config_file:
        config = json.load(config_file)
    for model_name, settings in config.items():
        if all(settings.get(field) for field in ("azure_endpoint", "api_version", "api_key")):
            client[model_name] = openai.AzureOpenAI(
                azure_endpoint=settings["azure_endpoint"],
                api_version=settings["api_version"],
                api_key=settings["api_key"],
            )
except (OSError, ValueError):
    pass


def glm_settings():
    """Read protected GLM config for BigModel or Alibaba Model Studio."""
    config_path = Path(os.environ.get(
        "M3_GLM_ENV_FILE", Path.home() / ".config" / "m3-agent" / "glm.env"
    ))
    file_values = dotenv_values(config_path) if config_path.is_file() else {}
    key = (os.environ.get("GLM_API_KEY") or file_values.get("GLM_API_KEY")
           or os.environ.get("DASHSCOPE_API_KEY") or file_values.get("DASHSCOPE_API_KEY"))
    base_url = os.environ.get("GLM_API_BASE_URL") or file_values.get("GLM_API_BASE_URL")
    if not key or not base_url:
        raise RuntimeError(
            f"GLM_API_KEY (or DASHSCOPE_API_KEY) and GLM_API_BASE_URL must be set in the environment or {config_path}"
        )
    parsed = urlparse(base_url.rstrip("/"))
    if parsed.scheme != "https" or parsed.username or parsed.password or parsed.query or parsed.fragment:
        raise RuntimeError("GLM API base URL must be a plain HTTPS API endpoint")
    if parsed.hostname in {"open.bigmodel.cn", "api.z.ai"}:
        provider = "glm"
        if parsed.path != "/api/paas/v4":
            raise RuntimeError("Use the general GLM API /api/paas/v4, not the Coding Plan endpoint")
    elif (parsed.hostname == "dashscope.aliyuncs.com" or
          re.fullmatch(r"[a-z0-9-]+\.cn-beijing\.maas\.aliyuncs\.com", parsed.hostname or "")):
        provider = "bailian"
        if parsed.path != "/compatible-mode/v1":
            raise RuntimeError("Alibaba Model Studio requires /compatible-mode/v1")
    else:
        raise RuntimeError("Unsupported GLM API host; use official BigModel/Z.ai or Alibaba Model Studio Beijing")
    expected_provider = os.environ.get("GLM_API_PROVIDER") or file_values.get("GLM_API_PROVIDER")
    if expected_provider and expected_provider != provider:
        raise RuntimeError(f"GLM_API_PROVIDER={expected_provider} does not match the configured API host")
    default_chat = "ZHIPU/GLM-5.3-Flash" if provider == "bailian" else "glm-5.3-flash"
    default_embedding = "text-embedding-v4" if provider == "bailian" else "embedding-3"
    chat_model = os.environ.get("GLM_CHAT_MODEL") or file_values.get("GLM_CHAT_MODEL") or default_chat
    embedding_model = os.environ.get("GLM_EMBEDDING_MODEL") or file_values.get("GLM_EMBEDDING_MODEL") or default_embedding
    allowed_embedding = {"bailian": "text-embedding-v4", "glm": "embedding-3"}
    if embedding_model != allowed_embedding[provider]:
        raise RuntimeError(f"{provider} graph conversion requires {allowed_embedding[provider]}")
    return {
        "key": key,
        "base_url": base_url.rstrip("/"),
        "provider": provider,
        "chat_model": chat_model,
        "embedding_model": embedding_model,
        "embedding_dim": 2048,
        "embedding_batch_limit": 10 if provider == "bailian" else 64,
    }


@lru_cache(maxsize=1)
def glm_client():
    settings = glm_settings()
    return openai.OpenAI(api_key=settings["key"], base_url=settings["base_url"])


def glm_embed_texts(texts, batch_size=10):
    """Embed texts together so graph conversion does not issue one API call per node."""
    if not texts:
        return [], 0
    settings = glm_settings()
    if not 1 <= batch_size <= settings["embedding_batch_limit"]:
        raise ValueError(f"{settings['provider']} embedding batch size must be between 1 and {settings['embedding_batch_limit']}")
    embeddings = []
    token_count = 0
    for start in range(0, len(texts), batch_size):
        batch = texts[start:start + batch_size]
        request = {"model": settings["embedding_model"], "input": batch}
        if settings["provider"] == "bailian":
            request["dimensions"] = settings["embedding_dim"]
        response = glm_client().embeddings.create(**request)
        ordered = sorted(response.data, key=lambda item: item.index)
        if len(ordered) != len(batch):
            raise RuntimeError("GLM embedding response length does not match the request")
        vectors = [item.embedding for item in ordered]
        if any(len(vector) != settings["embedding_dim"] for vector in vectors):
            raise RuntimeError(f"Expected {settings['embedding_dim']}-dimensional {settings['embedding_model']} vectors")
        embeddings.extend(vectors)
        token_count += getattr(response.usage, "total_tokens", 0) or 0
    return embeddings, token_count

MAX_RETRIES = 5

def get_response(model, messages, timeout=30):
    """Get chat completion response from specified model.

    Args:
        model (str): Model identifier
        messages (list): List of message dictionaries

    Returns:
        tuple: (response content, total tokens used)
    """
    response = client[model].chat.completions.create(
        model=model, messages=messages, temperature=temp, timeout=timeout, max_tokens=8192
    )
    
    # return answer and number of tokens
    return response.choices[0].message.content, response.usage.total_tokens

def get_response_with_retry(model, messages, timeout=30):
    """Retry get_response up to MAX_RETRIES times with error handling.

    Args:
        model (str): Model identifier
        messages (list): List of message dictionaries

    Returns:
        tuple: (response content, total tokens used)
        
    Raises:
        Exception: If all retries fail
    """
    for i in range(MAX_RETRIES):
        try:
            return get_response(model, messages, timeout)
        except Exception as e:
            sleep(20)
            logger.warning(f"Retry {i} times, exception: {e} from message {messages}")
            continue
    raise Exception(f"Failed to get response after {MAX_RETRIES} retries")

def parallel_get_response(model, messages, timeout=30):
    """Process multiple messages in parallel using ThreadPoolExecutor.
    Messages are processed in batches, with each batch completing before starting the next.

    Args:
        model (str): Model identifier
        messages (list): List of message lists to process

    Returns:
        tuple: (list of responses, total tokens used)
    """
    batch_size = config[model]["qpm"]
    responses = []
    total_tokens = 0

    for i in range(0, len(messages), batch_size):
        batch = messages[i:i + batch_size]
        with ThreadPoolExecutor(max_workers=len(batch)) as executor:
            batch_responses = list(executor.map(lambda msg: get_response_with_retry(model, msg, timeout), batch))
            
        # Extract answers and tokens from batch responses
        batch_answers = [response[0] for response in batch_responses]
        batch_tokens = [response[1] for response in batch_responses]
        
        responses.extend(batch_answers)
        total_tokens += sum(batch_tokens)

    return responses, total_tokens


def get_embedding(model, text, timeout=15):
    """Get embedding for text using specified model.

    Args:
        model (str): Model identifier
        text (str): Text to embed

    Returns:
        tuple: (embedding vector, total tokens used)
    """
    if model == "text-embedding-3-large" and os.environ.get("M3_EMBEDDING_PROVIDER") == "glm":
        vectors, tokens = glm_embed_texts([text], batch_size=1)
        return vectors[0], tokens
    response = client[model].embeddings.create(input=text, model=model, timeout=timeout)
    return response.data[0].embedding, response.usage.total_tokens


def get_embedding_with_retry(model, text, timeout=15):
    """Retry get_embedding up to MAX_RETRIES times with error handling.

    Args:
        model (str): Model identifier
        text (str): Text to embed

    Returns:
        tuple: (embedding vector, total tokens used)
        
    Raises:
        Exception: If all retries fail
    """
    for i in range(MAX_RETRIES):
        try:
            return get_embedding(model, text, timeout)
        except Exception as e:
            sleep(20)
            logger.warning(f"Retry {i} times, exception: {e} from get embedding")
            continue
    raise Exception(f"Failed to get embedding after {MAX_RETRIES} retries")

def parallel_get_embedding(model, texts, timeout=15):
    """Process multiple texts in parallel to get embeddings.

    Args:
        model (str): Model identifier
        texts (list): List of texts to embed

    Returns:
        tuple: (list of embeddings, total tokens used)
    """
    if model == "text-embedding-3-large" and os.environ.get("M3_EMBEDDING_PROVIDER") == "glm":
        return glm_embed_texts(texts)
    batch_size = config[model]["qpm"]
    embeddings = []
    total_tokens = 0
    
    # Process texts in batches
    for i in range(0, len(texts), batch_size):
        batch = texts[i:i + batch_size]
        max_workers = len(batch)
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            results = list(executor.map(lambda x: get_embedding_with_retry(model, x, timeout), batch))
            
        # Split batch results into embeddings and tokens
        batch_embeddings = [result[0] for result in results]
        batch_tokens = [result[1] for result in results]
        
        embeddings.extend(batch_embeddings)
        total_tokens += sum(batch_tokens)
        
    return embeddings, total_tokens

def get_whisper(model, file_path):
    """Transcribe audio file using Whisper model.

    Args:
        model (str): Model identifier
        file_path (str): Path to audio file

    Returns:
        str: Transcription text
    """
    file = open(file_path, "rb")
    return client[model].audio.transcriptions.create(model=model, file=file).text

def get_whisper_with_retry(model, file_path):
    """Retry Whisper transcription with error handling.

    Args:
        model (str): Model identifier
        file_path (str): Path to audio file

    Returns:
        str: Transcription text
        
    Raises:
        Exception: If all retries fail
    """
    for i in range(MAX_RETRIES):
        try:
            return get_whisper(model, file_path)
        except Exception as e:
            sleep(20)
            logger.warning(f"Retry {i} times, exception: {e}")
    raise Exception(f"Failed to get response after {MAX_RETRIES} retries")

def parallel_get_whisper(model, file_paths):
    """Process multiple audio files in parallel using Whisper model.

    Args:
        model (str): Model identifier
        file_paths (list): List of audio file paths

    Returns:
        list: List of transcription results
    """
    batch_size = config[model]["qpm"]
    responses = []
    
    for i in range(0, len(file_paths), batch_size):
        batch = file_paths[i:i + batch_size]
        max_workers = len(batch)
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            batch_responses = list(executor.map(lambda x: get_whisper_with_retry(model, x), batch))
            
        responses.extend(batch_responses)
        
    return responses

def generate_messages(inputs):
    """Generate message list for chat completion from mixed inputs.

    Args:
        inputs (list): List of input dictionaries with 'type' and 'content' keys
        type can be:
            "text" - text content
            "image/jpeg", "image/png" - base64 encoded images
            "video/mp4", "video/webm" - base64 encoded videos
            "video_url" - video URL
            "audio/mp3", "audio/wav" - base64 encoded audio
        content should be a string for text,
        a list of base64 encoded media for images/video/audio,
        or a string (url) for video_url
        inputs are like: 
        [
            {
                "type": "video_base64/mp4",
                "content": <base64>
            },
            {
                "type": "text",
                "content": "Describe the video content."
            },
            ...
        ]

    Returns:
        list: Formatted messages for chat completion
    """
    messages = []
    messages.append(
        {"role": "system", "content": "You are an expert in video understanding."}
    )
    content = []
    for input in inputs:
        if not input["content"]:
            logger.warning("empty content, skip")
            continue
        if input["type"] == "text":
            content.append({"type": "text", "text": input["content"]})
        elif input["type"] in ["images/jpeg", "images/png"]:
            img_format = input["type"].split("/")[1]
            if isinstance(input["content"][0], str):
                content.extend(
                    [
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/{img_format};base64,{img}",
                                "detail": "high",
                            },
                        }
                        for img in input["content"]
                    ]
                )
            else:
                for img in input["content"]:
                    content.append({
                        "type": "text",
                        "text": img[0],
                    })
                    content.append({
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/{img_format};base64,{img[1]}",
                            "detail": "high",
                        },
                    })
        elif input["type"] == "video_url":
            content.append(
                {
                    "type": "image_url",
                    "image_url": {"url": input["content"]},
                }
            )
        elif input["type"] in ["video_base64/mp4", "video_base64/webm"]:
            video_format = input["type"].split("/")[1]
            content.append(
                {
                    "type": "image_url",
                    "image_url": {"url": f"data:video/{video_format};base64,{input['content']}"},
                }
            )
        elif input["type"] in ["audio_base64/mp3", "audio_base64/wav"]:
            audio_format = input["type"].split("/")[1]
            content.append(
                {
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:audio/{audio_format};base64,{input['content']}"
                    },
                }
            )
        else:
            raise ValueError(f"Invalid input type: {input['type']}")
    messages.append({"role": "user", "content": content})
    return messages

def print_messages(messages):
    for message in messages:
        if message["role"] == "user":
            for item in message["content"]:
                if item["type"] == "text":
                    logger.debug(item['text'])
