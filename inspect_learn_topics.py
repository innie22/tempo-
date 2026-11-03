import sys, json, re

sys.stdout.reconfigure(encoding='utf-8')

with open('learnSolve.js', 'r', encoding='utf-8') as f:
    text = f.read()

# Find LEARN_TOPICS
start_idx = text.find('const LEARN_TOPICS = [')
end_idx = text.find('const ALL_ITEMS =', start_idx)
if start_idx != -1 and end_idx != -1:
    topics_block = text[start_idx:end_idx]
    # find all id: '...' and title: '...'
    topics = re.findall(r"id:\s*'([^']+)',[\s\S]*?title:\s*'([^']+)',[\s\S]*?shortDescription:\s*'([^']+)'", topics_block)
    print(f"Total topics in LEARN_TOPICS: {len(topics)}")
    for idx, (t_id, title, desc) in enumerate(topics):
        print(f"{idx+1}: {t_id} | {title} | {desc[:60]}")
else:
    print("Could not find LEARN_TOPICS")
