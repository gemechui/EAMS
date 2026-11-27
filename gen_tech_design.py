#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
EAMS Technical Design PDF generator.
Output: /home/z/my-project/download/EAMS_Technical_Design.pdf
Uses ReportLab. Cover is a ReportLab-native typographic title page (a sensible
default chosen for this multi-deliverable package; the pdf skill prefers HTML
covers but a clean typographic cover is within ReportLab's safe capability).
Palette honors the SRS Part 7.1 mandate: deep navy / teal / emerald.
"""
import os, sys, hashlib
sys.path.insert(0, '/home/z/my-project/skills/pdf/scripts')

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm, inch, cm
from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT, TA_JUSTIFY
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer, PageBreak,
    Table, TableStyle, KeepTogether, CondPageBreak, HRFlowable, Image)
from reportlab.platypus.tableofcontents import TableOfContents
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase.pdfmetrics import registerFontFamily

# ---------------------------------------------------------------- fonts
FD = '/usr/share/fonts'
pdfmetrics.registerFont(TTFont('NotoSerifSC', f'{FD}/truetype/noto-serif-sc/NotoSerifSC-Regular.ttf'))
pdfmetrics.registerFont(TTFont('NotoSerifSC-Bold', f'{FD}/truetype/noto-serif-sc/NotoSerifSC-Bold.ttf'))
registerFontFamily('NotoSerifSC', normal='NotoSerifSC', bold='NotoSerifSC-Bold')
pdfmetrics.registerFont(TTFont('FreeSerif', f'{FD}/truetype/freefont/FreeSerif.ttf'))
pdfmetrics.registerFont(TTFont('FreeSerif-Bold', f'{FD}/truetype/freefont/FreeSerifBold.ttf'))
pdfmetrics.registerFont(TTFont('FreeSerif-Italic', f'{FD}/truetype/freefont/FreeSerifItalic.ttf'))
pdfmetrics.registerFont(TTFont('FreeSerif-BoldItalic', f'{FD}/truetype/freefont/FreeSerifBoldItalic.ttf'))
registerFontFamily('FreeSerif', normal='FreeSerif', bold='FreeSerif-Bold',
                   italic='FreeSerif-Italic', boldItalic='FreeSerif-BoldItalic')
try:
    from pdf import install_font_fallback
    install_font_fallback()
except Exception:
    pass

# ---------------------------------------------------------------- brand palette (SRS 7.1)
NAVY        = colors.HexColor('#0F2A43')   # primary deep navy
NAVY_LIGHT  = colors.HexColor('#1B3A57')
TEAL        = colors.HexColor('#1F7A8C')   # secondary teal
EMERALD     = colors.HexColor('#2F9E6B')   # accent emerald
BG          = colors.HexColor('#F4F6F8')   # light neutral grey
CARD        = colors.HexColor('#FFFFFF')
BORDER      = colors.HexColor('#CBD5E0')
TEXT        = colors.HexColor('#1A2230')
MUTED       = colors.HexColor('#6B7785')
AMBER       = colors.HexColor('#B7791F')
RED         = colors.HexColor('#B23B3B')
STRIPE      = colors.HexColor('#EEF2F6')

# ---------------------------------------------------------------- styles
BODY = ParagraphStyle('Body', fontName='FreeSerif', fontSize=10.5, leading=16,
                     alignment=TA_JUSTIFY, textColor=TEXT, spaceAfter=8)
BODYL = ParagraphStyle('BodyL', parent=BODY, alignment=TA_LEFT)
BULLET = ParagraphStyle('Bullet', parent=BODY, leftIndent=14, bulletIndent=2, spaceAfter=4, alignment=TA_LEFT)
H1 = ParagraphStyle('H1', fontName='FreeSerif-Bold', fontSize=18, leading=24,
                    textColor=NAVY, spaceBefore=18, spaceAfter=10)
H2 = ParagraphStyle('H2', fontName='FreeSerif-Bold', fontSize=13.5, leading=19,
                    textColor=NAVY_LIGHT, spaceBefore=12, spaceAfter=6)
H3 = ParagraphStyle('H3', fontName='FreeSerif-Bold', fontSize=11.5, leading=16,
                    textColor=TEAL, spaceBefore=8, spaceAfter=4)
CODE = ParagraphStyle('Code', fontName='DejaVuSans', fontSize=8.5, leading=12,
                      textColor=TEXT, backColor=STRIPE, leftIndent=8, rightIndent=8,
                      spaceBefore=4, spaceAfter=8)
NOTE = ParagraphStyle('Note', parent=BODY, fontName='FreeSerif-Italic', textColor=MUTED, fontSize=9.5)
CAP = ParagraphStyle('Cap', fontName='FreeSerif-Italic', fontSize=8.5, textColor=MUTED,
                     alignment=TA_CENTER, spaceBefore=2, spaceAfter=10)
TH = ParagraphStyle('TH', fontName='FreeSerif-Bold', fontSize=9.5, textColor=colors.white, alignment=TA_CENTER, leading=12)
TC = ParagraphStyle('TC', fontName='FreeSerif', fontSize=9.5, textColor=TEXT, alignment=TA_LEFT, leading=12)
TC_C = ParagraphStyle('TCc', parent=TC, alignment=TA_CENTER)
TC_R = ParagraphStyle('TCr', parent=TC, alignment=TA_RIGHT)
COVER_T = ParagraphStyle('CT', fontName='FreeSerif-Bold', fontSize=30, leading=36, textColor=NAVY, alignment=TA_LEFT)
COVER_S = ParagraphStyle('CS', fontName='FreeSerif', fontSize=15, leading=22, textColor=TEAL, alignment=TA_LEFT)
COVER_M = ParagraphStyle('CM', fontName='FreeSerif', fontSize=10.5, leading=16, textColor=MUTED, alignment=TA_LEFT)
TOC_L0 = ParagraphStyle('TL0', fontName='FreeSerif-Bold', fontSize=11, leading=18, leftIndent=4, textColor=NAVY)
TOC_L1 = ParagraphStyle('TL1', fontName='FreeSerif', fontSize=10, leading=16, leftIndent=22, textColor=TEXT)

pdfmetrics.registerFont(TTFont('DejaVuSans', f'{FD}/truetype/dejavu/DejaVuSansMono.ttf'))

OUT = '/home/z/my-project/download/EAMS_Technical_Design.pdf'
AVAIL = A4[0] - 2*0.85*inch

# ---------------------------------------------------------------- helpers
def H(text, style, level=0):
    key = 'h_' + hashlib.md5(text.encode()).hexdigest()[:8]
    p = Paragraph(f'<a name="{key}"/>{text}', style)
    p.bookmark_name = key; p.bookmark_level = level
    p.bookmark_text = text; p.bookmark_key = key
    return p

def para(t, s=BODY): return Paragraph(t, s)
def bullets(items):
    return [Paragraph(f'<bullet>•</bullet> {t}', BULLET) for t in items]

def tbl(data, col_ratios, header=True, caption=None):
    cw = [r*AVAIL for r in col_ratios]
    t = Table(data, colWidths=cw, hAlign='CENTER', repeatRows=1 if header else 0)
    sty = [
        ('GRID',(0,0),(-1,-1),0.5,BORDER),
        ('VALIGN',(0,0),(-1,-1),'MIDDLE'),
        ('LEFTPADDING',(0,0),(-1,-1),6),('RIGHTPADDING',(0,0),(-1,-1),6),
        ('TOPPADDING',(0,0),(-1,-1),5),('BOTTOMPADDING',(0,0),(-1,-1),5),
    ]
    if header:
        sty += [('BACKGROUND',(0,0),(-1,0),NAVY),('TEXTCOLOR',(0,0),(-1,0),colors.white)]
        for r in range(1,len(data)):
            if r%2==0: sty.append(('BACKGROUND',(0,r),(-1,r),STRIPE))
    t.setStyle(TableStyle(sty))
    out=[t]
    if caption: out += [Spacer(1,4), Paragraph(caption, CAP)]
    out += [Spacer(1,10)]
    return out

class TocDoc(SimpleDocTemplate):
    def afterFlowable(self, f):
        if hasattr(f,'bookmark_name'):
            self.notify('TOCEntry', (getattr(f,'bookmark_level',0),
                          getattr(f,'bookmark_text',''), self.page, getattr(f,'bookmark_key','')))

# ---------------------------------------------------------------- header/footer
def hf(canvas, doc):
    canvas.saveState()
    canvas.setStrokeColor(BORDER); canvas.setLineWidth(0.5)
    canvas.line(0.85*inch, A4[1]-0.55*inch, A4[0]-0.85*inch, A4[1]-0.55*inch)
    canvas.setFont('FreeSerif', 7.5); canvas.setFillColor(MUTED)
    canvas.drawString(0.85*inch, A4[1]-0.48*inch, 'EAMS — Technical Design Specification')
    canvas.drawRightString(A4[0]-0.85*inch, A4[1]-0.48*inch, 'Version 1.0')
    canvas.line(0.85*inch, 0.55*inch, A4[0]-0.85*inch, 0.55*inch)
    canvas.drawString(0.85*inch, 0.4*inch, 'Ekub & Association Management System')
    canvas.drawRightString(A4[0]-0.85*inch, 0.4*inch, f'Page {doc.page}')
    canvas.restoreState()

def cover_page(canvas, doc):
    canvas.saveState()
    # left navy band
    canvas.setFillColor(NAVY); canvas.rect(0, 0, 1.1*cm, A4[1], fill=1, stroke=0)
    canvas.setFillColor(TEAL); canvas.rect(1.1*cm, 0, 0.18*cm, A4[1], fill=1, stroke=0)
    # emerald accent block
    canvas.setFillColor(EMERALD); canvas.rect(2.6*cm, A4[1]-4.2*cm, 3.4*cm, 0.22*cm, fill=1, stroke=0)
    canvas.restoreState()

# ---------------------------------------------------------------- build story
story = []

# --- Cover (page 1, drawn via canvas + flowables)
story.append(Spacer(1, 5.2*cm))
story.append(Paragraph('Ekub & Association<br/>Management System', COVER_T))
story.append(Spacer(1, 0.4*cm))
story.append(Paragraph('Technical Design Specification', COVER_S))
story.append(Spacer(1, 0.3*cm))
story.append(HRFlowable(width=6*cm, color=EMERALD, thickness=2, spaceBefore=0, spaceAfter=10))
story.append(Paragraph('Multi-association financial & membership platform', COVER_M))
story.append(Paragraph('Pre-implementation design package — distribution model, database '
                      'design, financial engine, draw engine, and approval workflows.', COVER_M))
story.append(Spacer(1, 6.5*cm))
story.append(Paragraph('Document Version 1.0', COVER_M))
story.append(Paragraph('Initial Market: Ethiopia  |  Currency: ETB', COVER_M))
story.append(Paragraph('Companion files: eams_database_schema.sql, eams_seed_data.sql, '
                      'eams_api_spec.yaml, EAMS_UI_Wireframes.pdf, EAMS_Test_Cases.xlsx, '
                      'EAMS_Deployment_Guide.pdf', COVER_M))
story.append(PageBreak())

# --- TOC
story.append(Paragraph('Table of Contents', H1))
toc = TableOfContents()
toc.levelStyles = [TOC_L0, TOC_L1]
story.append(toc)
story.append(PageBreak())

# --- 1. Executive Summary
story.append(H('1. Executive Summary', H1, 0))
story.append(para('This document is the pre-implementation technical design for the Ekub & '
 'Association Management System (EAMS) defined by the accompanying Software Requirements '
 'Specification. It translates the SRS into a concrete, buildable blueprint: a resolved '
 'distribution model, a complete PostgreSQL schema, a double-entry financial engine, an '
 'auditable draw engine, and the approval workflows that bind them together. The companion '
 'SQL schema, seed dataset, and OpenAPI specification referenced throughout this document '
 'are delivered alongside it as ready-to-run artifacts.'))
story.append(para('The SRS explicitly identifies the single most important design issue to '
 'resolve before any financial code is written: how members with different participation '
 'levels (Full, Half, Quarter, Custom) receive their distributions. This document resolves '
 'that question in Section 3 with a configurable three-mode distribution engine, and the '
 'resolution is encoded directly in the database schema (the <font name="DejaVuSans">'
 'distribution_mode</font> column on <font name="DejaVuSans">ekub_schemes</font>) and '
 'verified arithmetically in the seed dataset. Every other design decision in this document '
 'flows from that resolution.'))
story.append(para('The architecture is intentionally conservative on the points that matter '
 'most for a financial product: tenant isolation is enforced at the database tier with '
 'PostgreSQL Row-Level Security rather than only in application code; every monetary value '
 'is stored and computed as <font name="DejaVuSans">NUMERIC(18,2)</font>, never as binary '
 'floating point; every financial posting produces balanced double-entry journal lines; and '
 'no posted transaction is ever deleted — corrections are made by reversal, which itself '
 'produces balancing journal entries and an audit record. The platform super administrator '
 'cannot silently bypass association financial controls; RLS and the maker-checker matrix '
 'apply uniformly.'))

# --- 2. System Architecture
story.append(H('2. System Architecture', H1, 0))
story.append(para('EAMS is a tenant-aware, API-driven system. A single PostgreSQL database '
 'holds all associations, isolated by Row-Level Security. The backend (Django REST '
 'Framework in the recommended stack) exposes the OpenAPI specification delivered with this '
 'package; the frontend (Next.js / React with Tailwind) and an installable PWA consume it. '
 'Background workers (Celery + Redis) handle receipts, notifications, scheduled-contribution '
 'generation, and asynchronous report generation. File storage is private object storage; '
 'PDF and Excel reports are generated server-side.'))
story.append(H('2.1 Tenancy Model', H2, 1))
story.append(para('Every association-owned table carries an <font name="DejaVuSans">'
 'association_id</font> foreign key, either directly or through an enforced parent. '
 'On each authenticated request the backend sets two session GUCs before any query: '
 '<font name="DejaVuSans">app.current_association_id</font> and '
 '<font name="DejaVuSans">app.current_user_id</font>. RLS policies compare each row&apos;s '
 '<font name="DejaVuSans">association_id</font> against the '
 '<font name="DejaVuSans">current_association_id()</font> helper and silently filter out '
 'every row that does not match. The platform administrator sets '
 '<font name="DejaVuSans">app.is_platform_admin</font> to bypass tenant scoping for '
 'cross-association administration, but the financial-control policies '
 '(maker-checker, approval limits, reversal-not-deletion) still apply.'))
story.append(para('Six tables are marked <font name="DejaVuSans">FORCE ROW LEVEL SECURITY</font>, '
 'which means even the table owner is subject to the policies — this guarantees that a '
 'misconfigured application connection can never read another tenant&apos;s members, '
 'contributions, distributions, journal entries, receipts, expenses, or draw results.'))
story.append(H('2.2 Component Map', H2, 1))
story += tbl([
    [Paragraph('Layer', TH), Paragraph('Technology', TH), Paragraph('Responsibility', TH)],
    [para('Frontend', TC), para('Next.js / React + Tailwind', TC), para('28 screens, PWA shell, offline queue', TC)],
    [para('API', TC), para('Django REST Framework', TC), para('58 endpoints (see eams_api_spec.yaml)', TC)],
    [para('Database', TC), para('PostgreSQL 15+', TC), para('38+ tables, RLS, audit triggers, double-entry ledger', TC)],
    [para('Async', TC), para('Celery + Redis', TC), para('Schedules, receipts, notifications, reports', TC)],
    [para('Storage', TC), para('Private object storage', TC), para('Documents, legal files, evidence', TC)],
    [para('Integrations', TC), para('Telebirr / CBE Birr / M-Pesa / SMS / Email', TC), para('Payment + communication gateways', TC)],
], [0.16, 0.34, 0.50], caption='Table 1. Recommended technology stack per architectural layer.')

# --- 3. Resolved Distribution Model  (THE critical section)
story.append(H('3. Resolved Distribution Model', H1, 0))
story.append(para('The SRS flags the distribution model for differing participation levels as '
 'the most important issue to resolve before implementing the financial engine. The '
 'difficulty is structural: in a target-based Ekub, members participate at different levels '
 '(Full, Half, Quarter, Custom), so a single “one winner takes the whole pool” '
 'rule cannot fairly satisfy everyone. A Quarter participant whose target is ETB 2.5 '
 'million would never reach it if each round pays the entire multi-member pool, and a Full '
 'participant would be over-paid relative to their contribution share. The model below '
 'resolves this by separating the <b>distribution entitlement</b> (what a member is owed) '
 'from the <b>collection pool</b> (what has been collected) and letting each scheme choose '
 'how the two relate.'))
story.append(H('3.1 The Three Distribution Modes', H2, 1))
story.append(para('Each scheme selects one of three modes via '
 '<font name="DejaVuSans">ekub_schemes.distribution_mode</font>. The draw and distribution '
 'engines branch on this value; the eligibility view '
 '<font name="DejaVuSans">v_member_entitlement_balance</font> is consulted in every case to '
 'prevent over-distribution.'))
story += tbl([
    [Paragraph('Mode', TH), Paragraph('Round payout', TH), Paragraph('Best for', TH), Paragraph('Repeat winner in cycle', TH)],
    [para('traditional_pool', TC), para('Full collected pool to one winner', TC), para('Classic rotating Ekub, equal members', TC), para('No (each wins once)', TC_C)],
    [para('equal_rounds', TC), para('Fixed round_value per round', TC), para('Mixed Full/Half/Quarter targets', TC), para('Yes, until target met', TC_C)],
    [para('target_entitlement', TC), para('min(remaining_target, available pool)', TC), para('Variable pool / irregular collections', TC), para('Yes, until target met', TC_C)],
], [0.20, 0.30, 0.30, 0.20], caption='Table 2. The three distribution modes selectable per scheme.')

story.append(H('3.2 The Equal-Rounds Model (Recommended Default)', H2, 1))
story.append(para('The recommended default for mixed-participation schemes is <b>equal_rounds</b>. '
 'It defines a single <font name="DejaVuSans">round_value</font> — typically the smallest '
 'member target — and pays that amount to the winner of each round. A member whose target '
 'is an exact multiple of <font name="DejaVuSans">round_value</font> wins exactly enough '
 'rounds to be satisfied, then is excluded from future rounds by the eligibility view. The '
 'total amount distributed across the cycle always equals the sum of all member targets, '
 'and the total collected across the cycle equals the same figure, so the books balance by '
 'construction.'))
story.append(para('Worked example. Four members enroll in a target-based scheme: two Full '
 'members (target ETB 4,000,000 each, contributing ETB 400,000 per period) and two Half '
 'members (target ETB 2,000,000 each, contributing ETB 200,000 per period). '
 '<font name="DejaVuSans">round_value</font> is set to ETB 2,000,000, the smallest target. '
 'The pool per period is ETB 1,200,000. Over ten collection periods the scheme collects '
 'ETB 12,000,000, and over six distribution rounds it pays out ETB 12,000,000. Each Full '
 'member wins two rounds (2 × 2,000,000 = 4,000,000, target met); '
 'each Half member wins one round (target met). No member is over- or under-paid.'))
story += tbl([
    [Paragraph('Member', TH), Paragraph('Level', TH), Paragraph('Target (ETB)', TH), Paragraph('Rounds to satisfy', TH), Paragraph('Total received (ETB)', TH)],
    [para('M1', TC_C), para('Full', TC_C), para('4,000,000', TC_R), para('2', TC_C), para('4,000,000', TC_R)],
    [para('M2', TC_C), para('Full', TC_C), para('4,000,000', TC_R), para('2', TC_C), para('4,000,000', TC_R)],
    [para('M3', TC_C), para('Half', TC_C), para('2,000,000', TC_R), para('1', TC_C), para('2,000,000', TC_R)],
    [para('M4', TC_C), para('Half', TC_C), para('2,000,000', TC_R), para('1', TC_C), para('2,000,000', TC_R)],
    [Paragraph('<b>Total</b>', TC_C), Paragraph('', TC), Paragraph('<b>12,000,000</b>', TC_R), Paragraph('<b>6</b>', TC_C), Paragraph('<b>12,000,000</b>', TC_R)],
], [0.14, 0.16, 0.24, 0.22, 0.24], caption='Table 3. Equal-rounds distribution for the 4-member example.')
story.append(para('The seed dataset (eams_seed_data.sql) records exactly this scenario through '
 'two collection periods and one distribution round, then posts the balanced double-entry '
 'journal entries that prove the arithmetic. The verification query at the end of the seed '
 'file returns <font name="DejaVuSans">balance_difference = 0</font> for every posted entry.'))

story.append(H('3.3 Eligibility and the Entitlement Balance View', H2, 1))
story.append(para('Fairness depends on never distributing to a member whose target is already '
 'met. The database exposes this as a view rather than leaving it to application logic, so '
 'that every consumer (the draw engine, the distribution engine, the UI) reads the same '
 'authoritative remaining-target figure:'))
story.append(Paragraph("SELECT member_id, target_allocation, distributed_to_date, "
                       "remaining_target, target_satisfied<br/>FROM v_member_entitlement_balance "
                       "WHERE scheme_id = :sid AND enrollment_status = 'active';", CODE))
story.append(para('The draw engine&apos;s eligible snapshot is built from this view: any member '
 'with <font name="DejaVuSans">target_satisfied = true</font> is excluded, and the snapshot '
 'is frozen immutably into <font name="DejaVuSans">draw_sessions.eligibility_snapshot</font> '
 'at draw-preparation time so the set of people who could have won is preserved for audit '
 'even if enrollments change later.'))

story.append(H('3.4 Deductions and Net Distribution', H2, 1))
story.append(para('A distribution is split into gross, deductions, and net. '
 '<font name="DejaVuSans">net_amount</font> is a generated stored column '
 '(<font name="DejaVuSans">gross_amount - deductions</font>), so it can never '
 'disagree with its components. Deductions are recorded as separate rows in '
 '<font name="DejaVuSans">distribution_deductions</font>, each requiring its own approver, '
 'and no deduction may be made without a configured rule. Crucially, the member&apos;s '
 '<b>target</b> is reduced by the <b>gross</b> distribution (what they are owed), not the net '
 '(what they receive after fees) — the admin fee is association income, not a reduction of '
 'the member&apos;s entitlement. In the seed example, the Half winner is owed ETB 2,000,000 '
 '(gross), pays a 2% admin fee of ETB 40,000, and receives ETB 1,960,000 net; their target '
 'is fully satisfied.'))

# --- 4. Database Design
story.append(H('4. Database Design', H1, 0))
story.append(para('The schema (eams_database_schema.sql) defines 38 core tables grouped '
 'into eight domains: platform & organization, members, schemes, contributions, draws, '
 'distributions, financial accounting, and management & control. UUID primary keys are '
 'used throughout; monetary columns are <font name="DejaVuSans">NUMERIC(18,2)</font>; '
 'timestamps are <font name="DejaVuSans">TIMESTAMPTZ</font> stored in UTC and displayed in '
 'the association&apos;s configured time zone. Transaction and receipt numbers are unique '
 'within their association, enforced by composite unique constraints.'))
story.append(H('4.1 Key Integrity Controls', H2, 1))
story += bullets([
 '<b>Double-entry balance guard.</b> The <font name="DejaVuSans">v_journal_balance_check</font> '
 'view sums debit and credit per posted journal entry; the application rejects any posting '
 'whose balance difference is non-zero, and a nightly job flags any historical drift.',
 '<b>Per-line debit-or-credit constraint.</b> A <font name="DejaVuSans">CHECK</font> on '
 '<font name="DejaVuSans">journal_lines</font> forbids a line carrying both a debit and a '
 'credit, and forbids negative amounts.',
 '<b>Generated outstanding and net columns.</b> '
 '<font name="DejaVuSans">contribution_schedules.outstanding_amount</font> and '
 '<font name="DejaVuSans">distributions.net_amount</font> are '
 '<font name="DejaVuSans">GENERATED ALWAYS</font> stored columns, so they can never drift '
 'from their inputs.',
 '<b>Duplicate-payment prevention.</b> '
 '<font name="DejaVuSans">contributions</font> carries a composite unique constraint on '
 '(association, payment_method, payment_reference) so a digital reference cannot be recorded '
 'twice; distributions carries the same on its own payment reference.',
 '<b>Soft deactivation, never hard delete.</b> Master records use status fields; posted '
 'accounting transactions are never deleted. Reversals create a new '
 '<font name="DejaVuSans">payment_reversals</font> row and a reversing journal entry, '
 'preserving the original.',
 '<b>Immutable audit trail.</b> A generic <font name="DejaVuSans">fn_audit_log()</font> '
 'trigger attached to 30 financially-sensitive tables writes a JSONB diff of old and '
 'new values to <font name="DejaVuSans">audit_logs</font> on every insert, update, and '
 'delete, tagged with the acting user and client IP.',
])
story.append(H('4.2 Tenant Isolation via Row-Level Security', H2, 1))
story.append(para('RLS is enabled on every association-owned table and forced on the six most '
 'sensitive ones. The policy template is uniform: a row is visible/writable only if its '
 '<font name="DejaVuSans">association_id</font> equals the session&apos;s '
 '<font name="DejaVuSans">current_association_id()</font>, or the session is a platform '
 'administrator. Child tables without a direct association column '
 '(<font name="DejaVuSans">journal_lines</font>, <font name="DejaVuSans">role_permissions</font>) '
 'inherit isolation through an <font name="DejaVuSans">EXISTS</font> join to their parent. '
 'This means a bug in the API layer cannot leak tenant data — the database refuses the row.'))
story.append(H('4.3 Module-to-Table Map', H2, 1))
story += tbl([
    [Paragraph('Module', TH), Paragraph('Primary tables', TH)],
    [para('Association', TC), para('associations, branches, users, roles, role_permissions, user_roles, approval_limits', TC)],
    [para('Members', TC), para('members, member_documents, member_contacts', TC)],
    [para('Schemes', TC), para('ekub_schemes, participation_plans, scheme_enrollments, scheme_rules, rotation_positions', TC)],
    [para('Contributions', TC), para('contribution_schedules, contributions, payment_allocations, payment_reversals, receipts', TC)],
    [para('Draws', TC), para('draw_sessions, draw_participants, draw_results', TC)],
    [para('Distributions', TC), para('distributions, distribution_deductions, distribution_confirmations', TC)],
    [para('Accounting', TC), para('chart_of_accounts, journal_entries, journal_lines, cash_accounts, bank_accounts, expenses, bank_reconciliations', TC)],
    [para('Control', TC), para('approval_requests, audit_logs, notifications, legal_documents, disputes, system_settings', TC)],
], [0.22, 0.78], caption='Table 4. SRS modules mapped to their backing database tables.')

# --- 5. Financial Calculation Rules
story.append(H('5. Financial Calculation Rules', H1, 0))
story.append(para('All monetary arithmetic is performed in <font name="DejaVuSans">NUMERIC</font> '
 '(decimal) at the database and application tiers, and in Python '
 '<font name="DejaVuSans">Decimal</font> for any derived reporting figures. Binary '
 'floating-point is never used for money. The nine financial quantities named in SRS '
 '§4.1 are kept strictly separate and never aliased:'))
story += tbl([
    [Paragraph('Quantity', TH), Paragraph('Source', TH), Paragraph('How it is derived', TH)],
    [para('Member target allocation', TC), para('scheme_enrollments.agreed_target', TC), para('Set at enrollment from the participation plan', TC)],
    [para('Member periodic contribution', TC), para('participation_plans.contribution_amount', TC), para('plan units x scheme contribution unit (or fixed)', TC)],
    [para('Scheme collection pool', TC), para('sum(contributions.amount) verified', TC), para('Only verified contributions, allocated to the period', TC)],
    [para('Gross distribution', TC), para('distributions.gross_amount', TC), para('Scheme-defined entitlement (round_value or remaining target)', TC)],
    [para('Authorized deductions', TC), para('sum(distribution_deductions.amount)', TC), para('Each row requires an approver and a configured rule', TC)],
    [para('Net distribution', TC), para('distributions.net_amount', TC), para('GENERATED: gross - deductions', TC)],
    [para('Outstanding contribution', TC), para('contribution_schedules.outstanding_amount', TC), para('GENERATED: expected - paid', TC)],
    [para('Available scheme balance', TC), para('cash_accounts + bank_accounts', TC), para('Posted ledger balances minus distributions payable', TC)],
], [0.26, 0.30, 0.44], caption='Table 5. The nine financial quantities and their derivation.')
story.append(H('5.1 Double-Entry Posting', H2, 1))
story.append(para('Every financial event creates a journal entry with two or more balanced '
 'lines. A contribution receipt debits Cash and credits Contributions Payable (a liability '
 'held for distribution). A distribution debits Contributions Payable and credits Cash, with '
 'any admin-fee deduction credited to Administrative Fee Income. A reversal creates the '
 'mirror image of the original entry. The seed dataset contains four journal entries '
 '(two per Ekub model) whose trial balance nets to exactly zero and whose balance sheet '
 'balances: Assets ETB 440,000 = Liabilities ETB 400,000 + Income ETB 40,000.'))

# --- 6. Draw Engine
story.append(H('6. Draw Engine', H1, 0))
story.append(para('Two independent selection engines are implemented, selectable per scheme '
 'via <font name="DejaVuSans">distribution_method</font>. Both consult the same eligibility '
 'view and both write immutable evidence to the draw tables, so the audit story is identical '
 'regardless of method.'))
story.append(H('6.1 Random Draw (Auditable)', H2, 1))
story += bullets([
 '<b>Eligible snapshot.</b> At preparation, the engine snapshots the eligible member set '
 '(active enrollment, contribution-compliant, not defaulted, not previously satisfied in '
 'this cycle) into <font name="DejaVuSans">draw_sessions.eligibility_snapshot</font> as JSONB.',
 '<b>Seed commitment.</b> Before execution, the engine publishes a SHA-256 commitment of the '
 'random seed (<font name="DejaVuSans">seed_commitment</font>); after the winner is selected, '
 'the seed itself can be revealed and verified against the commitment, proving the result '
 'was not altered after the commitment was recorded.',
 '<b>Algorithm version.</b> <font name="DejaVuSans">algorithm_version</font> records which '
 'selection routine produced the result, so a future algorithm change cannot retroactively '
 're-classify old draws.',
 '<b>Immutable result.</b> <font name="DejaVuSans">draw_results.result_status</font> can be '
 'marked <font name="DejaVuSans">nullified</font> only through a documented cancellation '
 'and re-draw procedure approved by authorized officials; the original row is never deleted.',
])
story.append(H('6.2 Predetermined Rotation', H2, 1))
story.append(para('For rotation schemes, <font name="DejaVuSans">rotation_positions</font> '
 'stores the agreed sequence with unique constraints on both sequence number and member, so '
 'a member cannot appear twice and two members cannot occupy the same slot. Sequence changes '
 'require an approver and are themselves audited. The draw engine simply identifies the next '
 'pending position rather than performing a random selection, then proceeds through the same '
 'approval and distribution path as the random engine.'))

# --- 7. Approval Workflows
story.append(H('7. Approval Workflows (Maker-Checker)', H1, 0))
story.append(para('Sensitive operations are gated by a maker-checker matrix. '
 '<font name="DejaVuSans">approval_requests</font> records each pending decision with its '
 'transaction type, submitter, assigned approver, and status (pending, approved, rejected, '
 'returned, escalated). <font name="DejaVuSans">approval_limits</font> binds each role to a '
 'maximum amount per transaction type; if a distribution or expense exceeds the approver&apos;s '
 'limit, the workflow escalates to a committee rather than failing. A cashier cannot approve '
 'their own transactions, cannot delete posted payments, cannot modify approved distribution '
 'amounts, and cannot alter completed draw results — these are enforced both in the API and '
 'by database constraints.'))
story += tbl([
    [Paragraph('Operation', TH), Paragraph('Maker', TH), Paragraph('Checker', TH), Paragraph('Escalation', TH)],
    [para('Distribution payment', TC), para('Cashier', TC_C), para('Assistant → General Manager', TC_C), para('Committee above limit', TC)],
    [para('Payment reversal', TC), para('Cashier', TC_C), para('Assistant Manager', TC_C), para('General Manager above limit', TC)],
    [para('Expense approval', TC), para('Submitter', TC_C), para('General Manager', TC_C), para('Committee above limit', TC)],
    [para('Scheme approval', TC), para('Assistant Manager', TC_C), para('General Manager', TC_C), para('n/a', TC_C)],
    [para('Draw approval', TC), para('Assistant Manager', TC_C), para('General Manager', TC_C), para('n/a', TC_C)],
], [0.24, 0.18, 0.30, 0.28], caption='Table 6. Maker-checker matrix for the five gated operations.')

# --- 8. Roadmap Alignment
story.append(H('8. Implementation Roadmap Alignment', H1, 0))
story.append(para('This design package maps onto the SRS 17-week roadmap as the deliverables '
 'for Phase 2 (UI/UX and database architecture) and the input for Phase 3 onward. '
 'The schema is ready to load and migrate; the API specification is ready for code '
 'generation or hand-off; the seed data is ready for the demonstration environment; the '
 'wireframes are ready for UI implementation. The remaining business-policy questions in '
 'SRS Part 14 (whether members continue contributing after receiving their allocation, '
 'how defaults are handled, whether a member may join multiple schemes) are all expressible '
 'as <font name="DejaVuSans">scheme_rules</font> rows and do not require schema changes — '
 'they are configuration, not architecture.'))
story.append(para('Before any code is written against this design, the association must '
 'formally approve the choice of distribution mode per scheme type, confirm the '
 'round_value or target-entitlement rule for each, and ratify the approval-limit matrix. '
 'These are the fundamental business rules named in SRS Part 14, and the platform should '
 'undergo legal and regulatory review in Ethiopia before handling funds commercially.'))

# ---------------------------------------------------------------- build
doc = TocDoc(OUT, pagesize=A4, leftMargin=0.85*inch, rightMargin=0.85*inch,
             topMargin=0.8*inch, bottomMargin=0.8*inch,
             title='EAMS Technical Design Specification', author='Z.ai',
             creator='Z.ai', subject='Ekub & Association Management System — Technical Design')
doc.multiBuild(story, onFirstPage=cover_page, onLaterPages=hf)
print('Wrote', OUT)
