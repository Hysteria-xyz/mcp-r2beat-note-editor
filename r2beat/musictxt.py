"""Read/write R2Beat rnr_script/music.txt entries and per-song .txt files."""

from __future__ import annotations

import os
import re
from typing import Any


def format_entry(
    index: int | str,
    name: str,
    image: str,
    file: str,
    level: int | str,
    genre: str,
    artist: str = "",
    coin: str = "0",
    single_line: bool = False,
    self_closing: bool = False,
) -> str:
    """Format a <Music> entry XML element for music.txt."""
    attrs = [
        f'Index="{index}"',
        f'Name="{name}"',
        f'Image="{image}"',
        f'File="{file}"',
        f'Level="{level}"',
        f'Genre="{genre}"',
        f'Artist="{artist}"',
    ]
    if coin is not None:
        attrs.append(f'Coin="{coin}"')

    if single_line:
        inner = " ".join(attrs)
        return f"<Music {inner}></Music>" if not self_closing else f"<Music {inner}/>"

    body = "<Music\n" + "\n".join(f"\t{attr}" for attr in attrs) + "\n"
    if self_closing:
        return body + "/>"
    return body + "></Music>"


def parse_entries(text: str) -> list[dict[str, str]]:
    """Extract list of attribute dictionaries for all <Music> elements in text."""
    entries: list[dict[str, str]] = []
    for m in re.finditer(r"<Music\b([^>]*?)/?>", text, re.S):
        attrs = dict(re.findall(r'([\w]+)="([^"]*)"', m.group(1)))
        if attrs:
            entries.append(attrs)
    return entries


def append_entry(path: str, entry_text: str, encoding: str = "gb18030") -> None:
    """Append a <Music> entry to music.txt, creating header if the file is new."""
    dir_name = os.path.dirname(os.path.abspath(path))
    if dir_name:
        os.makedirs(dir_name, exist_ok=True)

    file_exists = os.path.exists(path)
    file_size = os.path.getsize(path) if file_exists else 0

    with open(path, "ab" if file_exists else "wb") as f:
        if file_size == 0:
            header = f'<?xml version="1.0" encoding="{encoding}" ?>\n'.encode(encoding)
            f.write(header)
        else:
            f.write(b"\n")
        f.write(entry_text.encode(encoding, errors="replace"))


def read_next_index(path: str, base: int = 0) -> int:
    """Read music.txt and return the next available Index integer (max + 1)."""
    if not os.path.exists(path):
        return base
    with open(path, "rb") as f:
        raw = f.read()
    text = raw.decode("gb18030", errors="ignore")
    max_idx = base
    for attrs in parse_entries(text):
        try:
            max_idx = max(max_idx, int(attrs.get("Index", "0")))
        except ValueError:
            pass
    return max_idx + 1


def find_entry_by_name(path: str, name: str) -> dict[str, str] | None:
    """Search music.txt for an entry matching the song name."""
    if not os.path.exists(path):
        return None
    with open(path, "rb") as f:
        raw = f.read()
    text = raw.decode("gb18030", errors="ignore")
    for attrs in parse_entries(text):
        if attrs.get("Name", "").strip().lower() == name.strip().lower():
            return attrs
    return None


def path_for_chart(chart_path: str, music_root: str = "rnr_music") -> str:
    """Strip music root directory prefix for clean music.txt file references."""
    p = chart_path.replace("\\", "/")
    if p.startswith(music_root + "/"):
        return p[len(music_root) + 1 :]
    return p
