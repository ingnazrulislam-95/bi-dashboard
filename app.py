"""Unified Sales & Finance Intelligence Dashboard: backend, adapters and demo data in one file.
Run: uvicorn app:app --reload   (serves the dashboard at http://localhost:8000)"""
import csv, io, os, random, re
from abc import ABC, abstractmethod
from pathlib import Path
from fastapi import FastAPI, HTTPException, UploadFile
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware

# ---------- Canonical schema: date (YYYY-MM-DD), region, product, customer, rep, revenue, cogs ----------
REQUIRED = ["date", "region", "product", "customer", "rep", "revenue", "cogs"]
MAX_BYTES = 5_000_000

# ---------- Synthetic demo data (deterministic, not client data) ----------
REG = ["EMEA", "North America", "APAC", "LATAM"]
PRO = ["Core Platform", "Analytics Add-on", "Support Plan", "Services"]
CUS = ["Northwind", "Acme Retail", "Helix Bio", "Orion Freight", "Blue Harbor",
       "Kestrel Energy", "Vantage Foods", "Lumen Health", "Pioneer Auto", "Summit Textiles"]
REP = ["A. Novak", "B. Okafor", "C. Lindqvist", "D. Moreau", "E. Tanaka", "F. Alvarez"]


def demo_rows() -> list[dict]:
    r, rows = random.Random(7), []
    for m in range(12):
        y, mo = divmod(9 + m, 12)
        for _ in range(40):
            p = r.choice(PRO)
            rev = round((2500 + r.random() * 17000) * (1 + m * 0.018))
            cogs = round(rev * (0.68 if p == "Services" else 0.4 + r.random() * 0.12))
            rows.append(dict(date=f"{2025 + y}-{mo + 1:02d}-01", region=r.choice(REG), product=p,
                             customer=r.choice(CUS), rep=r.choice(REP), revenue=rev, cogs=cogs))
    return rows


# ---------- Source-system adapters (interfaces only: NO live integration is implemented) ----------
class Adapter(ABC):
    name = ""
    required_env: list[str] = []

    def missing(self):
        return [k for k in self.required_env if not os.getenv(k)]

    def status(self):  # `live` stays False until authentication AND retrieval are implemented and tested
        m = self.missing()
        return {"name": self.name, "live": False, "state": "not_configured" if m else "configured_untested", "missing": m}

    @abstractmethod
    def fetch_transactions(self, start: str, end: str) -> list[dict]: ...


class SalesforceAdapter(Adapter):
    name, required_env = "Salesforce CRM", ["SF_LOGIN_URL", "SF_CLIENT_ID", "SF_USERNAME", "SF_PRIVATE_KEY_PATH"]

    def fetch_transactions(self, start, end):
        # TODO: OAuth 2.0 JWT bearer flow, then SOQL on Opportunity (Closed Won, CloseDate in range), Account, User.
        raise NotImplementedError("Salesforce retrieval is not implemented or tested.")


class SapAdapter(Adapter):
    name, required_env = "SAP ERP", ["SAP_BASE_URL", "SAP_CLIENT_ID", "SAP_CLIENT_SECRET"]

    def fetch_transactions(self, start, end):
        # TODO: OAuth client credentials, then released OData APIs (billing, journal entries, open items);
        # convert currency, align fiscal periods, deduplicate against CRM-booked revenue.
        raise NotImplementedError("SAP retrieval is not implemented or tested.")


# ---------- API ----------
app = FastAPI(title="BI Dashboard")
app.add_middleware(CORSMiddleware, allow_origins=os.getenv("CORS_ORIGINS", "http://localhost:8000").split(","),
                   allow_methods=["GET", "POST"], allow_headers=["*"])


@app.get("/")
def index():  # serve only index.html, never the whole folder (it would expose .env)
    return FileResponse(Path(__file__).with_name("index.html"))


@app.get("/api/health")
def health():
    return {"ok": True}


@app.get("/api/connections")
def connections():
    return [a.status() for a in (SalesforceAdapter(), SapAdapter())]


@app.get("/api/transactions")
def transactions():
    return {"source": "demo", "rows": demo_rows()}


@app.post("/api/import")
async def import_csv(file: UploadFile):
    raw = await file.read(MAX_BYTES + 1)
    if len(raw) > MAX_BYTES:
        raise HTTPException(413, "File exceeds 5 MB.")
    reader = csv.DictReader(io.StringIO(raw.decode("utf-8-sig")))
    missing = [c for c in REQUIRED if c not in [h.strip().lower() for h in (reader.fieldnames or [])]]
    if missing:
        raise HTTPException(422, f"Missing columns: {', '.join(missing)}")
    rows = []
    for i, rec in enumerate(reader, start=2):
        rec = {k.strip().lower(): (v or "").strip() for k, v in rec.items() if k}
        if not re.match(r"^\d{4}-\d{2}-\d{2}", rec["date"]):
            raise HTTPException(422, f"Row {i}: date must be YYYY-MM-DD.")
        try:
            rows.append({**{c: rec[c] for c in REQUIRED[:5]}, "revenue": float(rec["revenue"]), "cogs": float(rec["cogs"])})
        except ValueError:
            raise HTTPException(422, f"Row {i}: revenue and cogs must be numbers.")
    if not rows:
        raise HTTPException(422, "No data rows found.")
    return {"source": file.filename, "rows": rows}  # stateless: nothing is stored
