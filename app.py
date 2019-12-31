import sanic
import httpx
import sanic.request
import sanic.response
from sanic.response import json as jsonres
from fetch_downstream import available_calls

from sanic import Sanic

app = Sanic('dialoge_manager')

@app.route("/status")
async def manager(req: sanic.request.Request):
    qs = {
        "idiom_qa": "走马观花里的走马是什么意思",
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
    return jsonres({"raw_q": q, "uid": uid})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, workers=8)