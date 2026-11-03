import sys, re

sys.stdout.reconfigure(encoding='utf-8')

with open('mode.js', 'r', encoding='utf-8') as f:
    text = f.read()

idx = text.find('function renderRecoveryWorkingPlanSection(')
end = text.find('function renderRecoveryCommunityCard(', idx)
print(f"Working Plan section length: {end - idx}")

plan_code = text[idx:end]
with open('scratch/rmode_plan_dump.js', 'w', encoding='utf-8') as f_out:
    f_out.write(plan_code)

print("Buttons with onclick in Rmode working plan:")
for m in re.finditer(r'<button[^>]*onclick="([^"]*)"[^>]*>([\s\S]*?)<\/button>', plan_code):
    onclick = m.group(1)
    text_content = re.sub(r'\s+', ' ', m.group(2)).strip()
    print(f"  - Onclick: {onclick[:60]:60s} | Text: {text_content[:40]}")

print("\nTask item click handler:")
for m in re.finditer(r'onclick="window\.TempoMode\.(openRmodeTaskDetail|[^"]*)"', plan_code):
    print("  - Task click:", m.group(0))
