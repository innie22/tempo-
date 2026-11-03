import re, sys

sys.stdout.reconfigure(encoding='utf-8')

with open('communityPosts.js', 'r', encoding='utf-8') as f:
    text = f.read()

matches = re.findall(r'TempoI18n[A-Za-z0-9_.]*|isViLocale|getLanguage', text)
print("communityPosts.js i18n usages:", set(matches))
