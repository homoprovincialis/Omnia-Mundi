"""Real Chromium checks. Run against a local static server; never deploys."""
import argparse
from pathlib import Path
from playwright.sync_api import sync_playwright

parser = argparse.ArgumentParser()
parser.add_argument('--url', default='http://127.0.0.1:3010')
parser.add_argument('--layout-only', action='store_true', help='Skip photo readiness and final screenshots while source access is blocked')
args = parser.parse_args()
with sync_playwright() as p:
    browser = p.chromium.launch(executable_path='/usr/bin/chromium', headless=True, args=['--no-sandbox'])
    page = browser.new_page(viewport={'width': 1440, 'height': 900})
    page.goto(args.url)
    for width in [320, 375, 390, 768, 1024, 1440]:
        page.set_viewport_size({'width': width, 'height': 900})
        page.wait_for_timeout(50)
        assert page.evaluate('document.documentElement.scrollWidth <= innerWidth'), width
        positions = page.locator('.products img').evaluate_all('(imgs)=>imgs.map(i=>({w:i.width,h:i.height,x:i.getBoundingClientRect().x,y:i.getBoundingClientRect().y}))')
        assert len(positions) == 8
        assert all(i['w'] == 118 and i['h'] == 118 for i in positions)
        assert len({i['x'] for i in positions}) == (2 if width < 640 else 4)
        if not args.layout_only:
            assert page.locator('.products img').evaluate_all('(imgs)=>imgs.every(i=>i.complete && i.naturalWidth>0)'), 'Photos must be local and loaded'
            if width in [390, 1440]:
                Path('docs/screenshots').mkdir(parents=True, exist_ok=True)
                page.screenshot(path=f'docs/screenshots/homepage-{width}.png', full_page=True)
        print(f'PASS layout {width}px')
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
    browser.close()
