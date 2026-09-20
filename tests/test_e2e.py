import tempfile
import os

import server
from r2beat.chart import parse_xml

sid = "test1"
server.CHARTS.clear()

res = server.create_chart(chart_id=sid, name="Test Song", bpm=192, bgm="Test/Test.mp3")
print("create ok:", res["name"], round(res["tempos"][0]["bpm"], 2))

res = server.add_pattern(chart_id=sid, start_coord=0, end_coord=192, division=4,
                         note_types=["left", "down", "up", "right"], strategy="alternate", seed=1)
print("pattern added:", res["count"])

res = server.add_hold(chart_id=sid, direction="up", start_coord=195, end_coord=243)
print("hold added:", res["count"])

res = server.add_note(chart_id=sid, note_type="ramp", coord=0.5)
print("ramp added")

res = server.set_tempo(chart_id=sid, frame=0, bpm=192)
print("tempo ok")

res = server.validate_chart(sid)
print("validate ok:", res["ok"], "errs:", res["errors"], "warns:", res["warnings"])
print("stats:", res["stats"])

tmp = os.path.join(tempfile.gettempdir(), "r2beat_test_chart.xml")
res = server.save_chart(sid, tmp)
print("saved:", res.get("saved_to"), "bytes:", res.get("bytes"), "ok:", res["ok"])

with open(tmp, encoding="gb18030") as f:
    xml = f.read()
print("--- XML head ---")
print("\n".join(xml.splitlines()[:8]))

parsed = parse_xml(xml)
print("reload notes:", len(parsed.notes), "name:", parsed.name)

m = server.write_music_entry(sid, os.path.join(tempfile.gettempdir(), "r2beat_music.txt"))
print("entry index:", m["index"])
print("--- entry ---")
print(m["entry"])
os.remove(tmp)
os.remove(os.path.join(tempfile.gettempdir(), "r2beat_music.txt"))
print("ALL OK")