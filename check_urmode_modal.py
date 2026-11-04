with open('urmodeFlow.js', 'r', encoding='utf-8') as f:
    text = f.read()

pos = text.find('function getModalRoot')
print(text[pos:pos+500])
