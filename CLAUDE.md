# Zettel — Claude Code Context

Offline-first invoice generator for German freelancers / Kleinunternehmer. **Tauri 2 + Svelte 5 + Python sidecar.** ZUGFeRD/Factur-X PDF/A-3 output. Release-Historie in `CHANGELOG.md` — hier nicht duplizieren.

## Current state
- **Released:** v0.17.0 on `main`. Auto-Update aktiv seit v0.4.3. v0.18.0 (Positions-Reorder, PDF-Versionierung, Multi-DB-Tenants) in Vorbereitung.
- **DB schema:** `user_version = 26` (letzte Migration `0025_v0.16_expense_categories.sql`).
- **Dev-Linie:** neue Arbeit auf `release/vX.Y`-Branches (aktuell `release/v0.17`).
- **Test-Suite:** 134 Vitest-Cases (`pnpm test`) + 71 Pytest-Cases (`sidecar/tests/`). Pure-Math (Totals/Tax/Skonto/Currency/Date/DATEV) ist voll abgedeckt, Sidecar deckt ZUGFeRD-XML-Goldens + KoSIT-Validator-Roundtrip + i18n ab.

## Architecture

### Frontend (`src/`)
- **Svelte 5 runes only** (`$state`, `$derived`, `$effect`, `$props`). Kein `export let`, kein legacy store in Components, kein SvelteKit.
- **Router:** `svelte-spa-router` (hash-based). Alle Form-/Edit-Screens via `push("/...")` — **niemals** ein neues Tauri-WebviewWindow öffnen.
- **UI in `src/lib/ui/`** — shadcn-style Wrapper über Bits UI (Button, Card, Dialog, Dropdown, Input, Select, Textarea, Badge, Titlebar, Toaster, CommandPalette, DatePicker, ConfirmDialog, Slider). Theme tokens in `theme.svelte.ts`. Lucide-Icons via `@lucide/svelte`. Wrapper erweitern, nicht umgehen.
- **Settings ist ein Hub** (`/settings` → fünf Kategorie-Routen `/settings/{company,documents,appearance,data,advanced}`, Shell in `src/routes/settings/SettingsShell.svelte`).
- **Routen** (`src/routes/`): Dashboard, Customers/Vendors/Expenses/Invoices/Offers/Recurring/Reminders (List + Edit + Detail), Settings, TaxReport, UstvaReport, Export, Validate, NotFound.
- **DB-Layer (`src/lib/db/`):** `@tauri-apps/plugin-sql` (SQLite). Schema in `schema.ts` ist Drizzle-Typen (nicht Runtime). Queries sind raw parameterized SQL via `client.ts`. Migrationen in `migrations/*.sql`, compile-time via `include_str!` in `src-tauri/src/lib.rs:build_migrations()` für **beide** Pfade (`sqlite:zettel.db` und `sqlite:zettel-sandbox.db`).
- **Geschäftslogik-Module:** `dashboard/{period,queries,tax}`, `tax/{income,trade}` (pure, voll getestet), `reports/ustva`, `export/datev`, `sidecar/{invoice,offer,reminder,extract}`, `utils/{money,currency,date,invoice-number}`.

### Rust (`src-tauri/src/`)
- `lib.rs` — Plugin-Init, Migrations-Registry, Command-Registrierung. `apply_pending_restore_blocking()` läuft **vor** dem SQL-Plugin-Init, damit ein staged Restore die DB ersetzt, bevor sie geöffnet wird.
- `sidecar.rs` — spawnt Python-Sidecar (`std::process::Command`, JSON über stdin/stdout). Dev: Script direkt; Release: PyInstaller-Binary aus Tauri-Resources. Tauri-Commands: `generate_invoice`, `generate_offer`, `generate_reminder`, `extract_zugferd`, `extract_text_pdf`, `ping_sidecar`.
- `backup.rs` — ZIP-Snapshot (`VACUUM INTO` + PDFs + `manifest.json`). Staged Restore: extrahiert nach `<appdata>/pending_restore/`, Marker-File, dann `apply_pending_partial_restore` (`ATTACH DATABASE` + selektiver `INSERT`). App-Identifier ist hardcoded `digital.laux.zettel` (Pre-Builder hat keinen AppHandle). `CURRENT_SCHEMA` muss mit `user_version` der neuesten Migration matchen — sonst `Schema neuer als App-Version` beim Restore.
- `crypto.rs` — AES-256-GCM + Argon2id für Backup-Verschlüsselung. Magic-Header `ZETTEL-ENC-1`. Kein gespeichertes Master-Passwort.
- `fs_export.rs` — `save_text_file` (CSV ohne `plugin-fs`), `import_expense_pdf` (kollisionssichere Ablage `~/Documents/Zettel/Eingangsrechnungen/<vendor>/`).
- `sandbox.rs` — `is_sandbox`/`set_sandbox`, gesteuert über Flag-File `sandbox.flag` im AppData-Dir. Toggle → `plugin-process::relaunch`. `client.ts` wählt die DB-URL beim Open.
- `exchange.rs` — `fetch_ecb_exchange_rate(currency)`, blocking ureq gegen `eurofxref-daily.xml`, ~8s Timeout.
- `validator.rs` — E-Rechnungs-Validierung über den gebundelten KoSIT-Validator (**Java**). Extrahiert via Sidecar (`extract_xml_only`) erst die XML aus dem PDF, schreibt sie in eine Temp-Datei und startet Java als CLI-Subprozess (`Command::new(java) -jar validator.jar -s scenarios.xml -r <dir> -o <tmp> <input>`), parst dann den XML-Report (String-Scan: `valid`, Szenario, `failed-assert`-Findings). `resolve_java`: dev `tools/jre/bin/java` → Release `jre/bin/java` aus Resources → System-`java`. Commands: `validator_status`, `validate_einvoice_xml`, `validate_einvoice_pdf`. Nur Release-Build (bzw. dev mit lokalem `tools/jre` + `tools/kosit-validator`). Frontend-Bridge `src/lib/validator.ts`, UI `src/routes/Validate.svelte`. Setup-Skripte: `tools/download-validator.sh` (lädt `validator.jar` + Scenarios), `tools/build-jre.sh` (jlink-minimierte JRE, ~35 MB). Gebundelt via `tauri.bundle.conf.json` (`kosit-validator`, `jre`).
- `accent.rs` — Accent-Color-Reader (Windows-Registry).

### CLI (`cli/zettel.py`)
- Headless-DB-Steuerung (stdlib-only) für Automatisierung; Befehle: `status`, `customers`, `invoices`, `invoice:{create,show,issue,pdf,paid}`, `stats`.
- Repliziert App-Logik aus `invoices.ts` (DRAFT-Placeholder, lazy Numbering, Per-Line-Rundung, Payment-Protokoll, PDF-Versionierung, Sidecar-RPC). **Bei Logik-Änderungen beide Stellen anfassen.**
- Details: `cli/README.md`.

### Sidecar (`sidecar/`)
- `main.py` — JSON-RPC-Loop über stdin/stdout. `_add_gtk_dll_path` lookup: frozen → exe-dir → `C:\Program Files\GTK3-Runtime Win64\` → msys64. Override via `ZETTEL_GTK_PATH`.
- `invoice/pdf.py` — WeasyPrint, rendert Rechnung/Angebot/Mahnung mit drei Themes (classic/modern/minimal) aus **einer** `invoice.html.j2` via CSS-Variablen. Angebot ist PDF/A-3b ohne XML; Rechnung ist PDF/A-3 mit eingebettetem ZUGFeRD-XML via `factur-x.generate_from_binary(level=...)`.
- `invoice/zugferd.py` — Profile-URN-Map (`BASIC`/`EN16931`/`EXTENDED`); Reverse-Charge `CategoryCode K` (intra_eu) bzw. `G` (third_country) inkl. `ExemptionReason`. Currency-Code aus `invoice.currency`.
- `invoice/extract.py` — Factur-X-XML-Parser für eingehende Rechnungen (`factur-x` + `lxml`, defensiv für BASIC/EN16931/EXTENDED).
- `invoice/text_extract.py` — OCR-Light via `pypdf` + Regex-Heuristik (Datum/Betrag/Rechnungsnummer/Lieferantenname). Kein Tesseract — Scans sind explizit Non-Goal.
- `invoice/templates.py` — Jinja-Env mit `autoescape=True` (siehe Quirk unten), `_logo_data_uri` inlined Logos als `data:` URI.
- **Build:** `cd sidecar && python build.py` (`pyinstaller==6.11.1` im venv). Auf Windows wird **jede** `.dll` aus dem GTK3-Runtime-Dir neben die exe kopiert — keine Allowlist, weil gtk3-classic vs. official MSI verschiedene Lib-Versionen shippen.
- **Dev-Python-Lookup:** `ZETTEL_PYTHON` → `sidecar/.venv/Scripts/python.exe` (Win) bzw. `.../bin/python` (Unix) → `python` aus PATH.

## Critical conventions

### Migrations sind 3-Punkt-synchron
Eine neue Migration `000N_<name>.sql` heißt **immer drei Stellen gleichzeitig anfassen**:
1. `PRAGMA user_version = <neu>;` am Ende der Migration.
2. `CURRENT_SCHEMA` in `src-tauri/src/backup.rs` — sonst lehnt Restore frische Backups ab.
3. `CURRENT_DB_SCHEMA_VERSION` in `src/routes/settings/{Advanced,Data}.svelte` (Display + Pre-Wipe-Backup).
4. Plus `Migration { version, description, sql: include_str!(...) }` in `build_migrations()` in `lib.rs`.

**Migrationen sind nach Shipping unveränderlich** — Inhalt ändern = neue Migration. `.gitattributes` pinnt LF für `*.sql`, weil `include_str!` byte-stabil über Plattformen muss.

### Money & Numbering
- **Money:** immer Cent (Integer) in DB, Display via `src/lib/utils/money.ts`. Niemals float.
- **Nummern-Konventionen** (konfigurierbar in Settings): Kunden `K-0001`, Lieferanten `L-0001`, Rechnungen `RE-2026-0001`, Angebote `AN-2026-0001`, Ausgaben `EX-2026-0001`, Mahnungen `MA-2026-0001`.
- **Lazy Invoice Numbering** (nur Rechnungen): Drafts bekommen `DRAFT-<hex>`-Platzhalter; der echte `invoice_number_counter` wird **erst** in `issueInvoice()` (markSent / PDF) gezogen. `displayInvoiceNumber()` maskiert Platzhalter als „Entwurf #<4-hex>". Drafts löschen → keine Lücken. Angebote/Mahnungen/Ausgaben numerieren weiter eager.
- **Multi-Currency:** `invoice.currency` + `exchange_rate` + eingefrorener `eur_total_cent` (BigInt-Fixed-Point, 8 Dezimalstellen). DATEV nimmt den eingefrorenen Wert. **Storno-Signum:** `eur_total_cent` muss dasselbe Vorzeichen wie `subtotal/total` haben — sonst falsch in KPIs (Migration `0018` flippt Altdaten).
- **DB-Naming:** snake_case in SQL, gemappt auf camelCase in TS via `mapXxx()` Helpers in den jeweiligen Query-Modulen.

### Backdating, Sandbox
- `markSent(id, sentAt?)` / `markPaid(id, paidAt?)` akzeptieren optionalen Unix-Timestamp (Default jetzt). UI-Plausibilitäts-Warnung nur soft.
- **Sandbox:** Flag-File `sandbox.flag` → `client.ts` öffnet `sqlite:zettel-sandbox.db` statt `sqlite:zettel.db`. Beide Pfade haben dieselbe Migrations-Registry. Banner in `Layout.svelte`.

### UI conventions
- **Deutsche UI-Strings**, englische Identifier/Code/Comments.
- **Keine Kommentare außer wenn das WARUM nicht offensichtlich ist.**
- **No popup windows** — alles via In-App-Routing (`push("/...")`). `capabilities/default.json:windows` bleibt `["main"]`.
- **Unified hover** (v0.13): Back-Nav-Links zeigen `ArrowLeft`-Slide; Cards mit Lift-Animation (`-translate-y-0.5 + shadow-md`); animierte `ArrowRight` statt literale „→".

## ZUGFeRD / EN-16931 Gotchas
- **BR-CO-26 + Kleinunternehmer:** Wenn `company.vatId` fehlt, emittiert `zugferd-en16931.xml.j2` `<ram:ID>{{ taxNumber }}</ram:ID>` (BT-29) als Fallback **vor** `<ram:Name>` (XSD-Order!). FC-schemed `SpecifiedTaxRegistration` bleibt zusätzlich — viele B2B-Portale erwarten sie, auch wenn sie BR-CO-26 nicht erfüllt. Conditional nicht entfernen.
- **Jinja autoescape:** Env nutzt `autoescape=True`, **nicht** `select_autoescape(["html","xml"])` — letzteres prüft nur die letzte Extension, `.xml.j2` würde nicht matchen, und `&`/`<`/`>` in User-Strings würden `xmlParseEntityRef: no name` werfen.
- **Storno-XML** (CII Credit Note): `InvoiceReferencedDocument` muss in `ApplicableHeaderTradeSettlement` (NICHT in `…Agreement`). Beträge end-to-end negativ.
- **Reverse-Charge:** intra-EU = `CategoryCode K` + ExemptionReason „VAT exempt for EEA intra-community supply…"; Drittland = `CategoryCode G` + „Export outside EU". Buyer-USt-IdNr. in `<ram:SpecifiedTaxRegistration schemeID="VA">`.
- **Leistungszeitraum (v0.12):** Header-Period `service_period_start/end` (BG-14, BT-73/74) gewinnt gegen `delivery_date` (BT-72), wenn beide gesetzt; XOR App-seitig erzwungen. Line-Period (BG-26, BT-134/135) optional pro Position; Einzeltag = `start = end`. Lange Positions-Beschreibung in `*_items.long_description` (BT-154) zusätzlich zu `name` (BT-153).

## Cross-platform build
- CI: `.github/workflows/build.yml` Matrix windows-latest / macos-14 (arm64) / macos-13 (x86_64) / ubuntu-22.04. Jeder Runner installiert Python+GTK+Tauri-Deps, baut `python sidecar/build.py`, dann `pnpm tauri:build`.
- **Resources-Split** (v0.10-Fix): Production-Resources (`sidecar/dist`, `tools/jre`, `kosit-validator`) leben in `tauri.bundle.conf.json`, **nicht** in `tauri.conf.json`. Dev-Build hat sie nicht — sonst emittiert `cargo:rerun-if-changed` tausende Files und Tauri-Build crashed mit `Zugriff verweigert (os error 5)` durch AV-Interferenz auf Windows. `pnpm tauri:build` lädt die Bundle-Conf als Overlay.
- **Updater:** Ed25519-signiert, statisches `latest.json` bei GitHub Releases. Tauri-2-Quirk: NSIS-Setup-Sig ist `-setup.exe.sig`, nicht `*.nsis.zip.sig`. `bundle.createUpdaterArtifacts: true` muss in `tauri.conf.json` gesetzt sein.
- **Linux/macOS-Caveat:** WeasyPrint lädt Pango/Cairo dynamisch vom System. User brauchen `libpango1.0-0 libcairo2 libgdk-pixbuf2.0-0` (apt) bzw. `brew install pango cairo gdk-pixbuf`.
- Windows-Install-Path: `C:\Users\<user>\AppData\Local\zettel\` (NSIS user-scope).

## Stack quick-ref
| Layer | Tech |
|---|---|
| Frontend | Svelte 5 (runes), TypeScript strict, Vite 6, Tailwind v4, Bits UI |
| Routing | `svelte-spa-router` (hash) |
| Persistence | `@tauri-apps/plugin-sql` (SQLite); Drizzle nur als Type-Source |
| PDF | WeasyPrint + Jinja2 (Sidecar) |
| ZUGFeRD | `factur-x` + `lxml` |
| E-Rechnung-Validierung | KoSIT-Validator (`validator.jar`, **Java**) auf gebundelter jlink-JRE, von Rust als CLI gespawnt |
| Money | Cent-Integer (DB) / BigInt fixed-point (EUR-Konversion) |
| Tests | Vitest (pure TS), Sidecar-Tests in `sidecar/tests/` |

## Commands
- `pnpm tauri:dev` — full app
- `pnpm dev` — Frontend only (DB-Calls schlagen fehl, kein Tauri-API)
- `pnpm check` — svelte-check
- `pnpm test` — Vitest
- `pnpm db:generate` — Drizzle-Migrationen regenerieren
- `pnpm tauri:build` — Production-Build mit `tauri.bundle.conf.json`-Overlay

## Sidecar bootstrap (dev)
```bash
cd sidecar
python -m venv .venv
.venv/Scripts/activate     # Win — bash: source .venv/bin/activate
pip install -r requirements.txt
pytest                     # Sidecar-Tests (sidecar/tests/)
python build.py            # PyInstaller-Bundle nach sidecar/dist/
```
**GTK3-Runtime (Windows):** Installer via <https://github.com/tschoonj/GTK-for-Windows-Runtime-Environment-Installer>. WeasyPrint findet die DLLs über `_add_gtk_dll_path` in `main.py`. Override: `ZETTEL_GTK_PATH`.

## AppData locations
- **Windows:** `%APPDATA%\digital.laux.zettel\` (DB, `sandbox.flag`, `pending_restore/`)
- **macOS:** `~/Library/Application Support/digital.laux.zettel/`
- **Linux:** `~/.local/share/digital.laux.zettel/`
- **PDFs:** `~/Documents/Zettel/{Rechnungen,Angebote,Mahnungen,Eingangsrechnungen/<vendor>}/`

## Git workflow
- Feature-Arbeit auf `release/vX.Y`-Branches via PR. `main` = letztes shipped Release.
- Squash-merge PRs in den Release-Branch; konsolidierender PR `release/vX.Y → main` beim Release.
- Conventional Commits (`feat`/`fix`/`chore`/`docs`).
- **Alle `git`/`pnpm`/`gh`/`cargo`/`tauri`-Commands via PowerShell.** WSL-bash ist OK für Read/Edit/Write und read-only `git`/`grep` — aber nicht für `pnpm install`, sonst landen Linux-native rollup-Binaries im `node_modules` und der Windows-Build bricht.

## Don't
- Keine Backend-HTTP-Server — alles ist Tauri-Commands oder direkt SQLite.
- Kein React, kein SvelteKit, kein styled-components.
- Money niemals als float.
- Keine Telemetrie.
- Kein Tesseract (Scan-OCR ist Non-Goal).
- Kein ELSTER-Upload (würde GoBD-Disclaimer aufweichen).
- Keine SMTP-Anbindung.
- Inhalt einer geshippten Migration niemals nachträglich ändern — neue Version, neue Migration.
- Niemals ein neues `WebviewWindow` für Formulare öffnen.

## Further reading
- `CHANGELOG.md` — Vollständige Versions-Historie (v0.1 → heute)
- `docs/datev-export.md` — DATEV-Format-700-Mapping
- `docs/auto-update-setup.md` — Tauri-Updater-Signing-Flow
- `CONTRIBUTING.md` — PR-Konventionen
