import sys, json

sys.stdout.reconfigure(encoding='utf-8')

with open('scratch/topics_raw.js', 'r', encoding='utf-8') as f:
    text = f.read()

# Let's inspect each topic in LEARN_TOPICS
# There are 9 topics:
# 1. what_is_stress
# 2. stress_problem
# 3. stress_signs
# 4. stress_loop
# 5. recovery
# 6. academic_burnout
# 7. stress_eating
# 8. what_do_i_need
# 9. support_seeking

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
    block = text[idx-10:next_idx]
    with open(f'scratch/topic_{tid}.txt', 'w', encoding='utf-8') as tf:
        tf.write(block)
    print(f"Dumped {tid}, length {len(block)}")
