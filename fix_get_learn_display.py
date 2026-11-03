import sys

sys.stdout.reconfigure(encoding='utf-8')

with open('communityPosts.js', 'r', encoding='utf-8') as f:
    content = f.read()

old_get_learn = '''    function getLearnDisplay(item) {
        const isVi = isViLocale();
        if (window.TempoI18n && typeof window.TempoI18n.t === 'function') {
            const locTitle = window.TempoI18n.t(`community.learn.cards.${item.id}.title`);
            const locSummary = window.TempoI18n.t(`community.learn.cards.${item.id}.summary`);
            if (locTitle && locTitle !== `community.learn.cards.${item.id}.title`) {
                return {
                    title: locTitle,
                    summary: locSummary || item.summary
                };
            }
        }'''

new_get_learn = '''    function getLearnDisplay(item) {
        const isVi = isViLocale();
        if (window.TempoI18n && typeof window.TempoI18n.t === 'function') {
            const t1 = window.TempoI18n.t(`community.learn.cards.${item.id}.title`, {}, '');
            const t2 = window.TempoI18n.t(`learn.cards.${item.id}.title`, {}, '');
            const locTitle = (t1 && t1 !== 'title' && t1 !== `community.learn.cards.${item.id}.title`) ? t1 :
                             ((t2 && t2 !== 'title' && t2 !== `learn.cards.${item.id}.title`) ? t2 : '');

            const s1 = window.TempoI18n.t(`community.learn.cards.${item.id}.summary`, {}, '');
            const s2 = window.TempoI18n.t(`learn.cards.${item.id}.summary`, {}, '');
            const locSummary = (s1 && s1 !== 'summary' && s1 !== `community.learn.cards.${item.id}.summary`) ? s1 :
                               ((s2 && s2 !== 'summary' && s2 !== `learn.cards.${item.id}.summary`) ? s2 : '');

            if (locTitle) {
                return {
                    title: locTitle,
                    summary: locSummary || item.summary
                };
            }
        }'''

norm = content.replace('\r\n', '\n')
assert old_get_learn.replace('\r\n', '\n') in norm, "old_get_learn not found in communityPosts.js"

norm = norm.replace(old_get_learn.replace('\r\n', '\n'), new_get_learn.replace('\r\n', '\n'), 1)

content_crlf = norm.replace('\n', '\r\n')
with open('communityPosts.js', 'wb') as f:
    f.write(content_crlf.encode('utf-8'))

print("Updated getLearnDisplay in communityPosts.js (CRLF).")
