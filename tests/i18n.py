"""RU/EN acceptance: both pages, all breakpoints, persistence and unchanged facts."""
import argparse
import hashlib
import json
import re
import subprocess
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlparse, parse_qs
from playwright.sync_api import sync_playwright, expect

parser = argparse.ArgumentParser()
parser.add_argument('--url', default='http://127.0.0.1:3010')
args = parser.parse_args()
base = args.url.rstrip('/')
widths = [320,375,390,430,768,1024,1440,1920,2560]


def ready(page):
    page.evaluate('window.omniaReady || Promise.resolve()')


def no_mixed_english(page):
    assert not re.search('[А-Яа-яЁё]', page.locator('body').inner_text()), page.url
    assert not re.search('[А-Яа-яЁё]', page.title())
    for node in page.locator('[aria-label], [placeholder], img[alt], meta[name="description"]').all():
        for attr in ['aria-label','placeholder','alt','content']:
            value = node.get_attribute(attr)
            assert not value or not re.search('[А-Яа-яЁё]', value), (attr, value)


class MainText(HTMLParser):
    def __init__(self):
        super().__init__(); self.active=False; self.parts=[]
    def handle_starttag(self, tag, attrs):
        if tag=='main': self.active=True
    def handle_endtag(self, tag):
        if tag=='main': self.active=False
    def handle_data(self, data):
        if self.active: self.parts.append(data)


def check_example(page, lang):
    rows = page.locator('.profit-example tbody tr')
    assert rows.count() == 7
    shares = []
    for row, share in zip(rows.all(), [20,20,5,5,10,20,20]):
        actual = int(row.locator('td').inner_text().replace('%',''))
        assert actual == share
        shares.append(actual)
    assert sum(shares) == 100 and sum(shares[2:5]) == 20
    assert page.locator('.profit-example tfoot td').all_text_contents() == ['100%']
    assert page.locator('.role-list dt').all_text_contents() == ['Customer','Procurer','Manufacturer','Seller','Receiver','Moderator']
    assert page.locator('.purchase-steps li').count() == 6
    assert page.locator('.trade-chain').count() == 2
    assert '20%' in page.locator('#moderator-total').inner_text()
    text = page.locator('#stores').inner_text()
    assert ('может меняться ежедневно' if lang=='ru' else 'may change daily') in text
    if lang == 'en':
        text = page.locator('main').inner_text()
        for phrase in ['accepts it voluntarily','confirms the price before payment','without an advance purchase','is not store profit',"P is not the buyer's final price","not Omnia-Mundi's operating income",'does not automatically apply to store consignment','does not guarantee income','paid by the customer','Real orders, payments, registration, stores and payouts have not launched yet']:
            assert phrase in text, phrase
        assert page.locator('.profit-example th[scope="row"]').first.inner_text() == 'One source: Procurer or Manufacturer or Seller'


with sync_playwright() as p:
    browser = p.chromium.launch(executable_path='/usr/bin/chromium', headless=True, args=['--no-sandbox'])
    for lang in ['ru','en']:
        context = browser.new_context(viewport={'width':1440,'height':900})
        page = context.new_page()
        errors, external, failed = [], [], []
        page.on('pageerror',lambda error:errors.append(str(error)))
        page.on('request',lambda request:external.append(request.url) if not request.url.startswith(base+'/') else None)
        page.on('response',lambda response:failed.append((response.url,response.status)) if response.status>=400 else None)
        for file in ['index.html','how-it-works.html']:
            assert page.goto(f'{base}/{file}?lang={lang}').status == 200
            ready(page)
            assert page.locator('html').get_attribute('lang') == lang
            assert page.locator(f'[data-language={lang}]').get_attribute('aria-pressed') == 'true'
            # Completeness, identical placeholders and a missing-key failure (never silent mixed fallback).
            dictionaries = page.evaluate('window.OMNIA_MESSAGES')
            assert dictionaries['ru'].keys() == dictionaries['en'].keys()
            for key in dictionaries['ru']:
                assert dictionaries['ru'][key] and dictionaries['en'][key]
                assert re.findall(r'\{\w+\}',dictionaries['ru'][key]) == re.findall(r'\{\w+\}',dictionaries['en'][key])
                assert dictionaries['ru'][key].count('<strong>') == dictionaries['en'][key].count('<strong>')
                assert re.findall(r'\d+%',dictionaries['ru'][key]) == re.findall(r'\d+%',dictionaries['en'][key])
            assert page.evaluate("(()=>{try{OmniaI18n.t('missing.test');return false}catch{return true}})()")
            assert page.locator('meta[name=description]').get_attribute('content')
            if file == 'how-it-works.html':
                check_example(page,lang)
                if lang == 'ru':
                    baseline = MainText()
                    baseline.feed(subprocess.check_output(['git','show','origin/main:how-it-works.html']).decode())
                    tokenize = lambda text: re.findall(r'\w+|[^\w\s]', text)
                    assert 'Сайт в разработке' in page.locator('main').inner_text() and 'без предварительного выкупа' in page.locator('main').inner_text()
            else:
                assert page.locator('.products article').count() == 8
                assert page.locator('.image-sources li').count() == 8
                facts = page.evaluate('window.OMNIA_DATA.products')
                assert [item['cents'] for item in facts] == [3990,1250,2400,4500,2990,1890,6990,5500]
                assert [item['id'] for item in facts] == ['headphones','cup','wallet','lamp','bag','thermos','drill','watch']
                for article,item in zip(page.locator('.products article').all(),facts):
                    assert article.get_attribute('data-product') == item['id']
                    expected_money = page.evaluate('(cents)=>new Intl.NumberFormat(OmniaI18n.locale,{style:"currency",currency:"EUR"}).format(cents/100)',item['cents'])
                    assert article.locator('.price').inner_text() == expected_money
                    assert article.locator('img').get_attribute('alt') == article.locator('h2').inner_text()
                page.locator('.image-sources summary').click()
                manifest = json.loads(Path('assets/products/sources.json').read_text())
                for credit in manifest:
                    assert hashlib.sha256(Path(credit['file']).read_bytes()).hexdigest() == credit['sha256']
                    item = page.locator('.image-sources li').filter(has_text=credit['title'])
                    assert item.count() == 1
                    assert credit['author'].split(' (')[0] in item.inner_text()
                    assert item.locator('a').nth(0).get_attribute('href') == credit['source']
                    assert item.locator('a').nth(1).get_attribute('href') == credit['licenseUrl']
                    assert credit['license'] in item.inner_text()
                page.locator('.image-sources summary').click()
            for width in widths:
                page.set_viewport_size({'width':width,'height':900})
                assert page.evaluate('document.documentElement.scrollWidth<=innerWidth'), (file,lang,width)
                container = page.locator('.page').bounding_box()
                assert abs(container['width']-min(width,1920)) < 1
                assert abs(container['x']-max(0,(width-1920)/2)) < 1
                assert page.locator('.logo-link img').bounding_box()['width'] == (150 if width<640 else 160)
                boxes = page.locator('.header > *').evaluate_all('(nodes)=>nodes.map(n=>n.getBoundingClientRect().toJSON())')
                for i,first in enumerate(boxes):
                    for second in boxes[i+1:]:
                        assert min(first['right'],second['right'])-max(first['left'],second['left'])<=1 or min(first['bottom'],second['bottom'])-max(first['top'],second['top'])<=1,(file,lang,width)
                for selector in ['.primary-nav button','.primary-nav a','.account-actions button','.language-switcher button','#footer-nav button','#footer-nav a','main p:not(.result-status)','main h1','main h2','main th','main td','main li','main dd']:
                    assert page.locator(selector).evaluate_all('(nodes)=>nodes.every(n=>n.scrollWidth<=n.clientWidth+1&&n.scrollHeight<=n.clientHeight+1)'),(file,lang,width,selector)
                if file == 'index.html':
                    assert page.locator('.products img').evaluate_all('(imgs)=>imgs.every(n=>n.getBoundingClientRect().width===157&&n.getBoundingClientRect().height===157&&n.naturalWidth>0)')
                    old_hidden = page.locator('#filters').evaluate('(n)=>n.hidden')
                    page.locator('#filters').evaluate('(n)=>n.hidden=false')
                    page.locator('.image-sources').evaluate('(n)=>n.open=true')
                    assert page.evaluate('document.documentElement.scrollWidth<=innerWidth')
                    assert page.locator('#categories button,.image-sources li').evaluate_all('(nodes)=>nodes.every(n=>n.scrollWidth<=n.clientWidth+1&&n.scrollHeight<=n.clientHeight+1)')
                    if lang == 'en': no_mixed_english(page)
                    page.locator('#filters').evaluate('(n,hidden)=>n.hidden=hidden',old_hidden)
                    page.locator('.image-sources').evaluate('(n)=>n.open=false')
                    for selector,size in [('.products h2',16),('.price',16),('.country',15),('.catalog-heading h1',22),('.image-sources',15)]:
                        assert page.locator(selector).evaluate_all('(nodes,size)=>nodes.every(n=>parseFloat(getComputedStyle(n).fontSize)===size)',size)
                    title = page.locator('.products h2').first
                    old_title = title.inner_text()
                    title.evaluate('(n,text)=>n.textContent=text', ('Very long translated demonstration product name ' if lang=='en' else 'Очень длинное название демонстрационного товара ') * 4)
                    assert title.evaluate('(n)=>n.scrollWidth<=n.clientWidth+1&&n.scrollHeight<=n.clientHeight+1')
                    assert page.evaluate('document.documentElement.scrollWidth<=innerWidth')
                    assert page.locator('.products article').evaluate_all('''(cards)=>cards.every(card=>{
                        const image=card.querySelector('img').getBoundingClientRect();
                        const center=image.x+image.width/2;
                        return [...card.querySelectorAll('h2,.price,.country')].every(n=>{
                            if(getComputedStyle(n).textAlign!=='center')return false;
                            const range=document.createRange();range.selectNodeContents(n);
                            return [...range.getClientRects()].every(r=>Math.abs(r.x+r.width/2-center)<1);
                        });
                    })''')
                    title.evaluate('(n,text)=>n.textContent=text', old_title)
                if lang == 'en': no_mixed_english(page)
                # Actual keyboard switches, preserving language control focus.
                other = 'en' if lang=='ru' else 'ru'
                control = page.locator(f'[data-language={other}]')
                control.focus()
                page.keyboard.press('Tab')
                page.keyboard.press('Shift+Tab')
                assert control.evaluate('(n)=>getComputedStyle(n).outlineStyle!=="none"')
                page.keyboard.press('Enter')
                assert page.locator('html').get_attribute('lang') == other
                assert control.evaluate('(n)=>n===document.activeElement')
                page.locator(f'[data-language={lang}]').click()
                page.locator(f'[data-language={lang}]').evaluate('(n)=>n.blur()')
                if file == 'how-it-works.html': check_example(page,lang)
                if width in [390,1440,1920]:
                    Path('docs/screenshots/i18n').mkdir(parents=True,exist_ok=True)
                    name = 'homepage' if file=='index.html' else 'how-it-works'
                    page.screenshot(path=f'docs/screenshots/i18n/{name}-{lang}-{width}.png',full_page=True)
                print(f'PASS {file} {lang} {width}px: language controls, metadata, readable layout and content')
            # All placeholder dialogs are localized and keep Escape/focus behavior.
            for button in page.locator('[data-future],#footer-nav button').all():
                button.focus();page.keyboard.press('Enter')
                assert page.locator('#notice-title').inner_text() == ('Раздел находится в разработке' if lang=='ru' else 'This section is under development')
                assert page.locator('#notice-close').inner_text() == ('Закрыть' if lang=='ru' else 'Close')
                page.keyboard.press('Escape');assert button.evaluate('(n)=>n===document.activeElement')
            if file=='index.html':
                search = page.get_by_role('searchbox')
                search.fill('лампа' if lang=='ru' else 'lamp')
                assert page.locator('.products article').count()==1
                search.fill('NOT_A_PRODUCT_123')
                assert page.locator('#empty').is_visible()
                assert page.locator('#empty').inner_text() == dictionaries[lang]['catalog.empty']
                search.fill('')
                page.set_viewport_size({'width':1440,'height':900})
                page.locator('[data-category=electronics]').click()
                assert page.locator('.products article').count()==1
                page.locator(f'[data-language={other}]').click()
                assert page.locator('[data-category=electronics]').get_attribute('aria-pressed')=='true'
                assert page.locator('.products article').get_attribute('data-product')=='headphones'
                page.locator(f'[data-language={lang}]').click()
                page.locator('[data-category=all]').click()
            else:
                page.locator('.contents a[href="#income"]').click()
                page.locator(f'[data-language={other}]').click()
                assert urlparse(page.url).fragment=='income'
                page.locator(f'[data-language={lang}]').click()
                page.locator('.catalog-search-link').click()
                assert parse_qs(urlparse(page.url).query)['lang']==[lang] and urlparse(page.url).fragment=='catalog'
                ready(page)
                page.locator('#footer-nav a[href*="how-it-works.html"]').click()
                assert urlparse(page.url).path=='/how-it-works.html' and parse_qs(urlparse(page.url).query)['lang']==[lang]
            page.reload();ready(page)
            assert page.locator('html').get_attribute('lang')==lang
        assert not errors and not external and not failed,(errors,external,failed)
        context.close()

    # New users default to RU. Explicit URL beats storage; bare URLs reuse saved preference.
    context=browser.new_context();page=context.new_page()
    page.goto(base+'/index.html');ready(page)
    assert page.locator('html').get_attribute('lang')=='ru'
    page.locator('[data-language=en]').click();page.reload();ready(page)
    assert page.locator('html').get_attribute('lang')=='en'
    page.goto(base+'/how-it-works.html')
    assert page.locator('html').get_attribute('lang')=='en'
    page.goto(base+'/index.html?lang=ru');ready(page)
    assert page.locator('html').get_attribute('lang')=='ru'
    page.goto(base+'/index.html?lang=%3Cscript%3E');ready(page)
    assert page.locator('html').get_attribute('lang')=='ru'
    assert not page.evaluate("OmniaI18n.setLanguage('unsupported')")
    context.close()
    # Preserve category, query and anchors even when the old-language query no longer matches.
    context=browser.new_context(viewport={'width':1440,'height':900});page=context.new_page()
    page.goto(base+'/index.html?lang=ru&test=kept#catalog');ready(page)
    page.locator('[data-category=home]').click();page.get_by_role('searchbox').fill('лампа')
    assert page.locator('.products article').count()==1
    page.locator('[data-language=en]').click()
    assert page.locator('[data-category=home]').get_attribute('aria-pressed')=='true'
    assert page.get_by_role('searchbox').input_value()=='лампа'
    assert page.locator('#empty').inner_text()=='No demonstration products found. Change your search or category.'
    assert parse_qs(urlparse(page.url).query)['test']==['kept'] and urlparse(page.url).fragment=='catalog'
    page.get_by_role('searchbox').fill('')
    assert page.locator('.products article').count()==2
    context.close()
    # Block both reading and writing storage; URLs still provide complete persistence.
    context=browser.new_context()
    context.add_init_script("Object.defineProperty(window,'localStorage',{get(){throw new DOMException('Blocked','SecurityError')}})")
    page=context.new_page()
    for file in ['index.html','how-it-works.html']:
        page.goto(f'{base}/{file}?lang=en');ready(page)
        assert page.locator('html').get_attribute('lang')=='en'
        page.reload();ready(page)
        assert page.locator('html').get_attribute('lang')=='en'
        page.locator('[data-language=ru]').click()
        assert page.locator('html').get_attribute('lang')=='ru'
        page.locator('[data-language=en]').click()
        page.locator('#footer-nav a[href*="how-it-works.html"]').click()
        assert parse_qs(urlparse(page.url).query)['lang']==['en']
    context.close()
    # Fixed, previously approved material is not edited for translation.
    for file in ['assets/omnia-mundi-logo.svg','ASSETS.md','assets/products/sources.json','Omnia-Mundi_Website_Technical_Specification_RU.txt','Omnia-Mundi_Codex_Homepage_Phase_1_RU.txt','Omnia-Mundi_Development_Roadmap_RU.pdf']:
        assert Path(file).read_bytes()==subprocess.check_output(['git','show','origin/main:'+file])
    print('PASS URL/storage priority, direct links, new-user RU, invalid language, blocked storage, navigation and immutable facts')
    browser.close()
