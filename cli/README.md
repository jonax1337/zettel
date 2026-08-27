# Zettel CLI (`cli/zettel.py`)

Headless-Steuerung der Zettel-Datenbank für Automatisierung (z. B. Agenten,
Scripts, Cron). Nur Python-stdlib, keine Abhängigkeiten.

## DB-Auflösung

Wie die App (`src-tauri/src/tenants.rs`): `sandbox.flag` → Sandbox-DB,
sonst aktiver Tenant aus `tenants.json`, sonst Standard-`zettel.db`.

**Nicht parallel zur laufenden App schreiben** (SQLite single-writer).
Lesende Befehle sind unproblematisch.

## Befehle

```
python cli/zettel.py status                          # DB, Sandbox, Sidecar
python cli/zettel.py customers                       # Kunden listen
python cli/zettel.py invoices [--status X] [--year N]
python cli/zettel.py invoice:show <id>
python cli/zettel.py invoice:create --customer "ITGG Berlin e.V." \
    --items "IT-Vor-Ort-Service|2|Std|90|0;Remote-Support|1.5|Std|90|0" \
    [--issue-date 2026-08-27] [--issue] [--pdf]
python cli/zettel.py invoice:issue <id>              # Nummer ziehen (lazy)
python cli/zettel.py invoice:pdf <id>                # PDF via Sidecar
python cli/zettel.py invoice:paid <id>               # bezahlt + Payment-Eintrag
python cli/zettel.py stats                           # Umsatz / offene Posten
```

Positions-Format: `Beschreibung|Menge|Einheit|Einzelpreis-Euro[|MwSt%][|Langtext]`,
mehrere Positionen mit `;`.

## Konventions-Parität zur App

Der CLI repliziert bewusst die App-Logik aus `src/lib/db/invoices.ts`:

- **Draft-Placeholder** `DRAFT-<hex>` — kein Nummern-Slot wird verbrannt
- **Lazy Numbering**: echte `RE-{YYYY}-{NNNN}` erst bei `issue`/`pdf`
- **Per-Line-Rundung** (`computeTotals`), Cent-Integer überall
- **markPaid** protokolliert Restbetrag als `invoice_payments`-Eintrag (`auto`)
- **PDF-Versionierung**: existierendes PDF wird vor Regeneration nach
  `Versionen/<stem>__<mtime>.pdf` verschoben (wie `archive_pdf_version`)
- **Sidecar**: JSON-RPC über stdin/stdout, Dev-Venv oder `ZETTEL_SIDECAR`-Binary

Bei Änderungen an der App-Logik (Migrationen, Payload-Format) müssen beide
Stellen angefasst werden.
