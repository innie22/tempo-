import sys, json

sys.stdout.reconfigure(encoding='utf-8')

with open('learnSolve.js', 'r', encoding='utf-8') as f:
    text = f.read()

start_idx = text.find('const LEARN_TOPICS = [')
end_idx = text.find('// =========================================================================\n    // 4. COMPONENT STATE', start_idx)
topics_text = text[start_idx:end_idx]

with open('scratch/learn_topics_dump.txt', 'w', encoding='utf-8') as f:
    f.write(topics_text)

print("Dumped LEARN_TOPICS to scratch/learn_topics_dump.txt. Size:", len(topics_text))
