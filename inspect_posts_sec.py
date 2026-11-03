import sys

sys.stdout.reconfigure(encoding='utf-8')

with open('i18n.js', 'r', encoding='utf-8') as f:
    text = f.read()

pos1 = text.find('posts:')
print("pos1:", text[pos1:pos1+1500])

pos2 = text.find('posts:', pos1+10)
print("\npos2:", text[pos2:pos2+1500])
