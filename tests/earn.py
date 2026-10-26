"""Issue #10: actual RU/EN Earn page, visible financial rules, navigation and screenshots."""
import argparse
import hashlib
from datetime import datetime, timezone
from pathlib import Path
import json
import re
import subprocess
from urllib.parse import urlparse, parse_qs
from playwright.sync_api import sync_playwright, expect

parser=argparse.ArgumentParser()
parser.add_argument('--url',default='http://127.0.0.1:3010')
args=parser.parse_args()
base=args.url.rstrip('/')
route='/earn-with-omnia-mundi.html'
roles=['Procurer','Manufacturer','Seller','Receiver','Moderator']
widths=[320,375,390,430,768,1024,1440,1920,2560]


def assert_language(page,lang):
    assert page.locator('html').get_attribute('lang')==lang
    assert page.locator(f'[data-language={lang}]').get_attribute('aria-pressed')=='true'
    assert ('Earn with Omnia-Mundi' if lang=='en' else 'Зарабатывать с Omnia-Mundi')==page.title()
    assert page.locator('meta[name=description]').get_attribute('content')
    if lang=='en':
        assert not re.search('[А-Яа-яЁё]',page.locator('body').inner_text())
        for node in page.locator('[aria-label],[placeholder],img[alt],meta[name=description]').all():
            for attr in ['aria-label','placeholder','alt','content']:
                assert not re.search('[А-Яа-яЁё]',node.get_attribute(attr) or '')


def assert_content(page,lang):
    assert page.locator('.earning-role').count()==5
    assert page.locator('.earning-role h2').all_text_contents()==roles
    for role in page.locator('.earning-role').all():
        assert role.locator('dl>div').count()==5
        assert [n.get_attribute('data-field') for n in role.locator('dd').all()]==['work','requirements','benefits','reward','apply']
        assert all(len(n.inner_text())>40 for n in role.locator('dd').all())
    for specialization in ['Home','Warehouse','Store']:
        assert specialization in page.locator('#receiver [data-field=work]').inner_text()
    for specialization in ['Sender Curator','Receiver Curator','Order Supervisor']:
        assert specialization in page.locator('#moderator [data-field=reward]').inner_text()
    rows=page.locator('.profit-example tbody tr')
    assert rows.count()==7
    shares=[]
    expected_labels=[('One source: Procurer or Manufacturer or Seller' if lang=='en' else 'Один источник: Procurer или Manufacturer или Seller'),'Receiver','Sender Curator','Receiver Curator','Order Supervisor','Omnia-Mundi','Protection Fund']
    for row,label,share in zip(rows.all(),expected_labels,[20,20,5,5,10,20,20]):
        assert row.locator('th').inner_text()==label
        actual=int(row.locator('td').inner_text().replace('%',''))
        assert actual==share
        shares.append(actual)
    assert sum(shares)==100 and sum(shares[2:5])==20
    assert page.locator('.profit-example tfoot td').nth(0).inner_text()=='100%'
    text=page.locator('#profit').inner_text()
    assert ('может меняться ежедневно' if lang=='ru' else 'may change daily') in text

    phrases={
        'ru':{
            '#procurer [data-field=reward]':['раннее возмещение','только после окончательного закрытия','не прибыль'],
            '#manufacturer [data-field=work]':['без предварительного выкупа','магазин сам решает'],
            '#manufacturer [data-field=reward]':['не обязана равняться себестоимости','единственный источник','20% P'],
            '#seller [data-field=requirements]':['право распоряжаться','одного заявления недостаточно'],
            '#seller [data-field=reward]':['не отдельная выплата','Procurer и Manufacturer'],
            '#receiver [data-field=reward]':['не переносится автоматически','SSC не прибыль','доля прибыли Store Receiver'],
            '#receiver [data-field=requirements]':['самостоятельно финансирует'],
            '#moderator [data-field=reward]':['Вместе это 20%','не 20% плюс','не утверждена и не обещается'],
            '#accounts':['не шестая зарабатывающая роль','одном будущем аккаунте','независимыми проверками'],
            '#profit':['Положительная распределяемая прибыль P','не процент от конечной цены','не операционный доход'],
            '#development-status':['Сайт в разработке','ещё не работают'],
            '#participate':['Пока нельзя зарегистрироваться','персональные данные не запрашиваются']},
        'en':{
            '#procurer [data-field=reward]':['early reimbursement','only after final closure','not profit'],
            '#manufacturer [data-field=work]':['without an advance purchase','store decides'],
            '#manufacturer [data-field=reward]':['need not equal production cost','sole product source','20% of P'],
            '#seller [data-field=requirements]':['right to dispose','declaration alone is not enough'],
            '#seller [data-field=reward]':['not an extra payment','Procurer and Manufacturer'],
            '#receiver [data-field=reward]':['does not automatically apply','SSC is not profit','profit share is separate'],
            '#receiver [data-field=requirements]':['independently funds'],
            '#moderator [data-field=reward]':['Together this is 20%','not 20% plus','has not been approved and is not promised'],
            '#accounts':['not a sixth earning role','One future account','independent checks'],
            '#profit':['Positive distributable profit P','not a percentage of the buyer','not Omnia-Mundi’s operating income'],
            '#development-status':['under development','not available yet'],
            '#participate':['Registration and applications are not available','no personal data is requested']}}
    for selector,fragments in phrases[lang].items():
        text=page.locator(selector).inner_text()
        for fragment in fragments: assert fragment in text,(lang,selector,fragment)
    assert page.locator('#participate ol li').count()==5
    assert page.locator('form').evaluate_all('(forms)=>forms.every(f=>f.method==="dialog")')
    assert page.locator('input,textarea,select').count()==0
    assert page.locator('script[src="app.js"]').count()==0
    assert page.locator('main').get_by_text('Approved',exact=True).count()==0


with sync_playwright() as p:
    browser=p.chromium.launch(executable_path='/usr/bin/chromium',headless=True,args=['--no-sandbox'])
    captures=[]
    for lang in ['ru','en']:
        context=browser.new_context(viewport={'width':1440,'height':900})
        page=context.new_page();errors=[];external=[];failed=[]
        page.on('pageerror',lambda error:errors.append(str(error)))
        page.on('request',lambda request:external.append(request.url) if not request.url.startswith(base+'/') else None)
        page.on('response',lambda response:failed.append((response.url,response.status)) if response.status>=400 else None)
        assert page.goto(f'{base}{route}?lang={lang}&ref=issue10#content').status==200
        assert_language(page,lang);assert_content(page,lang)
        for width in widths:
            page.set_viewport_size({'width':width,'height':900})
            assert page.evaluate('document.documentElement.scrollWidth<=innerWidth'),(lang,width)
            box=page.locator('.page').bounding_box()
            assert abs(box['width']-min(width,1920))<1
            assert abs(box['x']-max(0,(width-1920)/2))<1
            assert page.locator('.logo-link img').bounding_box()['width']==(150 if width<640 else 160)
            assert page.locator('main').bounding_box()['width']<=850
            for selector in ['main p','main h1','main h2','main dt','main dd','main th','main td','main li','main button','.header button','.primary-nav button','#footer-nav button','#footer-nav a']:
                assert page.locator(selector).evaluate_all('(nodes)=>nodes.every(n=>n.scrollWidth<=n.clientWidth+1&&n.scrollHeight<=n.clientHeight+1)'),(lang,width,selector)
            for selector,size in [('main',16),('main h1',22),('main h2',18),('.development-status',15),('.profit-example',15),('.earn-apply',16)]:
                assert page.locator(selector).evaluate_all('(nodes,size)=>nodes.every(n=>parseFloat(getComputedStyle(n).fontSize)===size)',size),(lang,width,selector)
            boxes=page.locator('.header > *').evaluate_all('(nodes)=>nodes.map(n=>n.getBoundingClientRect().toJSON())')
            for i,a in enumerate(boxes):
                for b in boxes[i+1:]:
                    assert min(a['right'],b['right'])-max(a['left'],b['left'])<=1 or min(a['bottom'],b['bottom'])-max(a['top'],b['top'])<=1
            # CTA is keyboard-operable, has a visible focus and never submits an application.
            apply=page.locator('.earn-apply');apply.focus();page.keyboard.press('Tab');page.keyboard.press('Shift+Tab')
            assert apply.evaluate('(n)=>n===document.activeElement&&getComputedStyle(n).outlineStyle!=="none"')
            before=page.url;page.keyboard.press('Enter')
            assert page.get_by_role('dialog').is_visible()
            assert page.locator('#notice-title').inner_text()==('Раздел находится в разработке' if lang=='ru' else 'This section is under development')
            assert page.url==before
            page.keyboard.press('Escape');assert apply.evaluate('(n)=>n===document.activeElement');apply.evaluate('(n)=>n.blur()')
            # Language changes preserve the URL's query/hash and all financial facts.
            other='en' if lang=='ru' else 'ru'
            control=page.locator(f'[data-language={other}]');control.focus();page.keyboard.press('Tab');page.keyboard.press('Shift+Tab');page.keyboard.press('Enter')
            assert_language(page,other);assert_content(page,other)
            assert parse_qs(urlparse(page.url).query)['ref']==['issue10'] and urlparse(page.url).fragment=='content'
            page.locator(f'[data-language={lang}]').click();page.locator(f'[data-language={lang}]').evaluate('(n)=>n.blur()')
            if width in [390,1440,1920]:
                Path('docs/screenshots/earn').mkdir(parents=True,exist_ok=True)
                file=f'docs/screenshots/earn/earn-{lang}-{width}.png'
                screenshot=page.screenshot(path=file,full_page=True)
                captures.append({'file':file,'url':page.url,'language':lang,'viewport':{'width':width,'height':900},'deviceScaleFactor':1,'fullPage':True,'browser':'Chromium '+browser.version,'capturedAtUtc':datetime.now(timezone.utc).isoformat(),'sha256':hashlib.sha256(screenshot).hexdigest(),'renderedHtmlSha256':hashlib.sha256(page.content().encode()).hexdigest()})
            print(f'PASS Earn {lang} {width}px: 5 roles, visible financial rules, typography, no clipping, keyboard and language')
        page.reload();assert_language(page,lang)
        # All three pages expose actual Earn/How links, preserve lang and target hashes.
        for source in ['index.html','how-it-works.html']:
            page.goto(f'{base}/{source}?lang={lang}')
            page.locator('#footer-nav a[href*="earn-with-omnia-mundi.html"]').click()
            expect(page).to_have_url(f'{base}{route}?lang={lang}')
            assert_language(page,lang)
        assert page.locator('#footer-nav a[href*="earn-with-omnia-mundi.html"]').get_attribute('aria-current')=='page'
        page.locator('#profit a').click()
        expect(page).to_have_url(f'{base}/how-it-works.html?lang={lang}#income')
        page.locator('#footer-nav a[href*="earn-with-omnia-mundi.html"]').click()
        page.locator('.logo-link').click();expect(page).to_have_url(f'{base}/index.html?lang={lang}')
        page.locator('#footer-nav a[href*="earn-with-omnia-mundi.html"]').click()
        page.locator('.catalog-search-link').click();expect(page).to_have_url(f'{base}/index.html?lang={lang}#catalog')
        assert page.locator('.products article').count()==8
        page.locator('#footer-nav a[href*="earn-with-omnia-mundi.html"]').click()
        for button in page.locator('[data-future],#footer-nav button').all():
            button.click();assert page.get_by_role('dialog').is_visible();page.keyboard.press('Escape')
        assert page.locator('#footer-nav button').count()==14 and page.locator('#footer-nav a').count()==2
        assert not errors and not external and not failed,(errors,external,failed)
        context.close()
    context=browser.new_context();page=context.new_page()
    page.goto(base+route);assert_language(page,'ru')
    page.locator('[data-language=en]').click();page.goto(base+route);assert_language(page,'en')
    page.goto(base+route+'?lang=ru');assert_language(page,'ru');context.close()
    context=browser.new_context()
    context.add_init_script("Object.defineProperty(window,'localStorage',{get(){throw new DOMException('Blocked','SecurityError')}})")
    page=context.new_page();page.goto(base+route+'?lang=en');assert_language(page,'en')
    page.locator('[data-language=ru]').click();page.reload();assert_language(page,'ru')
    page.locator('#profit a').click();expect(page).to_have_url(base+'/how-it-works.html?lang=ru#income')
    page.locator('#footer-nav a[href*="earn-with-omnia-mundi.html"]').click();assert_language(page,'ru');context.close()
    context=browser.new_context(java_script_enabled=False);page=context.new_page()
    page.goto(base+route);assert page.locator('.earning-role h2').all_text_contents()==roles
    assert page.locator('#development-status').is_visible()
    page.locator('#profit a').click();assert page.url==base+'/how-it-works.html#income';context.close()
    # Existing pages, engine, assets and approved text are unchanged; only Earn footer metadata is added.
    unchanged=['index.html','how-it-works.html','i18n.js','navigation.js','app.js','AGENTS.md','ASSETS.md','assets/omnia-mundi-logo.svg','assets/products/sources.json','Omnia-Mundi_Website_Technical_Specification_RU.txt','Omnia-Mundi_Codex_Homepage_Phase_1_RU.txt','Omnia-Mundi_Development_Roadmap_RU.pdf']
    unchanged += [str(path) for path in Path('assets/products').glob('*.jpg')]
    for file in unchanged:assert Path(file).read_bytes()==subprocess.check_output(['git','show','origin/main:'+file]),file
    assert Path('style.css').read_text().startswith(subprocess.check_output(['git','show','origin/main:style.css']).decode())
    for lang in ['ru','en']:
        marker='window.OMNIA_MESSAGES.'+lang+' = '
        parse=lambda s:json.loads(s.split(marker,1)[1].strip().rstrip(';'))
        old=parse(subprocess.check_output(['git','show',f'origin/main:locales/{lang}.js']).decode())
        new=parse(Path(f'locales/{lang}.js').read_text())
        assert all(new[key]==value for key,value in old.items()),lang
    assert len(captures)==6
    Path('docs/screenshots/earn/captures.json').write_text(json.dumps(captures,ensure_ascii=False,indent=2)+'\n')
    print('PASS three-page language navigation, storage fallback, RU no-JS, 100% shares, unchanged existing pages/engine/assets/translations')
    browser.close()
