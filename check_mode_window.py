import sys
sys.stdout.reconfigure(encoding='utf-8')
with open('mode.js', 'r', encoding='utf-8') as f:
    text = f.read()

pos = text.rfind('return {')
print(text[pos:pos+1500])
