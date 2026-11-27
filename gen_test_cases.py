#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
EAMS Test Cases XLSX — maps every SRS Part 11 acceptance criterion (11.1-11.9)
to concrete test cases, plus a summary dashboard sheet.
Output: /home/z/my-project/download/EAMS_Test_Cases.xlsx
"""
import os
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter
from openpyxl.worksheet.table import Table, TableStyleInfo

OUT = '/home/z/my-project/download/EAMS_Test_Cases.xlsx'

# Brand palette (SRS 7.1)
NAVY = '0F2A43'; TEAL = '1F7A8C'; EMERALD = '2F9E6B'
STRIPE = 'EEF2F6'; MUTED = '6B7785'; TEXT = '1A2230'; WHITE = 'FFFFFF'

thin = Side(style='thin', color='CBD5E0')
BORDER = Border(left=thin, right=thin, top=thin, bottom=thin)
HDR_FONT = Font(name='Calibri', bold=True, color=WHITE, size=10)
HDR_FILL = PatternFill('solid', fgColor=NAVY)
CELL_FONT = Font(name='Calibri', color=TEXT, size=9.5)
STRIPE_FILL = PatternFill('solid', fgColor=STRIPE)
WRAP = Alignment(wrap_text=True, vertical='top')
CENTER = Alignment(horizontal='center', vertical='center', wrap_text=True)

# Each row: (ID, Module, SRS Ref, Scenario, Pre-conditions, Steps, Expected Result, Priority, Type)
T = []
def add(mod, srs, scen, pre, steps, exp, pri='High', typ='Functional'):
    prefix = {'Membership':'MEM','Scheme':'SCH','Contribution':'CON','Draw':'DRW',
              'Distribution':'DIS','Financial':'FIN','Multi-Assoc':'TEN','PWA':'PWA',
              'Acceptance':'ACC'}.get(mod,'GEN')
    T.append((f'TC-{prefix}-{len([x for x in T if x[0].startswith(f"TC-{prefix}")])+1:03d}',
              mod, srs, scen, pre, steps, exp, pri, typ))

# 11.1 Membership
add('Membership','11.1.1','Register a new member','Association active; assistant manager logged in',
    '1. Open Member Register > New.\n2. Fill required fields.\n3. Submit.',
    'Member created with status Pending and an approval request raised.', 'High')
add('Membership','11.1.2','Generate a unique member number','Member pending approval',
    '1. Approve the pending member.\n2. Read the generated member_number.',
    'A unique member_number is assigned within the association; uniqueness enforced by composite unique constraint.', 'High')
add('Membership','11.1.3','Prevent duplicate member records','A member with ID number ID-001 exists',
    '1. Attempt to register another member with ID number ID-001.',
    'System rejects the duplicate identification_number; error returned, no row created.', 'High')
add('Membership','11.1.4','Approve and activate membership','Member in Pending status',
    '1. General Manager approves the member.',
    'Membership status becomes Active; member portal access enabled.', 'High')
add('Membership','11.1.5','Suspend and reactivate a member','An active member exists',
    '1. Suspend with a reason.\n2. Reactivate.',
    'Status moves Active -> Suspended -> Active; both transitions audited.', 'Medium')
add('Membership','11.1.6','Member cannot access other members financial records','Two members A and B in same association',
    '1. Log in as member A.\n2. Attempt to query member B contribution history via API.',
    'RLS returns 0 rows for B; only A own records are visible.', 'High','Security')

# 11.2 Scheme
add('Scheme','11.2.1','Create a traditional Ekub scheme','General Manager logged in',
    '1. Run scheme wizard.\n2. Select Traditional Rotating model.\n3. Configure fixed contribution.\n4. Submit for approval.',
    'Scheme created in draft, then pending_approval; distribution_mode = traditional_pool.', 'High')
add('Scheme','11.2.2','Create a target-based scheme','General Manager logged in',
    '1. Run wizard.\n2. Select Target-Based model.\n3. Configure participation plans.\n4. Submit.',
    'Scheme created with distribution_mode equal_rounds or target_entitlement; round_value set.', 'High')
add('Scheme','11.2.3','Create full, half and quarter plans','A target-based scheme exists',
    '1. Add Full (units 1.0), Half (0.5), Quarter (0.25) plans with targets.',
    'Three participation_plans rows created; targets and contributions computed per unit multiplier.', 'High')
add('Scheme','11.2.4','Create a custom participation plan','A scheme exists',
    '1. Add a Custom plan with configurable units and target.',
    'Custom plan persisted with its own formula_type and contribution_amount.', 'Medium')
add('Scheme','11.2.5','Configure daily, weekly, biweekly, monthly, annual contributions','A scheme in draft',
    '1. Set contribution_frequency to each value in turn.',
    'Schedule generation honors each frequency; due dates spaced correctly.', 'Medium')
add('Scheme','11.2.6','Confirm calculations are correct','Enrolled members with verified contributions',
    '1. Compare periodic contribution = units x contribution unit.\n2. Compare outstanding = expected - paid.',
    'All computed figures match the approved formulas; generated columns equal manual calc.', 'High')
add('Scheme','11.2.7','Prevent enrollment beyond configured capacity','Scheme maximum_members = 5; 5 already enrolled',
    '1. Attempt to enroll a 6th member.',
    'Enrollment rejected with capacity error; no row created.', 'High')

# 11.3 Contribution
add('Contribution','11.3.1','Record a cash payment','Active member with a due schedule; cashier logged in',
    '1. Open Payment Collection.\n2. Select member + scheme.\n3. Enter amount, method=cash.\n4. Submit for verification.',
    'Contribution row created with verification_status pending; cash_account unchanged until verified.', 'High')
add('Contribution','11.3.2','Record a bank transfer','Cashier logged in',
    '1. Enter method=bank_transfer, bank_account, reference.',
    'Contribution recorded with bank_account_id and payment_reference; reference stored for dedup.', 'High')
add('Contribution','11.3.3','Record a digital payment','Cashier logged in; payment gateway reachable',
    '1. Enter method=digital with provider reference.\n2. Verify via provider callback.',
    'Contribution only marked verified after authenticated provider response, not on client success alone.', 'High','Security')
add('Contribution','11.3.4','Generate a receipt','A verified contribution exists',
    '1. Trigger receipt generation.',
    'Receipt row created with unique receipt_number; PDF produced; journal entry posted (Dr Cash / Cr Payable).', 'High')
add('Contribution','11.3.5','Record a partial payment','Member owes ETB 100,000',
    '1. Record ETB 40,000 against the schedule.',
    'paid_amount=40,000; outstanding_amount=60,000 (generated); status=partially_paid.', 'Medium')
add('Contribution','11.3.6','Record an advance payment','No currently due schedule',
    '1. Record an advance payment.',
    'Advance allocated to the next future schedule per association rules; no double-counting.', 'Medium')
add('Contribution','11.3.7','Calculate outstanding amounts','Schedules with mixed paid/partial/unpaid',
    '1. Query contribution_schedules.',
    'outstanding_amount = expected - paid for every row (generated column); totals reconcile.', 'High')
add('Contribution','11.3.8','Reject duplicate payment references','A digital reference REF-9 already recorded',
    '1. Attempt to record a second contribution with REF-9.',
    'Insert rejected by unique(association, method, reference) constraint; error returned.', 'High')
add('Contribution','11.3.9','Reverse an erroneous transaction with authorization','A verified contribution exists',
    '1. Cashier requests reversal with reason.\n2. Assistant Manager approves.',
    'payment_reversals row created; is_reversed=true; reversing journal entry posted; original row preserved.', 'High')
add('Contribution','11.3.10','Verify the audit history','After a contribution + reversal',
    '1. Query audit_logs for the contribution entity.',
    'Insert, update, and delete events present with old/new JSONB, user, IP, timestamp.', 'Medium')

# 11.4 Draw
add('Draw','11.4.1','Generate an eligible member list','Active scheme with verified contributions',
    '1. Prepare a draw session.',
    'Eligible snapshot built from v_member_entitlement_balance; only active, non-satisfied members included.', 'High')
add('Draw','11.4.2','Exclude ineligible members','A member defaulted; another already satisfied',
    '1. Inspect the eligibility snapshot.',
    'Defaulted and target-satisfied members excluded with a recorded eligibility_reason.', 'High')
add('Draw','11.4.3','Execute random selection','Prepared draw session',
    '1. Commit the seed.\n2. Execute the draw.',
    'Winner selected via secure RNG; seed_commitment recorded before execution.', 'High')
add('Draw','11.4.4','Record the winner','Executed draw',
    '1. Read draw_results.',
    'Single winner row recorded with selected_at and result_status selected.', 'High')
add('Draw','11.4.5','Prevent duplicate winners within the same cycle','Winner already selected this cycle',
    '1. Attempt to include the prior winner in the next round snapshot.',
    'Prior winner excluded (target_satisfied or repeat rule) unless allow_repeat_winner is true.', 'High')
add('Draw','11.4.6','Execute predetermined rotation','Rotation scheme with sequence set',
    '1. Prepare round.\n2. Identify next pending position.',
    'Next member in rotation_positions selected; no RNG used; sequence integrity preserved.', 'Medium')
add('Draw','11.4.7','Preserve draw history','After several rounds',
    '1. Query draw_sessions + draw_results.',
    'All historical sessions and results present; none deleted.', 'Medium')
add('Draw','11.4.8','Prevent unauthorized alteration of completed draws','An executed draw exists',
    '1. Attempt to update draw_results from a non-approver role.',
    'Update blocked by permission DRAW_APPROVE; only documented cancellation + re-draw allowed.', 'High','Security')
add('Draw','11.4.9','Verify draw evidence','A completed draw',
    '1. Reveal the seed and recompute the commitment hash.',
    'Revealed seed hashes to the stored seed_commitment; algorithm_version matches.', 'Medium','Audit')

# 11.5 Distribution
add('Distribution','11.5.1','Verify the selected beneficiary','Approved draw result',
    '1. Prepare distribution.',
    'Beneficiary matches the approved draw_results member; enrollment active.', 'High')
add('Distribution','11.5.2','Verify available funds','Pool less than gross entitlement',
    '1. Attempt to pay a distribution exceeding available cash.',
    'Payment blocked; status remains approved until funds sufficient.', 'High')
add('Distribution','11.5.3','Calculate gross distribution','Scheme with round_value 2,000,000',
    '1. Read distributions.gross_amount.',
    'gross_amount = round_value (equal_rounds) or min(remaining_target, pool) (target_entitlement).', 'High')
add('Distribution','11.5.4','Calculate authorized deductions','2% admin fee configured',
    '1. Add an admin_fee deduction row.',
    'deductions = 40,000 for a 2,000,000 gross; each deduction row has an approver.', 'High')
add('Distribution','11.5.5','Calculate net distribution','Gross 2,000,000, deductions 40,000',
    '1. Read distributions.net_amount.',
    'net_amount = 1,960,000 (generated column: gross - deductions).', 'High')
add('Distribution','11.5.6','Approve payment','Prepared distribution',
    '1. General Manager approves.',
    'payment_status moves prepared -> pending_approval -> approved; approval_request closed.', 'High')
add('Distribution','11.5.7','Record payment','Approved distribution',
    '1. Cashier records payment (method, reference, account).',
    'payment_status = paid; cash_account debited; journal entry posted.', 'High')
add('Distribution','11.5.8','Confirm beneficiary receipt','Paid distribution',
    '1. Record beneficiary confirmation (signature/OTP).',
    'distribution_confirmations row created with evidence_url.', 'Medium')
add('Distribution','11.5.9','Prevent duplicate payment','A paid distribution',
    '1. Attempt to record a second payment with the same reference.',
    'Rejected by unique(association, method, reference); no double payment.', 'High','Security')
add('Distribution','11.5.10','Reconcile the financial ledger','After several distributions',
    '1. Run trial balance.\n2. Compare to v_journal_balance_check.',
    'Every posted journal entry has balance_difference = 0; trial balance nets to zero.', 'High','Audit')

# 11.6 Financial
add('Financial','11.6.1','Verify debit and credit equality','Posted journal entries',
    '1. Query v_journal_balance_check.',
    'balance_difference = 0 for every posted entry.', 'High','Audit')
add('Financial','11.6.2','Reconcile cash balances','Cash transactions posted',
    '1. Compare cash_accounts.current_balance to ledger Cash account.',
    'Cash account balance equals sum of posted cash journal lines.', 'High')
add('Financial','11.6.3','Reconcile bank balances','Bank transactions posted',
    '1. Run bank reconciliation.',
    'statement_balance vs ledger_balance difference explained; reconciliation closed.', 'Medium')
add('Financial','11.6.4','Verify income and expenditure','Admin fee income and expenses posted',
    '1. Generate income & expenditure statement.',
    'Income (admin fees) and expenses match posted journal lines; net shown.', 'Medium')
add('Financial','11.6.5','Verify outstanding contributions','Mixed paid/partial schedules',
    '1. Run outstanding contribution report.',
    'Sum of outstanding_amount matches member statement balances.', 'High')
add('Financial','11.6.6','Verify distribution liabilities','Approved-but-unpaid distributions',
    '1. Query Contributions Payable balance.',
    'Payable balance reflects collected minus distributed; distributions payable shown.', 'Medium')
add('Financial','11.6.7','Verify financial statements','Full cycle data',
    '1. Generate balance sheet, income statement, cash flow.',
    'Balance sheet balances: Assets = Liabilities + Equity.', 'High')
add('Financial','11.6.8','Confirm reversed transactions remain auditable','A reversed contribution',
    '1. Query audit_logs and journal_entries for the reversed txn.',
    'Original entry and reversing entry both present; is_reversed flag true; audit trail complete.', 'High','Audit')

# 11.7 Multi-Association
add('Multi-Assoc','11.7.1','Create multiple associations','Platform admin logged in',
    '1. Create associations A and B.',
    'Two association rows with distinct codes; each tenant isolated.', 'High')
add('Multi-Assoc','11.7.2','Register members under different associations','Associations A and B exist',
    '1. Register member in A and member in B.',
    'Members created in their respective tenants; no cross-tenant link.', 'High')
add('Multi-Assoc','11.7.3','Create schemes under different associations','Tenants A and B',
    '1. Create a scheme in A and a scheme in B.',
    'Schemes scoped to their association_id.', 'Medium')
add('Multi-Assoc','11.7.4','Record separate contributions','Members in A and B',
    '1. Record a contribution in A and one in B.',
    'Contributions land in the correct tenant; cash accounts per association.', 'Medium')
add('Multi-Assoc','11.7.5','Association A cannot access association B records','Session scoped to A',
    '1. As A, query members of B.',
    'RLS returns 0 rows; cross-tenant access denied.', 'High','Security')
add('Multi-Assoc','11.7.6','Reports are tenant-specific','Data in A and B',
    '1. Run a collections report as A.',
    'Report contains only A data; no B figures leak.', 'High')
add('Multi-Assoc','11.7.7','Platform admin cannot silently bypass financial controls','Platform admin session',
    '1. Attempt to post a distribution directly.',
    'Maker-checker and approval limits still enforced; platform admin cannot post without approval.', 'High','Security')

# 11.8 PWA
add('PWA','11.8.1','Install the application','Supported browser',
    '1. Visit app.\n2. Add to home screen.',
    'PWA installs; manifest + service worker registered.', 'Medium')
add('PWA','11.8.2','Open it on mobile','Installed PWA',
    '1. Launch from home screen.',
    'App opens standalone; responsive layout renders.', 'Medium')
add('PWA','11.8.3','Test offline display','Installed PWA',
    '1. Disable network.\n2. Open app.',
    'Cached shell renders; offline status indicator shown.', 'Medium')
add('PWA','11.8.4','Test reconnection','Offline queue with a permitted record',
    '1. Re-enable network.',
    'Queued records sync; online status restored.', 'Medium')
add('PWA','11.8.5','Verify queued records','A queued contribution',
    '1. Reconnect.\n2. Inspect server.',
    'Queued record validated server-side before posting; never treated as confirmed offline.', 'High','Security')
add('PWA','11.8.6','Prevent duplicate synchronization','Same queued record synced twice',
    '1. Trigger sync twice.',
    'Idempotency key prevents duplicate posting; only one contribution created.', 'High','Security')
add('PWA','11.8.7','Verify notification permissions','First launch',
    '1. Grant notification permission.',
    'Push permission requested once; notifications delivered on events.', 'Low')
add('PWA','11.8.8','Test responsive screen layouts','375px / 768px / 1280px viewports',
    '1. Resize across breakpoints.',
    'No horizontal overflow at 375px; tables scroll within containers; sidebar collapses.', 'Medium')

# 11.9 Definition of Done (13 items) — mapped as acceptance scenarios
dod = [
 'Register an association','Create branches','Create staff accounts','Register members',
 'Create an Ekub scheme','Define participation levels','Generate contribution schedules',
 'Collect and verify member payments','Generate receipts','Conduct a random draw or follow a predetermined rotation',
 'Approve the beneficiary','Distribute funds','Record the transaction in the accounting ledger',
 'Reconcile financial balances','Generate accurate reports','Allow members to view their own records',
 'Install and use the application as a PWA']
for i, item in enumerate(dod, 1):
    add('Acceptance', f'11.9.{i}', f'DoD: {item}', 'Working build with seed data',
        f'1. Execute the end-to-end flow: {item.lower()}.',
        f'The capability is operational and verified against the seed dataset.', 'High','Acceptance')

# ---------------------------------------------------------------- build workbook
wb = Workbook()
wb.properties.creator = 'Z.ai'
wb.properties.title = 'EAMS Test Cases'

# Sheet 1: Test Cases
ws = wb.active
ws.title = 'Test Cases'
headers = ['Test Case ID','Module','SRS Ref','Test Scenario','Pre-conditions',
           'Steps','Expected Result','Priority','Type']
ws.append(headers)
for col, w in zip('ABCDEFGHI', [14,14,9,30,24,34,40,9,11]):
    ws.column_dimensions[col].width = w
for c in range(1, len(headers)+1):
    cell = ws.cell(row=1, column=c)
    cell.font = HDR_FONT; cell.fill = HDR_FILL; cell.alignment = CENTER; cell.border = BORDER
for r_i, row in enumerate(T, start=2):
    for c_i, val in enumerate(row, start=1):
        cell = ws.cell(row=r_i, column=c_i, value=val)
        cell.font = CELL_FONT; cell.alignment = WRAP; cell.border = BORDER
        if r_i % 2 == 0:
            cell.fill = STRIPE_FILL
    ws.row_dimensions[r_i].height = 48
ws.freeze_panes = 'A2'
ws.auto_filter.ref = f'A1:I{len(T)+1}'

# Sheet 2: Summary
ws2 = wb.create_sheet('Summary')
ws2.column_dimensions['A'].width = 22
ws2.column_dimensions['B'].width = 14
ws2.column_dimensions['C'].width = 14
ws2.column_dimensions['D'].width = 14
ws2.column_dimensions['E'].width = 14
ws2['A1'] = 'EAMS Test Case Summary'
ws2['A1'].font = Font(name='Calibri', bold=True, size=14, color=NAVY)
ws2['A2'] = 'Mapped to SRS Part 11 acceptance criteria (11.1 - 11.9).'
ws2['A2'].font = Font(name='Calibri', size=10, color=MUTED, italic=True)
ws2.append([])
hdr2 = ['Module','Total','High','Medium','Low']
ws2.append(hdr2)
for c in range(1,6):
    cell = ws2.cell(row=ws2.max_row, column=c)
    cell.font = HDR_FONT; cell.fill = HDR_FILL; cell.alignment = CENTER; cell.border = BORDER
modules = ['Membership','Scheme','Contribution','Draw','Distribution','Financial','Multi-Assoc','PWA','Acceptance']
for m in modules:
    rows = [x for x in T if x[1]==m]
    hi = sum(1 for x in rows if x[7]=='High')
    md = sum(1 for x in rows if x[7]=='Medium')
    lo = sum(1 for x in rows if x[7]=='Low')
    ws2.append([m, len(rows), hi, md, lo])
    for c in range(1,6):
        ws2.cell(row=ws2.max_row, column=c).border = BORDER
        ws2.cell(row=ws2.max_row, column=c).alignment = CENTER if c>1 else Alignment(vertical='center')
        ws2.cell(row=ws2.max_row, column=c).font = CELL_FONT
# total row
ws2.append(['TOTAL', len(T), sum(1 for x in T if x[7]=='High'),
            sum(1 for x in T if x[7]=='Medium'), sum(1 for x in T if x[7]=='Low')])
for c in range(1,6):
    cell = ws2.cell(row=ws2.max_row, column=c)
    cell.font = Font(name='Calibri', bold=True, color=WHITE); cell.fill = PatternFill('solid', fgColor=TEAL)
    cell.alignment = CENTER; cell.border = BORDER

ws2.append([])
ws2.append(['By Type'])
ws2['A'+str(ws2.max_row)].font = Font(name='Calibri', bold=True, size=12, color=NAVY)
types = {}
for x in T: types[x[8]] = types.get(x[8],0)+1
for k in sorted(types):
    ws2.append([k, types[k]])
    ws2.cell(row=ws2.max_row, column=1).font = CELL_FONT
    ws2.cell(row=ws2.max_row, column=2).font = CELL_FONT
    ws2.cell(row=ws2.max_row, column=2).alignment = CENTER

wb.save(OUT)
print(f'Wrote {OUT} | {len(T)} test cases across {len(modules)} modules')
