# Omnia-Mundi development rules

- Work in separate branches and open pull requests. Never merge main, deploy, or change repository visibility without explicit permission.
- Read docs/architecture.md and the full approved specification before expanding commercial workflows. The requested 29-section specification has not yet been supplied; do not claim compliance.
- Use the existing isolated checkout; do not create worktrees unless requested.
- EUR is the first settlement currency; store money in integer cents. Never invent fees, deposit percentages, reimbursement rules, payout schedules or fund contributions.
- Trade distributable net profit: 20% each to Procurer, Manufacturer, Seller, Receiver and Moderator. Within Moderator: 5%, 5%, 10% of total. Store Selling Cost is an expense, not profit. Business Connections: 35/35/30. Free Goods rewards are voluntary and shared equally between actual participants and Omnia-Mundi.
- Significant AI recommendations require human decisions. Task acceptance is voluntary and geography must be explicit.
- Never process real payments in sandbox mode. Integrations must fail closed when not configured.
- Enforce permissions on the server, validate input, protect sessions, avoid logging secrets, and audit state changes. Never trust roles or prices submitted by clients.
- Run npm test and a functional HTTP smoke check for changes. Document remaining limitations honestly.
