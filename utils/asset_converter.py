# utils/asset_converter.py
"""
Конвертер изображений в Python-модуль с base64
Сохраняет результат в папку data в корне проекта
"""
import os
import base64
from pathlib import Path
from typing import Dict, Tuple, Optional
from datetime import datetime


class AssetConverter:
    """Конвертирует файлы ассетов в Python модуль внутри папки data"""

    SUPPORTED_EXTENSIONS = {'.png', '.jpg', '.jpeg', '.webp', '.gif'}

    def __init__(self, assets_dir: str = "assets", output_dir: str = "data"):
        self.assets_dir = self._find_assets_dir(assets_dir)
        # НАХОДИМ КОРЕНЬ ПРОЕКТА (где находится main.py)
        self.project_root = self._find_project_root()
        self.output_dir = self.project_root / output_dir
        self.output_file = self.output_dir / "assets.py"
        self.converted_count = 0
        self.errors = []

    def _find_project_root(self) -> Path:
        """Находит корень проекта (где находится main.py или папка assets)"""
        # Начинаем поиск от текущего файла (utils/asset_converter.py)
        current = Path(__file__).parent

        # Поднимаемся вверх, пока не найдём main.py или папку assets
        for parent in [current] + list(current.parents):
            # Проверяем наличие main.py
            if (parent / "main.py").exists():
                print(f"📁 Корень проекта найден: {parent}")
                return parent
            # Проверяем наличие папки assets
            if (parent / "assets").exists():
                print(f"📁 Корень проекта найден: {parent}")
                return parent

        # Если не нашли, возвращаем текущую рабочую директорию
        print(f"📁 Корень проекта: {Path.cwd()}")
        return Path.cwd()

    def _find_assets_dir(self, assets_dir: str) -> Path:
        """Ищет папку assets в разных местах"""
        possible_paths = [
            Path(assets_dir),  # Прямой путь
            Path(__file__).parent.parent / assets_dir,  # На 2 уровня выше (из utils/)
            Path.cwd() / assets_dir,  # Текущая рабочая директория
            Path(__file__).parent / assets_dir,  # В той же папке что и скрипт
        ]

        for path in possible_paths:
            if path.exists() and path.is_dir():
                print(f"✅ Найдена папка ассетов: {path}")
                return path

        # Если не найдена, создаём в корне проекта
        root_assets = self._find_project_root() / assets_dir
        print(f"📁 Папка {assets_dir} не найдена, создаём: {root_assets}")
        root_assets.mkdir(parents=True, exist_ok=True)

        # Создаём пример изображения для демонстрации
        self._create_sample_asset(root_assets)

        return root_assets

    def _create_sample_asset(self, assets_path: Path):
        """Создаёт пример изображения, если папка пустая"""
        try:
            from PIL import Image, ImageDraw

            # Создаём простой градиентный фон
            img = Image.new('RGB', (800, 1280), color=(118, 179, 182))
            draw = ImageDraw.Draw(img)

            # Рисуем текст
            draw.text((400, 640), "GuitarFuns", fill=(255, 255, 255))

            # Сохраняем
            bg_path = assets_path / 'background.jpg'
            img.save(bg_path)
            print(f"🎨 Создан пример фона: {bg_path}")

        except ImportError:
            # Если PIL нет, создаём простой текстовый файл-заглушку
            readme_path = assets_path / 'README.txt'
            with open(readme_path, 'w') as f:
                f.write("Положите сюда ваши изображения:\n")
                f.write("- background.jpg (фон главного экрана)\n")
                f.write("- icon.png (иконка приложения)\n")
                f.write("- logo.png (логотип)\n")
            print(f"📄 Создан README: {readme_path}")
            print("⚠️ Установите Pillow для автоматического создания примера: pip install Pillow")

    def _ensure_output_dir(self):
        """Создаёт папку data и файл __init__.py если нужно"""
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Создаём __init__.py если его нет
        init_file = self.output_dir / "__init__.py"
        if not init_file.exists():
            with open(init_file, 'w', encoding='utf-8') as f:
                f.write('"""\nПакет данных приложения\nСодержит сконвертированные ассеты и другие данные\n"""\n\n')
                f.write('from .assets import Assets, load_asset_as_bytes, load_asset_as_base64\n\n')
                f.write('__all__ = ["Assets", "load_asset_as_bytes", "load_asset_as_base64"]\n')
            print(f"📦 Создан файл: {self.output_dir}/__init__.py")

    def scan_assets(self) -> Dict:
        """Сканирует папку assets и возвращает словарь {имя: данные}"""
        assets = {}

        if not self.assets_dir.exists():
            raise FileNotFoundError(f"Папка {self.assets_dir} не найдена")

        # Получаем список всех файлов
        all_files = list(self.assets_dir.rglob("*"))

        if not all_files:
            print(f"⚠️ Папка {self.assets_dir} пуста")
            print(f"📌 Положите изображения в: {self.assets_dir}")
            return assets

        print("\n📸 Найденные изображения:")
        for file_path in all_files:
            if file_path.is_file() and file_path.suffix.lower() in self.SUPPORTED_EXTENSIONS:
                # Создаём уникальное имя для переменной
                rel_path = file_path.relative_to(self.assets_dir)
                var_name = str(rel_path).replace('\\', '/').replace('/', '_').replace('.', '_')

                # Определяем MIME тип
                mime_type = self._get_mime_type(file_path.suffix)

                # Читаем и конвертируем в base64
                with open(file_path, 'rb') as f:
                    data = f.read()

                # Пытаемся получить размеры изображения
                width, height = self._get_image_size(data)

                assets[var_name] = {
                    'name': var_name,
                    'original_path': str(rel_path),
                    'mime_type': mime_type,
                    'size': len(data),
                    'base64': base64.b64encode(data).decode('ascii'),
                    'extension': file_path.suffix[1:],
                    'width': width,
                    'height': height
                }
                self.converted_count += 1

                # Выводим информацию о файле
                size_kb = len(data) / 1024
                dims = f" {width}x{height}" if width else ""
                print(f"   📸 {rel_path} -> {var_name} ({size_kb:.1f} KB{dims})")

        return assets

    def _get_image_size(self, data: bytes) -> Tuple[Optional[int], Optional[int]]:
        """Пытается получить размеры изображения без PIL"""
        try:
            # Простой парсинг PNG
            if data[:8] == b'\x89PNG\r\n\x1a\n':
                width = int.from_bytes(data[16:20], 'big')
                height = int.from_bytes(data[20:24], 'big')
                return width, height
            # Простой парсинг JPEG
            elif data[:2] == b'\xff\xd8':
                i = 2
                while i < len(data) - 1:
                    if data[i] != 0xFF:
                        i += 1
                        continue
                    marker = data[i + 1]
                    if marker == 0xC0 or marker == 0xC2:
                        height = int.from_bytes(data[i + 5:i + 7], 'big')
                        width = int.from_bytes(data[i + 7:i + 9], 'big')
                        return width, height
                    i += 2 + int.from_bytes(data[i + 2:i + 4], 'big')
        except:
            pass
        return None, None

    def _get_mime_type(self, ext: str) -> str:
        """Возвращает MIME тип по расширению"""
        mime_map = {
            '.png': 'image/png',
            '.jpg': 'image/jpeg',
            '.jpeg': 'image/jpeg',
            '.webp': 'image/webp',
            '.gif': 'image/gif'
        }
        return mime_map.get(ext.lower(), 'application/octet-stream')

    def generate_module(self, assets: Dict) -> str:
        """Генерирует содержимое Python модуля"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        lines = [
            '# -*- coding: utf-8 -*-',
            '"""',
            'Автоматически сгенерированный модуль ассетов',
            f'Создан: {timestamp}',
            f'Всего ассетов: {len(assets)}',
            '',
            'Использование:',
            '    from data import Assets, load_asset_as_bytes',
            '    ',
            '    # Получить изображение как bytes',
            '    data = load_asset_as_bytes("background_jpg")',
            '    ',
            '    # Получить base64 строку',
            '    b64 = Assets.get_base64("background_jpg")',
            '"""',
            '',
            'import base64',
            'from typing import Dict, Optional',
            'from io import BytesIO',
            '',
            '# Пытаемся импортировать Kivy (если есть)',
            'try:',
            '    from kivy.core.image import Image as CoreImage',
            '    from kivy.uix.image import Image',
            '    KIVY_AVAILABLE = True',
            'except ImportError:',
            '    KIVY_AVAILABLE = False',
            '',
            '',
            '# ============ БИНАРНЫЕ ДАННЫЕ АССЕТОВ ============',
            '',
        ]

        # Добавляем каждое изображение как отдельную переменную
        for var_name, asset in assets.items():
            lines.append(f'# {asset["original_path"]} ({asset["size"]} bytes)')
            if asset.get('width'):
                lines.append(f'# Размер: {asset["width"]}x{asset["height"]}')
            lines.append(f'_{var_name}_BASE64 = """{asset["base64"]}"""')
            lines.append(f'_{var_name}_MIME = "{asset["mime_type"]}"')
            lines.append('')

        # Добавляем словарь для лёгкого доступа
        lines.append('')
        lines.append('# ============ СЛОВАРЬ АССЕТОВ ============')
        lines.append('')
        lines.append('ASSETS_METADATA = {')

        for var_name, asset in assets.items():
            lines.append(f'    "{var_name}": {{')
            lines.append(f'        "original": "{asset["original_path"]}",')
            lines.append(f'        "mime": "{asset["mime_type"]}",')
            lines.append(f'        "size": {asset["size"]},')
            lines.append(f'        "ext": "{asset["extension"]}",')

            if asset.get('width'):
                lines.append(f'        "width": {asset["width"]},')
                lines.append(f'        "height": {asset["height"]},')

            lines.append('    },')

        lines.append('}')
        lines.append('')

        # Добавляем класс для работы с ассетами
        lines.extend([
            '',
            'class Assets:',
            '    """Класс для доступа к встроенным ассетам"""',
            '    ',
            '    @staticmethod',
            '    def get_image_data(name: str) -> Optional[bytes]:',
            '        """Возвращает бинарные данные изображения по имени"""',
            '        var_name = f"_{name}_BASE64"',
            '        if var_name in globals():',
            '            return base64.b64decode(globals()[var_name])',
            '        return None',
            '    ',
            '    @staticmethod',
            '    def get_base64(name: str) -> Optional[str]:',
            '        """Возвращает base64 строку изображения"""',
            '        var_name = f"_{name}_BASE64"',
            '        return globals().get(var_name)',
            '    ',
            '    @staticmethod',
            '    def list_assets() -> list:',
            '        """Возвращает список всех доступных ассетов"""',
            '        return list(ASSETS_METADATA.keys())',
            '    ',
            '    @staticmethod',
            '    def get_metadata(name: str) -> Optional[dict]:',
            '        """Возвращает метаданные ассета"""',
            '        return ASSETS_METADATA.get(name)',
            '',
        ])

        # Добавляем Kivy-методы
        lines.extend([
            '    @staticmethod',
            '    def get_kivy_image(name: str):',
            '        """Возвращает Kivy Image объект из ассета"""',
            '        if not KIVY_AVAILABLE:',
            '            return None',
            '        data = Assets.get_image_data(name)',
            '        if data:',
            '            return Image(source=data, ext="png")',
            '        return None',
            '    ',
            '    @staticmethod',
            '    def get_kivy_core_image(name: str):',
            '        """Возвращает Kivy CoreImage объект"""',
            '        if not KIVY_AVAILABLE:',
            '            return None',
            '        data = Assets.get_image_data(name)',
            '        if data:',
            '            return CoreImage(BytesIO(data), ext="png")',
            '        return None',
            '',
        ])

        # Добавляем удобные переменные для каждого ассета
        lines.extend([
            '',
            '# ============ КОНКРЕТНЫЕ АССЕТЫ ДЛЯ УДОБСТВА ============',
            '',
        ])

        for var_name in assets.keys():
            const_name = f'ASSET_{var_name.upper()}'
            lines.append(f'{const_name} = "{var_name}"')

        lines.extend([
            '',
            '',
            'def load_asset_as_bytes(name: str) -> Optional[bytes]:',
            '    """Загружает ассет как bytes"""',
            '    return Assets.get_image_data(name)',
            '',
            '',
            'def load_asset_as_base64(name: str) -> Optional[str]:',
            '    """Загружает ассет как base64 строку"""',
            '    return Assets.get_base64(name)',
            '',
        ])

        return '\n'.join(lines)

    def convert(self) -> bool:
        """Выполняет конвертацию"""
        print("=" * 50)
        print("🖼️  КОНВЕРТЕР АССЕТОВ")
        print("=" * 50)
        print(f"📁 Исходная папка: {self.assets_dir}")
        print(f"📦 Выходная папка: {self.output_dir}")
        print(f"📄 Выходной файл: {self.output_file}")

        try:
            # Создаём папку data
            self._ensure_output_dir()

            # Сканируем ассеты
            assets = self.scan_assets()

            if not assets:
                print(f"\n⚠️ Не найдено изображений в {self.assets_dir}")
                print(f"\n📌 Инструкция:")
                print(f"   1. Положите изображения в папку: {self.assets_dir}")
                print(f"   2. Поддерживаются форматы: {', '.join(self.SUPPORTED_EXTENSIONS)}")
                print(f"   3. Запустите скрипт снова")
                return False

            # Генерируем модуль
            content = self.generate_module(assets)

            # Сохраняем
            with open(self.output_file, 'w', encoding='utf-8') as f:
                f.write(content)

            # Выводим статистику
            total_size = sum(a['size'] for a in assets.values())
            print(f"\n✅ Конвертация завершена!")
            print(f"   📁 Выходной файл: {self.output_file.absolute()}")
            print(f"   🖼️  Ассетов: {self.converted_count}")
            print(f"   💾 Исходный размер: {total_size / 1024:.2f} KB")
            print(f"   📦 Размер модуля: {len(content) / 1024:.2f} KB")

            print(f"\n💡 Использование в коде:")
            print(f"   from data import Assets, load_asset_as_bytes")
            print(f"   data = load_asset_as_bytes('background_jpg')")

            return True

        except Exception as e:
            print(f"❌ Ошибка конвертации: {e}")
            import traceback
            traceback.print_exc()
            return False


def main():
    """Запуск конвертера из командной строки"""
    import argparse

    parser = argparse.ArgumentParser(description="Конвертер ассетов в Python модуль")
    parser.add_argument("--assets-dir", default="assets", help="Папка с исходными ассетами")
    parser.add_argument("--output-dir", default="data", help="Выходная папка (по умолчанию: data)")

    args = parser.parse_args()

    converter = AssetConverter(
        assets_dir=args.assets_dir,
        output_dir=args.output_dir
    )

    success = converter.convert()

    if not success:
        print("\n💡 Совет: Установите Pillow для лучшей обработки изображений:")
        print("   pip install Pillow")

    return 0 if success else 1


if __name__ == "__main__":
    exit(main())