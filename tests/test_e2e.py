import os
import sys
import tempfile
from pathlib import Path

# Add project root to sys.path
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

import server
from r2beat.chart import parse_xml

sid = "test1"
server.CHARTS.clear()

res = server.create_chart(chart_id=sid, name="Test Song", bpm=192, bgm="Test/Test.mp3")
print("create ok:", res["name"], round(res["tempos"][0]["bpm"], 2))

res = server.add_pattern(
    chart_id=sid,
    start_coord=0,
    end_coord=192,
    division=4,
    note_types=["left", "down", "up", "right"],
    strategy="alternate",
    seed=1,
)
print("pattern added:", res["count"])

res = server.add_hold(chart_id=sid, direction="up", start_coord=195, end_coord=243)
print("hold added:", res["count"])

res = server.add_note(chart_id=sid, note_type="ramp", coord=0.5)
print("ramp added")

res = server.set_tempo(chart_id=sid, frame=0, bpm=192)
print("tempo ok")

# Test mirror
res_mirror = server.mirror_chart(chart_id=sid)
print("mirror ok, flipped:", res_mirror["mirrored_count"])

# Test duplicate
res_dup = server.duplicate_chart(source_chart_id=sid, new_chart_id="test1_dup")
print("duplicate ok, notes:", len(res_dup["notes"]))

# Test validation
res = server.validate_chart(sid)
print("validate ok:", res["ok"], "errs:", res["errors"], "warns:", res["warnings"])
print("stats:", res["stats"])
assert res["ok"], f"Validation failed with errors: {res['errors']}"

tmp = os.path.join(tempfile.gettempdir(), "r2beat_test_chart.xml")
res = server.save_chart(sid, tmp)
print("saved:", res.get("saved_to"), "bytes:", res.get("bytes"), "ok:", res["ok"])

with open(tmp, "rb") as f:
    xml_bytes = f.read()
print("--- XML head ---")
print("\n".join(xml_bytes.decode("gb18030").splitlines()[:8]))

parsed = parse_xml(xml_bytes)
print("reload notes:", len(parsed.notes), "name:", parsed.name)
assert len(parsed.notes) > 0
assert parsed.name == "Test Song"

music_tmp = os.path.join(tempfile.gettempdir(), "r2beat_music.txt")
m = server.write_music_entry(sid, music_tmp)
print("entry index:", m["index"])
print("--- entry ---")
print(m["entry"])

if os.path.exists(tmp):
    os.remove(tmp)
if os.path.exists(music_tmp):
    os.remove(music_tmp)

print("ALL OK")
