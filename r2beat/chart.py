"""R2Beat chart model and XML codec matching real chart files (dzsfo/r2beat sample charts)."""

from dataclasses import dataclass, field, asdict


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

    def sorted(self):
        self.tempos.sort(key=lambda t: t.frame)
        self.notes.sort(key=lambda n: n.coord)
        return self

    def bpm_at(self, frame):
        active = self.tempos[0] if self.tempos else None
        for t in self.tempos:
            if t.frame <= frame:
                active = t
            else:
                break
        return active.bpm if active else 0.0


def _fmt_num(value, digits=2, always=False):
    f = f"{float(value):.{digits}f}"
    if always:
        return f
    if float(value).is_integer():
        return str(int(value))
    return f.rstrip("0").rstrip(".")


def _fmt_coord(value):
    return _fmt_num(value)


def _attr(name, value):
    return f' {name}="{value}"'


def chart_to_xml(chart, pretty=True):
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
    out.append(f"<LENGTH Value=\"{chart.length}\"></LENGTH>")
    for n in chart.notes:
        out.append(
            f'<AREA Coord="{_fmt_coord(n.coord)}" Kind="{n.kind}" Level="{n.level}" FxSndIndex="{n.fx}"></AREA>'
        )
    out.append("</TITLE>")
    sep = "\n" if pretty else ""
    return sep.join(out)


def chart_to_bytes(chart, pretty=True):
    return chart_to_xml(chart, pretty).encode(chart.encoding, errors="replace")


def parse_xml(text):
    chart = Chart()
    if text.startswith("<?xml"):
        import re

        m = re.search(r"encoding=\"([^\"]+)\"", text)
        if m:
            chart.encoding = m.group(1)
    import xml.etree.ElementTree as ET

    root = ET.fromstring(text)
    tag = root.tag.lower().rsplit("}", 1)[-1]
    if tag != "title":
        raise ValueError(f"Expected <TITLE> root, got <{root.tag}>")
    chart.name = root.get("Name", "")
    chart.star = root.get("Star", "")
    for child in root:
        t = child.tag.lower().rsplit("}", 1)[-1]
        if t in ("bpm",):
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


def chart_to_dict(chart):
    d = asdict(chart)
    return d


def chart_from_dict(d):
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