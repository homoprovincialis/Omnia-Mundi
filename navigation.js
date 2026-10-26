'use strict';
(() => {
  const i18n = window.OmniaI18n;
  const notice = document.querySelector('#notice');
  function showFuture() { if (!notice.open) notice.showModal(); }
  document.querySelectorAll('[data-future]').forEach(button => button.addEventListener('click', showFuture));
  i18n.subscribe(() => {
    document.querySelector('#notice-title').textContent = i18n.t('common.future');
    document.querySelector('#notice-close').textContent = i18n.t('common.close');
    const footer = document.querySelector('#footer-nav');
    footer.replaceChildren();
    for (const entry of window.OMNIA_DATA.footer) {
      const item = document.createElement(entry.href ? 'a' : 'button');
      item.textContent = i18n.t('footer.' + entry.id);
      if (entry.href) {
        item.href = i18n.link(entry.href);
        if (location.pathname.endsWith('/' + entry.href)) item.setAttribute('aria-current', 'page');
      } else {
        item.type = 'button';
        item.addEventListener('click', showFuture);
      }
      footer.append(item);
    }
  });
})();
