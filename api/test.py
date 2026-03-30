import requests
import json

# Отключаем проверку сертификата (только для теста!)
response = requests.get("https://guitarfans.ru/api/songs/artists/А", verify=False)
print(f"Status: {response.status_code}")
print(f"Content: {response.text}")
print(f"JSON: {response.json()}")