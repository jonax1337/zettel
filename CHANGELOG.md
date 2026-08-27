# Changelog

Alle nennenswerten Änderungen an Zettel werden hier dokumentiert.
Das Format orientiert sich an [Keep a Changelog](https://keepachangelog.com/de/1.1.0/),
Versionen folgen [Semantic Versioning](https://semver.org/lang/de/).

## [Unreleased]

## [0.19.0]

### Added
- **Zettel CLI (`cli/zettel.py`).** Headless-Steuerung der Zettel-Datenbank für Automatisierung — Rechnungen anlegen, bereitstellen, als bezahlt markieren, PDFs generieren, Kennzahlen abrufen. Nur Python-stdlib, nutzt denselben Sidecar (JSON-RPC) wie die App und folgt derselben DB-Auswahl (Sandbox > aktiver Tenant > Standard). Repliziert die App-Geschäftslogik exakt: DRAFT-Placeholder, lazy Rechnungsnummern, Per-Line-Rundung (Cent-Integer), Payment-Protokoll, PDF-Versionierung vor Überschreiben. Details: `cli/README.md`.

### Migration
- **Keine DB-Migration** — Schema bleibt auf `user_version = 26`.

## [0.18.4]

### Changed
- **Tenant-Switcher ohne Avatar-Icon.** Das führende Initialen-Icon vor den Tenants ist entfernt — im Sidebar-Trigger, in den Dropdown-Einträgen und im Verwalten-Dialog.

### Migration
- **Keine DB-Migration** — Schema bleibt auf `user_version = 26`.

## [0.18.3]

> **Hotfix.** Die E-Rechnungs-Validierung schlug in installierten Builds auf Windows immer fehl — der gebündelte Validator wird jetzt korrekt aufgerufen.

### Fixed
- **KoSIT-Validierung scheiterte mit „Kein Report gefunden … unerwarteter Fehler beim Öffnen der Datei".** Tauris `resource_dir()` liefert auf Windows einen *verbatim* Pfad (`\\?\C:\…`). Die JVM kann ein JAR aber nicht öffnen, wenn es als `\\?\`-präfigiertes `-jar`-Argument übergeben wird → jede Validierung brach ab, der Status blieb „Validator offline". JRE und Validator **waren** also korrekt mitinstalliert; nur der Aufruf war kaputt. Fix: Resource-Pfade (Validator-JAR, Szenarien, Repository, JRE) werden vor der Übergabe an `java` vom `\\?\`-Präfix befreit (`simplify()` in `validator.rs`).
- **Selbstheilung alter Stati.** Rechnungen, die unter einer älteren Version mit Status `unavailable` validiert wurden, zeigten dauerhaft „Validator offline". Beim Öffnen einer solchen Rechnung mit vorhandener PDF wird nun einmalig still neu validiert und der Status (`gültig`/`ungültig`) aktualisiert.

### Migration
- **Keine DB-Migration** — Schema bleibt auf `user_version = 26`.

## [0.18.2]

> **Fix zu v0.18.1.** Lange Datenbank-Pfade sprengen nicht mehr das Layout, der Tenant-Switcher unten in der Sidebar ist aufgeräumt.

### Fixed
- **Pfad-Overflow im Tenant-Switcher und Verwalten-Dialog.** Lange DB-Pfade verbreiterten die UI, weil der `Menu.Trigger`-Wrapper content-breit ist und `truncate` so ins Leere lief. `DropdownMenu` erhält ein optionales `triggerClass`; der Switcher-Trigger ist nun `w-full`, das Label wird abgeschnitten und der **vollständige Pfad erscheint nur noch im Hover-Tooltip**. Im Dialog werden Pfade ebenfalls abgeschnitten (Hover zeigt den vollen Pfad), `min-w-0` am Container verhindert das Aufblähen.

### Changed
- **Tenant-Switcher aufgeräumt.** Der Theme-Umschalter ist aus dem Switcher entfernt (Darstellung wird in den Einstellungen geändert). Der Divider über dem Switcher ist weg; der Trigger ist jetzt ein über fast die volle Breite gestreckter Button mit `border` + abgerundeten Ecken.

### Migration
- **Keine DB-Migration** — Schema bleibt auf `user_version = 26`.

## [0.18.1]

> **Politur zu v0.18.0.** Tenants lassen sich jetzt in einen Cloud-Ordner verschieben, neue DB-Dateien werden nach Firmenname benannt, die PDF-Versionen-Leiste ist kompakter, und die Sidebar unten links zeigt nur noch den Tenant-Switcher.

### Added
- **Tenant „Verschieben…".** Im Verwalten-Dialog kann die **aktive** Datenbank an einen neuen Ort verschoben werden (z. B. OneDrive für Geräte-Unabhängigkeit). Technisch ein `VACUUM INTO` auf die offene DB (konsistente Kopie, WAL-sicher) → Config zeigt auf den neuen Pfad → Relaunch. Die bisherige lokale Datei bleibt als Sicherung erhalten. Neuer Command `relocate_active_tenant`.

### Changed
- **DB-Dateiname aus Firmenname/Bezeichnung.** Beim Anlegen oder Verschieben eines Tenants wird der Dateiname aus der Bezeichnung bzw. dem Firmennamen vorgeschlagen (slugify, z. B. `firma-a.db`) statt generisch `zettel.db`.
- **PDF-Versionen-Leiste kompakter.** Statt einer `Card` (mit `py-6`) jetzt ein schlanker Border-Container mit niedrigen Zeilen; bei nur einer Version entfällt die Kopfzeile. Spürbar flacher in der Rechnungs-Detailansicht.
- **Sidebar unten links aufgeräumt.** Versions-Anzeige und Theme-Umschalter sind aus der Bottom-Bar verschwunden und in den Tenant-Switcher-Dropdown gewandert (Darstellung + Version als Footer). Unten steht jetzt nur noch der Switcher.

### Migration
- **Keine DB-Migration** — Schema bleibt auf `user_version = 26`.

## [0.18.0]

> **Feature-Release.** Positionen lassen sich im Editor frei umsortieren, generierte Rechnungs-PDFs werden versioniert (nichts wird mehr überschrieben), und mehrere getrennte Datenbanken („Tenants") sind über einen Org-Switcher unten in der Sidebar wählbar — inklusive Geräte-Unabhängigkeit über Cloud-Ordner wie OneDrive.

### Added
- **Positions-Reihenfolge umsortierbar (Rechnungen + Angebote).** Jede Positions-Zeile hat jetzt ein Drag-Handle (Greifen + Ziehen, mit Flip-Animation) sowie Hoch/Runter-Pfeile als tastatur-/klickfreundliche Alternative. Die `position`-Spalte wird beim Speichern weiterhin aus der Array-Reihenfolge vergeben — keine Schema-Änderung nötig. Bei akzeptierten (read-only) Angeboten sind die Controls deaktiviert.
- **PDF-Versionierung für Rechnungen.** Beim Neu-Erzeugen einer Rechnungs-PDF wird die bisherige Datei nicht mehr überschrieben, sondern nach `Rechnungen/Versionen/<Nummer>__<Zeitstempel>.pdf` archiviert; `<Nummer>.pdf` bleibt stets die aktuelle Version. Die Rechnungs-Detailansicht zeigt einen „PDF-Versionen"-Block mit allen Versionen (Datum/Uhrzeit, Öffnen, im Ordner zeigen) — ein Audit-Trail besonders für Rechnungen, die in mehreren Schritten bezahlt und dabei mehrfach erzeugt werden. Neue Tauri-Commands `archive_pdf_version` / `list_pdf_versions` in `fs_export.rs`.
- **Mehrere Datenbanken / Tenants mit Org-Switcher.** Unten links in der Sidebar gibt es einen Avatar-/Org-Switcher (shadcn-Stil): zwischen benannten Tenants wechseln (jeder mit eigener DB-Datei) und neue anlegen. Wechsel schreibt die Auswahl in `tenants.json` und startet die App neu (wie der Sandbox-Toggle). DB-Datei in einem Cloud-Ordner (OneDrive o. ä.) ablegen = geräteübergreifend nutzbar (Caveat: nicht gleichzeitig auf zwei Geräten öffnen). Neues Rust-Modul `tenants.rs`; der aktive Custom-DB-Pfad wird beim Start als Migrations-URL registriert (exakter String-Match mit `client.ts`-`Database.load`). Sandbox hat weiterhin Vorrang.

### Migration
- **Keine DB-Migration** — Schema bleibt auf `user_version = 26`. Alle drei Features kommen ohne Schema-Änderung aus (Positions-Reihenfolge nutzt die bestehende Spalte, PDF-Versionen leben im Dateisystem, Tenant-Auswahl in einer JSON-Config).

## [0.17.0]

> **Polish-Release.** Detail-Schliff an der UX der drei Editor-Screens — der unschöne Inline-Period-Picker auf Positions-Ebene ist gegen einen kompakten Popover mit Tab-Switcher (Einzeltag/Zeitraum) ausgetauscht. Dazu eine größere Test-Investition (Vitest +47, Pytest +19, Pytest-Stdin-Bug behoben) und die DB-Math-Module dedupliziert.

### Changed
- **Positions-Zeitraum (BG-26, BT-134/135) bekommt eine eigene Popover-Komponente.** Vorher war die Periode in der schmalen Beschreibungs-Spalte als aufgeklappter Bereich mit zwei nebeneinander stehenden Text-Toggles (Mode-Wechsel + Entfernen) implementiert — visuell beengt, das Umschalten zwischen Einzeltag und Zeitraum war ein zweiter Klick nach dem Öffnen. Neu: ein kompakter Chip-Button in der Description-Cell. Klick öffnet ein Popover (300 px breit) mit einem segmented Tab-Switcher „Einzeltag · Zeitraum" oben, dem passenden DatePicker(s) darunter (Range-Modus mit Min-Date-Constraint auf das Start-Datum), und einem Footer mit „Entfernen" / „Fertig". Befüllt zeigt der Trigger den Wert als Chip mit Akzent-Border an („15.05.2026" oder „15.05.2026 – 22.05.2026"). InvoiceEdit, OfferEdit und RecurringEdit teilen sich die neue Komponente; das Detail-Beschreibungs-Toggle steht als zweiter Chip daneben.
- **Math-Module dedupliziert.** `computeLineTotal` / `computeTotals` lebten dreimal nahezu identisch in `src/lib/db/{invoices,offers,expenses}.ts`. Neu in `src/lib/utils/totals.ts` als pure Funktion mit einheitlichem `TotalsItem`-Interface; die drei DB-Module re-exportieren sie. Tests in `totals.test.ts` (12 Cases) decken jetzt die Produktions-Math direkt ab. Expenses passt sich semantisch an, indem es `isKleinunternehmer: false` an die generische Variante übergibt — die Rechen-Logik ist identisch.

### Fixed
- **PeriodSwitcher: 6 svelte-check-Warnings** zu `state_referenced_locally`. Das Anfangs-Snapshot der Period-Props (Year/Quarter/Month/Custom-From/To) wird jetzt via `untrack()` aus `svelte` gelesen — Intent ist „Initial-Wert übernehmen, dann lokal weiter editieren", was die Warnings korrekt adressiert (statt sie nur zu verstecken).
- **NotFound-Screen poliert.** Raw `text-neutral-500` ersetzt durch das semantische `text-muted-foreground`-Token, Lucide-Icon und animierter Back-Link konsistent mit der „Unified hover"-Konvention aus v0.13.
- **Pytest-Suite auf Windows: 15 zuvor stille Failures behoben.** Drei Test-Module (`test_validator_golden.py`, `test_end_to_end.py`, `test_missing_fields.py`) riefen `subprocess.run(["java", "-jar", validator.jar, …])` ohne explizite Stdin-Umleitung auf. Auf Windows erbt der Subprozess das Console-Handle, KoSIT prüft via `FileInputStream.available()` ob seine stdin gepiped ist — und crasht beim Character-Device. Symptom: kein Report wird geschrieben, der Test-Assert „report file exists" failt. Same root cause wie der App-seitige v0.16.1-Hotfix (`validator.rs`). Fix: alle drei Module füttern jetzt eine leere reguläre Datei als stdin — disk-type-Handle, `available()` liefert sauber 0.

### Tests
- **Vitest:** +47 Cases (134 total, vorher 87). Neue Suites für `lib/utils/currency.ts` (24), `lib/utils/date.ts` (11), `lib/utils/totals.ts` (12). Roundtrip-Edge-Cases für Multi-Currency-Konvertierung, DST-Boundary für Datums-Arithmetik, Storno-Vorzeichen-Propagation durch `computeTotals`.
- **Pytest-Sidecar:** +19 Cases (71 total, vorher 52 effektiv). Neue `test_i18n.py` (14) mit Key-Parität DE/EN, Placeholder-Drift-Check, Fallback-Verhalten. Neue `test_line_period.py` (5) für BillingSpecifiedPeriod-Emission im ZUGFeRD-XML (single-day, range, missing, partial).

### Migration
- **Keine DB-Migration** — Schema bleibt auf `user_version = 26`. v0.17 ist reine UI-/Code-Polish.

### Notes
- **`pdf-language`-String im Footer** (Seite N von M) bleibt sprach-fest auf Deutsch in v0.17 — der CSS-Counter-Workaround (`@page` + `string-set`) ist in v0.18 vorgesehen.

## [0.16.1]

### Fixed
- **KoSIT-Validator: `IOException: Unzulässige Funktion` auf Windows.** Der KoSIT-Validator prüft via `FileInputStream.available()`, ob seine stdin gepiped ist (`Validator.isPiped()`). Auf Windows wirft `available()` für character devices (geerbtes Console-Handle, auch `NUL` via `Stdio::null()`) eine `IOException` — KoSIT fängt das nicht und bricht ab, bevor überhaupt ein Report geschrieben wird. Folge: jede Validierung im Dev-Modus und auch in der installierten App lieferte „Kein Report gefunden. stderr: java.io.IOException: Unzulässige Funktion". Fix in `src-tauri/src/validator.rs`: stdin wird jetzt aus einer leeren regulären Datei gefüttert (disk-type-Handle, `available()` liefert sauber 0, `isPiped()` wird false). Datei wird pro Validierungs-Aufruf im Temp-Verzeichnis angelegt und sofort wieder aufgeräumt.

## [0.16.0]

> **Internationalisierung + Detail-Schliff.** Englische PDF-Variante, mehrsprachige Katalog-Beschreibungen, kuratierte Ausgaben-Kategorien mit SKR03/SKR04-Konten-Mapping, und Bulk-Aktionen jetzt auch für Angebote und Eingangsrechnungen.

### Added
- **Englische PDF-Variante** (Migration `0024_v0.16_pdf_language.sql`). Pro Rechnung und Angebot wählbar zwischen Deutsch und Englisch, Default in Settings → Dokumente. Die Übersetzung deckt alle Labels (Tabellenköpfe, Meta-Box, Totals, Rechtshinweise, Footer-Spalten) ab — das eingebettete ZUGFeRD-XML bleibt bewusst sprach-neutral. Neue Sidecar-Module `invoice/i18n.py` mit Translation-Dict für DE und EN, Templates nutzen jetzt `{{ t('key', lang) }}` durchgängig.
- **Mehrsprachige Katalog-Beschreibungen** sind jetzt im Picker aktiv. Wenn ein Katalog-Eintrag eine `description_en` hat und die Rechnung auf Englisch gestellt ist, wird die englische Beschreibung in den Item-Block eingefügt — sonst Fallback auf Deutsch. Schema (`catalog_items.description_en`) existierte bereits seit v0.14; jetzt wird sie auch genutzt.
- **Kuratierte Ausgaben-Kategorien** (Migration `0025_v0.16_expense_categories.sql`). Neue Tabelle `expense_categories` mit 10 seed-Einträgen (Software/SaaS, Hardware, Telefon, Reisekosten, Fortbildung, Bürobedarf, Honorare, Werbung, Bankgebühren, Sonstige), jeweils mit SKR03- **und** SKR04-Konto-Mapping. ExpenseEdit-Item-Block bekommt einen Kategorie-Select; bei Auswahl wird das `datev_account`-Feld automatisch mit dem SKR03-Default vorbelegt. Beim DATEV-Export wird das Konto über die `categoryId` zur Laufzeit gegen das jeweils aktive SKR-Profil aufgelöst — ein Eintrag mit `categoryId` wechselt also je nach Export-Auswahl korrekt zwischen SKR03 und SKR04. Legacy-Freitext-Kategorie bleibt als Fallback erhalten und ist editierbar wenn keine kuratierte Kategorie gewählt ist.
- **Bulk-Aktionen in OffersList.** Checkbox-Spalte + Select-All. Bar zeigt kontextsensitiv: „Versenden" (alle Drafts), „Ablehnen" (alle Drafts/Sent), „Löschen" (alle Drafts/Rejected/Expired). Angenommene Angebote bleiben vor Bulk-Delete geschützt.
- **Bulk-Aktionen in ExpensesList.** Selbes Muster: „Als bezahlt" (alle Open) und „Löschen" (alle Drafts/Cancelled). Offene und bezahlte Belege werden vor Bulk-Delete geschützt.

### Changed
- **`Settings.defaultPdfLanguage`** als neue Spalte mit `'de'`-Default. InvoiceEdit und OfferEdit füllen den Sprach-Selector aus dieser Vorgabe vor.
- **DATEV-Export** löst `categoryId` zur Export-Zeit gegen das gewählte SKR-Profil auf. Explizit gesetzte `datev_account`-Overrides auf Item-Ebene gewinnen weiterhin gegen die Kategorie-Auflösung — User-Intent ist King.

### Migration
- `0024_v0.16_pdf_language.sql` — `user_version = 25`. `pdf_language`-Spalten in `invoices`, `offers`, `settings`.
- `0025_v0.16_expense_categories.sql` — `user_version = 26`. `expense_categories`-Tabelle mit 10 builtin-Einträgen + `expense_items.category_id`.
- `CURRENT_SCHEMA` in `backup.rs` auf **26**, `CURRENT_DB_SCHEMA_VERSION` in `Advanced.svelte` / `Data.svelte` und in `lib/utils/auto-backup.ts` synchron.

### Notes
- **Page-Counter im PDF-Footer** (`Seite N von M`) ist über CSS-Counter realisiert und bleibt in v0.16 sprach-fest auf Deutsch. Für englische Rechnungen also ein kleiner sichtbarer DE-String am Seitenrand. Korrektur erfordert WeasyPrint-Magic mit `string-set`/`@page`-Pseudo-Selektoren — kommt bei Bedarf in einer späteren Version.
- **Custom Ausgaben-Kategorien** (über die 10 builtin-Einträge hinaus) sind heute nur direkt in der DB anlegbar — eine Settings-Verwaltungs-UI folgt in v0.17. Die DB-Schicht (`createCategory`/`updateCategory`/`setCategoryArchived`) ist bereits vorhanden.
- **Legacy-Freitext-Kategorien** in bestehenden Eingangsrechnungen bleiben unangetastet — `expense_items.category` (freier Text) wird weiterhin als Fallback gerendert. Beim Re-Save ohne Kategorie-Pick bleibt der Freitext erhalten.

## [0.15.0]

> **Zahlungs-Workflow.** Vier zusammenhängende Schritte schließen die Lücke zwischen „Rechnung versendet" und „Geld auf dem Konto": **Teilzahlungen** mit eigener Tabelle, **Bank-Import** für CAMT.053/MT940 mit Auto-Match auf Rechnungsnummer, **Bulk-Aktionen** in der Rechnungsliste und **rotierendes Auto-Backup** beim App-Start.

### Added
- **Teilzahlungen** (Migration `0022_v0.15_partial_payments.sql`). Neue Tabelle `invoice_payments` (id, invoice_id, paid_at, amount_cent, eur_amount_cent, source, notes) und `invoices.amount_paid_cent` als Cache. Neuer Status `partial` zwischen `sent` und `paid` — die Rechnung wird beim Erfassen einer Zahlung automatisch auf `partial` (Saldo < Total) oder `paid` (Saldo = Total) gesetzt. InvoiceDetail bekommt eine Zahlungs-Card mit Saldo-Übersicht (Total / Bezahlt / Offen) und chronologischer Liste aller erfassten Eingänge. Im PDF wird BT-113 `TotalPrepaidAmount` + `DuePayableAmount` strukturiert ausgewiesen, im Totals-Block stehen „Bereits gezahlt" und „Noch offen". KPIs / Dashboard / UStVA / Mahn-Liste / Cash-Flow zählen `partial` korrekt mit; offene Saldi werden überall als `total − amount_paid_cent` berechnet.
- **Bank-Import** (`/bank-import`). Drag&Drop für CAMT.053-XML oder MT940-Text aus dem Online-Banking. Format-Auto-Detection. Sidecar-Parser für beide Formate (neue Dep `mt-940==4.30.0`), neuer Tauri-Command `parse_bank_statement`. Match-Heuristik in drei Pässen: (1) Rechnungsnummer im Verwendungszweck (high confidence), (2) Betrag matcht offenen Saldo ±1 Cent (medium), (3) Kunde-Substring im Zahler-Namen (low). User bestätigt jede Zuordnung einzeln, dann werden ausgewählte Bookings als `invoice_payments` mit `source='camt053'` oder `'mt940'` erfasst. Keine Online-Banking-Anbindung — reine Datei-Verarbeitung lokal.
- **Bulk-Aktionen in InvoicesList.** Checkbox-Spalte + „Alle auswählen". Sticky-Bottom-Bar zeigt kontextsensitiv: „Versenden" (nur wenn alle Drafts), „Als bezahlt" (nur wenn alle sent/partial), „Löschen" (nur wenn alle Drafts oder Stornos). Schützt versendete Rechnungen vor versehentlichem Bulk-Delete.
- **Auto-Backup** (Migration `0023_v0.15_auto_backup.sql`). Rotierender Wochen-Snapshot in `~/Dokumente/Zettel/Backups/auto-<wochentag>.zip`. Settings → Daten neue Card mit Intervall-Selector (täglich / 3-Tage / 7-Tage / 14-Tage / 30-Tage / Aus). Läuft silent beim App-Start in `Layout.svelte`; nur wenn das letzte Auto-Backup länger als `interval` her ist. Sandbox-Modus überspringt komplett. Letzter Lauf sichtbar in der Settings-Card.

### Changed
- **`InvoiceStatus`-Enum** erweitert um `'partial'`. Anzeigen in `InvoicesList` (neuer Filter-Wert + warning-Badge) und `InvoiceDetail` (Badge mit Label „Teilbezahlt") konsistent aktualisiert. KPI-Queries in `loadKpis`, `oldestOverdue`, `cashFlowForecast30d`, `dashboardStats`, `monthlyRevenueInPeriod`, `topCustomersInPeriod` zählen `'partial'` als offen-und-versendet (Soll-Versteuerung).
- **`markPaid()`** legt jetzt einen Payment-Eintrag mit `source='auto'` für den Restbetrag an, statt nur den Status zu setzen — die Zahlungsliste bleibt konsistent, egal ob man Teilzahlungen einzeln erfasst oder direkt voll abschließt.

### Migration
- `0022_v0.15_partial_payments.sql` — `user_version = 23`. `invoice_payments`-Tabelle + Index + `invoices.amount_paid_cent`-Spalte.
- `0023_v0.15_auto_backup.sql` — `user_version = 24`. `auto_backup_interval_days` (Default 0=aus) + `last_auto_backup_at` in `settings`.
- `CURRENT_SCHEMA` in `backup.rs` auf **24**, `CURRENT_DB_SCHEMA_VERSION` in `Advanced.svelte` / `Data.svelte` synchron.

### Notes
- **Multi-Currency-Teilzahlungen** speichern den Betrag in Rechnungswährung. `eur_amount_cent` ist nullable und für FX-Buchhaltung gedacht — wird in v0.15 noch nicht automatisch berechnet (Kurs vom Zahltag fehlt sonst). DATEV-Export greift weiter auf den eingefrorenen `eur_total_cent` auf Rechnungs-Ebene zu — keine Änderung an der Buchungslogik des Steuerberaters.
- **CAMT.053-Namespaces variieren** (`.001.02` / `.04` / `.08`). Parser strippt Namespaces defensiv statt einzelne XSDs zu pflegen.
- **MT940-Parser** nutzt die `mt-940`-Library — Bank-spezifische `:86:`-Varianten werden weitgehend abgedeckt, in Sonderfällen kann `transaction_details` als Fallback dienen.
- **Auto-Backup** verschlüsselt nicht — wer das will, nimmt weiter das manuelle Backup mit Passwort. Auto-Backup ist als Krücken-zur-Cloud-Synchronisation gedacht (man legt `~/Dokumente/Zettel/Backups/` z. B. in OneDrive).
- **Bulk-Aktionen heute nur in InvoicesList.** OffersList und ExpensesList kommen in v0.16.

## [0.14.1]

### Fixed
- **`segno`-Sidecar-Dep fehlte in `requirements.txt`.** v0.14.0 hat den EPC-QR-Code-Generator (`sidecar/invoice/qr.py`) eingeführt, der `segno` per Lazy-Import lädt — die Dependency war lokal im venv installiert, aber durch ein verlorenes Edit nicht in `sidecar/requirements.txt` gelandet. Folge: CI-Tests rot, und der Production-PyInstaller-Bundle hatte segno nicht, sodass beim End-Anwender jede PDF-Generierung auf EUR-Rechnungen mit IBAN mit `ModuleNotFoundError: No module named 'segno'` abbrach. Reine `requirements.txt`-Korrektur, keine Code-Änderung. Bestehende v0.14.0-Installer **funktionieren nicht** — bitte auf v0.14.1 updaten.

## [0.14.0]

> **Daily-Driver-UX.** Sieben fokussierte Verbesserungen, die im Tagesgeschäft Reibung rausnehmen: ein wiederverwendbarer **Artikel-Katalog** spart das ständige Neutippen, **EPC-QR-Codes** auf jeder EUR-Rechnung ersetzen das Überweisungs-Abtippen, **Skonto** wird strukturiert ins ZUGFeRD-XML geschrieben, der **Liquiditäts-Forecast** auf dem Dashboard zeigt die nächsten 30 Tage, alle Listen sind **sortierbar**, und ein **Onboarding-Wizard** holt frische Installationen sauber ab.

### Added
- **Artikel-/Leistungs-Katalog** (`/catalog`). Wiederverwendbare Positionen mit Name, Beschreibung (DE + optional EN für v0.16), Standardpreis, USt-Satz, Einheit, optionalem DATEV-Konto und Tags. Picker (`Aus Katalog…`-Button) in InvoiceEdit, OfferEdit, RecurringEdit und ExpenseEdit fügt eine vorbefüllte Position mit einem Klick ein. Volltext-Suche, Archivierungs-Modus. Migration `0020_v0.14_catalog.sql`.
- **EPC-QR-Code** (Girocode, EPC069-12) im Rechnungs-PDF. Wird automatisch generiert, wenn Currency = EUR, IBAN hinterlegt, kein Storno, kein Reverse-Charge. Empfänger scannt mit der Banking-App, die Überweisung ist vorbefüllt (Empfänger, IBAN, Betrag, Verwendungszweck = Rechnungsnummer). Neue Sidecar-Dep `segno==1.6.1`. Renderpfad rein client-seitig — kein Cloud-Call.
- **Skonto** (Frühzahler-Rabatt). Pro Rechnung und Angebot konfigurierbar (Prozent + Tage). Settings → Dokumente trägt einen Default (Standard: 2 % / 7 Tage, off). Strukturierte Ausgabe als `ApplicableTradePaymentDiscountTerms` im ZUGFeRD-XML (EN-16931 BT-20 ff.) plus prominente Textzeile auf der PDF. Beim Konvertieren Angebot → Rechnung wird der Skonto übernommen. Migration `0021_v0.14_skonto.sql`.
- **Mahn-Eskalations-Strip in InvoiceDetail.** Übersicht aller bisher zur Rechnung erzeugten Mahnstufen (M1/M2/M3) mit Datum und Status, plus „Nächste Stufe"-Vorschlag wenn überfällig. Klick führt direkt in den Mahn-Editor.
- **Skonto-Anzeige in InvoiceDetail.** Wenn die Rechnung Skonto bietet: Card mit Frist, Betrag und Status („noch gültig" / „abgelaufen" / „bezahlt").
- **Liquiditäts-Vorschau im Dashboard.** Card unter den KPIs: Summe aller offenen `sent`-Rechnungen mit Fälligkeit in den nächsten 30 Tagen + überfällige Posten + Schätzung aus aktiven Wiederkehrenden. Hilft bei der Cashflow-Planung ohne Banking-Anbindung. Nur sichtbar wenn > 0.
- **Sortierbare Tabellen** in allen Listen (Rechnungen, Angebote, Eingangsrechnungen, Kunden, Lieferanten, Mahnungen, Wiederkehrende, Katalog). Klick auf Spaltenkopf zyklisch: asc → desc → off. Persistiert in localStorage je Liste.
- **Onboarding-Wizard** beim ersten Start. 4-Step-Modal: Firma → Steuer (Klein/Regular + IDs, BR-CO-26-Check) → Bank → Fertig. ESC-bar mit „Später erinnern". Sandbox-Modus löst keinen Wizard aus.

### Changed
- **EN-16931-Payment-Terms-Block** im ZUGFeRD-XML emittiert jetzt zusätzlich zu `Description` + `DueDateDateTime` einen `ApplicableTradePaymentDiscountTerms`-Block, wenn Skonto gesetzt ist.
- **PDF-Footer-Layout** für Zahlungsbedingungen umgebaut: zweispaltig (Text links, QR-Code rechts), Skonto-Zeile als visuell hervorgehobener Akzent.
- **Stammdaten-Sidebar** erweitert um „Katalog" als drittes Item neben Kunden und Lieferanten.

### Migration
- `0020_v0.14_catalog.sql` — `user_version = 21`. `catalog_items`-Tabelle mit DE/EN-Beschreibungs-Spalten (EN bleibt für v0.16 vorbereitet, aber das Schema steht heute).
- `0021_v0.14_skonto.sql` — `user_version = 22`. `default_skonto_*` (3 Spalten) in `settings`; `skonto_percent` + `skonto_days` in `invoices` und `offers`.
- `CURRENT_SCHEMA` in `backup.rs` auf **22**, `CURRENT_DB_SCHEMA_VERSION` in `Advanced.svelte` und `Data.svelte` synchron auf **22**.

### Notes
- **EPC-QR funktioniert nur für EUR-SEPA** (Spezifikation der EPC). Bei USD/GBP/CHF-Rechnungen wird der QR-Block einfach weggelassen — kein Hinweis nötig, weil reine Inland-Use-Cases den nicht erwarten.
- **Skonto-Frist** wird ab Issue-Date gerechnet, nicht ab Due-Date — entspricht der Verkehrssitte und der EN-16931-Interpretation („Bei Zahlung innerhalb von X Tagen ab Rechnungsausstellung").
- **Katalog-EN-Beschreibung** ist heute schon einpflegbar, wird aber erst in v0.16 (englische PDF-Variante) ausgewertet. Schema-Vorgriff vermeidet eine zweite Migration auf derselben Tabelle.
- Onboarding-Trigger ist `companyName === ''` — Sandbox bekommt den Wizard, wenn die Sandbox-DB neu angelegt wird (intentional, da gleiche Logik).

## [0.13.0]

> **Settings-Refactor + UI-Konsistenz.** Die Einstellungen leben jetzt in fünf klar getrennten Kategorien — Stamm­daten, Dokumente, Darstellung, Daten und Erweitert — statt einer 1.180-Zeilen-Endlos-Liste. Pfeil-Animationen und Lift-Hover sind durch die ganze App konsistent gemacht; Toast-Notifications gleiten endlich rein und raus statt zu poppen.

### Changed
- **Settings als Kategorie-Hub.** `/settings` zeigt jetzt fünf klickbare Kategorie-Cards (Unternehmen / Dokumente / Darstellung / Daten / Erweitert). Jede Kategorie ist eine eigene Route unter `/settings/<kategorie>` mit Breadcrumb-Back-Nav. Die alte Single-Page-Liste ist weg. Inhaltlich keine Settings verloren — nur neu sortiert. Darstellung bekommt zusätzlich einen expliziten Theme-Picker (light/dark/system), vorher nur im Sidebar-Dropdown.
- **Einheitliche Hover-/Pfeil-Animationen.** Back-Nav-Links auf zehn Detail-Routen (Customer/Vendor/Invoice/Offer/Recurring/Reminder/Expense Edit + Invoice/Offer Detail + TaxReport) bekommen einen Slide-Effekt: `ArrowLeft` wandert beim Hover sanft nach links. Dashboard Steuer-Rücklage-Card und Sandbox-Banner kriegen die volle Lift-Animation (`-translate-y-0.5 + shadow-md`) wie die Offer/Expense-Cards; literale „→"-Zeichen sind durch animierte `ArrowRight`-Icons ersetzt. ReminderEdit-Back-Button auf das Standard-`<a use:link>`-Muster vereinheitlicht.

### Fixed
- **Toast-Animation.** Der Toaster hatte gar keine Svelte-Transitions — Toasts erschienen und verschwanden ohne Animation. Mit `in:fly` (von unten reinwischen), `out:fly` (nach rechts rausschieben) und `animate:flip` (smooth Nachrutschen, wenn ein Toast aus der Mitte des Stacks dismissed wird) fühlt sich das jetzt richtig an.

### Added
- **Danger Zone in Settings.** Drei klar getrennte irreversible Aktionen: „Alle Geschäftsdaten löschen" (Settings bleiben), „Einzelne Tabellen leeren" (Multi-Select mit Cascade auf Children/Mahnungen), „Nummerierungs-Counter zurücksetzen". Bestätigung per Tippen von `LÖSCHEN`; vor jeder Aktion wird automatisch ein unverschlüsseltes Backup nach `~/Dokumente/Zettel/Backups/pre-wipe-<ts>.zip` geschrieben als Rettungsanker.
- **YTD-Modus in der Steuer-Rücklage.** Zwei klickbare Cards in `/reports/taxes` und nebeneinander im Dashboard-Widget: „Bisher ausgelöst (YTD)" zeigt die Steuerlast aus dem realen YTD-Gewinn (konservativ, ohne Hochrechnung), „Aufs Jahr hochgerechnet" extrapoliert linear. Beim Schalten wechselt die Aufschlüsselung darunter mit. Hilft besonders früh im Jahr und bei stark schwankenden Einnahmen, weil eine einzelne Rechnung im April nicht mehr zu absurden Jahresprognosen führt.

### Fixed
- **Storno-Bug im Dashboard.** Beim Bearbeiten/Speichern einer Stornorechnung wurde `eur_total_cent` positiv gespeichert, während `total` korrekt negativ war. Die KPI-Queries (`COALESCE(eur_total_cent, total)` und `eur_total_cent * subtotal / total`) nettoeten Stornos dadurch nicht aus — der Saldo wurde so um den doppelten Storno-Betrag zu hoch angezeigt. Fix: `eurTotalCent` bekommt jetzt in `createInvoice` / `updateInvoice` das gleiche Vorzeichen wie subtotal/total. Migration `0018_v0.11_fix_storno_eur_total.sql` flippt bestehende falsche Werte in der DB.
- **Storno-Aggregation in der Steuer-Rücklage.** Die separate Storno-Spalte in der YTD-Aggregation zog vom Gewinn ab, was — weil Stornos schon negativ gespeichert sind — den Storno-Betrag doppelt addierte statt abzuziehen. Gleicher Bug bei der USt-Schuld-YTD. Query auf simples `SUM(subtotal)` umgestellt, da das natürliche Vorzeichen der Stornos das richtige Ergebnis liefert.
- **Draft-Ausgaben im Dashboard-Saldo.** Die Expense-Aggregation hatte keinen Status-Filter und summierte auch Entwürfe mit, die noch nicht final sind. Auf `status IN ('open','paid')` gezogen — konsistent mit dem Tax-Aggregator und dem mentalen Modell „Drafts zählen erst nach Übernahme".

### Changed
- **„ggü. Vorjahr" entfernt.** Der prozentuale YoY-Vergleich unter den Dashboard-KPIs ist raus — der Periode-Selector macht das Vergleichsbedürfnis ohnehin uneindeutig, und die kleine ±%-Zeile war mehr Rauschen als Signal. `loadKpisWithYoY` / `KpisWithYoY` / `previousYearPeriod` als toter Code mit gelöscht.
- **Sonstige Einkünfte / Nebenberuf-Bug.** Wer hauptberuflich angestellt ist und nebenbei selbst rechnet, hat die selbst-Einnahmen ja oben drauf auf den Anstellungs-Lohn — also schon im höheren Grenzsteuersatz. Neue Settings-Spalte `other_income_annual_cent` (Brutto-Jahres-Lohn) füttert eine *marginale* ESt-Berechnung: `ESt(other + selbst) − ESt(other)`. Bei `other = 0` identisch zum Solo-Fall. Migration `0017_v0.11_other_income.sql`.

## [0.11.0] — 2026-05-18

> **Steuer-Rücklage.** Eine fokussierte Story — Zettel sagt dir jetzt im Dashboard, wieviel Geld du von deinem YTD-Gewinn für die Einkommensteuer am Jahresende zurücklegen solltest. § 32a EStG-Tarif für VZ 2024, 2025 und 2026 hartcodiert aus amtlicher BMF-Bekanntmachung, durchgetestet mit 38 Vitest-Cases gegen Eckpunkte aller Zonen.

### Added
- **Steuerprofil in Settings.** Neue Card mit Rechtsform (Freiberufler / Gewerbetreibender), Hebesatz für Gewerbe-Steuer (Default 400 % = Bundesdurchschnitt, nur bei Gewerbe sichtbar), Kirchensteuersatz (0 / 8 / 9 %), Familienstand (ledig / verheiratet-Splittingtarif) und 4× Quartals-Vorauszahlungen (Q1-Q4). Klar gelabelt als Vorhersage, keine Steuerberatung. (#64)
- **Tarif-Library** in `src/lib/tax/` — pure Functions, voll testbar:
  - `income.ts` — § 32a EStG mit 5-Zonen-Formel, Splittingtarif für `married`, Soli mit Milderungszone (§ 4 Abs. 2 SolzG), KiSt 0/8/9 %. Konstanten in `TARIF_2024` ausgelagert, Update-Pfad dokumentiert.
  - `trade.ts` — Gewerbesteuer (Freibetrag 24.500 €, Messzahl 3,5 %, Hebesatz), § 35 EStG Anrechnung auf ESt (3,8 × Messbetrag, gedeckelt). Freiberufler-Pfad: sofort 0.
  - 23 Vitest-Tests gegen amtliche BMF-Tarifrechner-Werte (Grundtarif + Splittingtarif × 6 Einkommensstufen, Soli-Freigrenze + Milderungszone + voller Satz, KiSt 8/9, GewSt-Freibetrag, ESt-Anrechnung bei niedrigem vs. hohem Hebesatz). (#65)
- **Tarif für VZ 2024, 2025 und 2026** als hartcodierte Konstanten aus der amtlichen BMF-Bekanntmachung (Steuerfortentwicklungsgesetz Dez 2024). `estimateIncomeTax(profit, status, churchRate, year)` wählt automatisch den Tarif für das angegebene Jahr; bei Zukunfts-Jahren wird der jeweils neueste hinterlegte Tarif genutzt (mit Code-Kommentar zum Update-Pfad pro Bekanntmachung). 38 Vitest-Cases verifizieren jede Zone (Grundfreibetrag → Reichensteuer), Splittingtarif, Soli-Milderungszone und KiSt 8/9 % pro Jahr — plus Cross-Year-Eigenschaftstest (Steuerlast sinkt 2024→2026 wegen Grundfreibetrag-Anhebung).
- **Dashboard-Card „Steuer-Rücklage".** Kompakt unter den KPI-Cards, vor Aging/Wiedervorlage. Headline-Betrag + ein-Zeilen-Aufschlüsselung (ESt+Soli+KiSt · GewSt · USt · Vorauszahlungen). Klick → Detail-Route. (#66)
- **Detail-Route `/reports/taxes`** (neue Komponente `TaxReport.svelte`):
  - Headline mit empfohlener Rücklage
  - Tarifjahr-Card mit Quellen-Hinweis (§ 32a EStG, BMF-Bekanntmachung)
  - Hochrechnungs-Card mit Was-wenn-Input („Restjahres-Gewinn (€)") für Szenarien
  - Aufschlüsselungs-Tabelle inkl. § 35 EStG-Anrechnung sichtbar
  - Drei Disclaimer-Absätze: keine Steuerberatung, USt-Approximation, kein ELSTER
- **Pauschal-Modus (optional).** Settings-Toggle „Pauschal-Modus zusätzlich anzeigen" + Prozent-Input (Default 30 %, Range 0-50 %). Wenn aktiv: Dashboard-Card zeigt den Pauschal-Wert (`% × Brutto-Umsatz YTD`) neben der Detail-Rücklage; Detail-Route hat eine zusätzliche „Detail vs. Pauschal"-Card mit Differenz-Sublabel („Detail höher — Pauschal unterschätzt" o. ä.). Lernhilfe für User, die ihren Daumen-Wert kalibrieren wollen. (#67)

### Migration
- `0014_v0.11_tax_profile.sql` — `user_version = 15`. Erweitert `settings` um `legal_form`, `trade_tax_rate`, `church_tax_rate`, `tax_filing_status`, `est_prepayment_q1..q4_cent`. Default `freelancer` / Hebesatz 400 % / keine KiSt / `single` / 0 € Vorauszahlungen — Bestandsuser sehen die Card direkt nutzbar ohne Konfigurations-Pflicht.
- `0015_v0.11_pauschal_mode.sql` — `user_version = 16`. `use_pauschal_tax_reserve` (Bool, Default off) + `pauschal_tax_percent` (Real, Default 30).
- `CURRENT_SCHEMA` in `backup.rs` auf 16, `CURRENT_DB_SCHEMA_VERSION` in `Settings.svelte` synchron.

### Notes
- **Kein BMF-Live-API-Call.** Wir hatten in einer Zwischen-Iteration einen Tauri-Command auf `bmf-steuerrechner.de/interface/<JAHR>Version1.xhtml` integriert — der Service verlangt aber einen **partnerregistrierten Zugriffscode**, den wir nicht haben (`<information>Der angegebene Zugriffscode existiert nicht!</information>`). Deshalb rausgenommen. Die Konstanten der amtlichen BMF-Bekanntmachung liefern dasselbe Ergebnis offline + deterministisch + testbar.
- **Tarif-Update jährlich.** Neue BMF-Bekanntmachung im Spätsommer/Herbst → `TARIF_YYYY`-Block in `src/lib/tax/income.ts` ergänzen, Tests dazu. `getTarifYear(year)` fällt für Jahre > letztem hinterlegtem Jahr auf den jüngsten Tarif zurück.
- **USt-Schuld YTD im Tax-Report ist eine Approximation** (Rechnungs-USt − Vorsteuer ohne RC). Für die echte UStVA bleibt `/reports/ustva` der maßgebliche Workflow.
- **Kein ELSTER, kein EÜR-Export, kein AfA, kein Bankabgleich, kein Krankenversicherungs-Rechner** — alles als Roadmap-Kandidaten dokumentiert, keiner davon in v0.11.

## [0.10.0] — 2026-05-18

> **Flexibilität & Datenpflege.** Sechs Module, die das Tagesgeschäft flexibler machen und den wachsenden Datenbestand handhabbar halten — kein Funktions-Sprung, sondern gezielte UX-Aufwertung. Plus ein neuer Sidecar-Pfad für PDF-Anhänge an Rechnungen und ein dev/bundle-Config-Split, der Cargo-Build-Probleme auf Windows behebt.

### Added
- **Flexibles Dashboard.** Zeitraum-Switcher in der Header-Leiste (`Jahr | Quartal | Monat | Benutzerdefiniert` mit DateRangePicker), KPI-Cards (Umsatz netto/brutto, Aufwand, Saldo, Offene Posten) filtern am Zeitraum mit YoY-Vergleich (Vorzeichen-korrekt: Aufwand-Steigerung rot, Umsatz-Steigerung grün). Zwei Charts: Umsatz/Monat (Bar) und Top-5-Kunden (Tabelle). Offene-Forderungen-Zeile zeigt Gesamtsumme + Anzahl + Tage seit Fälligkeit der ältesten offenen Rechnung. Neue Card „Wiedervorlage" zeigt Kunden + Rechnungen mit `follow_up_date <= today + 7d`, gruppiert nach heute/diese Woche/überfällig. Default-Zeitraum persistiert lokal. (#56)
- **Mehrwährungs-Support.** Currency-Dropdown (EUR, USD, GBP, CHF, AUD, CAD, JPY, NOK, SEK, DKK, PLN, CZK) in InvoiceEdit + OfferEdit, bei nicht-EUR erscheint ein Kurs-Feld („1 EUR = X CCY"). `eur_total_cent` wird beim Speichern via BigInt fixed-point-Division (8 Nachkommastellen Genauigkeit) eingefroren — DATEV-Export nimmt diesen Wert, sodass nachträgliche Kurs-Schwankungen Buchhaltungs-Daten nicht verfälschen. ZUGFeRD-XML `InvoiceCurrencyCode` parametrisiert. PDF-Templates zeigen Currency-Symbol (€/$/£/¥) bzw. ISO-Code als Suffix. **„EZB-Kurs"-Button** holt den aktuellen Tageskurs von ecb.europa.eu (ureq blocking call, ~8s Timeout), Wert ist anschließend frei editierbar. Aus-Scope: Pro-Position-Währung, Mischwährung, Live-Kurs-Updates auf Bestandsrechnungen. (#57)
- **Interne Notizen + Wiedervorlage.** Drei neue Daten-Stellen: `customers.follow_up_date`, `invoices.notes_internal` (klar abgegrenzt vom PDF-`notes`-Feld) und `invoices.follow_up_date`. Notizen-Section in CustomerEdit, „Notizen (intern) & Wiedervorlage"-Card im InvoiceDetail mit Inline-Edit (funktioniert auch auf bezahlten Rechnungen via tightly-scoped `updateInvoiceInternalMeta`). Filter „Nur mit Wiedervorlage" in CustomersList + InvoicesList. (#59)
- **Globale Suche (Cmd/Ctrl+K).** Neue Command-Palette in `src/lib/ui/CommandPalette.svelte`, getriggert per Shortcut oder Such-Icon in der Titlebar. LIKE-Suche über alle 6 Entity-Typen (Rechnungen, Kunden, Lieferanten, Ausgaben, Angebote, Mahnungen) inkl. Item-Beschreibungen via EXISTS-Subquery. 150ms Debounce, Tastatur-Navigation, gruppierte Ergebnisse, letzte 5 Treffer als Recents in localStorage. (#60)
- **EZB-Wechselkurs als Tauri-Command.** `fetch_ecb_exchange_rate(currency: String)` in `src-tauri/src/exchange.rs` — minimaler ureq-Aufruf gegen `eurofxref-daily.xml`, regex-frei via Substring-Match (Format stabil seit Jahren).

### Changed
- **Eindeutiger Draft-Handle.** Entwürfe zeigen `Entwurf #<4-hex>` statt nur `Entwurf` — bei mehreren parallelen Drafts unterscheidbar. Status-Badge wird für Drafts ausgeblendet (Spalte trägt die Info bereits, Doppel-Anzeige war redundant); Storno-Drafts behalten ihren Badge wegen der `destructive`-Variante.
- **Dashboard ist nicht mehr YTD-only.** Alle KPI-Cards und Charts respektieren den gewählten Zeitraum; YoY-Werte werden gegen denselben Zeitraum im Vorjahr berechnet.
- **DATEV-Buchungen für nicht-EUR-Rechnungen** verteilen den `eur_total_cent` proportional auf die VAT-Gruppen mit Cent-Residual auf der größten Gruppe, sodass die Buchungssumme exakt dem eingefrorenen EUR-Total entspricht.

### Removed
- **Bonitäts-Markierung / Dunkle Liste** (Spec war #58, kurz integriert, dann zurückgenommen). Für ein Tool dieser Skala — wenige Dutzend persönlich bekannte Kunden — ein Schufa-LARP-Feature ohne realen Nutzen. Spalten `customers.credit_status` / `credit_note` wurden vor Release wieder aus der Migration entfernt.
- **PDF-Anhänge an Rechnungen** (Spec war #61, kurz integriert, dann zurückgenommen). Pipeline WeasyPrint → pypdf-Merge → factur-x war nie gegen KoSIT validiert, und der reale Use Case (Stundennachweis dem Empfänger zusenden) ist über Mail-Attachment einfacher als über ZUGFeRD-PDF-Embed. Tabelle `invoice_attachments`, `attachments.rs`, `attachments.ts`, sha2-Dep, pypdf-Merge — alles raus.
- **Aging-Bucket-Chart** (0-30/31-60/61-90/>90 Tage). Enterprise-AR-Feature; bei realistisch <20 offenen Rechnungen pro Freelancer ist die Liste sortiert nach `due_date` aussagekräftiger als eine vier-Balken-Visualisierung. Ersetzt durch eine einzeilige Summary mit Tagen-Verzug der ältesten offenen Rechnung.

### Fixed
- **Cargo build failed mit `Zugriff verweigert (os error 5)` auf Windows.** `bundle.resources` (sidecar/dist, tools/jre, kosit-validator) emittierte `cargo:rerun-if-changed` für tausende Files; intermittente AV-/Reparse-Point-Effekte ließen tauri-build mid-scan abstürzen. **Resources in `tauri.bundle.conf.json` ausgelagert** und als Overlay nur beim `pnpm tauri build` (lokal + CI) reingeladen. Dev-Mode arbeitet ohne diese Resources, weil `sidecar.rs` im Debug-Build das Python-Script nimmt und die JRE nur on-demand beim Validieren gebraucht wird. Funktional unverändert für Release-Builds.
- **PDF-Rechnungen zeigten nur €** unabhängig von `invoice.currency`. `cents_to_eur`-Filter in `sidecar/invoice/templates.py` ist jetzt currency-aware, Symbole-Map (€/$/£/¥) mit ISO-Code-Fallback.
- **Credit-Status-Enum**: `'watch'` durch `'caution'` ersetzt (Issue-Spec-Aligned) — Migration nicht nötig, war reines TS-Property.

### Migration
- `0012_v0.10_flexibility.sql` — `user_version = 13`. ALTERs auf `customers` (`credit_status`, `credit_note`, `follow_up_date`), `invoices` (`currency`, `exchange_rate`, `eur_total_cent`, `notes_internal`, `follow_up_date`), `offers` (`currency`, `exchange_rate`). Tabelle `invoice_attachments`.
- `0013_v0.10_cleanup.sql` — `user_version = 14`. DROPpt die gecutteten Bonität-Spalten (`customers.credit_status`, `customers.credit_note`) und die `invoice_attachments`-Tabelle. Migration 0012 bleibt byte-stabil — Bestands-Installationen kriegen 0013 als Folge-Migration, frische Installationen laufen beide nacheinander durch.
- `CURRENT_SCHEMA` in `backup.rs` auf 14, `CURRENT_DB_SCHEMA_VERSION` in `Settings.svelte` synchron auf 14 (war seit v0.9 stale auf 12).

### Notes
- **Kein Accounts/Berechtigungen-Modul in v0.10** — wurde aus Scope entfernt; Profile/Mandanten als 1.0-Roadmap-Kandidat dokumentiert.
- **Kein SMTP-Versand** — bewusst nicht in Scope.

## [0.9.0] — 2026-05-18

> **Nacherfassung & Sandbox.** Drei zusammenhängende UX-Lücken im Buchhaltungs-Workflow geschlossen, dazu ein eigener DatePicker mit Quick-Navigation, neues App-Icon und Indigo als Default-Akzent.

### Added
- **Lazy Invoice Numbering.** Neue Rechnungs-Entwürfe ziehen erst beim „Festschreiben" (Versand oder PDF-Generierung) eine echte Nummer aus dem `RE-YYYY-NNNN`-Counter. Bis dahin tragen sie einen `DRAFT-<hex>`-Platzhalter und werden in Listen/Detail als „Entwurf" angezeigt. Test-Drafts oder verworfene Erfassungen hinterlassen damit keine Lücken mehr im fortlaufenden Nummernkreis — GoBD-relevant. PDF-Generierung issued einen Draft automatisch, damit kein Dokument mit Platzhalter-Nummer rausgeht. Gilt nur für Rechnungen; Angebote/Mahnungen/Ausgaben behalten Eager-Numbering. (#51, PR #50)
- **Backdating für Status-Übergänge.** `markSent(id, sentAt?)` und `markPaid(id, paidAt?)` akzeptieren ein optionales Unix-Timestamp (Default = jetzt). InvoiceDetail zeigt jetzt einen Date-Picker-Dialog statt direkt durchzuschalten — bei Nacherfassung kann das echte Versand-/Zahldatum eingetragen werden. Soft-Validation warnt bei Plausibilitäts-Verletzungen (Zahldatum vor Versand, Zukunftsdatum). Fixt latente Bugs in Dashboard YTD, Monats-Chart und DATEV-Datumsspalten bei nachträglich erfassten Rechnungen. (#51, PR #50)
- **Sandbox-Modus.** Settings-Toggle „Sandbox aktivieren" schaltet die App auf eine separate Test-Datenbank `zettel-sandbox.db` um (App-Restart via `plugin-process::relaunch`). Echte Buchhaltungs-DB bleibt unberührt. Status wird in einem Flag-File `sandbox.flag` im AppData-Dir gehalten (out-of-DB, da es bestimmt _welche_ DB geöffnet wird). Migrations werden für beide DB-URLs registriert. Klickbarer Badge in der Titlebar und Info-Card auf dem Dashboard machen den Modus jederzeit sichtbar; Klick führt zurück zu den Settings. (#52, PR #50)
- **DatePicker-Komponente** in `src/lib/ui/DatePicker.svelte` (bits-ui `DatePicker.Root` + `Calendar` mit shadcn-Styling). Segmentiertes Eingabefeld `TT.MM.JJJJ` mit Zahlentastatur + Pfeiltasten-Steppen, Kalender-Icon rechts öffnet Popover. Quick-Navigation: Klick auf Monatsname → 3×4 Monatsgrid, Klick auf Jahr → 4×3 Jahresgrid mit 12er-Pages. Locale `de-DE`, Woche startet Montag, aktuelles Datum mit Ring-Akzent. Ersetzt alle 14 nativen `<input type="date">` in InvoiceEdit/OfferEdit/ExpenseEdit/RecurringEdit/ReminderEdit/Export/InvoiceDetail. (#53, PR #50)
- **Neues App-Icon.** SVG-Source mit stilisiertem Beleg (Inhalts-Zeilen, gerissene Unterkante, grünes Check-Siegel) auf Indigo→Violett-Gradient-Squircle. Alle Plattform-Größen via `pnpm tauri icon` regeneriert (Windows ICO, macOS ICNS, Linux/Android/iOS PNGs). (#54, PR #50)

### Changed
- **Default-Akzentfarbe Indigo statt Slate-Fallback.** `src/lib/accent.svelte.ts` mappt frische Installs ohne gespeicherte Präferenz jetzt auf Indigo (matched die Icon-Palette). Bestehende User mit gespeicherter Auswahl behalten ihre Farbe; „System" bleibt eine eigenständige Option mit OS-Akzent-Lookup auf Windows.

### Notes
- **Kein Schema-Migration in v0.9.** Sandbox ist Flag-File-basiert, Lazy Numbering nutzt die existierende `number`-Spalte mit Platzhalter-Werten — der UNIQUE-Constraint ist erfüllt, ohne dass nullable gemacht werden müsste. Bestands-Drafts mit schon vergebenen `RE-…`-Nummern bleiben unangetastet.
- Neue Transitive-Dep `@internationalized/date` als direkter Dep nachgezogen (bits-ui hatte sie schon transitive).

## [0.8.0] — 2026-05-17

> **Compliance-Garantie.** Jeder ZUGFeRD-Output wird automatisch lokal gegen den offiziellen KoSIT-Validator geprüft, eine jlink-minimierte JRE wird mitgeliefert, und 80 Tests decken die kritischen Pfade ab.

### Added
- **Built-in KoSIT-Validator.** `src-tauri/src/validator.rs` spawnt `java -jar`, parsed das VARL-Report-XML zu strukturierten Findings. Drei Tauri-Commands: `validator_status`, `validate_einvoice_pdf`, `validate_einvoice_xml`. erechnungs-validator.de wird damit überflüssig — Validierung ist offline und sofort. (PR #49)
- **Soft-Gate in beiden Workflows.** Ausgehend: nach jeder PDF-Generierung wird automatisch validiert, Status persistiert in `invoices.last_validation_status` / `last_validated_at` / `last_validation_findings_count`. Eingehend: die ZUGFeRD-Drop-Zone im ExpenseEdit validiert die Lieferanten-XML direkt nach dem Extract. Neue Komponente `ValidationBadge.svelte` zeigt grün/rot/grau auf InvoiceDetail + ExpenseEdit.
- **JRE mitgeliefert** (`tools/build-jre.sh` baut per `jlink` eine ~56 MB Runtime: `java.base/xml/scripting/desktop/...`). CI zieht Temurin 17 vor `pnpm tauri build`. Endnutzer brauchen kein System-Java mehr.
- **Pflichtfeld-Enforcement im UI.** CustomerEdit + Settings markieren EN16931-Pflichtfelder mit Sternchen + HTML5 `required`, Land als ISO-2-Code geprüft. Settings erzwingt Steuernummer XOR USt-IdNr. (BR-CO-26).
- **Test Foundation** (`.github/workflows/test.yml` auf jedem PR): 29 Vitest (money, invoice-number, datev), 41 Pytest (golden ZUGFeRD-XML, semantic invariants, missing-fields exploration, end-to-end Sidecar, KoSIT-Cross-Validation), 10 Cargo (AES-GCM-Crypto, Validator-Report-Parser).

### Changed
- **InvoiceDetail-Action-Bar konsolidiert** von 8 auf max. 4 sichtbare Elemente. Split-Button-Pattern (`[ PDF erzeugen ]  [ Öffnen ▾ ]  [ Versenden ]  [ ⋯ ]`). Storno-Badge ins Status-Label gemerged (`Storno · Versendet`).
- PDF öffnet nicht mehr automatisch nach Erzeugen — Toast hat eine „Öffnen"-Action.
- `/validate` aus der Sidebar entfernt (Workflow ist jetzt automatisch); Route bleibt per Direkt-URL erreichbar.

### Fixed
- **Compliance BR-IC-12.** Reverse-Charge intra-EU emittiert jetzt BT-80 (Deliver-to-country) im korrekten Schema-Slot. Cross-Test verifiziert über den echten KoSIT-Validator.

### Migration
- `0011_validation_status.sql` — `user_version = 12`. Fügt drei Spalten (`last_validation_status`, `last_validated_at`, `last_validation_findings_count`) je auf `invoices` und `expenses` hinzu. Idempotent.

## [0.7.0] — 2026-05-17

> **UI-Polish.** Reine Oberflächen-Iteration: dezente Bewegung, Geist als App-Font, frei wählbare Akzentfarbe (inkl. Windows-System-Akzent), und der letzte native Form-Primitive ist weg.

### Added
- **Geist + Geist Mono** als App-Font (self-hosted via `@fontsource-variable/*`). Ersetzt Inter, das vorher nur als CSS-Name geführt und auf Windows-Systemen ohne Inter-Install still auf Segoe UI zurückfiel — jetzt konsistent über alle Plattformen. Tabular-Zahlen (Rechnungsnummern, Beträge, IBAN, Daten) ziehen automatisch über die existierenden `font-mono`-Klassen Geist Mono. PDF-Templates sind bewusst nicht angefasst.
- **Akzentfarbe konfigurierbar** in Settings → Darstellung. Sieben Presets (Schiefer/Indigo/Violett/Rosé/Smaragd/Bernstein/Himmel) mit jeweils light- und dark-tauglichen oklch-Werten, plus **„System"-Option**, die auf Windows die DWM-Akzentfarbe aus der Registry zieht (`HKCU\Software\Microsoft\Windows\DWM\AccentColor`). macOS/Linux fallen auf das Slate-Default zurück, bis Plattform-APIs ergänzt sind. Wechsel ist instant, ohne Save-Knopf; Persistenz via localStorage (analog zum Theme).
- **Dezente Animationen** durchgängig: 180-ms-Fade auf Routenwechsel, gestaffeltes Card-/Row-Entry auf Dashboard und allen Listen-Tabellen, animiertes Active-Indicator-Bar in der Sidebar, leichter Hover-Lift auf klickbaren Cards, `active:scale`-Feedback auf Buttons und Checkboxen. `prefers-reduced-motion` schaltet alles auf 0.01 ms.
- **Eigener `Checkbox`-Wrapper** in `src/lib/ui/` über Bits UI mit shadcn-Styling, Indeterminate-State und Active-Press-Feedback. Ersetzt 13 native `<input type="checkbox">` quer durch den Code — damit nutzt jedes Form-Element jetzt unsere UI-Schicht.

### Changed
- `--primary`, `--primary-foreground` und `--ring` werden jetzt zur Laufzeit überschrieben statt nur über `data-theme="dark"` gemappt. Erlaubt Live-Switch der Akzentfarbe ohne Reload.

### Notes
- Kein Schema-Migration, keine Backend-Änderung. Sidecar + PDF-Pipeline sind unangetastet — v0.7 ist garantiert byte-identische PDFs gegenüber v0.6.
- Windows-only neue Dependency: `winreg` als `cfg(windows)`-Target-Dep. Andere Plattformen ziehen das nicht.

## [0.6.0] — 2026-05-17

> **Mahnwesen + OCR-Light.** v0.6 schließt zwei der offensichtlichsten Lücken im Workflow: überfällige Rechnungen können jetzt sauber gemahnt werden, und Eingangsrechnungen ohne ZUGFeRD-XML werden per Text-Heuristik vorbefüllt statt komplett manuell.

### Added
- **Mahnungen als first-class Dokumente** (`/reminders`). Neue Tabelle `reminders` mit eigenem Nummernkreis `MA-YYYY-NNNN`, 3-stufiges Level-Modell (Zahlungserinnerung / Mahnung / Letzte Mahnung), Snapshot der Original-Rechnung pro Mahnung. Eigene PDF-Vorlage `reminder.html.j2` (PDF/A-3b, bewusst ohne ZUGFeRD-XML — eine Mahnung ist keine E-Rechnung im Sinne EN16931). Aufschlüsselung Rechnungsbetrag + Mahngebühr + Verzugszinsen = neuer Gesamtbetrag. (#44, PR #45)
- **Überfällige-Rechnungen-Widget** auf `/reminders` mit Tage-Überfälligkeit, bestehenden Mahnstufen und Direkt-Button für die nächste Stufe. Auch `InvoiceDetail.svelte` zeigt einen kontextsensitiven Mahn-Button für `sent`-Rechnungen mit überschrittenem `dueDate`, der die nächste plausible Stufe vorschlägt.
- **Default-Mahntexte** in Settings (`reminder_text_l1/l2/l3`) als deutsche Standardformulierungen — pro Mahnung im Editor noch frei änderbar. Tage-bis-Fälligkeit und Gebühren-Defaults pro Stufe konfigurierbar (Standard: 14 / 14 / 14 Tage, 0 / 5 / 10 EUR).
- **OCR-Light** für Eingangsrechnungen ohne ZUGFeRD-Anhang (`/expenses` Drop-Zone). Neuer Sidecar-Command `extract_text_pdf` (pypdf liest Text-Schicht, Regex-Pattern extrahieren Rechnungsnummer / Datum / Total / Vendor-Name / USt-IdNr.). Vendor-Match per USt-IdNr. (zuverlässig) oder Name-Substring (heuristisch). Bei zwei Stufen (ZUGFeRD scheitert → Text-Heuristik) bekommt der User einen deutlichen „bitte alle Werte prüfen"-Toast. Tesseract/Image-OCR bleibt **explizit ausgeschlossen** — reine Scans sind weiterhin manuell. (#43, PR #46)

### Fixed
- **`CURRENT_SCHEMA` in `backup.rs` stand seit v0.5 auf 9, obwohl `PRAGMA user_version` bereits 10 war.** Latente Bug, der v0.5-Backups beim Restore mit „Schema neuer als App-Version" abgelehnt hätte (analog v0.4.0-Bug, siehe Changelog). Mit v0.6 auf 11 gezogen, Frontend-Mirror in `Settings.svelte:CURRENT_DB_SCHEMA_VERSION` ebenfalls.

### Migration
- `0010_reminders.sql` — `user_version = 11`. Erstellt `reminders` und fügt 13 Settings-Spalten für Mahnungs-Defaults hinzu. Idempotent (`CREATE TABLE IF NOT EXISTS`, alle `ALTER TABLE … ADD COLUMN` haben Defaults).

### Notes
- **Bewusst NICHT in v0.6:** dediziertes Mahnwesen-Settings-UI (Defaults reichen für MVP, Mahntexte werden im Editor pro Mahnung angepasst), automatischer Mahn-Versand per Mail/SMTP, Hintergrund-Scheduler, gerichtliches Mahnverfahren / Inkasso, Tesseract-OCR für gescannte PDFs.

## [0.5.0] — 2026-05-16

> **Buchhaltungs-Light.** Zettel deckte bisher nur Ausgangsbelege ab — v0.5 macht den Gegenpol auf. Eingangsrechnungen mit ZUGFeRD-Drag-&-Drop, Lieferantenverwaltung, DATEV-Export inklusive Aufwände + Stornos, und ein UStVA-Vorbereitungs-Report. Damit ist der vollständige Steuerberater-Übergabe-Workflow abgebildet.

### Added
- **Eingangsrechnungen** (`/expenses`). Neues Datenmodell `expenses` + `expense_items` mit eigenem Nummernkreis `EX-YYYY-NNNN`, Statusfluss `draft → open → paid / cancelled`, Reverse-Charge-Erfassung als Leistungsempfänger, Kategorie-Feld mit Autocomplete aus der Belegehistorie. (#39, PR #42)
- **Lieferanten** (`/vendors`). Eigenes Stammdatenmodell `L-NNNN`, inkl. Bankverbindung und Standard-Kategorie für Vorbefüllung.
- **ZUGFeRD-Drop-Zone.** Eingehende PDFs per Drag & Drop in den Editor: neuer Sidecar-Command `extract_zugferd` (Python via `factur-x` + lxml) parsed eingebettete Factur-X-XML defensiv (BASIC/EN16931/EXTENDED). Vendor-Matching per USt-IdNr. (fallback Name), bei Treffer wird das Formular automatisch befüllt. Original-PDF landet kollisionssicher unter `~/Documents/Zettel/Eingangsrechnungen/<vendor-slug>/`. (#38, PR #42)
- **DATEV-Export erweitert.** Buchungsstapel enthält jetzt Erlöse **und** Aufwände im selben CSV. Konten-Mapping um Kreditor + Aufwand-19 %/7 %/Exempt/§13b erweitert (SKR03 + SKR04). `expense_items.datev_account` überschreibt Default-Konten pro Position. Stornorechnungen werden als Soll/Haben-Drehung exportiert. UI mit Checkboxen „Rechnungen / Eingangsrechnungen / Stornos einschließen". (#40, PR #42)
- **UStVA-Vorbereitungs-Report** (`/reports/ustva`). Quartalsweise Aggregation der ELSTER-Kennzahlen 81 / 86 / 41 / 21 / 66 als reine Vorbereitungshilfe zum Abtippen. CSV-Export. Disclaimer prominent: keine Steuerberatung, kein ELSTER-Upload. (#41, PR #42)
- **Dashboard-Cards** für „Offene Eingangsrechnungen", „Ausgaben YTD" und „Saldo YTD" (Einnahmen − Ausgaben als reiner Indikator, kein EÜR-Ersatz).
- **Sidebar aufgeräumt.** Nav-Items in Gruppen (Stammdaten, Ausgangsbelege, Eingangsbelege, Auswertung, System) mit dezenten Section-Headers. „Export" → „DATEV-Export" zur Abgrenzung vom UStVA-Report.

### Changed
- **Update-Check in den Settings-Header verschoben.** Statt einer eigenen Karte zwischen Backup und Save-Button sitzt der „Nach Updates suchen"-Button jetzt rechts oben im Header neben der Versionsanzeige — klare Trennung zwischen Formular (Daten ändern) und Aktion (App aktualisieren).

### Migration
- `0009_expenses.sql` — `user_version = 10`. Erstellt `vendors`, `expenses`, `expense_items` und fügt 4 Settings-Spalten (`vendor_number_format/counter`, `expense_number_format/counter`) hinzu. Idempotent.

### Notes
- **Bewusst NICHT in v0.5:** OCR für Nicht-ZUGFeRD-PDFs, Banking-Anbindung (FinTS), ELSTER-Direktupload, GoBD-Zertifizierung, wiederkehrende Eingangsrechnungen. Bleiben Non-Goals oder v0.6+.

## [0.4.3] — 2026-05-16

### Fixed
- **Auto-Update brach mit „None of the fallback platforms found in response platforms object" ab.** Zwei Ursachen: (1) `bundle.createUpdaterArtifacts` war in `tauri.conf.json` nicht gesetzt, sodass Tauri 2 keine `.sig`-Dateien für die Updater-Bundles generierte. (2) Der `latest.json`-Builder im CI-Workflow suchte nach Tauri-v1-Format `*.nsis.zip.sig`, Tauri 2 signiert die NSIS-`-setup.exe` aber direkt (sig = `-setup.exe.sig`). Damit blieb `platforms` im Feed leer, jeder Update-Check schlug fehl.

### Notes
- Damit ist v0.4.3 das erste tatsächlich Update-fähige Release. v0.4.2 → v0.4.3 ist der erste echte Auto-Update-Roundtrip.

## [0.4.2] — 2026-05-16

> **Hinweis:** v0.4.1 wurde nicht ausgeliefert — der CI-Build schlug fehl, weil `pnpm-lock.yaml` nicht aktualisiert war. v0.4.2 bündelt die Auto-Update-Implementierung und die Angebote-Verbesserungen mit dem Lockfile-Fix.

### Added
- **Auto-Update.** Tauri-Updater-Integration mit Ed25519-signierten Releases gegen einen statischen `latest.json`-Feed bei GitHub Releases. Beim App-Start (10 Sek nach Mount) prüft die App still auf neue Versionen; bei Verfügbarkeit erscheint ein Toast „Update v0.x.x verfügbar — Installieren". In den Einstellungen gibt es zusätzlich einen „Nach Updates suchen"-Button und die Anzeige der installierten Version. Plattformübergreifend (Windows NSIS, macOS, Linux AppImage). (#30, PR #33)
- **PDF-Themes auch für Angebote.** Das in v0.4 eingeführte `settings.pdf_theme` wirkt jetzt auch auf Angebot-PDFs. Kein separates Theme-Setting; gleicher Wert für Rechnungen und Angebote. (#31, PR #35)
- **Angebot-PDFs sind PDF/A-3b.** Angebote werden jetzt PDF/A-3-konform gerendert (XMP, sRGB-OutputIntent, eingebettete Schriften), passend zum Archivierungs-Charakter. Keine ZUGFeRD-XML-Einbettung — Angebote sind keine E-Rechnungen. (#32, PR #36)

### Fixed
- **CI baute keine Artefakte mehr.** Der Auto-Update-PR hatte die neuen Tauri-Plugin-Deps in `package.json` aufgenommen, `pnpm-lock.yaml` aber nicht regeneriert. `pnpm install --frozen-lockfile` (CI-Default) brach ab; v0.4.1 und ein erster v0.4.2-Tag wurden ohne Release-Artefakte gepublisht. Lockfile regeneriert, alte Tags entfernt, v0.4.2 frisch getagged.

### Internal
- Neue Tauri-Plugins `tauri-plugin-updater` und `tauri-plugin-process` (für `relaunch()`).
- Neues Frontend-Modul `src/lib/updater.ts`, kapselt `check()` / `downloadAndInstall()` / `relaunch()` mit Tauri-Guard.
- `Toaster` um optionale Action erweitert (Label + onClick), damit der Update-Toast einen klickbaren Installieren-Button hat.
- CI signiert Build-Artefakte mit `TAURI_SIGNING_PRIVATE_KEY` und uploadet `.sig`-Dateien + ein generiertes `latest.json` an den Release.
- WeasyPrint 65.1's nativer `pdf_variant="pdf/a-3b"` deckt PDF/A-3b vollständig ab — keine neue Python-Dep (pikepdf wurde nicht benötigt).
- `offer.html.j2` bekommt die Theme-Body-Klasse, `pdf.py` reicht `settings` in den Jinja-Context, `src/lib/sidecar/offer.ts` ergänzt `pdf_theme` im Payload — pure Vererbung über die geteilte `invoice.css`, kein CSS-Duplikat.
- Setup-Doku für Maintainer: `docs/auto-update-setup.md`.

### Notes
- Bestehende v0.4.0-Installationen erhalten dieses Update **nicht** automatisch — Auto-Update beginnt erst ab v0.4.2 → v0.4.3. v0.4.0-User müssen einmalig manuell upgraden.

## [0.4.0] — 2026-05-16

### Added
- **PDF-Themes.** Drei wählbare Designs (Klassisch, Modern, Minimal), umgesetzt über CSS-Variablen in einer einzigen `invoice.html.j2` — keine Template-Duplikation. Auswahl in den Einstellungen. ZUGFeRD-XML bleibt unberührt. (#18, PR #25)
- **Reverse-Charge Drittland.** Neuer Wert `reverse_charge_type = 'third_country'` zusätzlich zu `'intra_eu'`. ZUGFeRD/Factur-X weist `CategoryCode G` + `ExemptionReason "Export outside EU"` aus; Buyer-USt-IdNr. ist für Drittland-Ausfuhrlieferungen optional. UI wird Select statt Boolean. (#19, PR #27)
- **Optionale Backup-Verschlüsselung.** Passwort beim Backup → AES-256-GCM um den ZIP-Stream, Key via Argon2id. Magic-Header `ZETTEL-ENC-1` erkennt verschlüsselte Backups beim Restore automatisch; alte unverschlüsselte Backups bleiben restorebar. Kein gespeichertes Master-Passwort. (#20, PR #28)
- **Granularer Restore.** Drei unabhängige Checkboxen (Kunden, Rechnungen+PDFs, Einstellungen). Voll-Restore unverändert. Teil-Restore läuft via `ATTACH DATABASE` + selektivem `INSERT` nach App-Start, kein Neustart nötig. PDFs werden nur kopiert wenn der Rechnungs-Bereich gewählt ist. (#21, PR #26)
- **„Als Vorlage speichern" in Rechnungs-Detail.** Erzeugt aus einer Rechnung eine wiederkehrende Vorlage mit vorausgefülltem Kunde, Positionen, Reverse-Charge-Flag und Zahlungsfrist. User setzt nur noch Intervall + Erst-Fälligkeit. (#22, PR #23)

### Fixed
- **Storno-XML Schema-Reihenfolge.** `InvoiceReferencedDocument` lag im CII-Schema an falscher Position (vor statt nach `SpecifiedTradeSettlementHeaderMonetarySummation`). Audit + Korrektur. (#17, PR #24)
- **Backup-Restore lehnte v0.4-Backups ab.** `CURRENT_SCHEMA`-Konstante in `backup.rs` war seit v0.2 nicht mehr mitgewachsen; der Manifest-Check hätte jedes v0.4-Backup mit „Schema neuer als App-Version" abgelehnt. Auf 9 angehoben.
- **Settings-Schema-Mirror.** `CURRENT_DB_SCHEMA_VERSION` im Frontend wurde mit Migration 0008 nicht mitgezogen — auf 9 korrigiert.

### Internal
- Schema-Migrationen 0007 (`settings.pdf_theme`, DB-Version 8) und 0008 (`invoices.reverse_charge_type`, DB-Version 9).
- Neues Rust-Modul `crypto.rs` (AES-256-GCM + Argon2id).
- Neuer Tauri-Command `apply_pending_partial_restore` mit `rusqlite` + `ATTACH DATABASE` für selektive Wiederherstellung.
- `bundle_backup` packt jetzt auch Angebote-PDFs in den ZIP (war seit v0.3 ein stiller Gap).
- QA-Report unter `docs/v0.4-qa-report.md`.

### Known limitations
- Themes greifen nur für Rechnungen, nicht für Angebote (Follow-up).
- Drittland-Rechnungen + Themes-Rendering sollten stichprobenartig gegen `erechnungs-validator.de` validiert werden vor dem Release-Tag.
- Encrypted-Backup-Roundtrip einmal manuell durchspielen vor dem Tag.

## [0.3.0] — 2026-05-16

### Added
- **Angebote / Quotes.** Neuer Dokumenttyp unter `/offers` mit eigenem Nummernkreis (`AN-{YYYY}-{NNNN}`, in Settings konfigurierbar) und Statusflow Entwurf → Versendet → Angenommen / Abgelehnt / Abgelaufen. Eigenes PDF-Template ohne ZUGFeRD-Embed (Angebote sind keine E-Rechnungen) und ohne PDF/A-3. Output landet in `~/Documents/Zettel/Angebote/`. Konfigurierbare Standard-Gültigkeit in Tagen; abgelaufene Angebote werden beim Öffnen der Liste / des Dashboards automatisch auf „Abgelaufen" gesetzt.
- **In Rechnung umwandeln.** Angenommene Angebote können mit einem Klick in einen Rechnungs-Entwurf konvertiert werden: Positionen werden 1:1 kopiert, Customer + Reverse-Charge-Flag übernommen, der User landet direkt im Rechnungs-Editor um Lieferdatum, Zahlungsfrist etc. zu finalisieren. Verknüpfung in beide Richtungen sichtbar.
- **Stornorechnungen / Korrekturrechnungen.** Versendete oder bezahlte Rechnungen können storniert werden — erzeugt einen Rechnungs-Entwurf mit gespiegelten Positionen, die der User für Teilrückerstattungen anpassen kann. Originalrechnung bleibt unverändert (rechtssicher, kein Soft-Delete bezahlter Belege). Totals werden negativ gespeichert, sodass Dashboard- und DATEV-Summen automatisch netten.
- **ZUGFeRD/Factur-X für Stornorechnungen.** `TypeCode 381` (Credit Note) statt 380, `ram:InvoiceReferencedDocument` (BT-25/BT-26) mit Originalrechnungsnummer und Ausstellungsdatum, negative Beträge in Header und Positionen, keine `SpecifiedTradePaymentTerms` (Stornos haben keine Fälligkeit).
- **Dashboard-Kachel „Offene Angebote".** KPI mit Summe und „läuft bald ab"-Hinweis (Angebote, die in den nächsten 7 Tagen verfallen).
- **Sidebar-Versionsanzeige** ist jetzt dynamisch aus `package.json` (zuvor hardcoded `v0.1.0`).

### Changed
- **DATEV-Export** unterscheidet zwischen Rechnungen und Stornorechnungen: Storno-Zeilen erhalten Soll/Haben-Kennzeichen `H` (statt `S`), Buchungstext-Präfix wird zu „Storno". DATEV invertiert die Buchungsrichtung automatisch.
- **Invoice Detail / Edit / List** zeigen Storno-Status mit Bannern und einem inline „Storno"-Badge; Zahlungs- und Fälligkeits-Sektionen werden für Stornos unterdrückt.

### Internal
- Schema-Migrationen 0005 (`offers` + `offer_items` + drei `offer_*` Settings-Spalten, DB-Version 6) und 0006 (`is_credit_note` + `corrects_invoice_id` auf `invoices`, DB-Version 7).
- Neuer Tauri-Command `generate_offer` neben `generate_invoice`; gemeinsamer Python-Sidecar, eigener Template-Pfad `templates/offer.html.j2`.
- `Invoice.isCreditNote` / `correctsInvoiceId` durchgehend durch DB-Layer, TS-Sidecar-Wrapper und Jinja-Templates propagiert.

### Known limitations
- Manuelle Validierung der Storno-PDFs gegen `erechnungs-validator.de` steht aus — insbesondere die Platzierung von `InvoiceReferencedDocument` im EN-16931-CII-Schema
- Angebote-PDFs sind nicht-PDF/A; reicht für interne Belege aber nicht für rechtssicheres Langzeit-Archiv
- Kein automatisches Versenden von Erinnerungen bei demnächst ablaufenden Angeboten

## [0.2.0] — 2026-05-16

### Added
- **Reverse-Charge / intra-EU B2B.** Toggle im Rechnungs-Editor, ZUGFeRD `CategoryCode K` + `ExemptionReason "VAT exempt for EEA intra-community supply of goods and services"`, deutsch-englischer Hinweistext „Steuerschuldnerschaft des Leistungsempfängers / Reverse charge" auf der Rechnung. Aktivierbar nur wenn beide Parteien eine USt-IdNr. haben und der Sender nicht Kleinunternehmer ist; erzwingt 0 % auf allen Positionen. (#2, PR #7)
- **BASIC + EXTENDED ZUGFeRD-Profile** in den Settings aktivierbar. Profil-URN wird in der `GuidelineSpecifiedDocumentContextParameter` im XML gesetzt; `factur-x`-Level passend zum Profil. (#3, PR #9)
- **DATEV-Export** (Buchungsstapel, Format 700) unter `/export`. Zeitraum + Kontenrahmen wählen, CSV mit UTF-8-BOM und CRLF-Zeilenenden speichern. SKR03 (Default) und SKR04. Eine Buchungszeile pro USt-Rate pro Rechnung. Kleinunternehmer-Rechnungen auf das steuerfreie Erlöskonto (8200/4200), Reverse-Charge auf das innergemeinschaftliche Lieferungs-Konto (8336/4125), Kunden-USt-IdNr. im Feld „EU-Land u. UStID". (#4, PR #8)
- **Backup & Restore** unter Einstellungen → ZIP mit konsistentem SQLite-Snapshot (via `VACUUM INTO`), allen erzeugten PDFs aus `~/Documents/Zettel/Rechnungen/` und `manifest.json` (App-Version + Schema-Version). Restore wird beim nächsten App-Start eingespielt; alte DB landet als `zettel.db.bak`. (#5, PR #11)
- **Wiederkehrende Rechnungen / Retainer-Vorlagen** unter `/recurring`: Vorlage mit Kunde, Intervall (monatlich / quartalsweise / jährlich), Erst-Fälligkeit, Zahlungsfrist, Positionen, Reverse-Charge-Flag. Dashboard zeigt fällige Vorlagen prominent; „Jetzt erzeugen" erstellt einen Rechnungs-Entwurf und bumpt die nächste Fälligkeit. Keine automatische Hintergrund-Generierung — User bestätigt jede Rechnung. (#6, PR #12)

### Internal
- `.gitattributes` pinnt LF für alle Code-Files. Migrations werden via Rust `include_str!` zur Compile-Zeit gelesen — CRLF-Checkouts auf Windows hatten zu „migration N was previously applied but has been modified"-Panics geführt. Future-proof für Cross-Plattform-Contributors. (PR #10)
- CI-Workflow überspringt den Matrix-Build bei reinen Doku-Änderungen (`paths-ignore`).
- Neuer Rust-Command `save_text_file(path, content)` für CSV-Exporte ohne `plugin-fs`.
- Neues Rust-Modul `backup.rs` mit pre-Builder-Hook `apply_pending_restore_blocking()`, der vor SQL-Plugin-Init läuft.
- Schema-Migrations 0003 (`is_reverse_charge`) und 0004 (`recurring_invoices` + `recurring_invoice_items`).

### Known limitations
- macOS Intel (x86_64) Build wurde aus der Matrix entfernt — GitHub-Free-Tier-Runner für `macos-13` haben Queue-Zeiten von 1h+. macOS Apple Silicon (arm64) wird gebaut und deckt die meisten Nutzer ab. Intel-Build kommt zurück, sobald Capacity oder ein Use-Case da ist.
- Manuelle Validierung der neuen Features (Reverse-Charge, BASIC/EXTENDED) gegen `erechnungs-validator.de` steht aus
- Keine Verschlüsselung für Backup-ZIPs

## [0.1.0] — 2026-05-16

### Added
- Offline-first Tauri-2-Desktop-App (Windows / macOS / Linux)
- Lokale Kunden- und Rechnungsverwaltung (SQLite)
- Status-Workflow für Rechnungen: Entwurf → Versandt → Bezahlt → Storniert
- Mehrere Umsatzsteuersätze pro Rechnung (0 %, 7 %, 19 %)
- Kleinunternehmer-Modus nach § 19 UStG inkl. korrektem ZUGFeRD-XML-Fallback (BR-CO-26)
- PDF/A-3-Generierung mit eingebettetem Factur-X / EN-16931-XML (Python-Sidecar, WeasyPrint + factur-x)
- Logo-Upload für Rechnungs-Header
- ZUGFeRD-Profil-Selector in Settings (EN 16931 in v0.1 aktiv; BASIC / EXTENDED vorbereitet)
- Konfigurierbare Nummernkreise (`K-0001`, `RE-{YYYY}-{NNNN}`)
- shadcn-Style-UI-Schicht (`src/lib/ui/`) über Bits-UI-Primitives, Light/Dark/System-Theme, Lucide-Icons
- GitHub-Actions-Matrix-Build für Windows / macOS (arm + x86) / Linux
- Issue- und Pull-Request-Templates

### Validation
- 5 von 5 manuell erzeugten Test-Rechnungen erfolgreich gegen [erechnungs-validator.de](https://erechnungs-validator.de) validiert

### Known limitations
- Code-Signing fehlt — Windows zeigt SmartScreen-Warnung beim ersten Start
- macOS-Builds sind nicht notarisiert
- WeasyPrint benötigt unter Linux/macOS Pango/Cairo/gdk-pixbuf aus dem System
- Reverse-Charge / intra-EU B2B (CategoryCode K) noch nicht abgedeckt
- Eingangsrechnungs-Verarbeitung nicht im Scope von 0.1

[Unreleased]: https://github.com/jonax1337/zettel/compare/v0.2.0...HEAD
[0.2.0]: https://github.com/jonax1337/zettel/releases/tag/v0.2.0
[0.1.0]: https://github.com/jonax1337/zettel/releases/tag/v0.1.0
