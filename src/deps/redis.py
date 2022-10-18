import redis


def get_session_redis():
    r = redis.Redis(host="localhost", port=6379, db=0)
    try:
        yield r
    finally:
        r.close()
