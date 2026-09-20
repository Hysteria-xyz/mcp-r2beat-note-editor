"""Read/write R2Beat rnr_script/music.txt entries and per-song .txt files."""

import os
import re


def format_entry(
    index,
    name,
    image,
    file,
    level,
    genre,
    artist,
    coin="0",
    single_line=False,
    self_closing=False,
):
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


def parse_entries(text):
    entries = []
    for m in re.finditer(r"<Music\b([^>]*?)/?>", text, re.S):
        attrs = dict(re.findall(r'([\w]+)="([^"]*)"', m.group(1)))
        entries.append(attrs)
    return entries


def append_entry(path, entry_text, encoding="gb18030"):
    mode = "ab" if os.path.exists(path) else "wb"
    with open(path, mode) as f:
        if os.path.getsize(path) == 0:
            f.write(f'<?xml version="1.0" encoding="{encoding}" ?>\n'.encode(encoding))
        if not f.tell() == 0 and os.path.getsize(path) > 0:
            f.write(b"\n")
        f.write(entry_text.encode(encoding))


def read_next_index(path, base=0):
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


def path_for_chart(chart_path, music_root="rnr_music"):
    p = chart_path.replace("\\", "/")
    if p.startswith(music_root + "/"):
        return p[len(music_root) + 1 :]
    return p