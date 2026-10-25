/* Localized interface copy and demo content; no real offers or availability. */
window.OMNIA_RU = {
  future: 'Раздел находится в разработке',
  close: 'Закрыть',
  empty: 'Демонстрационные товары не найдены. Измените поиск или категорию.',
  count: count => `Показано демонстрационных товаров: ${count}`,
  categories: [
    ['all', 'Все товары'], ['electronics', 'Электроника'], ['home', 'Для дома'],
    ['clothing', 'Одежда'], ['accessories', 'Аксессуары'], ['tools', 'Инструменты'], ['other', 'Другое']
  ],
  footer: ['Как это работает', 'Зарабатывать с Omnia-Mundi', 'Сеть Receiver',
    'Магазины Omnia-Mundi', 'Сеть поставок производителей', 'Omnia-Mundi Academy',
    'Business Connections', 'Цены и прозрачность', 'О проекте', 'Контакты',
    'Помощь', 'Правила', 'Конфиденциальность', 'Условия использования', 'Возвраты', 'Cookies'],
  // Fictional prices and countries are visual examples only, not seller assertions.
  products: [
    {id:'headphones', name:'Наушники', category:'electronics', cents:3990, country:'Германия'},
    {id:'cup', name:'Чашка', category:'home', cents:1250, country:'Португалия'},
    {id:'wallet', name:'Кошелёк', category:'accessories', cents:2400, country:'Италия'},
    {id:'lamp', name:'Настольная лампа', category:'home', cents:4500, country:'Франция'},
    {id:'bag', name:'Сумка', category:'accessories', cents:2990, country:'Испания'},
    {id:'thermos', name:'Термос', category:'other', cents:1890, country:'Австрия'},
    {id:'drill', name:'Шуруповёрт', category:'tools', cents:6990, country:'Германия'},
    {id:'watch', name:'Часы', category:'accessories', cents:5500, country:'Нидерланды'}
  ]
};
