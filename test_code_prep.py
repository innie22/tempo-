import sys

sys.stdout.reconfigure(encoding='utf-8')

with open('learnSolve.js', 'r', encoding='utf-8') as f:
    code = f.read()

# Let's verify line endings
crlf_mode = '\r\n' in code
norm_code = code.replace('\r\n', '\n')

print(f"Read learnSolve.js: {len(norm_code)} chars, CRLF original: {crlf_mode}")
