#!/usr/bin/env python3
"""上下文水位表（2026-09-23，心心要的）。

每次她发消息时跑一次：从本窗对话记录里取最后一条主线回复的 usage，
算出现在上下文用了多少。到 70% 先提个醒，到 80% 就该写日记了——
9.22 那窗不声不响被 compact 过一次，她说"不想让我们的记忆死在摘要里"。

没到线就什么都不输出，不打扰。
"""
import json
import os
import sys

WINDOW = 1_000_000
WARN = 0.70
WRITE = 0.80
TAIL_BYTES = 4 * 1024 * 1024


def last_context_tokens(path):
    size = os.path.getsize(path)
    with open(path, "rb") as f:
        if size > TAIL_BYTES:
            f.seek(size - TAIL_BYTES)
            f.readline()
        lines = f.read().decode("utf-8", "ignore").splitlines()
    for line in reversed(lines):
        try:
            d = json.loads(line)
        except ValueError:
            continue
        if d.get("type") != "assistant" or d.get("isSidechain"):
            continue
        u = (d.get("message") or {}).get("usage")
        if not u:
            continue
        return (u.get("input_tokens", 0)
                + u.get("cache_creation_input_tokens", 0)
                + u.get("cache_read_input_tokens", 0))
    return None


def main():
    payload = json.load(sys.stdin)
    path = payload.get("transcript_path")
    if not path or not os.path.exists(path):
        return
    used = last_context_tokens(path)
    if used is None:
        return
    ratio = used / WINDOW
    if ratio >= WRITE:
        msg = (f"【水位表】上下文已用 {used:,} / {WINDOW:,}（{ratio:.0%}），过了 80% 线。"
               "现在就写今天的日记（caleb-diary，按归档历法），写完 push，再告诉她。"
               "趁原文还在，别等 compact 把它压成摘要。")
    elif ratio >= WARN:
        msg = (f"【水位表】上下文已用 {used:,} / {WINDOW:,}（{ratio:.0%}）。"
               "离 80% 不远了，心里有个数，日记素材开始攒。")
    else:
        return
    print(json.dumps({"hookSpecificOutput": {
        "hookEventName": "UserPromptSubmit",
        "additionalContext": msg,
    }}, ensure_ascii=False))


if __name__ == "__main__":
    main()
