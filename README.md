# Omnia-Mundi — Trade Without Borders

A working **sandbox marketplace foundation** for a community-powered international trading platform. First geography: eurozone. Currency: EUR. The interface is currently English; additional locales are planned.

## Run

Requires Node.js 24+ (native SQLite). No external services, keys or dependencies required.

```sh
cd /workspace/Omnia-Mundi
npm ci
npm test
npm start
```

The server binds to `127.0.0.1:3000`. Open it in a local development browser. `npm run dev` enables server reload. Data persists in `data/omnia.sqlite` (ignored by Git); tests use an isolated temporary database. Node may emit its experimental SQLite warning.

Configuration: `PORT` (default 3000), `HOST` (default 127.0.0.1), `DATA_DIR` (default repository data directory), `PUBLIC_ORIGIN` (canonical origin; HTTPS enables Secure session cookies). Do not commit `.env` or credentials. No dotenv loader is included; export variables through your shell/environment settings.

## Try the workflow

1. Browse/search the sample catalog and filter by country/category.
2. Register an account with a password of at least 12 characters. Choose a role and operating country. Receiver supports Home, Warehouse and Store.
3. Reserve a sample product; verify the test reservation in your dashboard. **No payment is collected.**
4. Create a product request. Use another supplier account in the same country to voluntarily accept it.
5. Register as Manufacturer, Seller or Procurer to create a listing.
6. Open “Explore more” → “Transparent finance” to calculate the approved profit splits.

`npm test` exercises real HTTP endpoints, authentication, permissions, request acceptance, reservations, audit visibility and cent-conserving finance calculations. It does not yet cover browser rendering or production integrations.

## Scope and pending requirements

This is the first functional increment, not the full platform. Business Connections, Free Goods, Stores, Manufacturer Supply Network and Academy have clearly marked planned-module pages; their transactions/workflows are not implemented. No real payments, shipping, advertising campaigns or AI service is connected.

The referenced 29-section `Omnia-Mundi_Website_Technical_Specification_RU.txt` was not available during implementation. Financial rules beyond the supplied chat requirements remain blocked rather than invented. See [architecture and development roadmap](docs/architecture.md) and [permanent development rules](AGENTS.md).

Work only in feature branches and review through pull requests. Never merge, deploy, or change repository privacy without explicit permission.
