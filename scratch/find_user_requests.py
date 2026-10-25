import json

with open(r'C:\Users\YEN NHI\.gemini\antigravity\brain\6baf9c9e-16aa-475f-b2c0-d941b08ac2c6\.system_generated\logs\transcript.jsonl', 'r', encoding='utf-8') as f:
    for idx, line in enumerate(f):
        if '"source":"USER_EXPLICIT"' in line:
            try:
                data = json.loads(line)
                content = data.get('content', '')
                if 'USER_REQUEST' in content and ('recovery' in content.lower() or 'rmode' in content.lower()):
                    first_line = content.split('\n')[1] if '\n' in content else content[:60]
                    print(f'Line {idx}: {first_line[:120]}')
            except Exception:
                pass
