import httpx
from config import downstreams, context_redis, context_prefix
import redis
from sanic.log import logger

async def fetch_idiom_qa(q, uid, idiom=None):
    baseurl = downstreams["idiom_qa"]
    async with httpx.Client() as c:
        param = {"q": q, "uid": uid}
        if idiom:
            param["idiom"] = idiom
        r = await c.get(baseurl, params=param)
        r.encoding = "utf-8"
        logger.info("IdiomQA request: {0}".format(r.url))

        return r.json()

async def fetch_idiom_check(q, uid):
    baseurl = downstreams["idiom_check"]
    async with httpx.Client() as c:
        r = await c.get(baseurl, params={"q": q})
        logger.info("IdiomCheck request: {0}".format(r.url))
        return r.json()

async def fetch_poetry_qa(q, uid, contextual_poem=None):
    baseurl = downstreams["poetry_qa"]
    param = {"q": q}
    if contextual_poem:
        param['context_poem'] = contextual_poem
    async with httpx.Client() as c:
        r = await c.get(baseurl, params=param)
        logger.info("PoetryQA request: {0}".format(r.url))
        return r.json()

async def fetch_idiom_chat(q, uid):
    baseurl = downstreams["idiom_chat"]
    async with httpx.Client() as c:
        r = await c.get(baseurl, params={"query": q})
        logger.info("IdiomChat request: {0}".format(r.url))
        return r.json()

async def fetch_poetry_chat(q, uid):
    baseurl = downstreams["poetry_chat"]
    async with httpx.Client() as c:
        r = await c.get(baseurl, params={"q": q})
        logger.info("PoetryChat request: {0}".format(r.url))
        return r.json()

available_calls = {
    "idiom_qa": fetch_idiom_qa,
    "idiom_check": fetch_idiom_check,
    "idiom_chat": fetch_idiom_chat,
    "poetry_chat": fetch_poetry_chat,
    "poetry_qa": fetch_poetry_qa,
}

async def get_user_context(uid):
    r = redis.StrictRedis(**context_redis)
    hval = r.hgetall(context_prefix + str(uid))
    r.close()
    if hval is None:
        return dict()
    else:
        return hval

async def set_user_context(uid, key, val):
    if val is None:
        logger.debug(f"Ignored empty set for redis: key={key}")
        return

    logger.debug(f"To update redis: key={key}, val={val}")
    r = redis.StrictRedis(**context_redis)
    r.hset(context_prefix + str(uid), key, val)
    r.close()

async def del_user_context(uid, key):
    r = redis.StrictRedis(**context_redis)
    r.hdel(context_prefix + str(uid), key)
    r.close()

async def reset_user_context(uid):
    r = redis.StrictRedis(**context_redis)
    r.delete(context_prefix + str(uid))
    r.close()

async def flush_user_context():
    r = redis.StrictRedis(**context_redis)
    r.flushdb()
    r.close()

