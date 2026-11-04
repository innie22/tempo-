with open('scratch/test_dashboard_btn.py', 'r', encoding='utf-8') as f:
    c = f.read()

c = c.replace('return resp.get("result", {}).get("value")', 'return resp.get("result", {}).get("result", {}).get("value")')

with open('scratch/test_dashboard_btn.py', 'w', encoding='utf-8', newline='\n') as f:
    f.write(c)
