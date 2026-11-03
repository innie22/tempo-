import json

with open(r'C:\Users\YEN NHI\.gemini\antigravity\brain\6baf9c9e-16aa-475f-b2c0-d941b08ac2c6\.system_generated\logs\transcript.jsonl', 'r', encoding='utf-8') as f:
    for line in f:
        obj = json.loads(line)
        idx = obj.get('step_index')
        if 28670 <= idx <= 28690:
            tc = obj.get('tool_calls', [])
            names = [t.get('tool_name') for t in tc]
            print(f"Step {idx}: source={obj.get('source')}, tools={names}")
