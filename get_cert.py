# get_cert.py
import ssl
import socket
import os


def get_server_certificate(hostname, port=443):
    """Получает сертификат с сервера"""
    context = ssl.create_default_context()

    with socket.create_connection((hostname, port), timeout=10) as sock:
        with context.wrap_socket(sock, server_hostname=hostname) as ssock:
            # Получаем сертификат в PEM формате
            cert_der = ssock.getpeercert(binary_form=True)
            cert_pem = ssl.DER_cert_to_PEM_cert(cert_der)
            return cert_pem


# Создаем папку если её нет
os.makedirs('certs', exist_ok=True)

print("🔍 Получаем сертификат с guitarfans.ru...")
try:
    cert_pem = get_server_certificate("guitarfans.ru")

    # Сохраняем сертификат
    cert_path = os.path.join('certs', 'guitarfans.crt')
    with open(cert_path, 'w') as f:
        f.write(cert_pem)

    print(f"✅ Сертификат сохранен: {cert_path}")
    print("\n📋 Информация о сертификате:")

    # Показываем информацию
    import OpenSSL

    cert = OpenSSL.crypto.load_certificate(OpenSSL.crypto.FILETYPE_PEM, cert_pem)
    print(f"   Issuer: {cert.get_issuer().CN}")
    print(f"   Subject: {cert.get_subject().CN}")

except Exception as e:
    print(f"❌ Ошибка: {e}")
    print("\n📌 Альтернативный способ:")
    print("1. Откройте браузер и перейдите на https://guitarfans.ru")
    print("2. Нажмите на замок в адресной строке")
    print("3. Выберите 'Сертификат' → 'Подробно' → 'Копировать в файл'")
    print("4. Сохраните как certs/guitarfans.crt")