"""HTTP/browser acceptance checks for the single informational page in Issue #6."""
import argparse
from decimal import Decimal
from pathlib import Path
from playwright.sync_api import sync_playwright, expect

parser = argparse.ArgumentParser()
parser.add_argument('--url', default='http://127.0.0.1:3010')
args = parser.parse_args()
base = args.url.rstrip('/')
with sync_playwright() as p:
    browser = p.chromium.launch(executable_path='/usr/bin/chromium', headless=True, args=['--no-sandbox'])
    page = browser.new_page(viewport={'width': 1440, 'height': 900})
    errors, external, failed = [], [], []
    page.on('pageerror', lambda error: errors.append(str(error)))
    page.on('request', lambda request: external.append(request.url) if not request.url.startswith(base + '/') else None)
    page.on('response', lambda response: failed.append((response.url,response.status)) if response.status >= 400 else None)
    response = page.goto(base + '/how-it-works.html')
    assert response.status == 200
    assert page.locator('html').get_attribute('lang') == 'ru'
    assert page.get_by_role('heading', name='Как это работает', exact=True).count() == 1
    assert page.locator('script[src="app.js"]').count() == 0
    assert page.locator('input').count() == 0
    assert page.locator('form').evaluate_all('(forms)=>forms.every(f=>f.method==="dialog")')
    assert page.locator('header img').get_attribute('src') == 'assets/omnia-mundi-logo.svg'
    assert page.locator('header img').evaluate('(img)=>img.complete&&img.naturalWidth>0')
    assert page.locator('link[rel="stylesheet"]').get_attribute('href') == 'style.css'
    assert page.locator('#development-status').is_visible()
    status = page.locator('#development-status').inner_text()
    for fragment in ['Сайт в разработке', 'демонстрационные данные', 'заказы, платежи, регистрация, магазины и выплаты ещё не запущены']:
        assert fragment in status
    assert page.locator('.role-list dt').all_text_contents() == ['Customer','Procurer','Manufacturer','Seller','Receiver','Moderator']
    text = page.locator('main').inner_text()
    for fragment in ['Home','Warehouse','Store','Sender Curator','Receiver Curator','Order Supervisor','IT/Admin/Finance/Compliance/Support','отдельными допусками','принимает её добровольно','подтверждает цену до оплаты','без предварительного выкупа','без вступительного взноса и регулярного роялти','не является прибылью магазина','P — не конечная цена покупателя','не операционный доход','автоматически не переносится','не гарантирует доход','значимые решения контролирует человек']:
        assert fragment in text, fragment
    chains = page.locator('.trade-chain').all_text_contents()
    assert len(chains) == 2
    assert all(name in chains[0] for name in ['Procurer','Manufacturer','Seller','Receiver','Customer'])
    assert all(name in chains[1] for name in ['Manufacturer','Store Receiver','Customer','POS'])
    assert page.locator('.purchase-steps li').count() == 6

    # Validate the visible example, not merely data-* fields or a hidden total.
    expected = [('Один источник: Procurer или Manufacturer или Seller',20,200),('Receiver',20,200),('Sender Curator',5,50),('Receiver Curator',5,50),('Order Supervisor',10,100),('Omnia-Mundi',20,200),('Protection Fund',20,200)]
    shares, amounts = [], []
    rows = page.locator('.profit-example tbody tr')
    assert rows.count() == 7
    for row, (label, share, cents) in zip(rows.all(), expected):
        assert row.locator('th').inner_text() == label
        shown_share = int(row.locator('td').nth(0).inner_text().replace('%',''))
        shown_cents = int(Decimal(row.locator('td').nth(1).inner_text().replace('€','').strip().replace(',','.')) * 100)
        assert shown_share == share and shown_cents == cents
        shares.append(shown_share); amounts.append(shown_cents)
    assert sum(shares) == 100 and sum(amounts) == 1000
    assert sum(shares[2:5]) == 20
    assert page.locator('.profit-example tfoot td').all_text_contents() == ['100%','10,00 €']

    for width in [320,375,390,430,768,1024,1440,1920,2560]:
        page.set_viewport_size({'width':width,'height':900})
        page.wait_for_timeout(30)
        assert page.evaluate('document.documentElement.scrollWidth<=innerWidth'), width
        container = page.locator('.page').bounding_box()
        assert abs(container['width']-min(width,1920)) < 1
        assert abs(container['x']-max(0,(width-1920)/2)) < 1
        assert page.locator('main').bounding_box()['width'] <= 850
        for selector in ['main p','main li','main dt','main dd','main th','main td','main h1','main h2','.header button','.primary-nav button','#footer-nav button','#footer-nav a']:
            assert page.locator(selector).evaluate_all('(nodes)=>nodes.every(n=>n.scrollWidth<=n.clientWidth+1&&n.scrollHeight<=n.clientHeight+1)'), (width,selector)
        header = page.locator('.header > *').evaluate_all('(nodes)=>nodes.map(n=>n.getBoundingClientRect().toJSON())')
        for i, first in enumerate(header):
            for second in header[i+1:]:
                assert min(first['right'],second['right'])-max(first['left'],second['left']) <= 1 or min(first['bottom'],second['bottom'])-max(first['top'],second['top']) <= 1, width
        for selector,size in [('main',16),('main h1',22),('.development-status',15),('main h2',18),('.profit-example',15)]:
            assert page.locator(selector).evaluate_all('(nodes,size)=>nodes.every(n=>parseFloat(getComputedStyle(n).fontSize)===size)',size), selector
        if width in [320,390,1440,1920]:
            Path('docs/screenshots').mkdir(parents=True,exist_ok=True)
            page.screenshot(path=f'docs/screenshots/how-it-works-{width}.png',full_page=True)
        # Native anchors are keyboard-operable and retain the shared visible focus style.
        search = page.get_by_role('link',name='Поиск товаров в каталоге',exact=True)
        search.focus()
        assert search.evaluate('(n)=>n===document.activeElement&&getComputedStyle(n).outlineStyle!=="none"')
        for button in page.locator('[data-future], #footer-nav button').all():
            button.focus(); page.keyboard.press('Enter')
            assert page.get_by_role('dialog').is_visible()
            assert page.locator('#notice-title').inner_text() == 'Раздел находится в разработке'
            assert page.evaluate('document.documentElement.scrollWidth<=innerWidth')
            page.keyboard.press('Escape')
            assert button.evaluate('(n)=>n===document.activeElement')
            button.evaluate('(n)=>n.blur()')
        print(f'PASS How It Works {width}px: readable content/table, shared shell, keyboard, placeholders')

    # Both directions plus search and logo are real HTTP navigation, not dialogs.
    assert page.locator('#footer-nav').get_by_role('link',name='Как это работает').get_attribute('aria-current') == 'page'
    page.get_by_role('link',name='Каталог',exact=True).click()
    assert page.url == base + '/index.html?lang=ru#catalog'
    assert page.locator('.products article').count() == 8
    link = page.locator('#footer-nav').get_by_role('link',name='Как это работает',exact=True)
    link.focus(); page.keyboard.press('Enter')
    expect(page).to_have_url(base + '/how-it-works.html?lang=ru')
    page.get_by_role('link',name='Поиск товаров в каталоге',exact=True).click()
    assert page.url == base + '/index.html?lang=ru#catalog'
    page.locator('#footer-nav').get_by_role('link',name='Как это работает').click()
    page.locator('.logo-link').click()
    assert page.url == base + '/index.html?lang=ru'
    assert page.locator('.products article').count() == 8
    assert not errors and not external and not failed, (errors,external,failed)
    # The informational text and return links work even if JavaScript is unavailable.
    nojs = browser.new_context(java_script_enabled=False)
    static = nojs.new_page()
    assert static.goto(base + '/how-it-works.html').status == 200
    assert static.get_by_role('heading',name='Как это работает',exact=True).is_visible()
    assert static.locator('#development-status').is_visible()
    assert static.locator('.profit-example tbody tr').count() == 7
    static.get_by_role('link',name='Вернуться в каталог').click()
    assert static.url == base + '/index.html#catalog'
    nojs.close()
    print('PASS content, 100% P example, navigation both ways, no external requests/JS errors/404, static reading without JS')
    browser.close()
