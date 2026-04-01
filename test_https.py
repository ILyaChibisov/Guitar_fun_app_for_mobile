
import requests
import os
import sys

# Путь к CA bundle
ca_bundle = 'certs/ca_bundle.pem'

if os.path.exists(ca_bundle):
    print(f'✅ CA bundle найден: {ca_bundle}')
    verify = ca_bundle
else:
    print('⚠️ CA bundle не найден, используем certifi')
    import certifi
    verify = certifi.where()

print('Тестируем HTTPS соединение...')
try:
    response = requests.get(
        'https://guitarfans.ru/api/songs/artists/А',
        verify=verify,
        timeout=10
    )
    print(f'✅ Статус: {response.status_code}')
    data = response.json()
    artists = data.get('artists', [])
    print(f'Найдено исполнителей: {len(artists)}')
    if artists:
        print(f'Первые 3 исполнителя:')
        for artist in artists[:3]:
            print(f'  - {artist}')
    print('\n✅ HTTPS работает отлично!')
except Exception as e:
    print(f'❌ Ошибка: {e}')
