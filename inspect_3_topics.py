import sys, json

sys.stdout.reconfigure(encoding='utf-8')

with open('learnSolve.js', 'r', encoding='utf-8') as f:
    text = f.read()

# Let's inspect what_is_stress, stress_eating, stress_loop in learnSolve.js
for topic_id in ['what_is_stress', 'stress_eating', 'stress_loop']:
    idx = text.find(f"id: '{topic_id}'")
    if idx != -1:
        # find the end of this object
        end = text.find("        },", idx)
        print(f"=== {topic_id} ===")
        print(text[idx:end+10])
        print()
