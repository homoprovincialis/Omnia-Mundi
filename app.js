'use strict';
const copy = window.OMNIA_RU;
const query = document.querySelector('#search');
const categoryList = document.querySelector('#categories');
const grid = document.querySelector('#products');
const filterToggle = document.querySelector('#filter-toggle');
const filters = document.querySelector('#filters');
const mobile = window.matchMedia('(max-width: 639px)');
let selectedCategory = 'all';
const formatPrice = new Intl.NumberFormat('ru-RU', {style:'currency', currency:'EUR'});

for (const [id, label] of copy.categories) {
  const button = document.createElement('button');
  button.type = 'button'; button.textContent = label;
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
  const term = query.value.trim().toLocaleLowerCase('ru');
  const matches = copy.products.filter(p => (selectedCategory === 'all' || p.category === selectedCategory) && p.name.toLocaleLowerCase('ru').includes(term));
  grid.replaceChildren();
  for (const product of matches) {
    const article = document.createElement('article');
    const image = document.createElement('img');
    image.src = `assets/products/${product.id}.jpg`;
    image.alt = product.name; image.width = 118; image.height = 118;
    const title = document.createElement('h2'); title.textContent = product.name;
    const price = document.createElement('p'); price.className = 'price'; price.textContent = formatPrice.format(product.cents / 100);
    const country = document.createElement('p'); country.className = 'country'; country.textContent = product.country;
    article.append(image, title, price, country); grid.append(article);
  }
  const empty = document.querySelector('#empty');
  empty.hidden = matches.length !== 0; empty.textContent = copy.empty;
  document.querySelector('#result-status').textContent = copy.count(matches.length);
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
render();

// Real attribution is distinct from unfinished commercial navigation.
const sources = document.createElement('details');
sources.className = 'image-sources';
const summary = document.createElement('summary');
summary.textContent = copy.sourcesTitle;
const explanation = document.createElement('p');
explanation.textContent = copy.sourcesCredit;
const credits = document.createElement('ul');
for (const credit of copy.assetCredits) {
  const item = document.createElement('li');
  const source = document.createElement('a');
  source.href = credit.source;
  source.textContent = credit.title;
  const license = document.createElement('a');
  license.href = credit.licenseUrl;
  license.textContent = credit.license;
  item.append(`${credit.label}: ${credit.author}. `, source, ' — ', license, `. ${credit.changes}`);
  credits.append(item);
}
sources.append(summary, explanation, credits);
document.querySelector('footer').append(sources);
