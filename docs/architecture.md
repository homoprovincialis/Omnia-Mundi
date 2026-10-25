# Architecture and scope — first increment

Status: working marketplace foundation, not a complete commercial platform.

## Requirements provenance

Only the requirements in the user's chat message were available. `Omnia-Mundi_Website_Technical_Specification_RU.txt` was not attached to the execution context or present in the workspace. All 29 sections and acceptance scenarios must be reviewed before claiming specification compliance. Unknown financial terms are blocked, never guessed.

## Stack and boundaries

Node.js 24 LTS, native HTTP server, SQLite through node:sqlite, native browser modules and responsive CSS. No third-party runtime dependencies. This deliberately small initial architecture runs without external services or credentials. SQLite WAL is a single-instance development store, not a distributed production database. Database tables cover users, hashed sessions, listings, product requests, sandbox reservations and actor audit events. API validation and permissions are server-side. A future deployment should separate identity, marketplace, fulfilment, finance ledger, inventory, learning, AI orchestration and integration adapters, with PostgreSQL migrations and durable jobs.

## Working capabilities

- Search/filter seeded sample catalog; supplier roles create persistent listings.
- Register Customer, Procurer, Manufacturer, Seller or Receiver; Receiver chooses Home, Warehouse or Store. Operating country is explicit. Moderator cannot self-register.
- Authentication with salted scrypt hashes and hashed expiring session tokens; HttpOnly/SameSite cookies, basic login throttling and origin validation.
- Product requests and voluntary acceptance by eligible participants in the request country. Atomic update prevents double assignment. No auto-assignment.
- Sandbox reservations use prices from the database, collect no money, and appear in the account dashboard.
- Actor-scoped activity journal and allocation preview with integer cents.

Self-selected participant roles are pilot declarations, not verified business credentials. Production onboarding and multi-role permissions need specification review.

## Financial boundaries

The preview splits already-distributable net profit into five equal shares: one goods source (Procurer OR Manufacturer OR Seller), Receiver, Moderator, Omnia-Mundi and Protection Fund. The API requires a single sourceType and returns sourceType plus source, receiver, moderator, omniaMundi and protectionFund amounts in cents. It divides Moderator's share into 5/5/10 proportions of the total. Business Connections uses 35/35/30; recipient mapping awaits the specification. Voluntary Free Goods rewards divide among actual participants plus Omnia-Mundi. Protection Fund receives its 20% allocation in the preview; no actual money is collected or transferred. No deposits, reimbursements, payouts or store costs are charged. Store Selling Cost remains a separate actual expense in the requirements, not profit. Largest-remainder rounding preserves cents; ties use the primary order source, Receiver, Moderator, Omnia-Mundi, Protection Fund. Moderator is then divided in 1:1:2 proportions, preserving its rounded primary share; internal ties follow 5%, 5%, 10% order. Rounding can differ from ideal percentages by fractional cents and requires business approval. No double-entry financial ledger or real settlement is implemented.

## Explicitly pending

Business Connections transactions; Free Goods lifecycle; stores/franchise operations, inventory, consignment and offline sales; Manufacturer Supply Network workflows; Academy content/progress; privileged Moderator provisioning/workflows; standard promotion and voluntary 50/50 campaigns; multilingual content; verified identity, password reset, email verification, MFA; AI assistants with human approvals; deposits, reimbursements, payout timing and Protection Fund; real payment, logistics and notification integrations. Navigation for pending modules is labelled accordingly. No fake integrations return financial success. Connect approved payment providers only behind a sandbox adapter and explicit production configuration.

## Security and scale limitations

Pilot only: do not expose publicly or use real personal/financial data. Add production-grade distributed throttling, durable audit immutability, CSRF tokens for hardened deployments, HTTPS/reverse-proxy host validation, business verification, GDPR retention/export/deletion, backups, observability, request timeouts, load tests, stock/idempotency semantics, and an independent security review before deployment. Current audit storage is application append-only, not tamper-proof. No deployment is authorized.

## API

GET /api/health, /api/config, /api/me, /api/listings?q=&country=&category=, /api/requests, /api/dashboard.
POST /api/register, /api/login, /api/logout, /api/listings, /api/requests, /api/requests/:id/accept, /api/orders, /api/finance/preview.

Mutation JSON bodies are size-limited; authenticated endpoints return 401, forbidden roles 403, conflicts 409. The public catalog contains sample data and must not be presented as real supplier offers.

## Next increment

Obtain the complete specification, create a section-by-section traceability matrix and acceptance suite, confirm accounting/rounding and legal flows, then implement identity/permissions and order lifecycle with migrations and a double-entry ledger. Expand each direction as an independently tested workflow. Preserve the branch/PR review policy.
