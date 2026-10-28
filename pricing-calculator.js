'use strict';
// Demonstration only: no payment, order, tax determination or network activity.
(() => {
  const root = document.querySelector('#pricing-calculator');
  if (!root) return;
  const i18n = window.OmniaI18n;
  const inputs = {
    product: root.querySelector('#pricing-product'),
    shipping: root.querySelector('#pricing-shipping'),
    other: root.querySelector('#pricing-other'),
    ssc: root.querySelector('#pricing-ssc'),
    tax: root.querySelector('#pricing-tax'),
  };
  const routes = [...root.querySelectorAll('input[name="pricing-route"]')];
  const sscField = root.querySelector('#pricing-ssc-field');
  const receiverLabel = root.querySelector('#pricing-receiver-label');
  const error = root.querySelector('#pricing-error');
  const outputs = Object.fromEntries(
    [...root.querySelectorAll('[data-calc]')].map(node => [node.dataset.calc, node])
  );
  const defaultValues = {product:'50',shipping:'5',other:'0',ssc:'8',tax:'0'};
  const roles = [
    ['source', 20], ['receiver', 20], ['sender', 5],
    ['curator', 5], ['supervisor', 10], ['platform', 20], ['fund', 20],
  ];
  function parseScaled(value, maximum) {
    const text = value.trim().replace(',', '.');
    if (!/^(?:\d+)(?:\.\d{1,2})?$/.test(text)) return null;
    const [whole, fraction=''] = text.split('.');
    const scaled = Number(whole) * 100 + Number(fraction.padEnd(2, '0'));
    return Number.isSafeInteger(scaled) && scaled >= 0 && scaled <= maximum ? scaled : null;
  }
  function format(cents) {
    return new Intl.NumberFormat(i18n.locale, {
      style:'currency', currency:'EUR', minimumFractionDigits:2, maximumFractionDigits:2
    }).format(cents / 100);
  }
  // Divide integer cents using largest-remainder allocation so totals reconcile exactly.
  function allocate(cents) {
    const allocated = roles.map(([name, share], index) => {
      const product = cents * share;
      return {name, index, cents: Math.floor(product / 100), remainder: product % 100};
    });
    let remaining = cents - allocated.reduce((sum, item) => sum + item.cents, 0);
    const order = [...allocated].sort((a, b) => b.remainder - a.remainder || a.index - b.index);
    for (const item of order) {
      if (remaining <= 0) break;
      item.cents++;
      remaining--;
    }
    return Object.fromEntries(allocated.map(item => [item.name, item.cents]));
  }
  function render() {
    const inStore = routes.find(r => r.checked)?.value === 'store';
    sscField.hidden = !inStore;
    inputs.ssc.disabled = !inStore;
    receiverLabel.dataset.i18n = inStore ? 'pricing.calc.receiverStore' : 'pricing.calc.receiver';
    receiverLabel.textContent = i18n.t(receiverLabel.dataset.i18n);
    const parsed = Object.fromEntries(Object.entries(inputs).map(([key, el]) => [
      key, parseScaled(el.value, key === 'tax' ? 10000 : 100000000)
    ]));
    const valid = Object.entries(parsed).every(([key, value]) => (key === 'ssc' && !inStore) || value !== null);
    error.hidden = valid;
    for (const [key, el] of Object.entries(inputs)) {
      el.setAttribute('aria-invalid', String(!(key === 'ssc' && !inStore) && parsed[key] === null));
    }
    if (!valid) {
      Object.values(outputs).forEach(el => { el.textContent = '—'; });
      return;
    }
    const costs = parsed.product + parsed.shipping + parsed.other + (inStore ? parsed.ssc : 0);
    const profit = Math.round(costs * 30 / 100);
    const beforeTax = costs + profit;
    // The manually entered example tax rate is expressed in hundredths of a percent.
    const tax = Math.round(beforeTax * parsed.tax / 10000);
    const final = beforeTax + tax;
    const allocation = allocate(profit);
    const values = {
      cost:costs, profit, beforeTax, tax, final, ...allocation,
      distributed:Object.values(allocation).reduce((sum, value) => sum + value, 0),
    };
    for (const [key, el] of Object.entries(outputs)) el.textContent = format(values[key]);
  }
  Object.values(inputs).forEach(input => input.addEventListener('input', render));
  routes.forEach(radio => radio.addEventListener('change', render));
  root.querySelector('#pricing-reset').addEventListener('click', () => {
    Object.entries(defaultValues).forEach(([key, value]) => { inputs[key].value = value; });
    routes.find(r => r.value === 'store').checked = true;
    render();
  });
  i18n.subscribe(render);
})();