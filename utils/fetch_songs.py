import json
import urllib.request
import ssl

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

API = "https://guitarfans.ru/api"

# Ввод song_id через терминал
while True:
    raw = input("Введите ID песни (или 'q' для выхода): ").strip()
    if raw.lower() in ("q", "quit", "exit"):
        print("Выход.")
        break
    if not raw.isdigit():
        print("Ошибка: ID должен быть числом. Попробуйте ещё раз.")
        continue

    song_id = int(raw)
    url = f"{API}/songs/tab/{song_id}"
    req = urllib.request.Request(url, headers={"User-Agent": "GuitarFuns/1.0"})

    try:
        with urllib.request.urlopen(req, context=ctx, timeout=15) as r:
            data = json.loads(r.read().decode("utf-8"))
    except Exception as e:
        print(f"Ошибка загрузки песни {song_id}: {e}")
        continue

    filename = f"song_{song_id}.json"
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"Сохранено в {filename}")
    print("=== CONTENT ===")
    print(data.get("content", ""))
