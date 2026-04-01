# create_bundle.py
import os
import certifi

# Создаем папку если нет
os.makedirs('certs', exist_ok=True)

# Путь к нашему сертификату
guitarfans_cert = os.path.join('certs', 'guitarfans.crt')
# Путь к объединенному файлу
combined = os.path.join('certs', 'ca_bundle.pem')

print("🔍 Проверяем наличие сертификата...")
if os.path.exists(guitarfans_cert):
    print(f"✅ Найден сертификат: {guitarfans_cert}")

    # Копируем системные сертификаты
    print("📋 Копируем системные сертификаты...")
    with open(certifi.where(), 'r') as src:
        system_certs = src.read()

    # Читаем наш сертификат
    with open(guitarfans_cert, 'r') as src:
        our_cert = src.read()

    # Объединяем
    print("📦 Создаем объединенный файл...")
    with open(combined, 'w') as dst:
        dst.write(system_certs)
        dst.write('\n')
        dst.write(our_cert)

    print(f"✅ Создан файл: {combined}")
    print(f"📏 Размер: {os.path.getsize(combined)} байт")

    # Проверяем содержимое
    with open(combined, 'r') as f:
        content = f.read()
        if "BEGIN CERTIFICATE" in content:
            print("✅ Файл содержит корректные сертификаты")
else:
    print(f"❌ Сертификат не найден: {guitarfans_cert}")
    print("Запустите get_cert.py еще раз")