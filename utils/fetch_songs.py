import json
import urllib.request
import ssl

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

API = "https://guitarfans.ru/api"
song_id = 153371

url = f"{API}/songs/tab/{song_id}"
req = urllib.request.Request(url, headers={"User-Agent": "GuitarFuns/1.0"})

with urllib.request.urlopen(req, context=ctx, timeout=15) as r:
    data = json.loads(r.read().decode("utf-8"))

with open(f"song_{song_id}.json", "w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

print(f"Сохранено в song_{song_id}.json")
print("=== CONTENT ===")
print(data.get("content", ""))

# Диагностика проблемных строк
from chord_utils.chord_parser import is_chord_line, CHORD_PATTERN

print("\n=== ДИАГНОСТИКА ===")
for i, line in enumerate(data.get("content", "").splitlines()):
    if "C#" in line or "С#" in line:
        print(f"Строка {i}: {repr(line)}")
        print(f"  is_chord_line: {is_chord_line(line)}")
        print(f"  matches: {CHORD_PATTERN.findall(line)}")