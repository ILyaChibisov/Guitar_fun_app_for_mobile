# test_cache.py
import sys
sys.path.append('.')
from api.client import api

print(f"Кэш свежий: {api.is_cache_fresh()}")
print(f"Артистов в кэше: {len(api._prefetched_artists)}")
print(f"Песен в кэше: {len(api._prefetched_songs)}")