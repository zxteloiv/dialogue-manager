from sanic.log import error_logger, logger
from fetch_downstream import available_calls as ifs
from fetch_downstream import get_user_context, set_user_context, del_user_context
from fetch_downstream import reset_user_context, flush_user_context

# Idiom Chat Score distribution statistics
# count    9785.000000
# mean        1.136265
# std         2.027109
# min        -2.515888
# 25%        -0.279774
# 50%         0.262128
# 75%         2.159774
# max        11.337482
#
# Poetry Chat Score distribution statistics
# count    10000.000000
# mean         0.591908
# std          0.384050
# min          0.005458
# 25%          0.020329
# 50%          0.825712
# 75%          0.849618
# max          0.995685
#

def normalize_response_score(x, ifname: str):
    if ifname == "idiom_chat":
        mean, std = 1.136265, 2.027109
    elif ifname == "poetry_chat":
        mean, std = 0.591908, 0.384050
    else:
        raise ValueError("Required interface not found.")

    return (float(x) - mean) / std

def to_valid_text(s):
    if not isinstance(s, str):
        return None

    if len(s) > 0:
        return s

    return None

async def _get_poetry_qa(q, uid, ctx):
    try:
        poetry_qa = await ifs["poetry_qa"](q, uid, ctx.get('poem'))
        poetry_text = to_valid_text(poetry_qa.get('answer'))
        return poetry_text, "poem", to_valid_text(poetry_qa.get('key_text'))

    except Exception as e:
        error_logger.error('PoetryQA request failed: {0}'.format(e))

    return None, None, None

async def _get_idiom_qa(q, uid, ctx):
    try:
        idiom_qa = await ifs["idiom_qa"](q, uid, ctx.get('idiom'))
        idiom_text = to_valid_text(idiom_qa.get('text'))
        return idiom_text, "idiom", to_valid_text(idiom_qa.get('idiom'))

    except Exception as e:
        error_logger.error('IdiomQA request failed: {0}'.format(e))

    return None, None, None

async def _get_qa_answer(q, uid):
    ctx = await get_user_context(uid)

    # QA priority check
    idiom = ctx.get('idiom')
    call_seq = [_get_idiom_qa, _get_poetry_qa]
    if idiom is None:
        call_seq = list(reversed(call_seq))

    # try each interface in the sequence order
    for call in call_seq:
        res = await call(q, uid, ctx)
        if res[0] is not None:
            return res

    return None, None, None

async def _get_idiom_in_text(q, uid):
    try:
        res = await ifs["idiom_check"](q, uid)
        return res.get('idiom')
    except Exception as e:
        error_logger.error('IdiomCheck request failed: {0}'.format(e))
        return None

async def _get_poetry_chat(q, uid, ctx):
    # try both poetry and idiom chat
    try:
        poetry_chat = await ifs["poetry_chat"](q, uid)
        poetry_text = poetry_chat["candidates"][0]["poem_mandarin"]
        poetry_score = poetry_chat["candidates"][0]["score"]
        poetry_score = normalize_response_score(poetry_score, "poetry_chat")
        poetry_key = to_valid_text(poetry_chat['candidates'][0]['poem'])
        return poetry_text, poetry_score, poetry_key

    except Exception as e:
        error_logger.error('PoetryChat request failed: {0}'.format(e))
        return None, None, None


async def _get_idiom_chat(q, uid, ctx):
    try:
        idiom_chat = await ifs["idiom_chat"](q, uid)
        idiom_text = idiom_chat["rank"][0][0]
        idiom_score = idiom_chat["rank"][0][1]
        idiom_score = normalize_response_score(idiom_score, "idiom_chat")
        idiom_key = await _get_idiom_in_text(idiom_text, uid)
        return idiom_text, idiom_score, idiom_key

    except Exception as e:
        error_logger.error('IdiomChat request failed: {0}'.format(e))
        return None, None, None

async def _get_chat_answer(q, uid):
    """
    :param q:
    :param uid:
    :return: Tuple[answer text, update context key, update context val]
    """
    ctx = await get_user_context(uid)
    poetry_text, poetry_score, poetry_key = await _get_poetry_chat(q, uid, ctx)
    idiom_text, idiom_score, idiom_key = await _get_idiom_chat(q, uid, ctx)

    if poetry_text and idiom_text:
        final = "idiom_chat" if idiom_score >= poetry_score else "poetry_chat"
    elif poetry_text:
        final = "poetry_chat"
    elif idiom_text:
        final = "idiom_chat"
    else:
        return None, None, None

    logger.info(f"final answer chosen={final} "
                f"poetry_score={poetry_score} "
                f"idiom_score={idiom_score} ")

    if final == "poetry_chat":
        return poetry_text, "poem", poetry_key
    elif final == "idiom_chat":
        return idiom_text, "idiom", idiom_key


async def responding(q, uid):
    qa_answer = await _get_qa_answer(q, uid)

    text, key, val = qa_answer
    if text is not None:
        await del_user_context(uid, 'poem')
        await del_user_context(uid, 'idiom')
        await set_user_context(uid, key, val)
        return f"[{key}QA]" + text[:128]

    logger.info(f"QA systems not matched. storage={await get_user_context(uid)}")

    chat_answer = await _get_chat_answer(q, uid)
    text, key, val = chat_answer
    if text is not None:
        await del_user_context(uid, 'poem')
        await del_user_context(uid, 'idiom')
        await set_user_context(uid, key, val)
        return f"[{key}Chat]" + text[:128]

    await del_user_context(uid, 'poem')
    await del_user_context(uid, 'idiom')
    return "暂时回答不了您的问题。"

async def meta_responding(q: str, uid):
    async def _reset(*args, **kwargs):
        await reset_user_context(uid)
        return "[meta]已清除当前状态。", None

    async def _flush(*args, **kwargs):
        await flush_user_context()
        return "[meta]已清除所有人状态。", None

    async def _status(*args, **kwargs):
        return str(await get_user_context(uid)), None

    ctx = await get_user_context(uid)
    ops = {
        "%idiomqa": _get_idiom_qa,
        "%idiomchat": _get_idiom_chat,
        "%poemqa": _get_poetry_qa,
        "%poemchat": _get_poetry_chat,
        "%reset": _reset,
        "%flush": _flush,
        "%status": _status,
    }

    parts = q.split(':')
    op, new_q = parts[0].lower(), ":".join(parts[1:])
    if op == "%%":
        op = ctx.get("last_meta_op")

    call = ops.get(op)
    if call is None:
        return "[meta]不支持该指令。"

    res = await call(new_q, uid, ctx)
    await set_user_context(uid, 'last_meta_op', op)
    if res[0] and len(res[0]) > 0:
        key = "idiom" if "idiom" in op else ("poem" if "poem" in op else None)
        val = res[-1]
        if key and val:
            await del_user_context(uid, 'poem')
            await del_user_context(uid, 'idiom')
            await set_user_context(uid, key, val)
        return res[0]

