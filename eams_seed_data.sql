-- =============================================================================
-- EAMS — Seed / Demo Dataset
-- Demonstrates both Ekub models, the resolved distribution engine, and
-- balanced double-entry accounting. Run AFTER eams_database_schema.sql:
--     psql -d eams -f eams_seed_data.sql
--
-- Seeding runs as platform admin (RLS bypassed via the is_platform_admin GUC).
-- All monetary arithmetic is decimal (NUMERIC). Verify the journal balance at
-- the end by querying v_journal_balance_check — every row must show
-- balance_difference = 0.
--
-- WORKED EXAMPLES
--   Model A (traditional_pool): 20 members x ETB 50,000/month -> pool 1,000,000
--     per round. Round 1 pays the winner the full 1,000,000. 20 rounds complete
--     the cycle; each member wins exactly once.
--   Model B (equal_rounds): 4 members (2 Full target 4M, 2 Half target 2M).
--     round_value = 2,000,000. Total target = 12,000,000 -> 6 rounds. Pool per
--     period = 1,200,000 -> 10 periods. Total collected == total distributed.
--     Round 1 pays a Half winner 2,000,000 gross, 2% admin fee = 40,000
--     deduction, net 1,960,000. The Half member's target is fully satisfied.
-- =============================================================================

BEGIN;

SET LOCAL app.is_platform_admin = 'on';

-- -----------------------------------------------------------------------------
-- 0. Fixed UUIDs (for referential clarity in the demo)
-- -----------------------------------------------------------------------------
DO $$
DECLARE
    assoc_a    UUID := '11111111-1111-1111-1111-111111111111';
    assoc_b    UUID := '22222222-2222-2222-2222-222222222222';
    gm_a       UUID := 'aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa';
    cashier_a  UUID := 'bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb';
    asst_a     UUID := 'cccccccc-cccc-cccc-cccc-cccccccccccc';
    legal_a    UUID := 'dddddddd-dddd-dddd-dddd-dddddddddddd';
    branch_a1  UUID := 'b1b1b1b1-b1b1-b1b1-b1b1-b1b1b1b1b1b1';
    scheme_trad UUID := 'eeeeeeee-eeee-eeee-eeee-eeeeeeeeeeee';
    scheme_tgt  UUID := 'ffffffff-ffff-ffff-ffff-ffffffffffff';
    cash_acct   UUID := '10100000-0000-0000-0000-000000000001';
    bank_acct   UUID := '10200000-0000-0000-0000-000000000001';
    coa_cash    UUID := '20100000-0000-0000-0000-000000000001';
    coa_bank    UUID := '20200000-0000-0000-0000-000000000001';
    coa_payable UUID := '20300000-0000-0000-0000-000000000001';
    coa_fee_inc UUID := '20400000-0000-0000-0000-000000000001';
    coa_opex    UUID := '20500000-0000-0000-0000-000000000001';
    i INT;
    m_uuid UUID;
    sched_uuid UUID;
    contrib_uuid UUID;
    je_uuid UUID;
    draw_uuid UUID;
    dist_uuid UUID;
BEGIN
    -- ---------------------------------------------------------------------
    -- 1. ASSOCIATIONS
    -- ---------------------------------------------------------------------
    INSERT INTO associations (id, association_code, association_name, registration_number,
                              registration_date, address, phone, email, currency, status)
    VALUES
      (assoc_a, 'AHEA-001', 'Addis Hiwot Ekub Association', 'ERA/AA/1142/2007',
       '2015-04-12', 'Bole Road, Addis Ababa', '+251911001122', 'info@hiwotekub.et', 'ETB', 'active'),
      (assoc_b, 'ADDA-002', 'Adama Development Association', 'ERA/OR/0778/2009',
       '2017-09-01', 'Main Street, Adama', '+251922003344', 'admin@adama-dev.et', 'ETB', 'active');

    -- ---------------------------------------------------------------------
    -- 2. USERS (GM, Assistant, Cashier, Legal) for Association A
    -- ---------------------------------------------------------------------
    INSERT INTO users (id, association_id, branch_id, full_name, email, phone, password_hash, status)
    VALUES
      (gm_a,      assoc_a, NULL,      'Abebe Bekele',     'abebe@hiwotekub.et',     '+251911100001', 'argon2id$demo$hash', 'active'),
      (asst_a,    assoc_a, branch_a1, 'Chaltu Gemechu',   'chaltu@hiwotekub.et',    '+251911100002', 'argon2id$demo$hash', 'active'),
      (cashier_a, assoc_a, branch_a1, 'Dawit Tadesse',    'dawit@hiwotekub.et',     '+251911100003', 'argon2id$demo$hash', 'active'),
      (legal_a,   assoc_a, NULL,      'Eyerusalem Alemu', 'eyerusalem@hiwotekub.et','+251911100004', 'argon2id$demo$hash', 'active');

    -- ---------------------------------------------------------------------
    -- 3. BRANCH
    -- ---------------------------------------------------------------------
    INSERT INTO branches (id, association_id, branch_code, branch_name, address, manager_id, status)
    VALUES (branch_a1, assoc_a, 'BR-01', 'Bole Branch', 'Bole Road, Addis Ababa', asst_a, 'active');

    -- ---------------------------------------------------------------------
    -- 4. ROLES + PERMISSIONS (Association A)
    -- ---------------------------------------------------------------------
    INSERT INTO roles (id, association_id, role_name, description, is_system)
    VALUES
      ('role-gm-0000-0000-000000000001', assoc_a, 'General Manager', 'Association head; final approver', TRUE),
      ('role-am-0000-0000-000000000002', assoc_a, 'Assistant Manager', 'Operations and verification', TRUE),
      ('role-cs-0000-0000-000000000003', assoc_a, 'Cashier', 'Payment collection', TRUE),
      ('role-lg-0000-0000-000000000004', assoc_a, 'Legal Advisor', 'Legal and disputes', TRUE);

    -- Grant broad permissions to GM, operational subset to Assistant/Cashier
    INSERT INTO role_permissions (role_id, permission_id)
    SELECT r.id, p.id FROM roles r, permissions p
    WHERE r.association_id = assoc_a AND r.role_name = 'General Manager';

    INSERT INTO role_permissions (role_id, permission_id)
    SELECT r.id, p.id FROM roles r, permissions p
    WHERE r.association_id = assoc_a AND r.role_name = 'Assistant Manager'
      AND p.permission_code IN ('MEMBER_CREATE','MEMBER_EDIT','CONTRIBUTION_VERIFY','DRAW_CREATE','REPORT_FINANCIAL','AUDIT_VIEW');

    INSERT INTO role_permissions (role_id, permission_id)
    SELECT r.id, p.id FROM roles r, permissions p
    WHERE r.association_id = assoc_a AND r.role_name = 'Cashier'
      AND p.permission_code IN ('CONTRIBUTION_RECORD','DISTRIBUTION_PAY');

    INSERT INTO user_roles (user_id, role_id, branch_id) VALUES
      (gm_a,      'role-gm-0000-0000-000000000001', NULL),
      (asst_a,    'role-am-0000-0000-000000000002', branch_a1),
      (cashier_a, 'role-cs-0000-0000-000000000003', branch_a1),
      (legal_a,   'role-lg-0000-0000-000000000004', NULL);

    INSERT INTO approval_limits (association_id, role_id, transaction_type, max_amount)
    VALUES
      (assoc_a, 'role-gm-0000-0000-000000000001', 'distribution',  10000000),
      (assoc_a, 'role-gm-0000-0000-000000000001', 'expense',        500000),
      (assoc_a, 'role-am-0000-0000-000000000002', 'distribution',   1000000),
      (assoc_a, 'role-am-0000-0000-000000000002', 'payment_reverse', 500000);

    -- ---------------------------------------------------------------------
    -- 5. CASH / BANK ACCOUNTS + CHART OF ACCOUNTS (Association A)
    -- ---------------------------------------------------------------------
    INSERT INTO cash_accounts (id, association_id, branch_id, account_name, currency, opening_balance, current_balance)
    VALUES (cash_acct, assoc_a, branch_a1, 'Bole Petty Cash', 'ETB', 0, 0);

    INSERT INTO bank_accounts (id, association_id, branch_id, bank_name, account_name, account_number_enc, currency, opening_balance, current_balance)
    VALUES (bank_acct, assoc_a, branch_a1, 'Commercial Bank of Ethiopia', 'Hiwot Ekub Main', 'enc:1000123456789', 'ETB', 0, 0);

    INSERT INTO chart_of_accounts (id, association_id, account_code, account_name, account_type) VALUES
      (coa_cash,    assoc_a, '1000', 'Cash on Hand',           'asset'),
      (coa_bank,    assoc_a, '1010', 'Bank - CBE Main',        'asset'),
      (coa_payable, assoc_a, '2000', 'Contributions Payable',  'liability'),
      (coa_fee_inc, assoc_a, '4000', 'Administrative Fee Income','income'),
      (coa_opex,    assoc_a, '5000', 'Operating Expenses',     'expense');

    -- =====================================================================
    -- MODEL A — TRADITIONAL ROTATING EKUB  (traditional_pool)
    -- 20 members x ETB 50,000/month; pool 1,000,000/round; 20 rounds.
    -- =====================================================================
    INSERT INTO ekub_schemes (id, association_id, branch_id, scheme_code, scheme_name,
        scheme_type, distribution_method, distribution_mode, target_amount,
        contribution_frequency, distribution_frequency, contribution_start_date,
        maximum_members, minimum_members, scheme_status, created_by, approved_by)
    VALUES (scheme_trad, assoc_a, branch_a1, 'TRAD-001', 'Bole Monthly Gold Ekub',
        'traditional_rotating', 'random_draw', 'traditional_pool', 1000000,
        'monthly', 'monthly', '2026-01-05', 20, 20, 'active', gm_a, gm_a);

    -- 20 members + enrollments (all Full, contribution 50,000, target 1,000,000)
    FOR i IN 1..20 LOOP
        m_uuid := gen_random_uuid();
        INSERT INTO members (id, association_id, branch_id, member_number, full_name,
            phone, identification_type, identification_number, address, membership_status, registration_date)
        VALUES (m_uuid, assoc_a, branch_a1, 'A-'||lpad(i::text,4,'0'),
                'Member '||i||' (Traditional)', '+251912000'||lpad(i::text,3,'0'),
                'National ID', 'ID-TRAD-'||lpad(i::text,4,'0'),
                'Addis Ababa', 'active', '2025-12-15');

        INSERT INTO scheme_enrollments (id, association_id, scheme_id, member_id,
            agreed_contribution, agreed_target, enrollment_status)
        VALUES (gen_random_uuid(), assoc_a, scheme_trad, m_uuid, 50000, 1000000, 'active');

        -- Schedule row for round-1 due date
        INSERT INTO contribution_schedules (id, association_id, scheme_id, member_id,
            enrollment_id, due_date, expected_amount, status)
        SELECT gen_random_uuid(), assoc_a, scheme_trad, m_uuid, e.id,
               '2026-01-05', 50000, 'due'
        FROM scheme_enrollments e WHERE e.member_id = m_uuid AND e.scheme_id = scheme_trad;
    END LOOP;

    -- Record 20 verified contributions (pool = 1,000,000)
    FOR i IN 1..20 LOOP
        contrib_uuid := gen_random_uuid();
        SELECT e.id INTO sched_uuid  -- placeholder; we look up the schedule below
        FROM scheme_enrollments e WHERE e.scheme_id = scheme_trad LIMIT 1;

        INSERT INTO contributions (id, association_id, transaction_number, scheme_id, member_id,
            enrollment_id, payment_date, amount, currency, payment_method, cash_account_id,
            cashier_id, verification_status, verified_by, verified_at)
        SELECT contrib_uuid, assoc_a, 'TRAD-P-'||lpad(i::text,4,'0'), scheme_trad, m.id, e.id,
               '2026-01-05', 50000, 'ETB', 'cash', cash_acct, cashier_a,
               'verified', asst_a, '2026-01-05T10:00:00Z'
        FROM members m
        JOIN scheme_enrollments e ON e.member_id = m.id AND e.scheme_id = scheme_trad
        WHERE m.member_number = 'A-'||lpad(i::text,4,'0');

        -- Allocate contribution to its schedule + update schedule paid_amount
        UPDATE contribution_schedules cs
        SET paid_amount = paid_amount + 50000,
            status = 'paid'
        FROM contributions c, members m
        WHERE c.id = contrib_uuid
          AND c.member_id = m.id
          AND cs.scheme_id = scheme_trad AND cs.member_id = m.id
          AND cs.due_date = '2026-01-05';

        -- Update enrollment running contributed total
        UPDATE scheme_enrollments e SET contributed_amount = contributed_amount + 50000
        FROM contributions c WHERE c.id = contrib_uuid AND e.id = c.enrollment_id;
    END LOOP;

    -- Cash account now holds 1,000,000
    UPDATE cash_accounts SET current_balance = 1000000 WHERE id = cash_acct;

    -- Draw session round 1 (random_draw), eligible snapshot = all 20
    draw_uuid := gen_random_uuid();
    INSERT INTO draw_sessions (id, association_id, scheme_id, round_number, draw_method,
        draw_date, status, eligibility_snapshot, algorithm_version, seed_commitment,
        executed_by, approved_by, approved_at)
    SELECT draw_uuid, assoc_a, scheme_trad, 1, 'random_draw',
           '2026-01-06T11:00:00Z', 'executed',
           jsonb_agg(jsonb_build_object('member_number', m.member_number, 'eligible', true)),
           'EAMS-RNG-v1', encode(digest('seed-trad-r1-'||clock_timestamp()::text, 'sha256'),'hex'),
           asst_a, gm_a, '2026-01-06T11:30:00Z'
    FROM members m WHERE m.association_id = assoc_a AND m.member_number LIKE 'A-%';

    -- Winner = Member 1 (A-0001)
    INSERT INTO draw_results (draw_session_id, member_id, enrollment_id, result_status, approved_at)
    SELECT draw_uuid, m.id, e.id, 'selected', '2026-01-06T11:30:00Z'
    FROM members m JOIN scheme_enrollments e ON e.member_id = m.id AND e.scheme_id = scheme_trad
    WHERE m.member_number = 'A-0001';

    -- Distribution: gross 1,000,000, no deductions, net 1,000,000
    dist_uuid := gen_random_uuid();
    INSERT INTO distributions (id, association_id, scheme_id, draw_session_id, beneficiary_id,
        enrollment_id, round_number, installment_number, gross_amount, deductions,
        payment_method, cash_account_id, payment_status, payment_date, approved_by, approved_at,
        paid_by, paid_at)
    SELECT dist_uuid, assoc_a, scheme_trad, draw_uuid, m.id, e.id, 1, 1, 1000000, 0,
           'cash', cash_acct, 'paid', '2026-01-07', gm_a, '2026-01-06T12:00:00Z',
           cashier_a, '2026-01-07T09:00:00Z'
    FROM members m JOIN scheme_enrollments e ON e.member_id = m.id AND e.scheme_id = scheme_trad
    WHERE m.member_number = 'A-0001';

    -- Update winner enrollment: distributed_amount += 1,000,000 (target satisfied)
    UPDATE scheme_enrollments e SET distributed_amount = distributed_amount + 1000000
    FROM members m WHERE e.scheme_id = scheme_trad AND e.member_id = m.id AND m.member_number = 'A-0001';

    UPDATE cash_accounts SET current_balance = current_balance - 1000000 WHERE id = cash_acct;

    -- Distribution confirmation
    INSERT INTO distribution_confirmations (distribution_id, beneficiary_id, confirmation_method)
    SELECT dist_uuid, m.id, 'signature'
    FROM members m WHERE m.member_number = 'A-0001';

    -- Journal entry A-1: contributions collected (20 x 50,000 = 1,000,000)
    --   Dr Cash 1,000,000 / Cr Contributions Payable 1,000,000
    je_uuid := gen_random_uuid();
    INSERT INTO journal_entries (id, association_id, journal_number, transaction_date,
        source_type, source_id, description, status, posted_by, posted_at)
    VALUES (je_uuid, assoc_a, 'JE-TRAD-0001', '2026-01-05', 'contribution', scheme_trad,
            'Round 1 contributions - 20 members x 50,000', 'posted', asst_a, '2026-01-05T10:30:00Z');
    INSERT INTO journal_lines (journal_entry_id, account_id, debit_amount, credit_amount) VALUES
        (je_uuid, coa_cash,    1000000, 0),
        (je_uuid, coa_payable, 0, 1000000);

    -- Journal entry A-2: distribution paid (gross = net = 1,000,000)
    --   Dr Contributions Payable 1,000,000 / Cr Cash 1,000,000
    je_uuid := gen_random_uuid();
    INSERT INTO journal_entries (id, association_id, journal_number, transaction_date,
        source_type, source_id, description, status, posted_by, posted_at)
    VALUES (je_uuid, assoc_a, 'JE-TRAD-0002', '2026-01-07', 'distribution', dist_uuid,
            'Round 1 distribution to A-0001', 'posted', cashier_a, '2026-01-07T09:30:00Z');
    INSERT INTO journal_lines (journal_entry_id, account_id, debit_amount, credit_amount) VALUES
        (je_uuid, coa_payable, 1000000, 0),
        (je_uuid, coa_cash,    0, 1000000);

    -- =====================================================================
    -- MODEL B — TARGET-BASED EKUB  (equal_rounds)
    -- 2 Full (target 4M, contrib 400k) + 2 Half (target 2M, contrib 200k)
    -- round_value = 2,000,000; 6 rounds; pool/period = 1,200,000; 10 periods.
    -- =====================================================================
    INSERT INTO ekub_schemes (id, association_id, branch_id, scheme_code, scheme_name,
        scheme_type, distribution_method, distribution_mode, round_value, target_amount,
        contribution_frequency, distribution_frequency, contribution_start_date,
        admin_fee_percent, allow_repeat_winner, scheme_status, created_by, approved_by)
    VALUES (scheme_tgt, assoc_a, branch_a1, 'TGT-001', 'Bole Target Ekub 2026',
        'target_based', 'random_draw', 'equal_rounds', 2000000, 12000000,
        'monthly', 'monthly', '2026-02-05', 2.00, TRUE, 'active', gm_a, gm_a);

    -- Participation plans
    INSERT INTO participation_plans (id, association_id, scheme_id, plan_name,
        participation_units, target_allocation, contribution_formula_type, contribution_amount)
    VALUES
      ('plan-full-0000-0000-000000000001', assoc_a, scheme_tgt, 'Full',  1.00, 4000000, 'unit_multiplier', 400000),
      ('plan-half-0000-0000-000000000002', assoc_a, scheme_tgt, 'Half',  0.50, 2000000, 'unit_multiplier', 200000);

    -- 4 members: 2 Full (TB-0001/0002), 2 Half (TB-0003/0004)
    FOR i IN 1..4 LOOP
        m_uuid := gen_random_uuid();
        INSERT INTO members (id, association_id, branch_id, member_number, full_name,
            phone, identification_type, identification_number, address, membership_status, registration_date)
        VALUES (m_uuid, assoc_a, branch_a1, 'TB-'||lpad(i::text,4,'0'),
                'Member '||i||' (Target)', '+251913000'||lpad(i::text,3,'0'),
                'National ID', 'ID-TGT-'||lpad(i::text,4,'0'),
                'Addis Ababa', 'active', '2026-01-20');

        INSERT INTO scheme_enrollments (id, association_id, scheme_id, member_id,
            participation_plan_id, agreed_contribution, agreed_target, enrollment_status)
        SELECT gen_random_uuid(), assoc_a, scheme_tgt, m_uuid,
               CASE WHEN i <= 2 THEN 'plan-full-0000-0000-000000000001'
                    ELSE 'plan-half-0000-0000-000000000002' END,
               CASE WHEN i <= 2 THEN 400000 ELSE 200000 END,
               CASE WHEN i <= 2 THEN 4000000 ELSE 2000000 END,
               'active';
    END LOOP;

    -- Two periods of contributions (2026-02-05 and 2026-03-05): 4 x 2 = 8 payments
    -- Period 1 (Feb): 2x400k + 2x200k = 1,200,000
    -- Period 2 (Mar): 2x400k + 2x200k = 1,200,000
    -- Cumulative pool = 2,400,000 (enough to fund one 2,000,000 round)
    -- Insert the 8 contributions explicitly (clearer than nested loops)
    INSERT INTO contributions (id, association_id, transaction_number, scheme_id, member_id,
        enrollment_id, payment_date, amount, currency, payment_method, cash_account_id,
        cashier_id, verification_status, verified_by, verified_at)
    SELECT gen_random_uuid(), assoc_a,
           'TGT-P-'||lpad((row_number() OVER ())::text,4,'0'),
           scheme_tgt, m.id, e.id,
           CASE WHEN (row_number() OVER ()) <= 4 THEN '2026-02-05' ELSE '2026-03-05' END,
           e.agreed_contribution, 'ETB', 'cash', cash_acct, cashier_a,
           'verified', asst_a, '2026-02-06T10:00:00Z'
    FROM members m JOIN scheme_enrollments e ON e.member_id = m.id AND e.scheme_id = scheme_tgt;

    -- Schedules for both periods + allocate paid amounts + update enrollments
    INSERT INTO contribution_schedules (id, association_id, scheme_id, member_id, enrollment_id,
        due_date, expected_amount, paid_amount, status)
    SELECT gen_random_uuid(), assoc_a, scheme_tgt, m.id, e.id,
           '2026-02-05', e.agreed_contribution, e.agreed_contribution, 'paid'
    FROM members m JOIN scheme_enrollments e ON e.member_id = m.id AND e.scheme_id = scheme_tgt;

    INSERT INTO contribution_schedules (id, association_id, scheme_id, member_id, enrollment_id,
        due_date, expected_amount, paid_amount, status)
    SELECT gen_random_uuid(), assoc_a, scheme_tgt, m.id, e.id,
           '2026-03-05', e.agreed_contribution, e.agreed_contribution, 'paid'
    FROM members m JOIN scheme_enrollments e ON e.member_id = m.id AND e.scheme_id = scheme_tgt;

    -- Running contributed_amount per enrollment = 2 x agreed_contribution
    UPDATE scheme_enrollments e SET contributed_amount = 2 * e.agreed_contribution
    WHERE e.scheme_id = scheme_tgt;

    -- Cash now holds prior 0 + Model B 2,400,000 = 2,400,000
    UPDATE cash_accounts SET current_balance = 2400000 WHERE id = cash_acct;

    -- Draw round 1 (eligible: all 4, none satisfied yet)
    draw_uuid := gen_random_uuid();
    INSERT INTO draw_sessions (id, association_id, scheme_id, round_number, draw_method,
        draw_date, status, eligibility_snapshot, algorithm_version, seed_commitment,
        executed_by, approved_by, approved_at)
    SELECT draw_uuid, assoc_a, scheme_tgt, 1, 'random_draw',
           '2026-03-06T11:00:00Z', 'executed',
           jsonb_agg(jsonb_build_object('member_number', m.member_number,
                      'remaining_target', e.agreed_target - e.distributed_amount, 'eligible', true)),
           'EAMS-RNG-v1', encode(digest('seed-tgt-r1-'||clock_timestamp()::text, 'sha256'),'hex'),
           asst_a, gm_a, '2026-03-06T11:30:00Z'
    FROM members m JOIN scheme_enrollments e ON e.member_id = m.id AND e.scheme_id = scheme_tgt;

    -- Winner = TB-0003 (a Half member; target 2,000,000 == round_value -> satisfied in 1 round)
    INSERT INTO draw_results (draw_session_id, member_id, enrollment_id, result_status, approved_at)
    SELECT draw_uuid, m.id, e.id, 'selected', '2026-03-06T11:30:00Z'
    FROM members m JOIN scheme_enrollments e ON e.member_id = m.id AND e.scheme_id = scheme_tgt
    WHERE m.member_number = 'TB-0003';

    -- Distribution: gross 2,000,000; 2% admin fee deduction = 40,000; net 1,960,000
    dist_uuid := gen_random_uuid();
    INSERT INTO distributions (id, association_id, scheme_id, draw_session_id, beneficiary_id,
        enrollment_id, round_number, installment_number, gross_amount, deductions,
        payment_method, cash_account_id, payment_status, payment_date, approved_by, approved_at,
        paid_by, paid_at)
    SELECT dist_uuid, assoc_a, scheme_tgt, draw_uuid, m.id, e.id, 1, 1, 2000000, 40000,
           'cash', cash_acct, 'paid', '2026-03-07', gm_a, '2026-03-06T12:00:00Z',
           cashier_a, '2026-03-07T09:00:00Z'
    FROM members m JOIN scheme_enrollments e ON e.member_id = m.id AND e.scheme_id = scheme_tgt
    WHERE m.member_number = 'TB-0003';

    -- Deduction detail row
    INSERT INTO distribution_deductions (id, distribution_id, deduction_type, amount, reason, approved_by)
    SELECT gen_random_uuid(), dist_uuid, 'admin_fee', 40000, '2% administrative fee per scheme config', gm_a;

    -- Winner enrollment: distributed_amount += 2,000,000 (target satisfied)
    UPDATE scheme_enrollments e SET distributed_amount = distributed_amount + 2000000
    FROM members m WHERE e.scheme_id = scheme_tgt AND e.member_id = m.id AND m.member_number = 'TB-0003';

    UPDATE cash_accounts SET current_balance = current_balance - 1960000 WHERE id = cash_acct;

    INSERT INTO distribution_confirmations (distribution_id, beneficiary_id, confirmation_method)
    SELECT dist_uuid, m.id, 'signature'
    FROM members m WHERE m.member_number = 'TB-0003';

    -- Journal entry B-1: contributions collected over 2 periods = 2,400,000
    --   Dr Cash 2,400,000 / Cr Contributions Payable 2,400,000
    je_uuid := gen_random_uuid();
    INSERT INTO journal_entries (id, association_id, journal_number, transaction_date,
        source_type, source_id, description, status, posted_by, posted_at)
    VALUES (je_uuid, assoc_a, 'JE-TGT-0001', '2026-03-05', 'contribution', scheme_tgt,
            'Target Ekub - 2 periods x 1,200,000 contributions', 'posted', asst_a, '2026-03-05T10:30:00Z');
    INSERT INTO journal_lines (journal_entry_id, account_id, debit_amount, credit_amount) VALUES
        (je_uuid, coa_cash,    2400000, 0),
        (je_uuid, coa_payable, 0, 2400000);

    -- Journal entry B-2: distribution gross 2,000,000 with 40,000 admin-fee deduction
    --   Dr Contributions Payable 2,000,000
    --   Cr Cash 1,960,000  /  Cr Admin Fee Income 40,000
    je_uuid := gen_random_uuid();
    INSERT INTO journal_entries (id, association_id, journal_number, transaction_date,
        source_type, source_id, description, status, posted_by, posted_at)
    VALUES (je_uuid, assoc_a, 'JE-TGT-0002', '2026-03-07', 'distribution', dist_uuid,
            'Round 1 distribution to TB-0003 (2% admin fee)', 'posted', cashier_a, '2026-03-07T09:30:00Z');
    INSERT INTO journal_lines (journal_entry_id, account_id, debit_amount, credit_amount) VALUES
        (je_uuid, coa_payable, 2000000, 0),
        (je_uuid, coa_cash,    0, 1960000),
        (je_uuid, coa_fee_inc, 0, 40000);

    -- =====================================================================
    -- TENANT ISOLATION DEMO (Association B - minimal)
    -- =====================================================================
    INSERT INTO members (id, association_id, member_number, full_name, phone, address,
        membership_status, registration_date)
    VALUES (gen_random_uuid(), assoc_b, 'B-0001', 'Solomon Girma', '+251922556677',
            'Adama', 'active', '2026-01-10');
END $$;

COMMIT;

-- =============================================================================
-- VERIFICATION QUERIES (run manually to confirm the books balance)
-- =============================================================================
-- 1. Every posted journal entry must have balance_difference = 0:
--    SELECT * FROM v_journal_balance_check;
--
-- 2. Cash account balance after all postings:
--    SELECT account_name, current_balance FROM cash_accounts;
--    Expected: 2,400,000 (collected) - 1,000,000 (Model A dist) - 1,960,000 (Model B net)
--            = 440,000 ETB on hand.
--
-- 3. Member entitlement balances (target-based scheme):
--    SELECT member_id, target_allocation, distributed_to_date, remaining_target, target_satisfied
--    FROM v_member_entitlement_balance;
--    Expected: TB-0003 remaining_target = 0, target_satisfied = true.
--
-- 4. Trial balance (should net to zero):
--    SELECT account_type, SUM(debit_amount) AS dr, SUM(credit_amount) AS cr
--    FROM journal_lines jl JOIN journal_entries je ON je.id = jl.journal_entry_id
--    JOIN chart_of_accounts coa ON coa.id = jl.account_id
--    WHERE je.status = 'posted'
--    GROUP BY account_type ORDER BY account_type;
-- =============================================================================
