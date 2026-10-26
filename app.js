'use strict';
(() => {
  const i18n = window.OmniaI18n;
  const data = window.OMNIA_DATA;
  const query = document.querySelector('#search');
  const categoryList = document.querySelector('#categories');
  const grid = document.querySelector('#products');
  const filterToggle = document.querySelector('#filter-toggle');
  const filters = document.querySelector('#filters');
  const mobile = window.matchMedia('(max-width: 639px)');
  let selectedCategory = 'all';
  let credits = [];

  for (const id of data.categories) {
    const button = document.createElement('button');
    button.type = 'button';
    button.dataset.category = id;
    button.setAttribute('aria-pressed', String(id === selectedCategory));
    button.addEventListener('click', () => {
      selectedCategory = id;
      categoryList.querySelectorAll('button').forEach(b => b.setAttribute('aria-pressed', String(b === button)));
      render();
    });
    categoryList.append(button);
  }
  function render() {
    categoryList.querySelectorAll('button').forEach(button => {
      button.textContent = i18n.t('category.' + button.dataset.category);
    });
    const term = query.value.trim().toLocaleLowerCase(i18n.locale);
    const matches = data.products.filter(product =>
      (selectedCategory === 'all' || product.category === selectedCategory) &&
      i18n.t('product.' + product.id).toLocaleLowerCase(i18n.locale).includes(term));
    const money = new Intl.NumberFormat(i18n.locale, {style:'currency', currency:'EUR'});
    grid.replaceChildren();
    for (const product of matches) {
      const article = document.createElement('article');
      article.dataset.product = product.id;
      const image = document.createElement('img');
      image.src = `assets/products/${product.id}.jpg`;
      image.alt = i18n.t('product.' + product.id); image.width = 157; image.height = 157;
      const title = document.createElement('h2'); title.textContent = image.alt;
      const price = document.createElement('p'); price.className = 'price'; price.textContent = money.format(product.cents / 100);
      const country = document.createElement('p'); country.className = 'country'; country.textContent = i18n.t('country.' + product.country);
      article.append(image, title, price, country); grid.append(article);
    }
    const empty = document.querySelector('#empty');
    empty.hidden = matches.length !== 0; empty.textContent = i18n.t('catalog.empty');
    document.querySelector('#result-status').textContent = i18n.t('catalog.count', {count:matches.length});
    renderCredits();
  }
  const sources = document.createElement('details');
  sources.className = 'image-sources';
  document.querySelector('footer').append(sources);
  function renderCredits() {
    const summary = document.createElement('summary'); summary.textContent = i18n.t('sources.title');
    const explanation = document.createElement('p'); explanation.textContent = i18n.t('sources.credit');
    const list = document.createElement('ul');
    for (const credit of credits) {
      const item = document.createElement('li');
      const source = document.createElement('a'); source.href = credit.source; source.textContent = credit.title;
      const license = document.createElement('a'); license.href = credit.licenseUrl; license.textContent = credit.license;
      // The museum note is descriptive copy, not part of its proper name.
      const noteKey = data.sourceNotes[credit.id];
      const author = noteKey ? credit.author.split(' (')[0] : credit.author;
      const note = noteKey ? ` (${i18n.t(noteKey)})` : '';
      item.append(`${i18n.t('product.' + credit.id)}: ${author}${note}. `,
        source, ' — ', license, `. ${i18n.t('sources.changes')}`);
      list.append(item);
    }
    sources.replaceChildren(summary, explanation, list);
  }
  function syncFilters() {
    filters.hidden = mobile.matches;
    filterToggle.setAttribute('aria-expanded', String(!filters.hidden));
  }
  filterToggle.addEventListener('click', () => {
    if (mobile.matches) {
      filters.hidden = !filters.hidden;
      filterToggle.setAttribute('aria-expanded', String(!filters.hidden));
    }
    if (!filters.hidden) categoryList.querySelector('button').focus();
  });
  mobile.addEventListener('change', syncFilters);
  document.querySelector('.search').addEventListener('submit', event => event.preventDefault());
  query.addEventListener('input', render);
  syncFilters();
  i18n.subscribe(render);
  // A single unchanged local manifest is authoritative for authors, titles and licenses.
  window.omniaReady = fetch('assets/products/sources.json').then(response => {
    if (!response.ok) throw new Error('Image metadata unavailable');
    return response.json();
  }).then(manifest => { credits = manifest; renderCredits(); });
})();
