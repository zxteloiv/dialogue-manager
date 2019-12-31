import httpx
from config import downstreams

async def fetch_idiom_qa(q, uid):
    baseurl = downstreams["idiom_qa"]
    async with httpx.Client() as c:
        r = await c.get(baseurl, params={"q": q, "uid": uid})
        r.encoding = "utf-8"
        return r.text

async def fetch_poetry_qa(q, uid):
    baseurl = downstreams["poetry_qa"]
    async with httpx.Client() as c:
        r = await c.get(baseurl, params={"q": q})
        return r.json()

async def fetch_idiom_chat(q, uid):
    baseurl = downstreams["idiom_chat"]
    async with httpx.Client() as c:
        r = await c.get(baseurl, params={"query": q})
        return r.json()

async def fetch_poetry_chat(q, uid):
    baseurl = downstreams["poetry_chat"]
    async with httpx.Client() as c:
        r = await c.get(baseurl, params={"q": q})
        return r.json()

available_calls = {
    "idiom_qa": fetch_idiom_qa,
    "idiom_chat": fetch_idiom_chat,
    "poetry_chat": fetch_poetry_chat,
    "poetry_qa": fetch_poetry_qa,
}
