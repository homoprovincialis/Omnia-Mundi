"""Real Chromium checks. Run against a local static server; never deploys."""
import argparse
import math
from pathlib import Path
import hashlib
import json
import subprocess
from playwright.sync_api import sync_playwright

parser = argparse.ArgumentParser()
parser.add_argument('--url', default='http://127.0.0.1:3010')
parser.add_argument('--layout-only', action='store_true', help='Skip photo readiness and final screenshots while source access is blocked')
args = parser.parse_args()

def assert_product_alignment(page):
    products = page.locator('.products article').evaluate_all("""(articles)=>articles.map(article=>{
        const image=article.querySelector('img').getBoundingClientRect();
        return {imageCenter:image.x+image.width/2,
            texts:[...article.querySelectorAll('h2,.price,.country')].map(node=>{
                const box=node.getBoundingClientRect();
                const range=document.createRange(); range.selectNodeContents(node);
                return {text:node.textContent, align:getComputedStyle(node).textAlign,
                    center:box.x+box.width/2,
                    lines:[...range.getClientRects()].map(line=>line.x+line.width/2)};
            })};
    })""")
    for product in products:
        assert len(product['texts']) == 3, product
        for text in product['texts']:
            assert text['align'] == 'center', text
            assert abs(text['center'] - product['imageCenter']) < 1, text
            assert text['lines'] and all(abs(center - product['imageCenter']) < 1 for center in text['lines']), text

with sync_playwright() as p:
    browser = p.chromium.launch(executable_path='/usr/bin/chromium', headless=True, args=['--no-sandbox'])
    page = browser.new_page(viewport={'width': 1440, 'height': 900})
    errors, external_requests = [], []
    page.on('pageerror', lambda error: errors.append(str(error)))
    page.on('request', lambda request: external_requests.append(request.url) if not request.url.startswith(args.url.rstrip('/') + '/') else None)
    page.goto(args.url)
    for width in [320, 375, 390, 430, 768, 1024, 1440, 1920, 2560]:
        page.set_viewport_size({'width': width, 'height': 900})
        page.wait_for_timeout(50)
        assert page.evaluate('document.documentElement.scrollWidth <= innerWidth'), width
        container = page.locator('.page').bounding_box()
        assert abs(container['width'] - min(width, 1920)) < 1, (width, container)
        assert abs(container['x'] - max(0, (width - 1920) / 2)) < 1, (width, container)
        positions = page.locator('.products img').evaluate_all('(imgs)=>imgs.map(i=>({w:i.getBoundingClientRect().width,h:i.getBoundingClientRect().height,x:i.getBoundingClientRect().x,y:i.getBoundingClientRect().y}))')
        assert len(positions) == 8
        assert all(i['w'] == 157 and i['h'] == 157 for i in positions)
        assert_product_alignment(page)
        assert page.locator('.products h2').filter(has_text='Часы').count() == 1
        available = page.locator('.products').bounding_box()['width']
        columns = min(8, math.floor((available + 12) / 169))
        assert len({i['x'] for i in positions}) == columns, (width, available, columns)
        assert len({i['y'] for i in positions}) == math.ceil(8 / columns)
        if width >= 1920:
            assert columns == 8
        if width >= 640:
            assert abs(page.locator('.catalog').bounding_box()['x'] + page.locator('.catalog').bounding_box()['width'] - page.locator('.layout').bounding_box()['x'] - page.locator('.layout').bounding_box()['width']) < 1
        if not args.layout_only:
            assert page.locator('.products img').evaluate_all('(imgs)=>imgs.every(i=>i.complete && i.naturalWidth>0)'), 'Photos must be local and loaded'
            if width in [320, 390, 430, 1440, 1920, 2560]:
                Path('docs/screenshots').mkdir(parents=True, exist_ok=True)
                page.screenshot(path=f'docs/screenshots/homepage-{width}.png', full_page=True)
        # Verify every formerly small text group at every breakpoint, not only :root.
        typography = {
            '.primary-nav a': 16, '.primary-nav button': 16, '#search': 16,
            '.account-actions button': 16, '#categories button': 16,
            '.filters h2': 16, '.filters p': 15, '.products h2': 16,
            '.price': 16, '.country': 15, '.demo-label': 15,
            '.catalog-heading h1': 22, '#filter-toggle': 16,
            'footer button': 16, '.image-sources': 15, 'dialog': 16,
        }
        for selector, expected in typography.items():
            assert page.locator(selector).evaluate_all('(nodes,size)=>nodes.every(n=>parseFloat(getComputedStyle(n).fontSize)===size)', expected), (width, selector)
        # Exercise expanded filters and credits at all widths, including narrow phones.
        filters_were_hidden = page.locator('#filters').evaluate('(n)=>n.hidden')
        page.locator('#filters').evaluate('(n)=>n.hidden=false')
        page.locator('.image-sources').evaluate('(n)=>n.open=true')
        assert page.evaluate('document.documentElement.scrollWidth <= innerWidth'), width
        for selector in ['.header button', '.primary-nav a', '.primary-nav button', '#categories button', '.filters h2', '.filters p', '.products h2', '.products p', 'footer button', '.image-sources li']:
            assert page.locator(selector).evaluate_all('(nodes)=>nodes.every(n=>n.scrollWidth<=n.clientWidth+1 && n.scrollHeight<=n.clientHeight+1)'), (width, selector)
        page.locator('#filters').evaluate('(n,hidden)=>n.hidden=hidden', filters_were_hidden)
        page.locator('.image-sources').evaluate('(n)=>n.open=false')
        # The larger header controls must not overlap when they wrap on small screens.
        header_boxes = page.locator('.header > *').evaluate_all('(nodes)=>nodes.map(n=>n.getBoundingClientRect().toJSON())')
        for i, first in enumerate(header_boxes):
            for second in header_boxes[i + 1:]:
                overlap_x = min(first['right'], second['right']) - max(first['left'], second['left'])
                overlap_y = min(first['bottom'], second['bottom']) - max(first['top'], second['top'])
                assert overlap_x <= 1 or overlap_y <= 1, (width, first, second)
        login = page.get_by_role('button', name='Войти', exact=True)
        login.focus()
        page.keyboard.press('Enter')
        assert page.get_by_role('dialog').is_visible()
        assert page.locator('#notice').evaluate('(n)=>n.scrollWidth<=n.clientWidth+1 && n.scrollHeight<=n.clientHeight+1')
        assert page.evaluate('document.documentElement.scrollWidth <= innerWidth'), width
        page.keyboard.press('Escape')
        assert login.evaluate('(n)=>n===document.activeElement')
        login.evaluate('(n)=>n.blur()')
        # Long translated names must wrap rather than clip or widen a column.
        title = page.locator('.products h2').first
        original = title.inner_text()
        title.evaluate('(title)=>title.textContent="Очень длинное название демонстрационного товара / Long translated product name ".repeat(3)')
        assert title.evaluate('(title)=>title.scrollWidth<=title.clientWidth && title.scrollHeight<=title.clientHeight')
        assert page.evaluate('document.documentElement.scrollWidth <= innerWidth'), width
        assert_product_alignment(page)
        title.evaluate('(title,text)=>title.textContent=text', original)
        print(f'PASS {width}px: {columns} columns, all product text centered, 157px photos, fonts, overflow and keyboard')
    # More products must use more columns when space permits, without a hidden 8-column cap.
    page.locator('.products').evaluate('(grid)=>{for(let i=0;i<12;i++)grid.append(grid.firstElementChild.cloneNode(true));}')
    expanded = page.locator('.products img').evaluate_all('(imgs)=>imgs.map(i=>i.getBoundingClientRect().x)')
    assert len(set(expanded)) == math.floor((page.locator('.products').bounding_box()['width'] + 12) / 169)
    assert len(set(expanded)) > 8
    page.locator('.products').evaluate('(grid)=>{while(grid.children.length>8)grid.lastElementChild.remove();}')
    print('PASS additional demo cards use available width inside centered 1920px container at 2560px')
    page.set_viewport_size({'width': 390, 'height': 900})
    page.get_by_role('button', name='Фильтры', exact=True).click()
    assert page.locator('#filters').is_visible()
    page.get_by_role('button', name='Электроника', exact=True).click()
    assert page.locator('.products article').count() == 1
    page.get_by_role('searchbox').fill('чашка')
    assert page.locator('.products article').count() == 0
    page.get_by_role('button', name='Все товары', exact=True).click()
    assert page.locator('.products article').count() == 1
    page.get_by_role('searchbox').fill('лампа')
    assert page.locator('.products article').count() == 1
    page.get_by_role('searchbox').fill('несуществующий товар')
    assert page.locator('.products article').count() == 0
    assert page.locator('#empty').is_visible()
    page.get_by_role('searchbox').fill('')
    assert page.locator('.products article').count() == 8
    for button in page.locator('[data-future], #footer-nav button').all():
        button.click()
        assert page.get_by_role('dialog').is_visible()
        assert page.locator('#notice-title').inner_text() == 'Раздел находится в разработке'
        page.keyboard.press('Escape')
        assert not page.get_by_role('dialog').is_visible()
        assert button.evaluate('(b)=>b===document.activeElement')
    page.set_viewport_size({'width': 1440, 'height': 900})
    page.get_by_role('button', name='Фильтры', exact=True).click()
    assert page.get_by_role('button', name='Все товары', exact=True).evaluate('(b)=>b===document.activeElement')
    page.get_by_role('link', name='Каталог', exact=True).click()
    assert page.url.endswith('#catalog')
    print('PASS search, combined categories, empty state, responsive filters, future controls, focus and keyboard')
    page.get_by_text('Источники изображений', exact=True).click()
    credits = page.locator('.image-sources li')
    assert credits.count() == 8
    manifest = json.loads(Path('assets/products/sources.json').read_text())
    for credit in manifest:
        image_path = Path(credit['file'])
        assert hashlib.sha256(image_path.read_bytes()).hexdigest() == credit['sha256']
        item = credits.filter(has_text=credit['title'])
        assert item.count() == 1 and item.is_visible()
        assert credit['author'] in item.inner_text()
        assert credit['changes'] in item.inner_text()
        assert item.locator('a').nth(0).get_attribute('href') == credit['source']
        assert item.locator('a').nth(1).get_attribute('href') == credit['licenseUrl']
        assert credit['license'] in item.inner_text()
    page.set_viewport_size({'width': 390, 'height': 900})
    assert page.evaluate('document.documentElement.scrollWidth <= innerWidth')
    page.locator('.image-sources summary').focus()
    page.keyboard.press('Space')
    assert not page.locator('.image-sources').evaluate('(d)=>d.open')
    wallet = next(c for c in manifest if c['id'] == 'wallet')
    assert wallet['author'] == 'Pixloom' and wallet['license'] == 'CC BY-SA 4.0'
    assert not errors, errors
    assert not external_requests, external_requests
    # Immutable owner-provided inputs must match the base branch byte for byte.
    for name in ['assets/omnia-mundi-logo.svg', 'Omnia-Mundi_Website_Technical_Specification_RU.txt', 'Omnia-Mundi_Codex_Homepage_Phase_1_RU.txt', 'index.html', 'app.js', 'strings.ru.js', 'ASSETS.md', 'assets/products/sources.json']:
        assert Path(name).read_bytes() == subprocess.check_output(['git', 'show', f'origin/main:{name}'])
    print('PASS eight attributed local assets, hashes, wallet ShareAlike notice, no external requests or JS errors, unchanged logo and TXT')
    browser.close()
