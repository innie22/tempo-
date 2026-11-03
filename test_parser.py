import re

def is_vi(locale):
    return locale == 'vi'

def parse_step2_date_input(input_val, locale):
    if not input_val or not isinstance(input_val, str):
        return ''
    val = input_val.strip()
    if not val:
        return ''

    # 1. ISO
    m_iso = re.match(r'^(\d{4})-(\d{1,2})-(\d{1,2})$', val)
    if m_iso:
        y, m, d = int(m_iso.group(1)), int(m_iso.group(2)), int(m_iso.group(3))
        if 1900 <= y <= 2100 and 1 <= m <= 12 and 1 <= d <= 31:
            return f'{y}-{m:02d}-{d:02d}'

    # 2. English textual
    en_months = {
        'jan': 1, 'january': 1, 'feb': 2, 'february': 2, 'mar': 3, 'march': 3,
        'apr': 4, 'april': 4, 'may': 5, 'jun': 6, 'june': 6, 'jul': 7, 'july': 7,
        'aug': 8, 'august': 8, 'sep': 9, 'sept': 9, 'september': 9,
        'oct': 10, 'october': 10, 'nov': 11, 'november': 11, 'dec': 12, 'december': 12
    }
    m_text = re.match(r'^([a-zA-Z]{3,9})\s+(\d{1,2})(?:st|nd|rd|th)?,?\s+(\d{4})$', val)
    if m_text:
        month_key = m_text.group(1).lower()
        if month_key in en_months:
            m = en_months[month_key]
            d = int(m_text.group(2))
            y = int(m_text.group(3))
            if 1 <= d <= 31 and 1900 <= y <= 2100:
                return f'{y}-{m:02d}-{d:02d}'

    # 3. Numeric
    m_num = re.match(r'^(\d{1,2})[\/\-\.](\d{1,2})[\/\-\.](\d{4})$', val)
    if m_num:
        p1 = int(m_num.group(1))
        p2 = int(m_num.group(2))
        y = int(m_num.group(3))
        if is_vi(locale):
            d, m = p1, p2
        else:
            if p1 > 12:
                d, m = p1, p2
            elif p2 > 12:
                m, d = p1, p2
            else:
                m, d = p1, p2
        if 1 <= m <= 12 and 1 <= d <= 31 and 1900 <= y <= 2100:
            return f'{y}-{m:02d}-{d:02d}'

    return ''

# Test cases
tests = [
    # (input, locale, expected)
    ('02/11/2026', 'vi', '2026-11-02'),
    ('2/11/2026', 'vi', '2026-11-02'),
    ('31/10/2026', 'vi', '2026-10-31'),
    ('Nov 02, 2026', 'en', '2026-11-02'),
    ('Nov 2, 2026', 'en', '2026-11-02'),
    ('November 02, 2026', 'en', '2026-11-02'),
    ('Oct 31, 2026', 'en', '2026-10-31'),
    ('2026-11-02', 'vi', '2026-11-02'),
    ('2026-11-02', 'en', '2026-11-02'),
    ('11/02/2026', 'en', '2026-11-02'),
    ('', 'vi', ''),
    ('invalid', 'vi', ''),
]

for inp, loc, exp in tests:
    res = parse_step2_date_input(inp, loc)
    print(f"[{loc}] '{inp}' -> '{res}' (expected '{exp}') -> {res == exp}")
    assert res == exp, f"Failed for {inp} in {loc}"
print("All parser tests passed!")
