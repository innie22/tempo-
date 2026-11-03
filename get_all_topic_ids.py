import sys, json

sys.stdout.reconfigure(encoding='utf-8')

with open('learnSolve.js', 'r', encoding='utf-8') as f:
    text = f.read()

start_idx = text.find('const LEARN_TOPICS = [')
end_idx = text.find('// =========================================================================\n    // 4. COMPONENT STATE', start_idx)
topics_text = text[start_idx:end_idx]

import re
# Print all topic ids
topic_ids = re.findall(r"id:\s*'([^']+)'", topics_text)
print("Topic IDs:", topic_ids)
