import urllib.request, json
port = 9590
try:
    req = urllib.request.urlopen(f"http://127.0.0.1:{port}/json")
    targets = json.loads(req.read().decode("utf-8"))
    for i, t in enumerate(targets):
        print(f"Target {i}: type={t.get('type')}, url={t.get('url')}")
except Exception as e:
    print(e)
