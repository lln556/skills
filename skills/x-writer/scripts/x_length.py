# /// script
# requires-python = ">=3.10"
# ///
"""按 X（推特）的权重规则计算推文长度。

规则（twitter-text v3）：常见拉丁、标点等区间的字符算 1，其余（中日韩、emoji 等）算 2；
链接一律按 23 算；普通账号上限 280。

用法：
    uv run scripts/x_length.py 稿子.md          # 按行首 `1/`、`2/` 分段，逐条计数
    uv run scripts/x_length.py --text "一条推文"
"""

from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass
from pathlib import Path

LIMIT = 280
URL_WEIGHT = 23
LIGHT_RANGES = ((0, 4351), (8192, 8205), (8208, 8223), (8242, 8247))
URL_RE = re.compile(r"https?://\S+")
TWEET_HEAD_RE = re.compile(r"^(\d+)/\s*$", re.MULTILINE)


@dataclass(frozen=True)
class TweetLength:
    label: str
    weight: int

    @property
    def over(self) -> bool:
        return self.weight > LIMIT


def char_weight(ch: str) -> int:
    code = ord(ch)
    return 1 if any(lo <= code <= hi for lo, hi in LIGHT_RANGES) else 2


def weighted_length(text: str) -> int:
    text = text.strip()
    urls = URL_RE.findall(text)
    stripped = URL_RE.sub("", text)
    return sum(char_weight(c) for c in stripped) + URL_WEIGHT * len(urls)


def split_thread(doc: str) -> list[tuple[str, str]]:
    """按行首的 `1/`、`2/` 切分推文串；没有编号时整篇当一条。"""
    marks = list(TWEET_HEAD_RE.finditer(doc))
    if not marks:
        return [("全文", doc)]
    parts = []
    for i, m in enumerate(marks):
        end = marks[i + 1].start() if i + 1 < len(marks) else len(doc)
        body = doc[m.end():end]
        body = re.split(r"\n#{1,6} |\n---", body)[0]  # 截掉推文串之后的其他章节
        parts.append((f"{m.group(1)}/", body))
    return parts


def measure(doc: str) -> list[TweetLength]:
    return [TweetLength(label, weighted_length(body)) for label, body in split_thread(doc)]


def main() -> int:
    parser = argparse.ArgumentParser(description="按 X 规则计算推文长度")
    parser.add_argument("file", nargs="?", type=Path, help="稿子文件，按 1/ 2/ 分段")
    parser.add_argument("--text", help="直接计算一段文字")
    args = parser.parse_args()

    if args.text is not None:
        doc = args.text
    elif args.file is not None:
        doc = args.file.read_text(encoding="utf-8")
    else:
        parser.error("需要文件路径或 --text")

    results = measure(doc)
    for r in results:
        flag = "  超出！" if r.over else ""
        print(f"{r.label:>4} {r.weight:>4}/{LIMIT}{flag}")
    return 1 if any(r.over for r in results) else 0


if __name__ == "__main__":
    sys.exit(main())
