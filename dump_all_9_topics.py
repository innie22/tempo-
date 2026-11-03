import sys, json

sys.stdout.reconfigure(encoding='utf-8')

with open('learnSolve.js', 'r', encoding='utf-8') as f:
    text = f.read()

# Let's inspect the LEARN_TOPICS array
start = text.find('const LEARN_TOPICS = [')
end = text.find('const SOLVE_SITUATIONS = [', start)
if end == -1:
    end = text.find('function openModal', start)

topics_text = text[start:end]

# Let's extract each topic object structure
import re
pattern = re.compile(r"\{\s*id:\s*'([^']+)'", re.MULTILINE)
matches = list(pattern.finditer(topics_text))
print(f"Total topics found: {len(matches)}")
for idx, m in enumerate(matches):
    t_id = m.group(1)
    # find next match or end
    next_pos = matches[idx+1].start() if idx+1 < len(matches) else len(topics_text)
    block = topics_text[m.start():next_pos]
    title_m = re.search(r"title:\s*['\"]([^'\"]+)['\"]", block)
    badge_m = re.search(r"badge:\s*['\"]([^'\"]+)['\"]", block)
    title = title_m.group(1) if title_m else 'No title'
    badge = badge_m.group(1) if badge_m else 'No badge'
    print(f"{idx+1}. ID: {t_id:20s} | Badge: {badge:20s} | Title: {title}")
