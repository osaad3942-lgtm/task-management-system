# app/core/redis_client.py
import redis
import json
import os

redis_host = os.getenv("REDIS_HOST", "localhost")
redis_port = int(os.getenv("REDIS_PORT", 6379))

try:
    r = redis.Redis(host=redis_host, port=redis_port, db=0,
                    decode_responses=True, socket_connect_timeout=1)
    r.ping()  # Test connection at startup
    REDIS_AVAILABLE = True
except Exception:
    r = None
    REDIS_AVAILABLE = False


def get_cache(key):
    if not REDIS_AVAILABLE or r is None:
        return None
    try:
        data = r.get(key)
        return json.loads(data) if data else None
    except Exception:
        return None


def set_cache(key, value, expire=60):
    if not REDIS_AVAILABLE or r is None:
        return
    try:
        r.set(key, json.dumps(value, default=str), ex=expire)
    except Exception:
        pass


def delete_cache(key):
    if not REDIS_AVAILABLE or r is None:
        return
    try:
        r.delete(key)
    except Exception:
        pass