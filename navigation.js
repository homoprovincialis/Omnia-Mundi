'use strict';
// Shared, catalog-independent footer and honest future-feature dialogs.
(() => {
  const copy = window.OMNIA_RU;
  const notice = document.querySelector('#notice');
  function showFuture() { if (!notice.open) notice.showModal(); }
  document.querySelector('#notice-title').textContent = copy.future;
  document.querySelector('#notice-close').textContent = copy.close;
  document.querySelectorAll('[data-future]').forEach(button => button.addEventListener('click', showFuture));
  for (const label of copy.footer) {
    // The first approved footer item is the only implemented informational route.
    const implemented = label === copy.footer[0];
    const item = document.createElement(implemented ? 'a' : 'button');
    item.textContent = label;
    if (implemented) {
      item.href = 'how-it-works.html';
      if (location.pathname.endsWith('/how-it-works.html')) item.setAttribute('aria-current', 'page');
    } else {
      item.type = 'button';
      item.addEventListener('click', showFuture);
    }
    document.querySelector('#footer-nav').append(item);
  }
})();
