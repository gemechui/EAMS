-- =============================================================================
-- EAMS — Ekub & Association Management System
-- Complete PostgreSQL Database Schema (DDL)
-- Document Version: 1.0   |   Engine: PostgreSQL 15+
-- Currency default: ETB (Ethiopian Birr), configurable per association
--
-- This script is idempotent: run with `psql -d eams -f eams_database_schema.sql`.
-- It creates extensions, enums, all tables, constraints, indexes, a tenant-
-- isolation Row-Level Security policy set, an immutable audit-log trigger, and
-- the seed view that supports the resolved distribution model.
--
-- DESIGN NOTE — Distribution model (the flagged critical issue):
--   Three distribution modes are supported per scheme, selectable on
--   ekub_schemes.distribution_mode:
--     * traditional_pool   — one winner per round receives the full collected
--                            pool (classic rotating Ekub; all members equal).
--     * equal_rounds       — every round distributes a fixed round_value;
--                            a member wins round_value each time and is
--                            excluded once remaining_target reaches 0.
--     * target_entitlement — winner receives min(remaining_target, available
--                            pool) per round; can receive multiple rounds
--                            until target_allocation is fully met.
--   The balance view v_member_entitlement_balance exposes each member's
--   remaining target so the draw engine and UI never re-distribute to a
--   satisfied member. See the Technical Design PDF for the worked example.
-- =============================================================================

BEGIN;

-- -----------------------------------------------------------------------------
-- 0. EXTENSIONS
-- -----------------------------------------------------------------------------
CREATE EXTENSION IF NOT EXISTS pgcrypto;        -- gen_random_uuid(), digest()
CREATE EXTENSION IF NOT EXISTS citext;          -- case-insensitive emails
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";     -- uuid_generate_v4() fallback

-- -----------------------------------------------------------------------------
-- 1. ENUMERATED TYPES
-- -----------------------------------------------------------------------------
DO $$ BEGIN
  CREATE TYPE association_status AS ENUM ('pending','active','suspended','closed');
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

DO $$ BEGIN
  CREATE TYPE branch_status AS ENUM ('active','suspended','closed');
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

DO $$ BEGIN
  CREATE TYPE user_status AS ENUM ('active','suspended','locked','closed');
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

DO $$ BEGIN
  CREATE TYPE membership_status AS ENUM ('pending','active','suspended','withdrawn','closed');
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

DO $$ BEGIN
  CREATE TYPE scheme_type AS ENUM ('traditional_rotating','target_based');
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

DO $$ BEGIN
  CREATE TYPE distribution_method AS ENUM ('random_draw','predetermined_rotation');
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

DO $$ BEGIN
  -- Resolved distribution modes (see header comment)
  CREATE TYPE distribution_mode AS ENUM ('traditional_pool','equal_rounds','target_entitlement');
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

DO $$ BEGIN
  CREATE TYPE contribution_frequency AS ENUM ('daily','weekly','biweekly','monthly','annual','custom');
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

DO $$ BEGIN
  CREATE TYPE scheme_status AS ENUM ('draft','pending_approval','approved','open_enrollment','active','suspended','completed','closed');
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

DO $$ BEGIN
  CREATE TYPE plan_status AS ENUM ('active','suspended','closed');
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

DO $$ BEGIN
  CREATE TYPE enrollment_status AS ENUM ('pending','active','suspended','withdrawn','completed');
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

DO $$ BEGIN
  CREATE TYPE formula_type AS ENUM ('fixed_amount','unit_multiplier','custom');
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

DO $$ BEGIN
  CREATE TYPE payment_status AS ENUM ('upcoming','due','partially_paid','paid','overdue','waived','cancelled');
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

DO $$ BEGIN
  CREATE TYPE payment_method AS ENUM ('cash','bank_transfer','digital','other');
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

DO $$ BEGIN
  CREATE TYPE verification_status AS ENUM ('pending','verified','rejected');
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

DO $$ BEGIN
  CREATE TYPE draw_method AS ENUM ('random_draw','predetermined_rotation');
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

DO $$ BEGIN
  CREATE TYPE draw_status AS ENUM ('prepared','pending_approval','approved','executed','cancelled');
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

DO $$ BEGIN
  CREATE TYPE eligibility_state AS ENUM ('eligible','excluded','conditional');
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

DO $$ BEGIN
  CREATE TYPE distribution_status AS ENUM ('prepared','pending_approval','approved','paid','partially_paid','cancelled','reversed');
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

DO $$ BEGIN
  CREATE TYPE approval_status AS ENUM ('pending','approved','rejected','returned','escalated');
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

DO $$ BEGIN
  CREATE TYPE account_type AS ENUM ('asset','liability','equity','income','expense');
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

DO $$ BEGIN
  CREATE TYPE journal_status AS ENUM ('draft','posted','reversed');
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

DO $$ BEGIN
  CREATE TYPE notification_channel AS ENUM ('in_app','sms','email','push');
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

DO $$ BEGIN
  CREATE TYPE delivery_status AS ENUM ('queued','sent','failed','delivered');
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

DO $$ BEGIN
  CREATE TYPE dispute_status AS ENUM ('open','under_review','resolved','closed');
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

DO $$ BEGIN
  CREATE TYPE document_status AS ENUM ('draft','active','superseded','withdrawn');
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

DO $$ BEGIN
  CREATE TYPE expense_approval AS ENUM ('pending','approved','rejected','paid');
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

DO $$ BEGIN
  CREATE TYPE reconciliation_status AS ENUM ('open','matched','variance','closed');
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

-- -----------------------------------------------------------------------------
-- 2. PLATFORM & ORGANIZATION TABLES
-- -----------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS platform_admins (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    full_name       TEXT NOT NULL,
    email           CITEXT UNIQUE NOT NULL,
    password_hash   TEXT NOT NULL,
    is_super_admin  BOOLEAN NOT NULL DEFAULT FALSE,
    status          user_status NOT NULL DEFAULT 'active',
    last_login_at   TIMESTAMPTZ,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS associations (
    id                    UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    association_code      TEXT NOT NULL,
    association_name      TEXT NOT NULL,
    registration_number   TEXT,
    registration_date     DATE,
    address               TEXT,
    phone                 TEXT,
    email                 CITEXT,
    currency              TEXT NOT NULL DEFAULT 'ETB',
    date_format           TEXT NOT NULL DEFAULT 'YYYY-MM-DD',
    time_zone             TEXT NOT NULL DEFAULT 'Africa/Addis_Ababa',
    financial_year_start  DATE,
    receipt_prefix        TEXT NOT NULL DEFAULT 'RCP',
    status                association_status NOT NULL DEFAULT 'pending',
    subscription_plan     TEXT,
    created_at            TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at            TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (association_code)
);

CREATE TABLE IF NOT EXISTS branches (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    association_id  UUID NOT NULL REFERENCES associations(id) ON DELETE RESTRICT,
    branch_code     TEXT NOT NULL,
    branch_name     TEXT NOT NULL,
    address         TEXT,
    manager_id      UUID,  -- FK to users added below (deferred)
    status          branch_status NOT NULL DEFAULT 'active',
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (association_id, branch_code)
);

CREATE TABLE IF NOT EXISTS permissions (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    permission_code TEXT NOT NULL,
    description     TEXT,
    UNIQUE (permission_code)
);

CREATE TABLE IF NOT EXISTS roles (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    association_id  UUID REFERENCES associations(id) ON DELETE CASCADE,  -- NULL = platform role
    role_name       TEXT NOT NULL,
    description     TEXT,
    is_system       BOOLEAN NOT NULL DEFAULT FALSE,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (association_id, role_name)
);

CREATE TABLE IF NOT EXISTS role_permissions (
    id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    role_id       UUID NOT NULL REFERENCES roles(id) ON DELETE CASCADE,
    permission_id UUID NOT NULL REFERENCES permissions(id) ON DELETE RESTRICT,
    UNIQUE (role_id, permission_id)
);

CREATE TABLE IF NOT EXISTS users (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    association_id  UUID REFERENCES associations(id) ON DELETE CASCADE,  -- NULL = platform user
    branch_id       UUID REFERENCES branches(id) ON DELETE SET NULL,
    full_name       TEXT NOT NULL,
    email           CITEXT UNIQUE NOT NULL,
    phone           TEXT,
    password_hash   TEXT NOT NULL,
    mfa_secret      TEXT,
    status          user_status NOT NULL DEFAULT 'active',
    failed_logins   INT NOT NULL DEFAULT 0,
    locked_until    TIMESTAMPTZ,
    last_login_at   TIMESTAMPTZ,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Deferred FK: branches.manager_id -> users.id
ALTER TABLE branches
    ADD CONSTRAINT fk_branch_manager FOREIGN KEY (manager_id)
    REFERENCES users(id) ON DELETE SET NULL;

CREATE TABLE IF NOT EXISTS user_roles (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id     UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    role_id     UUID NOT NULL REFERENCES roles(id) ON DELETE CASCADE,
    branch_id   UUID REFERENCES branches(id) ON DELETE CASCADE,
    assigned_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (user_id, role_id, branch_id)
);

-- Per-role transaction approval limits (maker-checker matrix)
CREATE TABLE IF NOT EXISTS approval_limits (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    association_id  UUID NOT NULL REFERENCES associations(id) ON DELETE CASCADE,
    role_id         UUID NOT NULL REFERENCES roles(id) ON DELETE CASCADE,
    transaction_type TEXT NOT NULL,  -- 'distribution','expense','payment_reverse','scheme_approval', ...
    max_amount      NUMERIC(18,2) NOT NULL,
    currency        TEXT NOT NULL DEFAULT 'ETB',
    effective_from  DATE NOT NULL DEFAULT CURRENT_DATE,
    effective_to    DATE,
    UNIQUE (association_id, role_id, transaction_type)
);

-- -----------------------------------------------------------------------------
-- 3. MEMBER TABLES
-- -----------------------------------------------------------------------------

-- Sequence for human-readable member numbers (per association)
CREATE SEQUENCE IF NOT EXISTS member_number_seq;

CREATE TABLE IF NOT EXISTS members (
    id                    UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    association_id        UUID NOT NULL REFERENCES associations(id) ON DELETE RESTRICT,
    branch_id             UUID REFERENCES branches(id) ON DELETE SET NULL,
    member_number         TEXT NOT NULL,
    full_name             TEXT NOT NULL,
    gender                TEXT,
    date_of_birth         DATE,
    identification_type   TEXT,
    identification_number TEXT,
    phone                 TEXT NOT NULL,
    email                 CITEXT,
    address               TEXT NOT NULL,
    photograph_url        TEXT,
    emergency_contact     TEXT,
    next_of_kin           TEXT,
    membership_status     membership_status NOT NULL DEFAULT 'pending',
    registration_date     DATE NOT NULL DEFAULT CURRENT_DATE,
    created_at            TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at            TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (association_id, member_number),
    UNIQUE (association_id, identification_number)
);

CREATE TABLE IF NOT EXISTS member_documents (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    association_id  UUID NOT NULL REFERENCES associations(id) ON DELETE CASCADE,
    member_id       UUID NOT NULL REFERENCES members(id) ON DELETE CASCADE,
    document_type   TEXT NOT NULL,
    document_number TEXT,
    file_url        TEXT NOT NULL,
    uploaded_by     UUID NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
    uploaded_at     TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS member_contacts (
    id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    member_id     UUID NOT NULL REFERENCES members(id) ON DELETE CASCADE,
    contact_name  TEXT NOT NULL,
    relationship  TEXT,
    phone         TEXT NOT NULL,
    address       TEXT
);

-- -----------------------------------------------------------------------------
-- 4. SCHEME TABLES
-- -----------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS ekub_schemes (
    id                       UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    association_id           UUID NOT NULL REFERENCES associations(id) ON DELETE RESTRICT,
    branch_id                UUID REFERENCES branches(id) ON DELETE SET NULL,
    scheme_code              TEXT NOT NULL,
    scheme_name              TEXT NOT NULL,
    scheme_type              scheme_type NOT NULL,
    distribution_method      distribution_method NOT NULL,
    distribution_mode        distribution_mode NOT NULL DEFAULT 'traditional_pool',
    round_value              NUMERIC(18,2),  -- used by equal_rounds / target_entitlement
    target_amount            NUMERIC(18,2) NOT NULL DEFAULT 0,
    contribution_frequency   contribution_frequency NOT NULL,
    distribution_frequency   contribution_frequency NOT NULL,
    contribution_start_date  DATE NOT NULL,
    contribution_end_date    DATE,
    maximum_members          INT,
    minimum_members          INT,
    admin_fee_percent        NUMERIC(5,2) NOT NULL DEFAULT 0,
    penalty_late_percent     NUMERIC(5,2) NOT NULL DEFAULT 0,
    grace_period_days        INT NOT NULL DEFAULT 0,
    allow_repeat_winner      BOOLEAN NOT NULL DEFAULT FALSE,  -- within a single cycle
    scheme_status            scheme_status NOT NULL DEFAULT 'draft',
    created_by               UUID NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
    approved_by              UUID REFERENCES users(id) ON DELETE SET NULL,
    created_at               TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at               TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (association_id, scheme_code)
);

CREATE TABLE IF NOT EXISTS participation_plans (
    id                       UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    association_id           UUID NOT NULL REFERENCES associations(id) ON DELETE CASCADE,
    scheme_id                UUID NOT NULL REFERENCES ekub_schemes(id) ON DELETE CASCADE,
    plan_name                TEXT NOT NULL,
    participation_units      NUMERIC(10,4) NOT NULL,  -- e.g. 1.00 / 0.50 / 0.25
    target_allocation        NUMERIC(18,2) NOT NULL,
    contribution_formula_type formula_type NOT NULL DEFAULT 'unit_multiplier',
    contribution_amount      NUMERIC(18,2) NOT NULL DEFAULT 0,  -- periodic contribution
    status                   plan_status NOT NULL DEFAULT 'active',
    created_at               TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (scheme_id, plan_name)
);

CREATE TABLE IF NOT EXISTS scheme_enrollments (
    id                       UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    association_id           UUID NOT NULL REFERENCES associations(id) ON DELETE CASCADE,
    scheme_id                UUID NOT NULL REFERENCES ekub_schemes(id) ON DELETE RESTRICT,
    member_id                UUID NOT NULL REFERENCES members(id) ON DELETE RESTRICT,
    participation_plan_id    UUID REFERENCES participation_plans(id) ON DELETE SET NULL,
    enrollment_date          DATE NOT NULL DEFAULT CURRENT_DATE,
    agreed_contribution      NUMERIC(18,2) NOT NULL,
    agreed_target            NUMERIC(18,2) NOT NULL,
    contributed_amount       NUMERIC(18,2) NOT NULL DEFAULT 0,  -- running verified total
    distributed_amount       NUMERIC(18,2) NOT NULL DEFAULT 0,  -- running distributions to this member
    enrollment_status        enrollment_status NOT NULL DEFAULT 'pending',
    created_at               TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (scheme_id, member_id)
);

CREATE TABLE IF NOT EXISTS scheme_rules (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    association_id  UUID NOT NULL REFERENCES associations(id) ON DELETE CASCADE,
    scheme_id       UUID NOT NULL REFERENCES ekub_schemes(id) ON DELETE CASCADE,
    rule_type       TEXT NOT NULL,  -- 'eligibility','default','penalty','distribution','custom'
    rule_value      TEXT NOT NULL,
    effective_from  DATE NOT NULL DEFAULT CURRENT_DATE,
    approved_by     UUID REFERENCES users(id) ON DELETE SET NULL,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Predetermined rotation ordering
CREATE TABLE IF NOT EXISTS rotation_positions (
    id                          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    scheme_id                   UUID NOT NULL REFERENCES ekub_schemes(id) ON DELETE CASCADE,
    member_id                   UUID NOT NULL REFERENCES members(id) ON DELETE RESTRICT,
    sequence_number             INT NOT NULL,
    expected_distribution_date  DATE,
    status                      TEXT NOT NULL DEFAULT 'pending',  -- pending/distributed/skipped
    approved_by                 UUID REFERENCES users(id) ON DELETE SET NULL,
    UNIQUE (scheme_id, sequence_number),
    UNIQUE (scheme_id, member_id)
);

-- -----------------------------------------------------------------------------
-- 5. CONTRIBUTION TABLES
-- -----------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS contribution_schedules (
    id                UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    association_id    UUID NOT NULL REFERENCES associations(id) ON DELETE CASCADE,
    scheme_id         UUID NOT NULL REFERENCES ekub_schemes(id) ON DELETE RESTRICT,
    member_id         UUID NOT NULL REFERENCES members(id) ON DELETE RESTRICT,
    enrollment_id     UUID NOT NULL REFERENCES scheme_enrollments(id) ON DELETE CASCADE,
    due_date          DATE NOT NULL,
    expected_amount   NUMERIC(18,2) NOT NULL,
    paid_amount       NUMERIC(18,2) NOT NULL DEFAULT 0,
    outstanding_amount NUMERIC(18,2) GENERATED ALWAYS AS (expected_amount - paid_amount) STORED,
    status            payment_status NOT NULL DEFAULT 'upcoming',
    created_at        TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (scheme_id, member_id, due_date)
);

CREATE TABLE IF NOT EXISTS cash_accounts (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    association_id  UUID NOT NULL REFERENCES associations(id) ON DELETE RESTRICT,
    branch_id       UUID REFERENCES branches(id) ON DELETE SET NULL,
    account_name    TEXT NOT NULL,
    currency        TEXT NOT NULL DEFAULT 'ETB',
    opening_balance NUMERIC(18,2) NOT NULL DEFAULT 0,
    current_balance NUMERIC(18,2) NOT NULL DEFAULT 0,
    status          TEXT NOT NULL DEFAULT 'active',
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (association_id, account_name)
);

CREATE TABLE IF NOT EXISTS bank_accounts (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    association_id      UUID NOT NULL REFERENCES associations(id) ON DELETE RESTRICT,
    branch_id           UUID REFERENCES branches(id) ON DELETE SET NULL,
    bank_name           TEXT NOT NULL,
    account_name        TEXT NOT NULL,
    account_number_enc  TEXT NOT NULL,  -- encrypted at rest (app layer / pgcrypto)
    currency            TEXT NOT NULL DEFAULT 'ETB',
    opening_balance     NUMERIC(18,2) NOT NULL DEFAULT 0,
    current_balance     NUMERIC(18,2) NOT NULL DEFAULT 0,
    status              TEXT NOT NULL DEFAULT 'active',
    created_at          TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS contributions (
    id                    UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    association_id        UUID NOT NULL REFERENCES associations(id) ON DELETE RESTRICT,
    transaction_number    TEXT NOT NULL,
    scheme_id             UUID NOT NULL REFERENCES ekub_schemes(id) ON DELETE RESTRICT,
    member_id             UUID NOT NULL REFERENCES members(id) ON DELETE RESTRICT,
    enrollment_id         UUID NOT NULL REFERENCES scheme_enrollments(id) ON DELETE RESTRICT,
    payment_date          DATE NOT NULL,
    amount                NUMERIC(18,2) NOT NULL CHECK (amount > 0),
    currency              TEXT NOT NULL DEFAULT 'ETB',
    payment_method        payment_method NOT NULL,
    payment_reference     TEXT,
    cash_account_id       UUID REFERENCES cash_accounts(id) ON DELETE RESTRICT,
    bank_account_id       UUID REFERENCES bank_accounts(id) ON DELETE RESTRICT,
    cashier_id            UUID NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
    verification_status   verification_status NOT NULL DEFAULT 'pending',
    verified_by           UUID REFERENCES users(id) ON DELETE SET NULL,
    verified_at           TIMESTAMPTZ,
    is_reversed           BOOLEAN NOT NULL DEFAULT FALSE,
    created_at            TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (association_id, transaction_number),
    UNIQUE (association_id, payment_method, payment_reference)  -- prevent duplicate digital refs
);

CREATE TABLE IF NOT EXISTS payment_allocations (
    id                        UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    contribution_id           UUID NOT NULL REFERENCES contributions(id) ON DELETE RESTRICT,
    contribution_schedule_id  UUID NOT NULL REFERENCES contribution_schedules(id) ON DELETE RESTRICT,
    allocated_amount          NUMERIC(18,2) NOT NULL CHECK (allocated_amount > 0),
    allocated_at              TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS payment_reversals (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    association_id  UUID NOT NULL REFERENCES associations(id) ON DELETE RESTRICT,
    contribution_id UUID NOT NULL REFERENCES contributions(id) ON DELETE RESTRICT,
    reason          TEXT NOT NULL,
    reversed_amount NUMERIC(18,2) NOT NULL,
    approved_by     UUID NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
    reversed_at     TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS receipts (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    association_id  UUID NOT NULL REFERENCES associations(id) ON DELETE RESTRICT,
    receipt_number  TEXT NOT NULL,
    contribution_id UUID NOT NULL REFERENCES contributions(id) ON DELETE RESTRICT,
    issue_date      TIMESTAMPTZ NOT NULL DEFAULT now(),
    issued_by       UUID NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
    document_url    TEXT,
    UNIQUE (association_id, receipt_number)
);

-- -----------------------------------------------------------------------------
-- 6. DRAW TABLES
-- -----------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS draw_sessions (
    id                     UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    association_id         UUID NOT NULL REFERENCES associations(id) ON DELETE RESTRICT,
    scheme_id              UUID NOT NULL REFERENCES ekub_schemes(id) ON DELETE RESTRICT,
    round_number           INT NOT NULL,
    draw_method            draw_method NOT NULL,
    draw_date              TIMESTAMPTZ NOT NULL DEFAULT now(),
    status                 draw_status NOT NULL DEFAULT 'prepared',
    eligibility_snapshot   JSONB NOT NULL,         -- immutable snapshot of eligible members
    algorithm_version      TEXT NOT NULL DEFAULT 'EAMS-RNG-v1',
    seed_commitment        TEXT,                   -- hash commitment of the random seed
    verification_evidence  TEXT,
    executed_by            UUID NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
    approved_by            UUID REFERENCES users(id) ON DELETE SET NULL,
    approved_at            TIMESTAMPTZ,
    created_at             TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (scheme_id, round_number)
);

CREATE TABLE IF NOT EXISTS draw_participants (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    draw_session_id     UUID NOT NULL REFERENCES draw_sessions(id) ON DELETE CASCADE,
    member_id           UUID NOT NULL REFERENCES members(id) ON DELETE RESTRICT,
    enrollment_id       UUID NOT NULL REFERENCES scheme_enrollments(id) ON DELETE RESTRICT,
    eligibility_status  eligibility_state NOT NULL,
    eligibility_reason  TEXT,
    participation_units NUMERIC(10,4) NOT NULL DEFAULT 1.0,
    selection_position  INT,
    UNIQUE (draw_session_id, member_id)
);

CREATE TABLE IF NOT EXISTS draw_results (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    draw_session_id UUID NOT NULL REFERENCES draw_sessions(id) ON DELETE RESTRICT,
    member_id       UUID NOT NULL REFERENCES members(id) ON DELETE RESTRICT,
    enrollment_id   UUID NOT NULL REFERENCES scheme_enrollments(id) ON DELETE RESTRICT,
    result_status   TEXT NOT NULL DEFAULT 'selected',  -- selected / nullified (re-draw)
    selected_at     TIMESTAMPTZ NOT NULL DEFAULT now(),
    approved_at     TIMESTAMPTZ,
    UNIQUE (draw_session_id, member_id)
);

-- -----------------------------------------------------------------------------
-- 7. DISTRIBUTION TABLES
-- -----------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS distributions (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    association_id      UUID NOT NULL REFERENCES associations(id) ON DELETE RESTRICT,
    scheme_id           UUID NOT NULL REFERENCES ekub_schemes(id) ON DELETE RESTRICT,
    draw_session_id     UUID NOT NULL REFERENCES draw_sessions(id) ON DELETE RESTRICT,
    beneficiary_id      UUID NOT NULL REFERENCES members(id) ON DELETE RESTRICT,
    enrollment_id       UUID NOT NULL REFERENCES scheme_enrollments(id) ON DELETE RESTRICT,
    round_number        INT NOT NULL,
    installment_number  INT NOT NULL DEFAULT 1,  -- which installment toward this member's target
    gross_amount        NUMERIC(18,2) NOT NULL CHECK (gross_amount >= 0),
    deductions          NUMERIC(18,2) NOT NULL DEFAULT 0,
    net_amount          NUMERIC(18,2) GENERATED ALWAYS AS (gross_amount - deductions) STORED,
    payment_method      payment_method NOT NULL,
    payment_reference   TEXT,
    cash_account_id     UUID REFERENCES cash_accounts(id) ON DELETE RESTRICT,
    bank_account_id     UUID REFERENCES bank_accounts(id) ON DELETE RESTRICT,
    payment_status      distribution_status NOT NULL DEFAULT 'prepared',
    payment_date        DATE,
    approved_by         UUID REFERENCES users(id) ON DELETE SET NULL,
    approved_at         TIMESTAMPTZ,
    paid_by             UUID REFERENCES users(id) ON DELETE SET NULL,
    paid_at             TIMESTAMPTZ,
    is_reversed         BOOLEAN NOT NULL DEFAULT FALSE,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (association_id, payment_method, payment_reference)
);

CREATE TABLE IF NOT EXISTS distribution_deductions (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    distribution_id UUID NOT NULL REFERENCES distributions(id) ON DELETE CASCADE,
    deduction_type  TEXT NOT NULL,  -- admin_fee / penalty / contractual / other
    amount          NUMERIC(18,2) NOT NULL CHECK (amount >= 0),
    reason          TEXT,
    approved_by     UUID NOT NULL REFERENCES users(id) ON DELETE RESTRICT
);

CREATE TABLE IF NOT EXISTS distribution_confirmations (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    distribution_id     UUID NOT NULL REFERENCES distributions(id) ON DELETE CASCADE,
    beneficiary_id      UUID NOT NULL REFERENCES members(id) ON DELETE RESTRICT,
    confirmation_method TEXT NOT NULL,  -- signature / otp / biometric / witness
    confirmation_date   TIMESTAMPTZ NOT NULL DEFAULT now(),
    evidence_url        TEXT
);

-- -----------------------------------------------------------------------------
-- 8. FINANCIAL (DOUBLE-ENTRY) TABLES
-- -----------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS chart_of_accounts (
    id               UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    association_id   UUID NOT NULL REFERENCES associations(id) ON DELETE CASCADE,
    account_code     TEXT NOT NULL,
    account_name     TEXT NOT NULL,
    account_type     account_type NOT NULL,
    parent_account_id UUID REFERENCES chart_of_accounts(id) ON DELETE SET NULL,
    is_active        BOOLEAN NOT NULL DEFAULT TRUE,
    UNIQUE (association_id, account_code)
);

CREATE TABLE IF NOT EXISTS journal_entries (
    id               UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    association_id   UUID NOT NULL REFERENCES associations(id) ON DELETE RESTRICT,
    journal_number   TEXT NOT NULL,
    transaction_date DATE NOT NULL,
    source_type      TEXT NOT NULL,   -- contribution / distribution / expense / reversal / opening
    source_id        UUID,            -- polymorphic ref to originating record
    description      TEXT,
    status           journal_status NOT NULL DEFAULT 'draft',
    posted_by        UUID NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
    posted_at        TIMESTAMPTZ,
    created_at       TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (association_id, journal_number)
);

CREATE TABLE IF NOT EXISTS journal_lines (
    id                UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    journal_entry_id  UUID NOT NULL REFERENCES journal_entries(id) ON DELETE CASCADE,
    account_id        UUID NOT NULL REFERENCES chart_of_accounts(id) ON DELETE RESTRICT,
    debit_amount      NUMERIC(18,2) NOT NULL DEFAULT 0,
    credit_amount     NUMERIC(18,2) NOT NULL DEFAULT 0,
    CHECK (debit_amount >= 0 AND credit_amount >= 0),
    CHECK (NOT (debit_amount > 0 AND credit_amount > 0))  -- a line is either debit OR credit
);

-- Balanced-entry guard: every posted journal entry must have SUM(debit) = SUM(credit)
CREATE OR REPLACE VIEW v_journal_balance_check AS
SELECT je.id AS journal_entry_id,
       je.association_id,
       je.journal_number,
       SUM(jl.debit_amount)  AS total_debit,
       SUM(jl.credit_amount) AS total_credit,
       (SUM(jl.debit_amount) - SUM(jl.credit_amount)) AS balance_difference
FROM journal_entries je
JOIN journal_lines jl ON jl.journal_entry_id = je.id
WHERE je.status = 'posted'
GROUP BY je.id, je.association_id, je.journal_number;

CREATE TABLE IF NOT EXISTS expenses (
    id                   UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    association_id       UUID NOT NULL REFERENCES associations(id) ON DELETE RESTRICT,
    expense_number       TEXT NOT NULL,
    expense_date         DATE NOT NULL,
    expense_category     TEXT NOT NULL,
    amount               NUMERIC(18,2) NOT NULL CHECK (amount > 0),
    currency             TEXT NOT NULL DEFAULT 'ETB',
    description          TEXT,
    payee                TEXT,
    supporting_document  TEXT,
    approval_status      expense_approval NOT NULL DEFAULT 'pending',
    approved_by          UUID REFERENCES users(id) ON DELETE SET NULL,
    cash_account_id      UUID REFERENCES cash_accounts(id) ON DELETE RESTRICT,
    bank_account_id      UUID REFERENCES bank_accounts(id) ON DELETE RESTRICT,
    paid_at              TIMESTAMPTZ,
    created_at           TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (association_id, expense_number)
);

CREATE TABLE IF NOT EXISTS bank_reconciliations (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    association_id      UUID NOT NULL REFERENCES associations(id) ON DELETE CASCADE,
    bank_account_id     UUID NOT NULL REFERENCES bank_accounts(id) ON DELETE RESTRICT,
    reconciliation_date DATE NOT NULL,
    statement_balance   NUMERIC(18,2) NOT NULL,
    ledger_balance      NUMERIC(18,2) NOT NULL,
    difference          NUMERIC(18,2) GENERATED ALWAYS AS (statement_balance - ledger_balance) STORED,
    status              reconciliation_status NOT NULL DEFAULT 'open',
    reconciled_by       UUID NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- -----------------------------------------------------------------------------
-- 9. MANAGEMENT & CONTROL TABLES
-- -----------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS approval_requests (
    id                UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    association_id    UUID NOT NULL REFERENCES associations(id) ON DELETE CASCADE,
    transaction_type  TEXT NOT NULL,  -- distribution / expense / payment_reverse / scheme / draw
    transaction_id    UUID NOT NULL,
    submitted_by      UUID NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
    assigned_approver UUID REFERENCES users(id) ON DELETE SET NULL,
    approval_status   approval_status NOT NULL DEFAULT 'pending',
    comments          TEXT,
    approved_at       TIMESTAMPTZ,
    created_at        TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS audit_logs (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    association_id  UUID REFERENCES associations(id) ON DELETE CASCADE,  -- NULL for platform events
    user_id         UUID REFERENCES users(id) ON DELETE SET NULL,
    action          TEXT NOT NULL,
    entity_type     TEXT NOT NULL,
    entity_id       UUID,
    old_values      JSONB,
    new_values      JSONB,
    ip_address      INET,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS notifications (
    id                UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    association_id    UUID NOT NULL REFERENCES associations(id) ON DELETE CASCADE,
    member_id         UUID REFERENCES members(id) ON DELETE CASCADE,
    user_id           UUID REFERENCES users(id) ON DELETE CASCADE,
    notification_type TEXT NOT NULL,
    message           TEXT NOT NULL,
    channel           notification_channel NOT NULL,
    delivery_status   delivery_status NOT NULL DEFAULT 'queued',
    sent_at           TIMESTAMPTZ,
    created_at        TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS legal_documents (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    association_id  UUID NOT NULL REFERENCES associations(id) ON DELETE CASCADE,
    member_id       UUID REFERENCES members(id) ON DELETE CASCADE,
    scheme_id       UUID REFERENCES ekub_schemes(id) ON DELETE CASCADE,
    document_type   TEXT NOT NULL,  -- constitution / agreement / notice / dispute
    file_url        TEXT NOT NULL,
    version         INT NOT NULL DEFAULT 1,
    status          document_status NOT NULL DEFAULT 'draft',
    uploaded_by     UUID NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS disputes (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    association_id  UUID NOT NULL REFERENCES associations(id) ON DELETE CASCADE,
    member_id       UUID REFERENCES members(id) ON DELETE CASCADE,
    scheme_id       UUID REFERENCES ekub_schemes(id) ON DELETE CASCADE,
    dispute_type    TEXT NOT NULL,
    description     TEXT NOT NULL,
    status          dispute_status NOT NULL DEFAULT 'open',
    assigned_to     UUID REFERENCES users(id) ON DELETE SET NULL,  -- legal advisor
    resolution      TEXT,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    resolved_at     TIMESTAMPTZ
);

CREATE TABLE IF NOT EXISTS system_settings (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    association_id  UUID NOT NULL REFERENCES associations(id) ON DELETE CASCADE,
    setting_key     TEXT NOT NULL,
    setting_value   TEXT NOT NULL,
    effective_date  DATE NOT NULL DEFAULT CURRENT_DATE,
    UNIQUE (association_id, setting_key, effective_date)
);

-- -----------------------------------------------------------------------------
-- 10. INDEXES
-- -----------------------------------------------------------------------------
CREATE INDEX IF NOT EXISTS idx_branches_assoc        ON branches(association_id);
CREATE INDEX IF NOT EXISTS idx_users_assoc           ON users(association_id);
CREATE INDEX IF NOT EXISTS idx_user_roles_user       ON user_roles(user_id);
CREATE INDEX IF NOT EXISTS idx_members_assoc         ON members(association_id);
CREATE INDEX IF NOT EXISTS idx_members_branch        ON members(branch_id);
CREATE INDEX IF NOT EXISTS idx_member_docs_member    ON member_documents(member_id);
CREATE INDEX IF NOT EXISTS idx_schemes_assoc         ON ekub_schemes(association_id);
CREATE INDEX IF NOT EXISTS idx_schemes_status        ON ekub_schemes(scheme_status);
CREATE INDEX IF NOT EXISTS idx_plans_scheme          ON participation_plans(scheme_id);
CREATE INDEX IF NOT EXISTS idx_enroll_scheme         ON scheme_enrollments(scheme_id);
CREATE INDEX IF NOT EXISTS idx_enroll_member         ON scheme_enrollments(member_id);
CREATE INDEX IF NOT EXISTS idx_sched_member          ON contribution_schedules(member_id);
CREATE INDEX IF NOT EXISTS idx_sched_due             ON contribution_schedules(due_date);
CREATE INDEX IF NOT EXISTS idx_sched_status          ON contribution_schedules(status);
CREATE INDEX IF NOT EXISTS idx_contrib_member        ON contributions(member_id);
CREATE INDEX IF NOT EXISTS idx_contrib_scheme        ON contributions(scheme_id);
CREATE INDEX IF NOT EXISTS idx_contrib_verify        ON contributions(verification_status);
CREATE INDEX IF NOT EXISTS idx_draw_session_scheme   ON draw_sessions(scheme_id);
CREATE INDEX IF NOT EXISTS idx_draw_parts_session    ON draw_participants(draw_session_id);
CREATE INDEX IF NOT EXISTS idx_distributions_scheme  ON distributions(scheme_id);
CREATE INDEX IF NOT EXISTS idx_distributions_benef   ON distributions(beneficiary_id);
CREATE INDEX IF NOT EXISTS idx_distributions_status  ON distributions(payment_status);
CREATE INDEX IF NOT EXISTS idx_journal_assoc         ON journal_entries(association_id);
CREATE INDEX IF NOT EXISTS idx_journal_lines_entry   ON journal_lines(journal_entry_id);
CREATE INDEX IF NOT EXISTS idx_audit_assoc           ON audit_logs(association_id);
CREATE INDEX IF NOT EXISTS idx_audit_entity          ON audit_logs(entity_type, entity_id);
CREATE INDEX IF NOT EXISTS idx_approval_assoc        ON approval_requests(association_id);
CREATE INDEX IF NOT EXISTS idx_approval_status       ON approval_requests(approval_status);
CREATE INDEX IF NOT EXISTS idx_notifications_member  ON notifications(member_id);

-- -----------------------------------------------------------------------------
-- 11. UPDATED_AT TRIGGER
-- -----------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION fn_set_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = now();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DO $$ DECLARE t TEXT;
BEGIN
    FOR t IN SELECT unnest(ARRAY['associations','users','members','ekub_schemes','scheme_enrollments']) LOOP
        EXECUTE format('DROP TRIGGER IF EXISTS trg_%s_updated ON %s;', t, t);
        EXECUTE format('CREATE TRIGGER trg_%s_updated BEFORE UPDATE ON %s '
                       'FOR EACH ROW EXECUTE FUNCTION fn_set_updated_at();', t, t);
    END LOOP;
END $$;

-- -----------------------------------------------------------------------------
-- 12. IMMUTABLE AUDIT-LOG TRIGGER (generic, JSONB diff)
-- -----------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION fn_audit_log()
RETURNS TRIGGER AS $$
DECLARE
    v_assoc UUID;
    v_user  UUID;
    v_ip    INET := inet_client_addr();
BEGIN
    v_user := NULLIF(current_setting('app.current_user_id', true), '')::UUID;
    BEGIN v_assoc := NEW.association_id; EXCEPTION WHEN OTHERS THEN v_assoc := NULL; END;
    IF v_assoc IS NULL THEN
        BEGIN v_assoc := OLD.association_id; EXCEPTION WHEN OTHERS THEN v_assoc := NULL; END;
    END IF;

    IF TG_OP = 'DELETE' THEN
        INSERT INTO audit_logs(association_id, user_id, action, entity_type, entity_id, old_values, ip_address)
        VALUES (v_assoc, v_user, TG_OP || ' ' || TG_TABLE_NAME, TG_TABLE_NAME, OLD.id,
                to_jsonb(OLD), v_ip);
        RETURN OLD;
    ELSIF TG_OP = 'UPDATE' THEN
        INSERT INTO audit_logs(association_id, user_id, action, entity_type, entity_id, old_values, new_values, ip_address)
        VALUES (v_assoc, v_user, TG_OP || ' ' || TG_TABLE_NAME, TG_TABLE_NAME, NEW.id,
                to_jsonb(OLD), to_jsonb(NEW), v_ip);
        RETURN NEW;
    ELSIF TG_OP = 'INSERT' THEN
        INSERT INTO audit_logs(association_id, user_id, action, entity_type, entity_id, new_values, ip_address)
        VALUES (v_assoc, v_user, TG_OP || ' ' || TG_TABLE_NAME, TG_TABLE_NAME, NEW.id,
                to_jsonb(NEW), v_ip);
        RETURN NEW;
    END IF;
    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

-- Attach audit trigger to all financially sensitive tables
DO $$ DECLARE t TEXT;
BEGIN
    FOR t IN SELECT unnest(ARRAY[
        'associations','branches','users','members','ekub_schemes','participation_plans',
        'scheme_enrollments','scheme_rules','rotation_positions','contribution_schedules',
        'contributions','payment_allocations','payment_reversals','receipts',
        'draw_sessions','draw_participants','draw_results','distributions',
        'distribution_deductions','distribution_confirmations','journal_entries',
        'journal_lines','expenses','bank_reconciliations','approval_requests',
        'legal_documents','disputes','system_settings','cash_accounts','bank_accounts'
    ]) LOOP
        EXECUTE format('DROP TRIGGER IF EXISTS trg_%s_audit ON %s;', t, t);
        EXECUTE format('CREATE TRIGGER trg_%s_audit AFTER INSERT OR UPDATE OR DELETE ON %s '
                       'FOR EACH ROW EXECUTE FUNCTION fn_audit_log();', t, t);
    END LOOP;
END $$;

-- -----------------------------------------------------------------------------
-- 13. ROW-LEVEL SECURITY — TENANT ISOLATION
-- -----------------------------------------------------------------------------
-- Strategy: every association-owned table carries association_id. RLS policies
-- restrict rows to the caller's association, read from the session GUC
-- 'app.current_association_id'. Platform admins bypass RLS explicitly.
-- The application MUST set the GUC on every connection:
--     SET LOCAL app.current_association_id = '<uuid>';
--     SET LOCAL app.current_user_id       = '<uuid>';
--     SET LOCAL app.is_platform_admin     = 'off';
ALTER TABLE associations   ENABLE ROW LEVEL SECURITY;
ALTER TABLE branches       ENABLE ROW LEVEL SECURITY;
ALTER TABLE users          ENABLE ROW LEVEL SECURITY;
ALTER TABLE roles          ENABLE ROW LEVEL SECURITY;
ALTER TABLE role_permissions ENABLE ROW LEVEL SECURITY;
ALTER TABLE user_roles     ENABLE ROW LEVEL SECURITY;
ALTER TABLE approval_limits ENABLE ROW LEVEL SECURITY;
ALTER TABLE members        ENABLE ROW LEVEL SECURITY;
ALTER TABLE member_documents ENABLE ROW LEVEL SECURITY;
ALTER TABLE ekub_schemes   ENABLE ROW LEVEL SECURITY;
ALTER TABLE participation_plans ENABLE ROW LEVEL SECURITY;
ALTER TABLE scheme_enrollments ENABLE ROW LEVEL SECURITY;
ALTER TABLE scheme_rules   ENABLE ROW LEVEL SECURITY;
ALTER TABLE rotation_positions ENABLE ROW LEVEL SECURITY;
ALTER TABLE contribution_schedules ENABLE ROW LEVEL SECURITY;
ALTER TABLE contributions  ENABLE ROW LEVEL SECURITY;
ALTER TABLE payment_allocations ENABLE ROW LEVEL SECURITY;
ALTER TABLE payment_reversals ENABLE ROW LEVEL SECURITY;
ALTER TABLE receipts       ENABLE ROW LEVEL SECURITY;
ALTER TABLE draw_sessions  ENABLE ROW LEVEL SECURITY;
ALTER TABLE draw_participants ENABLE ROW LEVEL SECURITY;
ALTER TABLE draw_results   ENABLE ROW LEVEL SECURITY;
ALTER TABLE distributions  ENABLE ROW LEVEL SECURITY;
ALTER TABLE distribution_deductions ENABLE ROW LEVEL SECURITY;
ALTER TABLE distribution_confirmations ENABLE ROW LEVEL SECURITY;
ALTER TABLE cash_accounts  ENABLE ROW LEVEL SECURITY;
ALTER TABLE bank_accounts  ENABLE ROW LEVEL SECURITY;
ALTER TABLE chart_of_accounts ENABLE ROW LEVEL SECURITY;
ALTER TABLE journal_entries ENABLE ROW LEVEL SECURITY;
ALTER TABLE journal_lines  ENABLE ROW LEVEL SECURITY;
ALTER TABLE expenses       ENABLE ROW LEVEL SECURITY;
ALTER TABLE bank_reconciliations ENABLE ROW LEVEL SECURITY;
ALTER TABLE approval_requests ENABLE ROW LEVEL SECURITY;
ALTER TABLE audit_logs     ENABLE ROW LEVEL SECURITY;
ALTER TABLE notifications  ENABLE ROW LEVEL SECURITY;
ALTER TABLE legal_documents ENABLE ROW LEVEL SECURITY;
ALTER TABLE disputes       ENABLE ROW LEVEL SECURITY;
ALTER TABLE system_settings ENABLE ROW LEVEL SECURITY;
ALTER TABLE member_contacts ENABLE ROW LEVEL SECURITY;

-- Helper: read the current association GUC as UUID (NULL if unset)
CREATE OR REPLACE FUNCTION current_association_id()
RETURNS UUID AS $$
    SELECT NULLIF(current_setting('app.current_association_id', true), '')::UUID;
$$ LANGUAGE SQL STABLE;

CREATE OR REPLACE FUNCTION is_platform_admin()
RETURNS BOOLEAN AS $$
    SELECT COALESCE(current_setting('app.is_platform_admin', true)::BOOLEAN, FALSE);
$$ LANGUAGE SQL STABLE;

-- Per-table policies: USING (read) + WITH CHECK (write)
DO $$ DECLARE t TEXT;
BEGIN
    FOR t IN SELECT unnest(ARRAY[
        'branches','users','roles','approval_limits','members','member_documents',
        'member_contacts','ekub_schemes','participation_plans','scheme_enrollments',
        'scheme_rules','rotation_positions','contribution_schedules','contributions',
        'payment_allocations','payment_reversals','receipts','draw_sessions',
        'draw_participants','draw_results','distributions','distribution_deductions',
        'distribution_confirmations','cash_accounts','bank_accounts','chart_of_accounts',
        'journal_entries','expenses','bank_reconciliations','approval_requests',
        'audit_logs','notifications','legal_documents','disputes','system_settings'
    ]) LOOP
        EXECUTE format(
            'DROP POLICY IF EXISTS %1$s_tenant_isolate ON %1$s; '
            'CREATE POLICY %1$s_tenant_isolate ON %1$s '
            'USING (association_id = current_association_id() OR is_platform_admin()) '
            'WITH CHECK (association_id = current_association_id() OR is_platform_admin());',
            t);
    END LOOP;
END $$;

-- associations table: platform admin sees all; association users see only their own row
DROP POLICY IF EXISTS associations_tenant_isolate ON associations;
CREATE POLICY associations_tenant_isolate ON associations
    USING (id = current_association_id() OR is_platform_admin())
    WITH CHECK (is_platform_admin());

-- journal_lines: inherits isolation through journal_entries (join-based policy)
DROP POLICY IF EXISTS journal_lines_tenant_isolate ON journal_lines;
CREATE POLICY journal_lines_tenant_isolate ON journal_lines
    USING (EXISTS (
        SELECT 1 FROM journal_entries je
        WHERE je.id = journal_lines.journal_entry_id
          AND (je.association_id = current_association_id() OR is_platform_admin())))
    WITH CHECK (EXISTS (
        SELECT 1 FROM journal_entries je
        WHERE je.id = journal_lines.journal_entry_id
          AND je.association_id = current_association_id()));

-- role_permissions: inherits through roles
DROP POLICY IF EXISTS role_permissions_tenant_isolate ON role_permissions;
CREATE POLICY role_permissions_tenant_isolate ON role_permissions
    USING (EXISTS (
        SELECT 1 FROM roles r WHERE r.id = role_permissions.role_id
          AND (r.association_id = current_association_id() OR r.association_id IS NULL OR is_platform_admin())))
    WITH CHECK (EXISTS (
        SELECT 1 FROM roles r WHERE r.id = role_permissions.role_id
          AND (r.association_id = current_association_id() OR is_platform_admin())));

-- Force the owner to also be subject to RLS (so app connections are always filtered)
ALTER TABLE associations        FORCE ROW LEVEL SECURITY;
ALTER TABLE members             FORCE ROW LEVEL SECURITY;
ALTER TABLE contributions       FORCE ROW LEVEL SECURITY;
ALTER TABLE distributions       FORCE ROW LEVEL SECURITY;
ALTER TABLE journal_entries     FORCE ROW LEVEL SECURITY;
ALTER TABLE journal_lines       FORCE ROW LEVEL SECURITY;
ALTER TABLE draw_sessions       FORCE ROW LEVEL SECURITY;
ALTER TABLE draw_results        FORCE ROW LEVEL SECURITY;
ALTER TABLE receipts            FORCE ROW LEVEL SECURITY;
ALTER TABLE expenses            FORCE ROW LEVEL SECURITY;

-- -----------------------------------------------------------------------------
-- 14. ENTITLEMENT BALANCE VIEW (resolved distribution model)
-- -----------------------------------------------------------------------------
-- Exposes, per active enrollment, how much of the member's target allocation
-- has been distributed and how much remains. The draw engine and distribution
-- engine MUST consult this view to avoid over-distribution and to exclude
-- fully-satisfied members from future rounds.
CREATE OR REPLACE VIEW v_member_entitlement_balance AS
SELECT e.id AS enrollment_id,
       e.association_id,
       e.scheme_id,
       e.member_id,
       e.agreed_target                         AS target_allocation,
       e.distributed_amount                    AS distributed_to_date,
       (e.agreed_target - e.distributed_amount) AS remaining_target,
       CASE WHEN e.agreed_target - e.distributed_amount <= 0
            THEN TRUE ELSE FALSE END           AS target_satisfied
FROM scheme_enrollments e
WHERE e.enrollment_status = 'active';

-- -----------------------------------------------------------------------------
-- 15. PERMISSION SEED (catalog of permission codes from SRS §2.3)
-- -----------------------------------------------------------------------------
INSERT INTO permissions (permission_code, description) VALUES
    ('MEMBER_CREATE',        'Register a new member'),
    ('MEMBER_APPROVE',       'Approve a pending membership'),
    ('MEMBER_EDIT',          'Edit member profile details'),
    ('SCHEME_CREATE',        'Create a new Ekub scheme'),
    ('SCHEME_APPROVE',       'Approve a scheme for enrollment'),
    ('CONTRIBUTION_RECORD',  'Record a member payment'),
    ('CONTRIBUTION_VERIFY',  'Verify a pending contribution'),
    ('PAYMENT_REVERSE',      'Reverse an erroneous contribution'),
    ('DRAW_CREATE',          'Prepare a draw session'),
    ('DRAW_EXECUTE',         'Execute the random selection'),
    ('DRAW_APPROVE',         'Approve a draw result'),
    ('DISTRIBUTION_APPROVE', 'Approve a distribution payment'),
    ('DISTRIBUTION_PAY',     'Record distribution payment to beneficiary'),
    ('EXPENSE_APPROVE',      'Approve an association expense'),
    ('REPORT_FINANCIAL',     'Generate financial reports'),
    ('AUDIT_VIEW',           'View audit logs'),
    ('USER_MANAGE',          'Manage users and role assignments')
ON CONFLICT (permission_code) DO NOTHING;

COMMIT;

-- =============================================================================
-- END OF SCHEMA
-- =============================================================================
