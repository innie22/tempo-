import sys

sys.stdout.reconfigure(encoding='utf-8')

with open('scratch/topics_raw.js', 'r', encoding='utf-8') as f:
    text = f.read()

import re

topic_ids = [
    'what_is_stress',
    'stress_problem',
    'stress_signs',
    'stress_loop',
    'recovery',
    'academic_burnout',
    'stress_eating',
    'what_do_i_need',
    'support_seeking'
]

for tid in topic_ids:
    idx = text.find(f"id: '{tid}'")
    next_idx = text.find("id: '", idx + 20)
    if next_idx == -1:
        next_idx = len(text)
    block = text[idx:next_idx]
    
    tool = re.search(r'relatedTool:\s*\{([^}]+)\}', block)
    mode = re.search(r'relatedMode:\s*\{([^}]+)\}', block)
    rel_learn = re.search(r'relatedLearnIds:\s*\[([^\]]+)\]', block)
    rel_solve = re.search(r'relatedSolveIds:\s*\[([^\]]+)\]', block)
    print(f"=== {tid} ===")
    if tool: print("  tool:", tool.group(1).strip())
    if mode: print("  mode:", mode.group(1).strip())
    if rel_learn: print("  relatedLearn:", rel_learn.group(1).strip())
    if rel_solve: print("  relatedSolve:", rel_solve.group(1).strip())
