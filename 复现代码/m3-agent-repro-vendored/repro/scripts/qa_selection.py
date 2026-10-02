"""Deterministic type-diverse QA selection shared by inference and graph checks."""


def select_qa_pairs(annotations, limit=None):
    pairs = [
        (video_id, qa)
        for video_id, video in annotations.items()
        for qa in video["qa_list"]
    ]
    if limit is None or limit >= len(pairs):
        return pairs
    if limit <= 10:
        # Keep the API smoke test small: two videos can still cover all five
        # M3 question types while requiring far fewer graph conversions.
        ranked_videos = sorted(
            annotations,
            key=lambda video_id: (
                -len({label for qa in annotations[video_id]["qa_list"]
                      for label in qa.get("type", [])}),
                list(annotations).index(video_id),
            ),
        )
        allowed_videos = set(ranked_videos[:min(2, limit)])
        pairs = [pair for pair in pairs if pair[0] in allowed_videos]
    selected = []
    covered_types = set()
    selected_videos = set()
    remaining = list(enumerate(pairs))
    if limit <= 10:
        for video_id in ranked_videos[:min(2, limit)]:
            candidates = [(index, pair) for index, pair in remaining if pair[0] == video_id]
            if not candidates:
                continue
            best = max(candidates, key=lambda pair: (len(set(pair[1][1].get("type", []))), -pair[0]))
            remaining.remove(best)
            selected.append(best[1])
            covered_types.update(best[1][1].get("type", []))
            selected_videos.add(video_id)
    while remaining and len(selected) < limit:
        best = max(
            remaining,
            key=lambda pair: (
                len(set(pair[1][1].get("type", [])) - covered_types),
                int(pair[1][0] not in selected_videos),
                -pair[0],
            ),
        )
        remaining.remove(best)
        video_id, qa = best[1]
        selected.append((video_id, qa))
        covered_types.update(qa.get("type", []))
        selected_videos.add(video_id)
    return selected
