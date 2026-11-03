import sys

sys.stdout.reconfigure(encoding='utf-8')

with open('learnSolve.js', 'r', encoding='utf-8') as f:
    text = f.read()

start = text.find('const TEMPO_TIPS = {')
end = text.find('// =========================================================================\n    // 5. MODAL DETAIL VIEW SYSTEM', start)
print(text[start:end])
