import asyncio
import json
import websockets
import urllib.request

def eval_js(expr):
    req = urllib.request.urlopen("http://localhost:9222/json")
    pages = json.loads(req.read().decode())
    target = next((p for p in pages if "localhost:8000" in p.get("url", "")), None)
    if not target:
        raise RuntimeError("Target page not found")
    ws_url = target["webSocketDebuggerUrl"]

    async def _run():
        async with websockets.connect(ws_url, max_size=50*1024*1024) as ws:
            msg_id = 1
            await ws.send(json.dumps({
                "id": msg_id,
                "method": "Runtime.evaluate",
                "params": {
                    "expression": expr,
                    "returnByValue": True,
                    "awaitPromise": True
                }
            }))
            resp = json.loads(await ws.recv())
            if "exceptionDetails" in resp.get("result", {}):
                raise RuntimeError(resp["result"]["exceptionDetails"])
            return resp.get("result", {}).get("result", {}).get("value")
    return asyncio.run(_run())

res = eval_js("""
(async () => {
    try {
        const planBefore = window.TempoPlanStore.getActivePlan('emergency');
        const taskBefore = planBefore?.plannedTasks?.[0]?.task;
        const callRes = await window.TempoMode.handleCardTaskComplete('task-stats-4', true);
        const planAfter = window.TempoPlanStore.getActivePlan('emergency');
        const taskAfter = planAfter?.plannedTasks?.[0]?.task;
        return {
            callRes,
            taskBeforeCompleted: taskBefore?.completed,
            taskAfterCompleted: taskAfter?.completed,
            planAfterTasks: planAfter?.plannedTasks?.map(p => ({ id: p.task.id, completed: p.task.completed }))
        };
    } catch (e) {
        return { error: e.message, stack: e.stack };
    }
})()
""")
print(json.dumps(res, indent=2))
