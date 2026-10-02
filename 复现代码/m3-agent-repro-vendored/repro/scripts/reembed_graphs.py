#!/usr/bin/env python3
"""Create separate GLM text-vector copies of official M3 memory graphs."""
import argparse
import json
import os
import pickle
import tempfile
from pathlib import Path

from mmagent.utils.chat_api import glm_embed_texts, glm_settings
from mmagent.utils.general import load_video_graph
from repro.scripts.qa_selection import select_qa_pairs


ROOT = Path(__file__).resolve().parents[2]


def text_nodes(graph):
    for node_id in graph.text_nodes:
        node = graph.nodes[node_id]
        if node.type not in {"episodic", "semantic"}:
            continue
        contents = node.metadata.get("contents", [])
        if len(contents) != 1 or len(node.embeddings) != 1:
            raise RuntimeError(f"Text node {node_id} has an unsupported content/embedding shape")
        yield node_id, contents[0]


def save_graph(graph, target):
    target.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temp_name = tempfile.mkstemp(prefix=".graph-", suffix=".pkl", dir=target.parent)
    try:
        with os.fdopen(descriptor, "wb") as stream:
            pickle.dump(graph, stream, protocol=pickle.HIGHEST_PROTOCOL)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temp_name, target)
    finally:
        if os.path.exists(temp_name):
            os.unlink(temp_name)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--split", choices=("robot", "web"), required=True)
    parser.add_argument("--limit-videos", type=int)
    parser.add_argument("--smoke-max-qas", type=int,
                        help="Convert only videos referenced by the matching type-diverse QA subset.")
    parser.add_argument("--batch-size", type=int, default=10)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    if args.limit_videos is not None and args.limit_videos < 1:
        parser.error("--limit-videos must be positive")
    if not 1 <= args.batch_size <= 64:
        parser.error("--batch-size must be between 1 and 64")
    annotation_path = ROOT / "data" / "annotations" / f"{args.split}.json"
    annotations = json.loads(annotation_path.read_text(encoding="utf-8"))
    if args.smoke_max_qas is not None:
        if args.smoke_max_qas < 1:
            parser.error("--smoke-max-qas must be positive")
        selected_ids = dict.fromkeys(video_id for video_id, _ in select_qa_pairs(annotations, args.smoke_max_qas))
        videos = [(video_id, annotations[video_id]) for video_id in selected_ids]
    else:
        videos = list(annotations.items())
    videos = videos[:args.limit_videos]
    source_paths = [ROOT / item["mem_path"] for _, item in videos]
    missing = [str(path) for path in source_paths if not path.is_file()]
    if missing:
        raise SystemExit(f"{len(missing)} source graph(s) missing; first: {missing[0]}")
    if args.dry_run:
        total_bytes = sum(path.stat().st_size for path in source_paths)
        text_count = unique_count = request_count = 0
        for source in source_paths:
            pairs = list(text_nodes(load_video_graph(str(source))))
            distinct = len(set(text for _, text in pairs))
            text_count += len(pairs)
            unique_count += distinct
            request_count += (distinct + args.batch_size - 1) // args.batch_size
        print(
            f"Ready to convert {len(videos)} {args.split} graph(s); "
            f"source size={total_bytes / 2**30:.2f} GiB; "
            f"text nodes={text_count}; unique texts={unique_count}; "
            f"estimated embedding API requests={request_count}"
        )
        return

    settings = glm_settings()
    if args.batch_size > settings["embedding_batch_limit"]:
        parser.error(f"--batch-size must be at most {settings['embedding_batch_limit']} for {settings['provider']}")
    target_root = ROOT / "data" / f"memory_graphs_{settings['provider']}"
    converted = skipped = total_nodes = total_tokens = 0
    for video_id, item in videos:
        source = ROOT / item["mem_path"]
        relative = source.relative_to(ROOT / "data" / "memory_graphs")
        target = target_root / relative
        if target.is_file():
            existing = load_video_graph(str(target))
            if (getattr(existing, "text_embedding_model", None) != settings["embedding_model"] or
                    getattr(existing, "text_embedding_provider", None) != settings["provider"] or
                    getattr(existing, "text_embedding_dim", None) != settings["embedding_dim"]):
                raise RuntimeError(f"Existing graph embedding metadata does not match current settings: {target}")
            skipped += 1
            continue
        graph = load_video_graph(str(source))
        pairs = list(text_nodes(graph))
        unique = list(dict.fromkeys(text for _, text in pairs))
        vectors, token_count = glm_embed_texts(unique, batch_size=args.batch_size)
        if len(vectors) != len(unique):
            raise RuntimeError(f"Embedding count mismatch for {video_id}")
        by_text = dict(zip(unique, vectors))
        for node_id, text in pairs:
            graph.nodes[node_id].embeddings = [by_text[text]]
        graph.text_embedding_model = settings["embedding_model"]
        graph.text_embedding_provider = settings["provider"]
        graph.text_embedding_dim = settings["embedding_dim"]
        save_graph(graph, target)
        converted += 1
        total_nodes += len(pairs)
        total_tokens += token_count
        print(f"{video_id}: {len(pairs)} text nodes converted", flush=True)
    print(f"Converted={converted}, already_present={skipped}, text_nodes={total_nodes}, API_tokens={total_tokens}")


if __name__ == "__main__":
    main()
