import sys

sys.stdout.reconfigure(encoding='utf-8')

with open('learnSolve.js', 'r', encoding='utf-8') as f:
    text = f.read()

# Let's see the topics array directly
start = text.find('const LEARN_TOPICS = [')
end = text.find('function getItemById(id)', start)
topics_code = text[start:end]

with open('scratch/topics_raw.js', 'w', encoding='utf-8') as f_out:
    f_out.write(topics_code)

print("Saved scratch/topics_raw.js, length:", len(topics_code))
