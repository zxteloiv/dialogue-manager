import sanic
import httpx
import sanic.request
import sanic.response
from sanic.response import json as jsonres, text as textres
from fetch_downstream import available_calls, get_user_context
from response import responding, meta_responding

from sanic import Sanic
from sanic.log import error_logger, logger

app = Sanic('dialoge_manager')

@app.route("/status")
async def status(req: sanic.request.Request):
    qs = {
        "idiom_qa": "走马观花里的走马是什么意思",
        "idiom_check": "走马观花里的走马是什么意思",
        "idiom_chat": "明天会下雨吗",
        "poetry_chat": "去过最美的地方是哪里",
        "poetry_qa": "床前明月光的作者是",
    }

    rtn = {"errno": 0, "interface_health": {}, "message": {}}
    uid = 10
    for if_name, if_call in available_calls.items(): # name and function to every interface
        q = qs.get(if_name)
        if q:
            try:
                msg = await if_call(q, uid)
                succ = True
            except Exception as e:
                msg, succ = "{0}".format(e), False
        else:
            msg, succ = "Empty Query", False

        rtn["interface_health"][if_name] = "OK" if succ else "Failed"
        rtn["message"][if_name] = msg

    return jsonres(rtn)


@app.route("/manager")
async def manager(req: sanic.request.Request):
    q, uid = list(map(req.args.get, ('q', 'uid')))
    try:
        logger.info(f"Query coming. storage={await get_user_context(uid)}")
        if q.startswith('%'):
            r = await meta_responding(q, uid)
        else:
            r = await responding(q, uid)
        output = textres(r)

    except Exception as e:
        error_logger.error('manager route: {0}'.format(e))
        output = textres("下游服务器错误，无法回答您的提问。")

    logger.info(f"Query accomplished, storage={await get_user_context(uid)}")

    return output


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--port', '-p', default=8019, type=int, help="port number, default to 8019")
    parser.add_argument('--worker-num', '-w', default=8, type=int)

    args = parser.parse_args()
    app.unsafe_storage = dict()
    app.run(host="0.0.0.0", port=args.port, workers=args.worker_num)