# check_folders.py
import os

chords_path = "chords"
print("Папки в chords:")
for item in os.listdir(chords_path):
    full_path = os.path.join(chords_path, item)
    if os.path.isdir(full_path) and not item.startswith('__'):
        print(f"  - {item}")