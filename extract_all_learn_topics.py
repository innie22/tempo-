import sys, re

sys.stdout.reconfigure(encoding='utf-8')

with open('learnSolve.js', 'r', encoding='utf-8') as f:
    lines = f.readlines()

topics_lines = lines[499:751]
topics_text = ''.join(topics_lines)

# Find all blocks with id: '...'
topic_blocks = re.findall(r"\{\s*id:\s*'([^']+)',[\s\S]*?title:\s*'([^']+)',[\s\S]*?shortDescription:\s*'([^']+)'", topics_text)
print(f"Total topics in LEARN_TOPICS: {len(topic_blocks)}")
for idx, (t_id, title, desc) in enumerate(topic_blocks):
    print(f"{idx+1}: {t_id} | {title} | {desc[:60]}")
