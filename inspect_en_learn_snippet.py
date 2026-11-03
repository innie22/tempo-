import sys

sys.stdout.reconfigure(encoding='utf-8')

with open('i18n.js', 'r', encoding='utf-8') as f:
    text = f.read()

idx_en_learn = text.find('learn: {', 60000)
print("EN learn start snippet:\n", text[idx_en_learn-300:idx_en_learn+50])

idx_en_cards = text.find('stress_loop:', idx_en_learn)
idx_en_learn_end = text.find('},', idx_en_cards + 200)
print("EN learn end snippet:\n", text[idx_en_learn_end-50:idx_en_learn_end+150])
