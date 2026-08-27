#!/usr/bin/env python3
"""
Zettel CLI — headless Steuerung der Zettel-Datenbank.

Repliziert die App-Geschäftslogik aus src/lib/db/invoices.ts exakt:
  - Draft-Placeholder `DRAFT-<hex>` (kein Nummern-Slot wird verbrannt)
  - Lazy Invoice-Numbering: echte Nummer erst bei issue/markSent/PDF
  - computeTotals: Per-Line-Rundung (Finanzamt-Konvention), Cent-Integer
  - markPaid protokolliert Restbetrag als invoice_payments-Eintrag
  - PDF-Generierung über den Sidecar (JSON-RPC über stdin/stdout)

DB-Auswahl folgt derselben Quelle der Wahrheit wie die App:
  sandbox.flag vorhanden  -> zettel-sandbox.db
  sonst aktiver Tenant    -> dessen Pfad aus tenants.json
  sonst                   -> zettel.db (Standard)

Nur stdlib — bewusst ohne externe Abhängigkeiten.

Warnung: Nicht parallel zur laufenden Zettel-App mit schreibendem Zugriff
verwenden (SQLite single-writer). Lesende Befehle sind unproblematisch.
"""
from __future__ import annotations

import argparse
import json
import math
import os
import sqlite3
import subprocess
import sys
import time
import uuid
from datetime import datetime
from pathlib import Path

APP_IDENTIFIER = "digital.laux.zettel"

# ----------------------------------------------------------------------------
# DB-Auflösung (Spiegel von src-tauri/src/tenants.rs)
# ----------------------------------------------------------------------------


def app_data_dir() -> Path:
    if sys.platform == "win32":
        base = Path(os.environ.get("APPDATA", Path.home() / "AppData" / "Roaming"))
    elif sys.platform == "darwin":
        base = Path.home() / "Library" / "Application Support"
    else:
        base = Path(os.environ.get("XDG_DATA_HOME", Path.home() / ".local" / "share"))
    return base / APP_IDENTIFIER


def resolve_db_path() -> Path:
    """Aktive DB: Sandbox > aktiver Tenant > Standard. Wie resolve_active_url()."""
    d = app_data_dir()
    if (d / "sandbox.flag").exists():
        return d / "zettel-sandbox.db"
    cfg_path = d / "tenants.json"
    if cfg_path.exists():
        try:
            cfg = json.loads(cfg_path.read_text(encoding="utf-8"))
            active = cfg.get("active")
            if active and active != "default":
                for t in cfg.get("tenants", []):
                    if t.get("id") == active and str(t.get("path", "")).strip():
                        return Path(t["path"])
        except (json.JSONDecodeError, OSError):
            pass
    return d / "zettel.db"


def connect() -> sqlite3.Connection:
    path = resolve_db_path()
    if not path.exists():
        sys.exit(f"Fehler: Datenbank nicht gefunden: {path}")
    con = sqlite3.connect(path)
    con.row_factory = sqlite3.Row
    return con


# ----------------------------------------------------------------------------
# Geschäftslogik (Spiegel von src/lib/utils/totals.ts + invoices.ts)
# ----------------------------------------------------------------------------


def js_round(v: float) -> int:
    """Math.round wie in JS: half away from zero (Pythons round() ist banker's)."""
    return int(math.floor(v + 0.5)) if v >= 0 else int(math.ceil(v - 0.5))


def compute_line_total(quantity: float, unit_price_cent: int) -> int:
    return js_round(quantity * unit_price_cent)


def compute_totals(items: list[dict], is_kleinunternehmer: bool, is_reverse_charge: bool) -> dict:
    vat_exempt = is_kleinunternehmer or is_reverse_charge
    subtotal = 0
    vat_amount = 0
    for it in items:
        line = compute_line_total(it["quantity"], it["unitPrice"])
        subtotal += line
        if not vat_exempt:
            vat_amount += js_round(line * it["vatRate"] / 100)
    return {"subtotal": subtotal, "vatAmount": vat_amount, "total": subtotal + vat_amount}


def format_invoice_number(pattern: str, counter: int, dt: datetime) -> str:
    yyyy = str(dt.year)
    yy = yyyy[2:]
    mm = str(dt.month).zfill(2)
    return (
        pattern.replace("{YYYY}", yyyy)
        .replace("{YY}", yy)
        .replace("{MM}", mm)
        .replace("{NNNN}", str(counter).zfill(4))
        .replace("{NNN}", str(counter).zfill(3))
        .replace("{NN}", str(counter).zfill(2))
        .replace("{N}", str(counter))
    )


def draft_placeholder() -> str:
    return f"DRAFT-{uuid.uuid4().hex[:16]}"


def is_draft_number(n: str | None) -> bool:
    return bool(n) and n.startswith("DRAFT-")


def display_number(number: str, status: str) -> str:
    if status == "draft" and is_draft_number(number):
        return f"Entwurf #{number[6:10]}"
    return number


def now_unix() -> int:
    return int(time.time())


def parse_date(s: str | None) -> int | None:
    """Akzeptiert YYYY-MM-DD / TT.MM.JJJJ (lokal, 12:00 Uhr) oder Unix-Timestamp."""
    if not s:
        return None
    s = s.strip()
    if s.isdigit():
        return int(s)
    for fmt in ("%Y-%m-%d", "%d.%m.%Y"):
        try:
            dt = datetime.strptime(s, fmt)
            return int(datetime(dt.year, dt.month, dt.day, 12, 0, 0).timestamp())
        except ValueError:
            continue
    sys.exit(f"Ungültiges Datum: {s} (erwartet YYYY-MM-DD oder TT.MM.JJJJ)")


def fmt_eur(cent) -> str:
    if cent is None:
        return "—"
    return f"{cent / 100:,.2f} €".replace(",", "X").replace(".", ",").replace("X", ".")


def fmt_date(unix) -> str:
    if not unix:
        return "—"
    return datetime.fromtimestamp(unix).strftime("%d.%m.%Y")


# ----------------------------------------------------------------------------
# Sidecar-Integration (JSON-RPC wie src-tauri/src/sidecar.rs)
# ----------------------------------------------------------------------------


def resolve_sidecar() -> tuple[str | None, str | None]:
    """(python_exe, main.py) für Dev oder (exe, None) für Release-Binary."""
    env = os.environ.get("ZETTEL_SIDECAR")
    if env:
        p = Path(env)
        if p.is_file():
            if p.suffix.lower() == ".exe":
                return str(p), None
            return str(p), str(_find_main_py())
    repo_root = Path(__file__).resolve().parent.parent
    main_py = repo_root / "sidecar" / "main.py"
    for venv_py in (
        repo_root / "sidecar" / ".venv" / "Scripts" / "python.exe",
        repo_root / "sidecar" / ".venv" / "bin" / "python",
    ):
        if venv_py.is_file() and main_py.is_file():
            return str(venv_py), str(main_py)
    for bundled in (
        Path.home() / "AppData" / "Local" / "Zettel" / "sidecar" / "zettel-sidecar.exe",
    ):
        if bundled.is_file():
            return str(bundled), None
    return None, None


def _find_main_py() -> str:
    repo_root = Path(__file__).resolve().parent.parent
    main_py = repo_root / "sidecar" / "main.py"
    if not main_py.is_file():
        sys.exit("sidecar/main.py nicht gefunden (Repo-Pfad?).")
    return str(main_py)


def call_sidecar(command: str, payload: dict) -> dict:
    exe, main_py = resolve_sidecar()
    if not exe:
        sys.exit(
            "Kein Sidecar verfügbar. Dev: sidecar/.venv anlegen. "
            "Release: ZETTEL_SIDECAR auf zettel-sidecar.exe setzen."
        )
    cmd = [exe] if main_py is None else [exe, main_py]
    req = json.dumps({"command": command, "payload": payload})
    proc = subprocess.run(
        cmd,
        input=req,
        capture_output=True,
        text=True,
        timeout=300,
        cwd=str(Path(main_py).parent) if main_py else None,
    )
    if proc.returncode != 0:
        sys.exit(f"Sidecar-Fehler (exit {proc.returncode}):\n{proc.stderr[-2000:]}")
    try:
        return json.loads(proc.stdout.strip().splitlines()[-1])
    except (json.JSONDecodeError, IndexError):
        sys.exit(f"Sidecar-Antwort nicht parsebar:\n{proc.stdout[-2000:]}\n{proc.stderr[-2000:]}")


# ----------------------------------------------------------------------------
# PDF-Payload-Bau (Spiegel von src/lib/sidecar/invoice.ts buildPayload)
# ----------------------------------------------------------------------------


def skonto_of(inv: dict) -> dict | None:
    if inv.get("skonto_percent") is None or inv.get("skonto_days") is None:
        return None
    total = abs(inv["total"])
    return {
        "percent": inv["skonto_percent"],
        "days": inv["skonto_days"],
        "discountCent": js_round(total * inv["skonto_percent"] / 100),
        "deadlineUnix": (inv["issue_date"] or now_unix()) + inv["skonto_days"] * 86400,
    }


def build_pdf_payload(inv: dict, items: list[dict], customer: dict, company: dict, output_path: str) -> dict:
    skonto = skonto_of(inv)
    return {
        "invoice": {
            "number": inv["number"],
            "issueDate": inv["issue_date"],
            "deliveryDate": inv["delivery_date"],
            "dueDate": inv["due_date"],
            "subtotal": inv["subtotal"],
            "vatAmount": inv["vat_amount"],
            "total": inv["total"],
            "isKleinunternehmer": bool(inv["is_kleinunternehmer"]),
            "isReverseCharge": bool(inv["is_reverse_charge"]),
            "reverseChargeType": inv["reverse_charge_type"],
            "isCreditNote": bool(inv["is_credit_note"]),
            "correctsInvoice": None,
            "notes": inv["notes"],
            "paymentTerms": inv["payment_terms"],
            "currency": inv["currency"] or "EUR",
            "exchangeRate": inv["exchange_rate"],
            "eurTotalCent": inv["eur_total_cent"],
            "servicePeriodStart": inv["service_period_start"],
            "servicePeriodEnd": inv["service_period_end"],
            "skontoPercent": skonto["percent"] if skonto else None,
            "skontoDays": skonto["days"] if skonto else None,
            "skontoAmountCent": skonto["discountCent"] if skonto else None,
            "skontoDeadline": skonto["deadlineUnix"] if skonto else None,
            "amountPaidCent": inv["amount_paid_cent"] or 0,
            "pdfLanguage": inv["pdf_language"] or "de",
        },
        "items": [
            {
                "position": it["position"],
                "description": it["description"],
                "quantity": it["quantity"],
                "unit": it["unit"],
                "unitPrice": it["unit_price"],
                "vatRate": it["vat_rate"],
                "lineTotal": it["line_total"],
                "longDescription": it["long_description"],
                "linePeriodStart": it["line_period_start"],
                "linePeriodEnd": it["line_period_end"],
            }
            for it in items
        ],
        "company": {
            "companyName": company["company_name"],
            "ownerName": company["owner_name"],
            "street": company["street"],
            "postalCode": company["postal_code"],
            "city": company["city"],
            "country": company["country"],
            "taxNumber": company["tax_number"],
            "vatId": company["vat_id"],
            "email": company["email"],
            "phone": company["phone"],
            "website": company["website"],
            "bankName": company["bank_name"],
            "bankIban": company["bank_iban"],
            "bankBic": company["bank_bic"],
            "isKleinunternehmer": bool(company["is_kleinunternehmer"]),
            "kleinunternehmerNote": company["kleinunternehmer_note"],
            "logoPath": company["logo_path"],
        },
        "customer": {
            "name": customer.get("name"),
            "contactPerson": customer.get("contactPerson") or customer.get("contact_person"),
            "street": customer.get("street"),
            "postalCode": customer.get("postalCode") or customer.get("postal_code"),
            "city": customer.get("city"),
            "country": customer.get("country"),
            "vatId": customer.get("vatId") or customer.get("vat_id"),
        },
        "outputPath": output_path,
        "profile": company["zugferd_profile"] or "en16931",
        "settings": {"pdf_theme": company["pdf_theme"] or "classic"},
    }


# ----------------------------------------------------------------------------
# Commands
# ----------------------------------------------------------------------------


def cmd_status(_args) -> None:
    path = resolve_db_path()
    con = connect()
    n_inv = con.execute("SELECT COUNT(*) FROM invoices").fetchone()[0]
    n_cust = con.execute("SELECT COUNT(*) FROM customers").fetchone()[0]
    sandbox = (app_data_dir() / "sandbox.flag").exists()
    print(f"DB:         {path}")
    print(f"Sandbox:    {'JA' if sandbox else 'nein'}")
    print(f"Rechnungen: {n_inv}  ·  Kunden: {n_cust}")
    exe, _ = resolve_sidecar()
    print(f"Sidecar:    {exe or 'nicht verfügbar'}")
    con.close()


def cmd_customers(_args) -> None:
    con = connect()
    rows = con.execute("SELECT * FROM customers ORDER BY id").fetchall()
    if not rows:
        print("Keine Kunden.")
    for c in rows:
        print(f"{c['id']:>3}  {c['customer_number']:<8} {c['name']:<40} {c['city'] or '':<20} {c['email'] or ''}")
    con.close()


def resolve_customer(con, ref: str) -> sqlite3.Row:
    row = con.execute(
        "SELECT * FROM customers WHERE id = ? OR customer_number = ? OR name = ? COLLATE NOCASE",
        (int(ref) if ref.isdigit() else -1, ref, ref),
    ).fetchone()
    if not row:
        sys.exit(f"Kunde nicht gefunden: {ref} (siehe 'zettel.py customers')")
    return row


def cmd_invoice_list(args) -> None:
    con = connect()
    q = "SELECT * FROM invoices"
    cond, params = [], []
    if args.status:
        cond.append("status = ?")
        params.append(args.status)
    if args.year:
        cond.append("CAST(strftime('%Y', issue_date, 'unixepoch') AS INT) = ?")
        params.append(args.year)
    if cond:
        q += " WHERE " + " AND ".join(cond)
    q += " ORDER BY id DESC"
    for r in con.execute(q, params).fetchall():
        print(
            f"{r['id']:>3}  {display_number(r['number'], r['status']):<15} "
            f"{fmt_date(r['issue_date'])}  {fmt_eur(r['total']):>12}  {r['status']:<9} "
            f"{'PDF' if r['pdf_path'] else '—':<3} fällig {fmt_date(r['due_date'])}"
        )
    con.close()


def load_invoice_full(con, invoice_id: int) -> tuple[dict, list[dict], dict]:
    inv = con.execute("SELECT * FROM invoices WHERE id = ?", (invoice_id,)).fetchone()
    if not inv:
        sys.exit(f"Rechnung {invoice_id} nicht gefunden.")
    items = [
        dict(r)
        for r in con.execute(
            "SELECT * FROM invoice_items WHERE invoice_id = ? ORDER BY position", (invoice_id,)
        ).fetchall()
    ]
    try:
        cust = json.loads(inv["customer_snapshot"])
    except (json.JSONDecodeError, TypeError):
        cust = {}
    return dict(inv), items, cust


def issue_invoice(con, invoice_id: int, sent_at: int | None = None) -> str:
    """Spiegel von issueInvoice(): DRAFT -> echte Nummer, status sent."""
    inv = con.execute("SELECT * FROM invoices WHERE id = ?", (invoice_id,)).fetchone()
    if not inv:
        sys.exit(f"Rechnung {invoice_id} nicht gefunden.")
    if inv["status"] != "draft":
        return inv["number"]
    ts = sent_at or now_unix()
    final_number = inv["number"]
    if is_draft_number(inv["number"]):
        con.execute(
            "UPDATE settings SET invoice_number_counter = invoice_number_counter + 1, "
            "updated_at = unixepoch() WHERE id = 1"
        )
        row = con.execute(
            "SELECT invoice_number_counter, invoice_number_format FROM settings WHERE id = 1"
        ).fetchone()
        final_number = format_invoice_number(
            row["invoice_number_format"], row["invoice_number_counter"], datetime.now()
        )
    con.execute(
        "UPDATE invoices SET number = ?, status = 'sent', sent_at = ?, updated_at = unixepoch() "
        "WHERE id = ? AND status = 'draft'",
        (final_number, ts, invoice_id),
    )
    con.commit()
    return final_number


def safe_filename(s: str) -> str:
    return "".join(c if c not in '\\/:*?"<>|' else "_" for c in s)


def archive_pdf_version(path: Path) -> str | None:
    """Spiegel von fs_export.rs archive_pdf_version: bestehendes PDF vor dem
    Überschreiben nach <dir>/Versionen/<stem>__<mtime>.pdf verschieben."""
    if not path.is_file():
        return None
    versions_dir = path.parent / "Versionen"
    versions_dir.mkdir(parents=True, exist_ok=True)
    mtime = int(path.stat().st_mtime)
    dest = versions_dir / f"{path.stem}__{mtime}.pdf"
    n = 2
    while dest.exists():
        dest = versions_dir / f"{path.stem}__{mtime}-{n}.pdf"
        n += 1
    path.rename(dest)
    return str(dest)


def generate_pdf_for(con, invoice_id: int) -> tuple[str, str]:
    inv, items, cust = load_invoice_full(con, invoice_id)
    if inv["status"] == "draft" and is_draft_number(inv["number"]):
        issue_invoice(con, invoice_id)
        inv, items, cust = load_invoice_full(con, invoice_id)
    settings = dict(con.execute("SELECT * FROM settings WHERE id = 1").fetchone())
    out_dir = Path.home() / "Documents" / "Zettel" / "Rechnungen"
    out_dir.mkdir(parents=True, exist_ok=True)
    output_path = out_dir / f"{safe_filename(inv['number'])}.pdf"
    archive_pdf_version(output_path)
    payload = build_pdf_payload(inv, items, cust, settings, str(output_path))
    resp = call_sidecar("generate_invoice", payload)
    if not resp.get("success"):
        err = resp.get("error", {})
        sys.exit(f"PDF-Fehler [{err.get('code')}]: {err.get('message')}\n{err.get('details', '')[:800]}")
    con.execute(
        "UPDATE invoices SET pdf_path = ?, updated_at = unixepoch() WHERE id = ?",
        (resp["pdfPath"], invoice_id),
    )
    con.commit()
    return inv["number"], resp["pdfPath"]


def parse_items_arg(spec: str | None) -> list[dict]:
    """Format: 'Beschreibung|Menge|Einheit|Einzelpreis-Euro[|MwSt%][|Langtext]'.
    Mehrere Positionen mit ; trennen."""
    if not spec:
        return []
    items = []
    for part in spec.split(";"):
        part = part.strip()
        if not part:
            continue
        fields = part.split("|")
        if len(fields) < 4:
            sys.exit(f"Position ungültig (min. 4 Felder): {part}")
        desc = fields[0].strip()
        qty = float(fields[1].strip().replace(",", "."))
        unit = fields[2].strip() or "Std"
        price_eur = float(fields[3].strip().replace(",", "."))
        vat = float(fields[4].strip().replace(",", ".")) if len(fields) > 4 and fields[4].strip() else 0
        long_desc = fields[5].strip() if len(fields) > 5 and fields[5].strip() else None
        items.append(
            {
                "description": desc,
                "quantity": qty,
                "unit": unit,
                "unitPrice": js_round(price_eur * 100),
                "vatRate": int(vat),
                "longDescription": long_desc,
            }
        )
    return items


def cmd_invoice_create(args) -> None:
    con = connect()
    settings = dict(con.execute("SELECT * FROM settings WHERE id = 1").fetchone())
    customer = resolve_customer(con, args.customer)
    items = parse_items_arg(args.items)
    if not items:
        sys.exit("Keine Positionen angegeben (siehe --items).")
    is_rc = args.reverse_charge != "none"
    totals = compute_totals(items, bool(settings["is_kleinunternehmer"]), is_rc)
    issue_ts = parse_date(args.issue_date) or now_unix()
    terms_days = args.payment_terms if args.payment_terms is not None else (settings["default_payment_terms_days"] or 14)
    due_ts = parse_date(args.due_date) or (issue_ts + terms_days * 86400)
    payment_terms = f"Zahlbar innerhalb von {terms_days} Tagen ohne Abzug."
    snapshot = {
        "customerNumber": customer["customer_number"],
        "name": customer["name"],
        "contactPerson": customer["contact_person"],
        "street": customer["street"],
        "postalCode": customer["postal_code"],
        "city": customer["city"],
        "country": customer["country"],
        "email": customer["email"],
        "vatId": customer["vat_id"],
    }
    cur = con.execute(
        """INSERT INTO invoices
           (number, customer_id, customer_snapshot, issue_date, delivery_date, due_date,
            status, subtotal, vat_amount, total, is_kleinunternehmer, is_reverse_charge,
            reverse_charge_type, notes, payment_terms, is_credit_note, corrects_invoice_id,
            currency, exchange_rate, eur_total_cent, notes_internal, follow_up_date,
            service_period_start, service_period_end, skonto_percent, skonto_days, pdf_language)
           VALUES (?, ?, ?, ?, ?, ?, 'draft', ?, ?, ?, ?, ?, ?, ?, ?, 0, NULL,
                   'EUR', NULL, ?, NULL, NULL, ?, ?, ?, ?, ?)""",
        (
            draft_placeholder(),
            customer["id"],
            json.dumps(snapshot, ensure_ascii=False),
            issue_ts,
            parse_date(args.delivery_date),
            due_ts,
            totals["subtotal"],
            totals["vatAmount"],
            totals["total"],
            1 if settings["is_kleinunternehmer"] else 0,
            1 if is_rc else 0,
            args.reverse_charge,
            args.notes,
            payment_terms,
            totals["total"],
            parse_date(args.service_start),
            parse_date(args.service_end),
            args.skonto_percent,
            args.skonto_days,
            args.pdf_language,
        ),
    )
    invoice_id = cur.lastrowid
    for i, it in enumerate(items, start=1):
        con.execute(
            """INSERT INTO invoice_items
               (invoice_id, position, description, quantity, unit, unit_price, vat_rate, line_total,
                long_description, line_period_start, line_period_end)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                invoice_id,
                i,
                it["description"],
                it["quantity"],
                it["unit"],
                it["unitPrice"],
                it["vatRate"],
                compute_line_total(it["quantity"], it["unitPrice"]),
                it.get("longDescription"),
                None,
                None,
            ),
        )
    con.commit()
    print(f"Draft erstellt: id={invoice_id}  {fmt_eur(totals['total'])}  Kunde: {customer['name']}")
    if args.issue:
        print(f"Bereitgestellt: {issue_invoice(con, invoice_id)}")
    if args.pdf:
        number, pdf_path = generate_pdf_for(con, invoice_id)
        print(f"PDF: {pdf_path}")
    con.close()


def cmd_invoice_show(args) -> None:
    con = connect()
    inv, items, cust = load_invoice_full(con, args.id)
    print(f"Rechnung {display_number(inv['number'], inv['status'])}  [{inv['status']}]")
    print(f"Kunde:        {cust.get('name')} ({cust.get('customerNumber')})")
    print(f"Datum:        {fmt_date(inv['issue_date'])}  ·  fällig {fmt_date(inv['due_date'])}")
    if inv["service_period_start"]:
        print(f"Leistung:     {fmt_date(inv['service_period_start'])} – {fmt_date(inv['service_period_end'])}")
    print(f"Zahlungsziel: {inv['payment_terms'] or '—'}")
    print()
    for it in items:
        print(f"  {it['position']}. {it['description']}")
        print(f"     {it['quantity']:g} {it['unit']} × {fmt_eur(it['unit_price'])} = {fmt_eur(it['line_total'])}")
    print()
    print(f"Netto: {fmt_eur(inv['subtotal'])}  ·  USt: {fmt_eur(inv['vat_amount'])}  ·  Gesamt: {fmt_eur(inv['total'])}")
    if inv["pdf_path"]:
        print(f"PDF:   {inv['pdf_path']}")
    con.close()


def cmd_invoice_pdf(args) -> None:
    con = connect()
    number, path = generate_pdf_for(con, args.id)
    print(f"{number}: {path}")
    con.close()


def cmd_invoice_issue(args) -> None:
    con = connect()
    print(f"Bereitgestellt: {issue_invoice(con, args.id, parse_date(args.sent_at))}")
    con.close()


def cmd_invoice_paid(args) -> None:
    con = connect()
    inv = con.execute("SELECT * FROM invoices WHERE id = ?", (args.id,)).fetchone()
    if not inv:
        sys.exit(f"Rechnung {args.id} nicht gefunden.")
    if inv["status"] == "draft":
        issue_invoice(con, args.id)
        inv = con.execute("SELECT * FROM invoices WHERE id = ?", (args.id,)).fetchone()
    ts = parse_date(args.paid_at) or now_unix()
    total = abs(inv["total"])
    already = inv["amount_paid_cent"] or 0
    remaining = total - already
    if remaining > 0:
        con.execute(
            "INSERT INTO invoice_payments (invoice_id, paid_at, amount_cent, source) VALUES (?, ?, ?, 'auto')",
            (args.id, ts, remaining),
        )
    con.execute(
        "UPDATE invoices SET status = 'paid', paid_at = ?, amount_paid_cent = ?, updated_at = unixepoch() "
        "WHERE id = ? AND status IN ('sent','partial','draft')",
        (ts, total, args.id),
    )
    con.commit()
    print(f"Als bezahlt markiert: {inv['number']} ({fmt_eur(total)})")
    con.close()


def cmd_stats(_args) -> None:
    con = connect()
    year = datetime.now().year
    row = con.execute(
        "SELECT COALESCE(SUM(total),0) FROM invoices "
        "WHERE status NOT IN ('cancelled','draft') "
        "AND strftime('%Y', issue_date, 'unixepoch') = ?",
        (str(year),),
    ).fetchone()
    print(f"Umsatz {year} (ohne Entwurf/Storno): {fmt_eur(row[0])}")
    row = con.execute(
        "SELECT COUNT(*), COALESCE(SUM(total),0) FROM invoices WHERE status IN ('sent','partial')"
    ).fetchone()
    print(f"Offene Forderungen: {row[0]} · {fmt_eur(row[1])}")
    con.close()


def main() -> None:
    ap = argparse.ArgumentParser(prog="zettel", description="Zettel CLI")
    sub = ap.add_subparsers(dest="cmd", required=True)

    sub.add_parser("status", help="DB/Sidecar-Status").set_defaults(func=cmd_status)
    sub.add_parser("customers", help="Kunden listen").set_defaults(func=cmd_customers)

    p_ls = sub.add_parser("invoices", help="Rechnungen listen")
    p_ls.add_argument("--status", choices=["draft", "sent", "partial", "paid", "cancelled"])
    p_ls.add_argument("--year", type=int)
    p_ls.set_defaults(func=cmd_invoice_list)

    p_new = sub.add_parser("invoice:create", help="Rechnung (Draft) anlegen")
    p_new.add_argument("--customer", required=True, help="ID, Kundennummer oder Name")
    p_new.add_argument(
        "--items", required=True,
        help="'Desc|Menge|Einheit|Preis€[|MwSt][|Langtext]' — mehrere mit ;",
    )
    p_new.add_argument("--issue-date")
    p_new.add_argument("--due-date")
    p_new.add_argument("--delivery-date")
    p_new.add_argument("--service-start")
    p_new.add_argument("--service-end")
    p_new.add_argument("--payment-terms", type=int, help="Tage (Default aus Settings)")
    p_new.add_argument("--reverse-charge", default="none", choices=["none", "intra_eu", "third_country"])
    p_new.add_argument("--skonto-percent", type=float)
    p_new.add_argument("--skonto-days", type=int)
    p_new.add_argument("--pdf-language", default="de")
    p_new.add_argument("--notes")
    p_new.add_argument("--issue", action="store_true", help="Direkt bereitstellen (Nummer ziehen)")
    p_new.add_argument("--pdf", action="store_true", help="PDF generieren (impliziert --issue)")
    p_new.set_defaults(func=cmd_invoice_create)

    p_show = sub.add_parser("invoice:show", help="Rechnung anzeigen")
    p_show.add_argument("id", type=int)
    p_show.set_defaults(func=cmd_invoice_show)

    p_pdf = sub.add_parser("invoice:pdf", help="PDF generieren")
    p_pdf.add_argument("id", type=int)
    p_pdf.set_defaults(func=cmd_invoice_pdf)

    p_iss = sub.add_parser("invoice:issue", help="Draft bereitstellen (Nummer ziehen)")
    p_iss.add_argument("id", type=int)
    p_iss.add_argument("--sent-at")
    p_iss.set_defaults(func=cmd_invoice_issue)

    p_paid = sub.add_parser("invoice:paid", help="Als bezahlt markieren")
    p_paid.add_argument("id", type=int)
    p_paid.add_argument("--paid-at")
    p_paid.set_defaults(func=cmd_invoice_paid)

    p_stats = sub.add_parser("stats", help="Kennzahlen")
    p_stats.set_defaults(func=cmd_stats)

    args = ap.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
