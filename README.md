# Unified Sales & Finance Intelligence Dashboard

One flat folder, no build step. `app.py` is the FastAPI backend (API, demo data, adapter stubs) and serves `index.html`, the dashboard (Chart.js).
Demo mode uses clearly labelled synthetic data. **No live Salesforce or SAP integration exists.** The code has not been run in an automated test yet; use the checklist.

## Run
    python -m venv .venv && source .venv/bin/activate
    pip install -r requirements.txt
    cp .env.example .env
    uvicorn app:app --reload          # open http://localhost:8000

## Files
- `app.py` backend: `/api/health`, `/api/connections`, `/api/transactions`, `/api/import` (CSV, 5 MB max, validated, not stored)
- `index.html` Executive overview, Sales analytics, Data connections, filters, CSV import
- `sample_data.csv` import template: `date, region, product, customer, rep, revenue, cogs` (date as YYYY-MM-DD)
- `.env.example` server-side settings for the future adapters

## Metrics
Booked revenue = closed-won revenue in period. Gross profit = revenue - COGS. Margin = GP / revenue. Target achievement = booked / (monthly target x months).
Win rate = won / (won + lost). Retention = prior-period customers who bought again / prior-period customers. Pipeline is forecast, never added to booked revenue.
Modelled in demo mode only: budget, target, leads, lost deals, pipeline, receivables, aging.

## Connecting real systems (not implemented)
- Salesforce: Connected App, OAuth 2.0 JWT bearer, read-only integration user, API access to Opportunity, Lead, Account, User. Implement `SalesforceAdapter.fetch_transactions`.
- SAP: read-only technical user, released OData/CDS views (billing, GL, open items), SAP Cloud Connector or gateway. Implement `SapAdapter.fetch_transactions`.
- Map customer/product IDs, convert currency, align fiscal periods, deduplicate CRM vs ERP revenue. Secrets only in the backend environment.

## Not yet built
SAP Finance, Operations, Detailed Analysis pages; XLSX import; export; waterfall/funnel charts; login, roles, per-client isolation (needs a database); branding and fiscal-calendar config; automated tests.

## Testing checklist
- [ ] App starts; `/api/connections` never shows "Live"
- [ ] Filters change every KPI and chart; an empty selection shows the empty state
- [ ] `sample_data.csv` imports; a bad column, number, date or file over 5 MB shows a clear error
- [ ] With the backend stopped, the page shows an error, not blank
- [ ] Phone width and dark mode render correctly

## Deployment
Run `uvicorn app:app --host 0.0.0.0 --port 8000` behind an HTTPS reverse proxy. Set `CORS_ORIGINS`, inject secrets from your platform's secret store, and add authentication before exposing client data.
