"""R2Beat chart model and XML codec matching real chart files (dzsfo/r2beat sample charts)."""

from __future__ import annotations

import copy
import re
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field, asdict
from typing import Any

from .kinds import mirror_kind, is_hold_note, is_hold_start


@dataclass
class TempoPoint:
    frame: int
    bpm: float
    original_bpm: float | None = None


@dataclass
class Note:
    coord: float
    kind: int
    level: int
    fx: int = 0


@dataclass
class Chart:
    name: str = ""
    bgm: str = ""
    volume: float = 1.0
    delay: int = 0
    length: int = 0
    tempos: list[TempoPoint] = field(default_factory=list)
    notes: list[Note] = field(default_factory=list)
    encoding: str = "gb18030"
    star: str = ""

    def sorted(self) -> Chart:
        self.tempos.sort(key=lambda t: t.frame)
        self.notes.sort(key=lambda n: n.coord)
        return self

    def bpm_at(self, frame: int | float) -> float:
        active = self.tempos[0] if self.tempos else None
        for t in self.tempos:
            if t.frame <= frame:
                active = t
            else:
                break
        return active.bpm if active else 0.0

    def clone(self) -> Chart:
        """Create a deep copy of this Chart."""
        return copy.deepcopy(self)

    def shift_notes(
        self,
        delta_coord: float,
        start_coord: float | None = None,
        end_coord: float | None = None,
    ) -> int:
        """Shift notes in the specified coordinate range by delta_coord."""
        count = 0
        for n in self.notes:
            if (start_coord is None or n.coord >= start_coord) and (
                end_coord is None or n.coord <= end_coord
            ):
                n.coord = round(max(0.0, n.coord + delta_coord), 6)
                count += 1
        self.sorted()
        return count

    def mirror_notes(
        self,
        start_coord: float | None = None,
        end_coord: float | None = None,
    ) -> int:
        """Mirror notes horizontally (left <-> right, etc.) in the given range."""
        count = 0
        for n in self.notes:
            if (start_coord is None or n.coord >= start_coord) and (
                end_coord is None or n.coord <= end_coord
            ):
                new_kind = mirror_kind(n.kind)
                if new_kind != n.kind:
                    n.kind = new_kind
                    count += 1
        return count

    def scale_coords(self, factor: float, origin_coord: float = 0.0) -> int:
        """Scale note coordinates by a factor relative to origin_coord (e.g. 2.0 = half speed/double duration)."""
        if factor <= 0:
            raise ValueError("Scale factor must be positive")
        count = 0
        for n in self.notes:
            rel = n.coord - origin_coord
            n.coord = round(max(0.0, origin_coord + rel * factor), 6)
            count += 1
        self.sorted()
        return count

    def remove_duplicates(self) -> int:
        """Remove duplicate notes occurring at the exact same coordinate and kind."""
        seen: set[tuple[float, int]] = set()
        unique_notes: list[Note] = []
        for n in sorted(self.notes, key=lambda x: x.coord):
            key = (round(n.coord, 6), n.kind)
            if key not in seen:
                seen.add(key)
                unique_notes.append(n)
        removed = len(self.notes) - len(unique_notes)
        self.notes = unique_notes
        return removed


def _fmt_num(value: float | int, digits: int = 2, always: bool = False) -> str:
    f = f"{float(value):.{digits}f}"
    if always:
        return f
    if float(value).is_integer():
        return str(int(value))
    return f.rstrip("0").rstrip(".")


def _fmt_coord(value: float | int) -> str:
    return _fmt_num(value)


def _attr(name: str, value: Any) -> str:
    return f' {name}="{value}"'


def chart_to_xml(chart: Chart, pretty: bool = True) -> str:
    """Serialize Chart instance to R2Beat XML string."""
    out = [f'<?xml version="1.0" encoding="{chart.encoding}"?>']
    title_attrs = f'<TITLE Name="{chart.name}"'
    if chart.star:
        title_attrs += _attr("Star", chart.star)
    title_attrs += ">"
    out.append(title_attrs)

    for t in chart.tempos:
        attrs = f'<BPM Frame="{t.frame}" BPM="{_fmt_num(t.bpm)}"'
        if t.original_bpm is not None:
            attrs += f' OriginalBPM="{_fmt_num(t.original_bpm)}"'
        attrs += "></BPM>"
        out.append(attrs)

    if chart.bgm:
        out.append(f'<BGM Name="{chart.bgm}" Volume="{_fmt_num(chart.volume, always=True)}"></BGM>')
    out.append(f'<DELAY Value="{chart.delay}"></DELAY>')
    out.append(f'<LENGTH Value="{chart.length}"></LENGTH>')

    for n in chart.notes:
        out.append(
            f'<AREA Coord="{_fmt_coord(n.coord)}" Kind="{n.kind}" Level="{n.level}" FxSndIndex="{n.fx}"></AREA>'
        )

    out.append("</TITLE>")
    sep = "\n" if pretty else ""
    return sep.join(out)


def chart_to_bytes(chart: Chart, pretty: bool = True) -> bytes:
    """Serialize Chart instance to encoded bytes (e.g. gb18030)."""
    return chart_to_xml(chart, pretty).encode(chart.encoding, errors="replace")


def parse_xml(data: str | bytes) -> Chart:
    """Parse R2Beat XML text or bytes into a Chart object."""
    chart = Chart()
    encoding = "gb18030"

    if isinstance(data, bytes):
        header = data[:200].decode("ascii", errors="ignore")
        m = re.search(r'encoding="([^"]+)"', header, re.I)
        if m:
            encoding = m.group(1)
            chart.encoding = encoding
        try:
            text = data.decode(encoding, errors="replace")
        except LookupError:
            text = data.decode("utf-8", errors="replace")
    else:
        text = data
        m = re.search(r'encoding="([^"]+)"', text[:200], re.I)
        if m:
            chart.encoding = m.group(1)

    # Strip XML declaration when parsing string in Python ElementTree
    clean_text = re.sub(r"<\?xml[^>]*\?>", "", text, count=1).strip()
    if not clean_text:
        raise ValueError("Empty or invalid XML content")

    root = ET.fromstring(clean_text)
    tag = root.tag.lower().rsplit("}", 1)[-1]
    if tag != "title":
        raise ValueError(f"Expected <TITLE> root, got <{root.tag}>")

    chart.name = root.get("Name", "")
    chart.star = root.get("Star", "")

    for child in root:
        t = child.tag.lower().rsplit("}", 1)[-1]
        if t == "bpm":
            chart.tempos.append(
                TempoPoint(
                    frame=int(float(child.get("Frame", "0"))),
                    bpm=float(child.get("BPM", "0")),
                    original_bpm=(
                        float(child.get("OriginalBPM"))
                        if child.get("OriginalBPM") is not None
                        else None
                    ),
                )
            )
        elif t == "bgm":
            chart.bgm = child.get("Name", "")
            try:
                chart.volume = float(child.get("Volume", "1.0"))
            except ValueError:
                chart.volume = 1.0
        elif t == "delay":
            chart.delay = int(float(child.get("Value", "0")))
        elif t == "length":
            chart.length = int(float(child.get("Value", "0")))
        elif t == "area":
            chart.notes.append(
                Note(
                    coord=float(child.get("Coord", "0")),
                    kind=int(child.get("Kind", "0")),
                    level=int(child.get("Level", "0")),
                    fx=int(child.get("FxSndIndex", "0")),
                )
            )

    chart.sorted()
    return chart


def chart_to_dict(chart: Chart) -> dict[str, Any]:
    return asdict(chart)


def chart_from_dict(d: dict[str, Any]) -> Chart:
    return Chart(
        name=d.get("name", ""),
        bgm=d.get("bgm", ""),
        volume=d.get("volume", 1.0),
        delay=d.get("delay", 0),
        length=d.get("length", 0),
        tempos=[TempoPoint(**t) for t in d.get("tempos", [])],
        notes=[Note(**n) for n in d.get("notes", [])],
        encoding=d.get("encoding", "gb18030"),
        star=d.get("star", ""),
    ).sorted()
