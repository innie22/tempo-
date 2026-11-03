import sys
sys.stdout.reconfigure(encoding='utf-8')

with open('index.html', 'r', encoding='utf-8', newline='') as f:
    text = f.read()

idx = text.find('id="modal-create-post"')
if idx == -1:
    idx = text.find('modal-create-post')
if idx == -1:
    idx = text.find('form-modal-create-post')
print("modal-create-post at", idx)
if idx != -1:
    print(text[idx-100:idx+1500])
