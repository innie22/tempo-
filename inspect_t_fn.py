import urllib.request
import json
import websocket

port = 9460 # Let's see if there is an existing debug port or test via node/python
# Let's inspect i18n.js implementation of t()
with open('i18n.js', 'r', encoding='utf-8') as f:
    text = f.read()

idx = text.find('function t(')
print(text[idx:idx+800])
