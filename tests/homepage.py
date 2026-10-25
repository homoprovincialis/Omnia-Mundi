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
with sync_playwright() as p:
    browser = p.chromium.launch(executable_path='/usr/bin/chromium', headless=True, args=['--no-sandbox'])
    page = browser.new_page(viewport={'width': 1440, 'height': 900})
    errors, external_requests = [], []
    page.on('pageerror', lambda error: errors.append(str(error)))
    page.on('request', lambda request: external_requests.append(request.url) if not request.url.startswith(args.url.rstrip('/') + '/') else None)
    page.goto(args.url)
    for width in [320, 375, 390, 768, 1024, 1440, 1920]:
        page.set_viewport_size({'width': width, 'height': 900})
        page.wait_for_timeout(50)
        assert page.evaluate('document.documentElement.scrollWidth <= innerWidth'), width
        positions = page.locator('.products img').evaluate_all('(imgs)=>imgs.map(i=>({w:i.getBoundingClientRect().width,h:i.getBoundingClientRect().height,x:i.getBoundingClientRect().x,y:i.getBoundingClientRect().y}))')
        assert len(positions) == 8
        assert all(i['w'] == 118 and i['h'] == 118 for i in positions)
        available = page.locator('.products').bounding_box()['width']
        columns = min(8, 2 if width < 640 else math.floor((available + 12) / 130))
        assert len({i['x'] for i in positions}) == columns, (width, available, columns)
        assert len({i['y'] for i in positions}) == math.ceil(8 / columns)
        if width >= 1440:
            assert columns == 8
        if width >= 640:
            assert abs(page.locator('.catalog').bounding_box()['x'] + page.locator('.catalog').bounding_box()['width'] - page.locator('.layout').bounding_box()['x'] - page.locator('.layout').bounding_box()['width']) < 1
        if not args.layout_only:
            assert page.locator('.products img').evaluate_all('(imgs)=>imgs.every(i=>i.complete && i.naturalWidth>0)'), 'Photos must be local and loaded'
            if width in [390, 1440, 1920]:
                Path('docs/screenshots').mkdir(parents=True, exist_ok=True)
                page.screenshot(path=f'docs/screenshots/homepage-{width}.png', full_page=True)
        print(f'PASS layout {width}px: {columns} columns')
    # More products must use more columns when space permits, without a hidden 8-column cap.
    page.locator('.products').evaluate('(grid)=>{for(let i=0;i<12;i++)grid.append(grid.firstElementChild.cloneNode(true));}')
    expanded = page.locator('.products img').evaluate_all('(imgs)=>imgs.map(i=>i.getBoundingClientRect().x)')
    assert len(set(expanded)) == math.floor((page.locator('.products').bounding_box()['width'] + 12) / 130)
    assert len(set(expanded)) > 8
    page.locator('.products').evaluate('(grid)=>{while(grid.children.length>8)grid.lastElementChild.remove();}')
    print('PASS additional demo cards expand beyond eight columns at 1920px')
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
    for name in ['assets/omnia-mundi-logo.svg', 'Omnia-Mundi_Website_Technical_Specification_RU.txt', 'Omnia-Mundi_Codex_Homepage_Phase_1_RU.txt']:
        assert Path(name).read_bytes() == subprocess.check_output(['git', 'show', f'origin/main:{name}'])
    print('PASS eight attributed local assets, hashes, wallet ShareAlike notice, no external requests or JS errors, unchanged logo and TXT')
    browser.close()
