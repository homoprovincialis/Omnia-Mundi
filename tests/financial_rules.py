"""Approved PR #14 inputs and shared assertions for the two informational pages."""
import re
import subprocess

# Owner-approved inputs already present before the validation task. Pinning this
# commit retains byte-for-byte protection instead of accepting arbitrary edits.
APPROVED = '04e6ab7d95ca8e2b6aa1e26f467df8ddb188197b'
UPDATED = {'how-it-works.html', 'Omnia-Mundi_Website_Technical_Specification_RU.txt',
           'locales/ru.js', 'locales/en.js'}


def approved_input(path):
    ref = APPROVED if path in UPDATED else 'origin/main'
    return subprocess.check_output(['git', 'show', f'{ref}:{path}'])


def assert_financial_copy(page, lang, key):
    text = page.locator('main').inner_text()
    # Neither visible copy nor tables may contain hypothetical currency amounts.
    assert not re.search(r'(?:[€$£]\s*\d|\d[\d.,\s]*[€$£]|\d[\d.,\s]*(?:EUR|евро|euros?|руб))', text, re.I), page.url
    ssc = page.locator('[data-i18n="'+key+'"], [data-i18n-html="'+key+'"]').inner_text()
    fragments = {
        'ru': ['покупатель', 'конечной цены товара', 'отдельно', 'индивидуально',
               'магазина', 'расход', 'количества товаров', 'других факторов',
               'может меняться ежедневно', 'не является прибылью'],
        'en': ['customer', 'final product price', 'separately', 'individually',
               'store', 'expenses', 'number of products', 'other factors',
               'may change daily', ('is not store profit' if key == 'how.p7' else 'not Store Receiver profit')]
    }
    for fragment in fragments[lang]:
        assert fragment in ssc, (page.url, fragment)
    rows = page.locator('.profit-example tbody tr')
    assert rows.count() == 7
    assert [row.locator('td').inner_text() for row in rows.all()] == ['20%', '20%', '5%', '5%', '10%', '20%', '20%']
    assert page.locator('.profit-example thead th').count() == 2
    assert page.locator('.profit-example tfoot td').all_text_contents() == ['100%']
