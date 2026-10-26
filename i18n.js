'use strict';
// Local dictionaries only. URL > stored preference > RU; storage is optional.
(() => {
  const dictionaries = window.OMNIA_MESSAGES;
  const supported = Object.keys(dictionaries);
  const valid = value => supported.includes(value);
  const listeners = new Set();
  let stored;
  try { stored = localStorage.getItem('omnia.language'); } catch { /* URL remains sufficient. */ }
  const requested = new URL(location.href).searchParams.get('lang');
  let language = valid(requested) ? requested : valid(stored) ? stored : 'ru';

  function t(key, params = {}) {
    const value = dictionaries[language][key];
    if (typeof value !== 'string') throw new Error(`Missing ${language} translation: ${key}`);
    return value.replace(/\{(\w+)\}/g, (_, name) => {
      if (!(name in params)) throw new Error(`Missing translation parameter: ${name}`);
      return String(params[name]);
    });
  }
  function link(href) {
    const url = new URL(href, location.href);
    if (url.origin !== location.origin || !url.pathname.endsWith('.html')) return href;
    url.searchParams.set('lang', language);
    return url.pathname + url.search + url.hash;
  }
  function localizeLinks() {
    document.querySelectorAll('a[href]').forEach(anchor => {
      const href = anchor.getAttribute('href');
      if (!href.startsWith('#')) anchor.setAttribute('href', link(href));
    });
  }
  function applyRich(node, value) {
    // Only fixed local translation copy can contain inline emphasis, never user input.
    const template = document.createElement('template');
    template.innerHTML = value;
    if ([...template.content.querySelectorAll('*')].some(n => n.tagName !== 'STRONG' || n.attributes.length)) {
      throw new Error('Unsupported translation markup');
    }
    node.replaceChildren(template.content);
  }
  function apply() {
    document.documentElement.lang = language;
    document.querySelectorAll('[data-i18n]').forEach(node => { node.textContent = t(node.dataset.i18n); });
    document.querySelectorAll('[data-i18n-html]').forEach(node => applyRich(node, t(node.dataset.i18nHtml)));
    for (const attr of ['aria-label', 'placeholder', 'content']) {
      document.querySelectorAll(`[data-i18n-${attr}]`).forEach(node => {
        node.setAttribute(attr, t(node.getAttribute(`data-i18n-${attr}`)));
      });
    }
    document.querySelectorAll('[data-language]').forEach(button => {
      button.setAttribute('aria-pressed', String(button.dataset.language === language));
      button.setAttribute('aria-label', t('common.' + button.dataset.language));
    });
    listeners.forEach(listener => listener());
    localizeLinks();
  }
  function setLanguage(next) {
    if (!valid(next)) return false;
    language = next;
    const url = new URL(location.href);
    url.searchParams.set('lang', language);
    history.replaceState(null, '', url);
    try { localStorage.setItem('omnia.language', language); } catch { /* No persistence permission needed. */ }
    apply();
    return true;
  }
  window.OmniaI18n = Object.freeze({
    t, link, setLanguage,
    get language() { return language; },
    get locale() { return language === 'ru' ? 'ru-RU' : 'en-IE'; },
    subscribe(listener) { listeners.add(listener); listener(); return () => listeners.delete(listener); },
  });
  document.querySelectorAll('[data-language]').forEach(button => {
    button.addEventListener('click', () => setLanguage(button.dataset.language));
  });
  setLanguage(language);
})();
