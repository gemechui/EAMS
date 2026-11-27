# EAMS — Ekub & Association Management System

> A secure, multi-tenant platform that manages the complete lifecycle of associations and their Ekub schemes — from member registration and contribution collection through draws, fund distribution, reconciliation and scheme closure.

**Document Version:** 1.0 · **Initial Market:** Ethiopia · **Currency:** ETB · **Platform:** Web Application + Progressive Web App (PWA)

This repository is the **pre-implementation technical design package** for EAMS. It translates the Software Requirements Specification into a concrete, buildable blueprint: a resolved distribution model, a complete PostgreSQL schema with tenant isolation, an API specification, UI wireframes, test cases, and a deployment guide. The companion site is auto-deployed to GitHub Pages on every push.

---

## 📦 Repository Contents

| Path | Description |
| --- | --- |
| [`database/eams_database_schema.sql`](database/eams_database_schema.sql) | Complete PostgreSQL DDL — 38+ tables, foreign keys, unique constraints, indexes, an immutable audit trigger on 30 tables, and full Row-Level Security tenant isolation (forced on the 6 sensitive tables). |
| [`database/eams_seed_data.sql`](database/eams_seed_data.sql) | Demonstration dataset for both Ekub models with balanced double-entry journals. Verification queries prove the books balance to zero. |
| [`api/eams_api_spec.yaml`](api/eams_api_spec.yaml) | OpenAPI 3.1 specification — 58 endpoints, 85 schemas, all references validated. Ready for code generation or team hand-off. |
| [`docs/EAMS_Technical_Design.pdf`](docs/EAMS_Technical_Design.pdf) | The resolved distribution model, schema walkthrough, financial calculation rules, draw engine design, and the maker-checker approval matrix. |
| [`docs/EAMS_UI_Wireframes.pdf`](docs/EAMS_UI_Wireframes.pdf) | All 28 screens from the SRS, each as a labeled wireframe with a field/function list. |
| [`docs/EAMS_Test_Cases.xlsx`](docs/EAMS_Test_Cases.xlsx) | 82 test cases mapped to every SRS §11.1–11.9 acceptance criterion, plus a summary dashboard sheet. |
| [`docs/EAMS_Deployment_Guide.pdf`](docs/EAMS_Deployment_Guide.pdf) | Docker-based hosting, environment variables, migrations with RLS, backups & disaster recovery, security hardening, monitoring, and a go-live checklist. |
| [`scripts/`](scripts/) | The Python generators that produced the PDFs and spreadsheet — recoverable artifacts for future revisions. |
| [`.github/workflows/deploy.yml`](.github/workflows/deploy.yml) | GitHub Actions workflow that deploys the landing page and documentation to GitHub Pages on push. |
| [`index.html`](index.html) | The GitHub Pages landing page (repository homepage when Pages is enabled). |

---

## 🎯 The Resolved Distribution Model

The SRS flags **how members with different participation levels (Full, Half, Quarter, Custom) receive their distributions** as the single most important design issue to resolve before implementing the financial engine. This package resolves it with a configurable three-mode engine, selectable per scheme via `ekub_schemes.distribution_mode`:

| Mode | Round payout | Best for |
| --- | --- | --- |
| `traditional_pool` | Full collected pool to one winner | Classic rotating Ekub; equal members |
| `equal_rounds` *(recommended default)* | Fixed `round_value` per round | Mixed Full / Half / Quarter targets |
| `target_entitlement` | `min(remaining_target, available_pool)` per round | Variable pool / irregular collections |

The recommended default — **`equal_rounds`** — pays a fixed `round_value` (typically the smallest member target) per round. A member wins exactly enough rounds to satisfy their target, then is excluded from future rounds by the `v_member_entitlement_balance` view. Total distributed always equals total collected equals the sum of all member targets, so **the books balance by construction**. The traditional rotating Ekub is the `traditional_pool` special case.

A full worked example and the eligibility/deduction logic are in the [Technical Design PDF](docs/EAMS_Technical_Design.pdf).

---

## 🚀 Quick Start

Requirements: PostgreSQL 15+ and the `psql` client.

```bash
# 1. Create the database and a least-privilege application role
createdb eams
psql -d eams -c "CREATE USER eams_app WITH PASSWORD 'change-me';"
psql -d eams -c "GRANT ALL PRIVILEGES ON DATABASE eams TO eams_app;"

# 2. Load the schema (tables, constraints, RLS policies, audit triggers)
psql -d eams -f database/eams_database_schema.sql

# 3. Load the demonstration dataset (demonstration only — never production)
psql -d eams -f database/eams_seed_data.sql

# 4. Verify the books balance — every posted entry must show balance_difference = 0
psql -d eams -c "SELECT * FROM v_journal_balance_check;"
```

After loading the seed, the cash account should hold **ETB 440,000** (2,400,000 collected − 1,000,000 Model A distribution − 1,960,000 Model B net distribution), the balance sheet should balance (Assets 440,000 = Liabilities 400,000 + Income 40,000), and both winners' remaining targets should be zero. If any of these fail, do not proceed.

For the full Docker-based deployment, TLS, backups, and the go-live checklist, see the [Deployment Guide](docs/EAMS_Deployment_Guide.pdf).

---

## 🌐 Enabling the GitHub Pages Site

The repository includes a static landing page (`index.html`) and an Actions workflow that deploys it (and the `docs/`, `database/`, `api/`, `scripts/` folders as static files) to GitHub Pages on every push.

1. Push this repository to GitHub.
2. In the repo, go to **Settings → Pages → Build and deployment → Source** and select **GitHub Actions**.
3. The `Deploy to GitHub Pages` workflow runs on every push to `main` (or `master`) and on manual dispatch.
4. Your site publishes at `https://<your-org>.github.io/<your-repo>/`.

The landing page is fully responsive and self-contained (inline CSS/JS, no build step).

---

## 🏗️ Architecture at a Glance

- **Frontend:** Next.js / React + Tailwind (28 screens, PWA shell, offline queue)
- **API:** Django REST Framework (58 endpoints — see the OpenAPI spec)
- **Database:** PostgreSQL 15+ (38+ tables, RLS, audit triggers, double-entry ledger)
- **Async:** Celery + Redis (schedules, receipts, notifications, reports)
- **Storage:** Private object storage (documents, legal files, evidence)
- **Integrations:** Telebirr / CBE Birr / M-Pesa Ethiopia, SMS, email, push

Tenant isolation is enforced **at the database tier** with Row-Level Security rather than only in application code. Every association-owned table carries an `association_id`; on each authenticated request the backend sets session GUCs (`app.current_association_id`, `app.current_user_id`) and RLS silently filters every row that does not match.

---

## 🧪 Testing

The [Test Cases spreadsheet](docs/EAMS_Test_Cases.xlsx) contains 82 cases across 9 modules, mapped one-to-one to the SRS §11.1–11.9 acceptance criteria (Membership, Scheme, Contribution, Draw, Distribution, Financial, Multi-Association, PWA, and the Definition of Done). Use it as the acceptance-test backlog.

---

## 📋 Before Going Live

The remaining open business questions in SRS Part 14 (whether members keep contributing after receiving their allocation, how defaults are handled, whether a member may join multiple schemes) are all expressible as `scheme_rules` rows — **configuration, not architecture**. Before handling funds commercially:

- Formally approve the distribution mode and `round_value` per scheme.
- Ratify the approval-limit matrix.
- Undergo legal and regulatory review in Ethiopia.
- Complete every item on the [Deployment Guide go-live checklist](docs/EAMS_Deployment_Guide.pdf).

---

## 📄 License

Released under the [MIT License](LICENSE). The EAMS specification and design documents are provided as-is for implementation by the association and its development team.

---

## 🔗 Companion Files

This repository is the packaged form of the standalone deliverables. Each artifact can also be used independently:
- The SQL files load directly into any PostgreSQL 15+ instance.
- The OpenAPI YAML imports into Swagger UI, Postman, or code generators (openapi-generator, orval).
- The PDFs and XLSX are self-contained reference documents.
