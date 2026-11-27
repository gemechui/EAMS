#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
EAMS UI Wireframes PDF — all 28 screens from SRS Part 7.
Output: /home/z/my-project/download/EAMS_UI_Wireframes.pdf
Each screen = one A4 portrait page with a labeled wireframe (chrome + content
zones) and a field/function list. Palette honors SRS 7.1 (navy/teal/emerald).
"""
import os, sys
sys.path.insert(0, '/home/z/my-project/skills/pdf/scripts')
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm, cm
from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT, TA_CENTER
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer, PageBreak,
    Table, TableStyle, KeepTogether)
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase.pdfmetrics import registerFontFamily
from reportlab.pdfgen import canvas as canvasmod

FD = '/usr/share/fonts'
pdfmetrics.registerFont(TTFont('FreeSerif', f'{FD}/truetype/freefont/FreeSerif.ttf'))
pdfmetrics.registerFont(TTFont('FreeSerif-Bold', f'{FD}/truetype/freefont/FreeSerifBold.ttf'))
pdfmetrics.registerFont(TTFont('DejaVuSans', f'{FD}/truetype/dejavu/DejaVuSansMono.ttf'))
registerFontFamily('FreeSerif', normal='FreeSerif', bold='FreeSerif-Bold')

NAVY = colors.HexColor('#0F2A43'); NAVY_L = colors.HexColor('#1B3A57')
TEAL = colors.HexColor('#1F7A8C'); EMERALD = colors.HexColor('#2F9E6B')
BG = colors.HexColor('#F4F6F8'); CARD = colors.HexColor('#FFFFFF')
BORDER = colors.HexColor('#CBD5E0'); TEXT = colors.HexColor('#1A2230')
MUTED = colors.HexColor('#6B7785'); STRIPE = colors.HexColor('#EEF2F6')
FIELD = colors.HexColor('#E8EDF2'); PLACE = colors.HexColor('#D7DEE6')

OUT = '/home/z/my-project/download/EAMS_UI_Wireframes.pdf'
PW, PH = A4
M = 1.4*cm

ST_LBL = ParagraphStyle('l', fontName='FreeSerif', fontSize=7, textColor=TEXT, leading=9, alignment=TA_CENTER)

class WF:
    def __init__(self, c, x, y, w, h):
        self.c = c; self.x = x; self.y = y; self.w = w; self.h = h
    def box(self, x, y, w, h, fill=CARD, border=BORDER, lw=0.6, radius=2):
        self.c.setFillColor(fill); self.c.setStrokeColor(border); self.c.setLineWidth(lw)
        self.c.roundRect(self.x+x, self.y+y, w, h, radius, fill=1, stroke=1)
    def placeholder(self, x, y, w, h, text='placeholder'):
        self.box(x, y, w, h, fill=PLACE, border=BORDER)
        self.c.setFillColor(MUTED); self.c.setFont('FreeSerif', 7)
        self.c.drawCentredString(self.x+x+w/2, self.y+y+h/2-3, text)
    def field(self, x, y, w, label):
        self.box(x, y, w, 11, fill=FIELD, border=BORDER)
        self.c.setFillColor(MUTED); self.c.setFont('FreeSerif', 6.5)
        self.c.drawString(self.x+x+2, self.y+y+11+1.5, label)
    def row(self, x, y, w, cols):
        cw = (w-2)/len(cols)
        for i, txt in enumerate(cols):
            self.box(x+i*cw, y, cw, 9, fill=STRIPE if i==0 else CARD)
            self.c.setFillColor(TEXT); self.c.setFont('FreeSerif', 6.5)
            self.c.drawString(self.x+x+i*cw+2, self.y+y+3, txt[:18])
    def btn(self, x, y, w, text, fill=TEAL):
        self.box(x, y, w, 9, fill=fill, border=fill)
        self.c.setFillColor(colors.white); self.c.setFont('FreeSerif-Bold', 6.5)
        self.c.drawCentredString(self.x+x+w/2, self.y+y+3, text)

NAV_ITEMS = ['Dashboard','Associations','Members','Schemes','Contributions',
             'Draws','Distributions','Cash & Bank','Reports','Approvals','Settings']

def draw_chrome(wf, content_h, title='Association Dashboard'):
    wf.box(0, 0, 30, content_h+58, fill=NAVY, border=NAVY)
    wf.c.setFillColor(colors.white); wf.c.setFont('FreeSerif-Bold', 8)
    wf.c.drawString(wf.x+4, wf.y+content_h+50, 'EAMS')
    wf.c.setFont('FreeSerif', 6.5)
    ny = content_h+38
    for it in NAV_ITEMS:
        wf.c.setFillColor(colors.HexColor('#9FB3C8'))
        wf.c.drawString(wf.x+4, ny, it); ny -= 9
    wf.box(30, content_h+22, wf.w-30, 36, fill=CARD, border=BORDER)
    wf.c.setFillColor(NAVY); wf.c.setFont('FreeSerif-Bold', 8)
    wf.c.drawString(wf.x+34, wf.y+content_h+48, title)
    wf.placeholder(34+wf.w*0.30, content_h+30, 90, 12, 'search')
    wf.btn(wf.w-22, content_h+30, 18, 'Profile', fill=NAVY_L)
    wf.btn(wf.w-44, content_h+30, 18, 'Notif', fill=EMERALD)
    wf.c.setFillColor(MUTED); wf.c.setFont('FreeSerif', 6)
    wf.c.drawString(wf.x+34, wf.y+content_h+26, 'Home / '+title)

def kpi_row(wf, x, y, w, items):
    n=len(items); gap=3; cw=(w-gap*(n-1))/n
    for i,(lbl,val) in enumerate(items):
        bx=x+i*(cw+gap)
        wf.box(bx, y, cw, 26, fill=CARD, border=BORDER)
        wf.c.setFillColor(NAVY); wf.c.setFont('FreeSerif-Bold', 9)
        wf.c.drawString(wf.x+bx+4, wf.y+y+16, val)
        wf.c.setFillColor(MUTED); wf.c.setFont('FreeSerif', 6.5)
        wf.c.drawString(wf.x+bx+4, wf.y+y+6, lbl)

def r_dashboard(wf, ch, title, kpis, table_cols, table_rows=4):
    draw_chrome(wf, ch, title)
    cx=34; cw=wf.w-34
    kpi_row(wf, cx, ch-4, cw, kpis)
    wf.box(cx, ch-4-30, cw*0.48, 26, fill=CARD, border=BORDER)
    wf.placeholder(cx+2, ch-4-28, cw*0.48-4, 22, 'collection trend chart')
    wf.box(cx+cw*0.50, ch-4-30, cw*0.50, 26, fill=CARD, border=BORDER)
    wf.placeholder(cx+cw*0.50+2, ch-4-28, cw*0.50-4, 22, 'scheme performance')
    ty=ch-4-30-6
    wf.box(cx, ty-3-9*(table_rows+1), cw, 9*(table_rows+1)+6, fill=CARD, border=BORDER)
    wf.row(cx+2, ty-3, cw-4, table_cols)
    for i in range(table_rows):
        wf.row(cx+2, ty-3-9*(i+1)-2, cw-4, [c[:18] for c in table_cols])

def r_list(wf, ch, title, cols, filters, rows=5):
    draw_chrome(wf, ch, title)
    cx=34; cw=wf.w-34
    fx=cx; fy=ch-4
    for i,f in enumerate(filters):
        wf.field(fx, fy-11, 60, f); fx+=64
    wf.btn(fx, fy-11, 30, 'Search', fill=TEAL)
    wf.btn(fx+34, fy-11, 30, 'Export', fill=EMERALD)
    ty=fy-22; th=9*(rows+1)+6
    wf.box(cx, ty-th, cw, th, fill=CARD, border=BORDER)
    wf.row(cx+2, ty-3, cw-4, cols)
    for i in range(rows):
        wf.row(cx+2, ty-3-9*(i+1)-2, cw-4, [c[:18] for c in cols])
    wf.btn(cx, ty-th-12, 40, '+ New', fill=EMERALD)

def r_form(wf, ch, title, sections):
    draw_chrome(wf, ch, title)
    cx=34; cw=wf.w-34
    y=ch-4
    for sec, flds in sections:
        wf.box(cx, y-14, cw, 14, fill=STRIPE, border=BORDER)
        wf.c.setFillColor(NAVY_L); wf.c.setFont('FreeSerif-Bold', 7.5)
        wf.c.drawString(wf.x+cx+3, wf.y+y-9, sec)
        y -= 18
        colw=(cw-6)/2
        for i in range(0, len(flds), 2):
            wf.field(cx, y-11, colw, flds[i])
            if i+1 < len(flds): wf.field(cx+colw+6, y-11, colw, flds[i+1])
            y -= 16
        y -= 4
    wf.btn(cx, y-12, 34, 'Save', fill=EMERALD)
    wf.btn(cx+38, y-12, 40, 'Submit', fill=TEAL)

def r_wizard(wf, ch, title, steps, current):
    draw_chrome(wf, ch, title)
    cx=34; cw=wf.w-34
    sw=cw/len(steps)
    for i,s in enumerate(steps):
        fill = TEAL if i==current else STRIPE
        wf.box(cx+i*sw, ch-4-10, sw-2, 10, fill=fill, border=BORDER)
        wf.c.setFillColor(colors.white if i==current else MUTED); wf.c.setFont('FreeSerif-Bold', 6.5)
        wf.c.drawCentredString(wf.x+cx+i*sw+(sw-2)/2, wf.y+ch-4-7, f'{i+1}. {s}')
    wf.box(cx, ch-4-10-6, cw, 60, fill=CARD, border=BORDER)
    wf.placeholder(cx+3, ch-4-10-4, cw-6, 56, 'wizard step content (fields / selections)')
    wf.btn(cx, ch-4-10-6-12, 34, 'Back', fill=NAVY_L)
    wf.btn(cx+38, ch-4-10-6-12, 34, 'Next', fill=EMERALD)

def r_tabs(wf, ch, title, tabs, active=0):
    draw_chrome(wf, ch, title)
    cx=34; cw=wf.w-34
    tw=cw/len(tabs)
    for i,t in enumerate(tabs):
        wf.box(cx+i*tw, ch-4-9, tw-2, 9, fill=(TEAL if i==active else STRIPE), border=BORDER)
        wf.c.setFillColor(colors.white if i==active else MUTED); wf.c.setFont('FreeSerif', 6.5)
        wf.c.drawCentredString(wf.x+cx+i*tw+(tw-2)/2, wf.y+ch-4-6, t)
    wf.box(cx, ch-4-9-6, cw, 70, fill=CARD, border=BORDER)
    wf.placeholder(cx+3, ch-4-9-4, cw-6, 66, 'tab content')

def r_detail(wf, ch, title, kpis, cols, rows=3):
    r_dashboard(wf, ch, title, kpis, cols, rows)

def r_member_portal(wf, ch, title):
    draw_chrome(wf, ch, title)
    cx=34; cw=wf.w-34
    nav = ['Dashboard','Profile','My Schemes','Contributions','Receipts','Draw Status','Distribution','Documents','Complaints']
    wf.box(cx, ch-4-90, 60, 90, fill=STRIPE, border=BORDER)
    ny=ch-4-12
    for n in nav:
        wf.c.setFillColor(NAVY); wf.c.setFont('FreeSerif', 7)
        wf.c.drawString(wf.x+cx+4, wf.y+ny, n); ny-=10
    kpi_row(wf, cx+66, ch-4, cw-66, [('Outstanding','ETB 25,000'),('Paid','ETB 175,000'),('Next Draw','Round 3')])
    wf.box(cx+66, ch-4-30, cw-66, 40, fill=CARD, border=BORDER)
    wf.placeholder(cx+68, ch-4-28, cw-70, 36, 'my contribution history + receipts')

# ---------------------------------------------------------------- 28 screens (6-tuples)
SCREENS = [
 (1,'Login','Authentication entry — association-aware, MFA-ready',
  lambda wf,ch,t: r_form(wf,ch,t,[('Credentials',['Email or username','Password']),('Options',['Remember me'])]),
  ['Secure password hashing (argon2id)','Account lockout after N failed attempts','Multi-factor authentication (TOTP)','Association-aware login scoped to the user association','Forgot-password recovery flow','Remember-me token (optional, time-boxed)'],'Fields & features'),
 (2,'Platform Dashboard','Super-administrators — platform-wide metrics',
  lambda wf,ch,t: r_dashboard(wf,ch,t,[('Associations','48'),('Active','41'),('Suspended','5'),('Members','38,420')],['Association','Members','Schemes','Status']),
  ['Total / active / suspended associations','Total registered members platform-wide','Active schemes across all tenants','Subscription status and system health tiles','Recent platform audit log preview'],'KPIs & content'),
 (3,'Association Dashboard','Per-association KPIs and activity',
  lambda wf,ch,t: r_dashboard(wf,ch,t,[('Members','1,000'),('Active schemes','10'),('Expected','1.2M ETB'),('Outstanding','180k ETB')],['Member','Scheme','Contribution','Status']),
  ['Total and active members','Expected vs actual collections','Outstanding contributions and pending approvals','Upcoming draws and recent transactions'],'KPIs & content'),
 (4,'Association Registration','Create a new association and assign its General Manager',
  lambda wf,ch,t: r_form(wf,ch,t,[('Association',['Association name','Registration number','Registration date','Address','Phone','Email','Currency']),('General Manager',['GM full name','GM email','GM phone','Send invite']),('Financial',['Financial year start','Receipt prefix','Time zone','Date format'])]),
  ['Unique association code auto-assigned','Legal document upload (constitution, registration)','Initial General Manager account created and invited','Financial settings configurable now or later','Status set to Pending until platform admin activates'],'Form sections'),
 (5,'Branch Management','Create branches, assign managers and staff',
  lambda wf,ch,t: r_list(wf,ch,t,['Branch','Code','Manager','Members','Collections','Status'],['Search','Branch','Status']),
  ['Add / edit branch with unique branch code','Assign branch manager and staff','View branch membership, collections, performance','Branch-level financial drill-down'],'Functions'),
 (6,'Member Register','Searchable, filterable member table with bulk import',
  lambda wf,ch,t: r_list(wf,ch,t,['Member ID','Name','Phone','Branch','Schemes','Status'],['Search','Branch','Status','Scheme']),
  ['Search by name, number, phone, ID','Filter by branch, status, scheme','Export to Excel','Register new member and bulk import','View member profile'],'Functions'),
 (7,'Member Registration Form','Capture full member profile across 8 sections',
  lambda wf,ch,t: r_form(wf,ch,t,[('Personal',['Full name','Gender','Date of birth']),('Identification',['ID type','ID number']),('Contact & Address',['Phone','Email','Address']),('Enrollment',['Branch','Emergency contact','Next of kin'])]),
  ['Sections: Personal, Identification, Contact, Address, Emergency, Documents, Branch, Agreement','Photograph and document uploads','Duplicate member detection on ID number','Membership status defaults to Pending','Creates approval request for General Manager'],'Form sections'),
 (8,'Member Profile','Tabbed 360-degree member view',
  lambda wf,ch,t: r_tabs(wf,ch,t,['Overview','Schemes','Contributions','Receipts','Draws','Distributions','Documents','Complaints']),
  ['Eight tabs covering the full member lifecycle','Each tab backed by tenant-isolated queries','Contribution and distribution history per scheme','Member financial statement export from the Overview tab'],'Tabs'),
 (9,'Ekub Scheme Register','List of all schemes with collection/distribution totals',
  lambda wf,ch,t: r_list(wf,ch,t,['Code','Name','Type','Method','Target','Members','Collected','Status'],['Search','Type','Status']),
  ['Scheme code, type, distribution method, target','Members enrolled, total collected, total distributed','Status badge (draft through completed)','Create new scheme opens the wizard'],'Columns & functions'),
 (10,'Scheme Creation Wizard','8-step scheme configuration',
  lambda wf,ch,t: r_wizard(wf,ch,t,['General','Model','Plans','Frequency','Draw','Eligibility','Distribution','Review'], 7),
  ['Step 1 General, 2 Ekub model, 3 Participation plans, 4 Contribution frequency, 5 Draw method, 6 Eligibility, 7 Distribution, 8 Review','Distribution mode selectable at step 7 (traditional_pool / equal_rounds / target_entitlement)','round_value captured for equal_rounds and target_entitlement','Submit for General Manager approval at the end'],'Wizard steps'),
 (11,'Participation Plan Management','Define Full / Half / Quarter / Custom plans',
  lambda wf,ch,t: r_list(wf,ch,t,['Plan','Units','Target','Contribution','Formula','Status'],['Search','Scheme']),
  ['Create Full, Half, Quarter, Custom participation plans','Set target allocation and contribution unit per plan','Configure contribution formula (fixed / unit_multiplier / custom)','Preview calculations before saving'],'Functions'),
 (12,'Scheme Enrollment','Enroll a member in a plan; preview obligations',
  lambda wf,ch,t: r_form(wf,ch,t,[('Selection',['Member','Scheme','Participation plan']),('Preview',['Agreed contribution','Agreed target','Remaining rounds'])]),
  ['Member and scheme selection','Participation plan drives contribution + target','Live preview of contribution obligation and target entitlement','Confirm agreement checkbox required','On submit: generates contribution_schedules rows'],'Actions'),
 (13,'Contribution Schedule','Due / expected / paid / outstanding per member',
  lambda wf,ch,t: r_list(wf,ch,t,['Member','Scheme','Due date','Expected','Paid','Outstanding','Status'],['Member','Scheme','Status','Due before','Due after']),
  ['Outstanding amount is a generated column (expected minus paid)','Generate schedules automatically from enrollment + frequency','Regenerate future schedules with approval','Print and export schedules'],'Columns & functions'),
 (14,'Payment Collection','Cashier records a member payment',
  lambda wf,ch,t: r_form(wf,ch,t,[('Payment',['Member','Scheme','Due installment','Amount','Payment date']),('Method',['Payment method','Bank account','Transaction reference','Supporting document'])]),
  ['Cash, bank transfer, digital, other','Bank account selector shown when method is bank','Transaction reference captured for bank and digital','Buttons: Save, Submit for verification, Generate receipt','Duplicate-reference prevention enforced server-side'],'Buttons'),
 (15,'Payment Verification','Maker-checker verification queue',
  lambda wf,ch,t: r_list(wf,ch,t,['Txn #','Cashier','Member','Amount','Method','Reference','Status'],['Cashier','Method','Verification']),
  ['Pending transactions with cashier and supporting evidence','Actions: Verify, Reject, Request correction','Verification triggers journal posting and balance update','Rejected transactions return to cashier for correction'],'Actions'),
 (16,'Receipt Management','Search, view, print, download, resend receipts',
  lambda wf,ch,t: r_list(wf,ch,t,['Receipt #','Member','Amount','Date','Issued by','Status'],['Search','Date range']),
  ['Search receipts by number, member, or date range','View, print, and download PDF receipts','Resend electronic receipts (SMS / email)','Verify receipt authenticity against the ledger'],'Functions'),
 (17,'Collection Dashboard','Expected vs actual vs outstanding analytics',
  lambda wf,ch,t: r_dashboard(wf,ch,t,[('Expected','1.2M'),('Actual','1.02M'),('Rate','85%'),('Overdue','90k')],['Scheme','Expected','Collected','Outstanding']),
  ['Expected vs actual collection percentage','Outstanding and overdue amounts','Collection by scheme and by cashier','Collection trend chart over time'],'KPIs & content'),
 (18,'Draw Management','Prepare and execute a draw; record witnesses',
  lambda wf,ch,t: r_form(wf,ch,t,[('Session',['Scheme','Distribution round','Draw method']),('Eligibility',['Eligible members (auto)','Excluded + reason','Witnesses']),('Evidence',['Seed commitment','Algorithm version'])]),
  ['Eligible list generated from v_member_entitlement_balance','Excluded members shown with reason','Witnesses recorded for transparency','Seed commitment captured before execution','Submit result for General Manager approval'],'Functions'),
 (19,'Draw Results','Auditable draw outcome and announcement',
  lambda wf,ch,t: r_detail(wf,ch,t,[('Round','1'),('Eligible','20'),('Winner','A-0001'),('Status','Approved')],['Draw #','Date','Method','Winner','Eligible','Status']),
  ['Scheme, draw number, date, selection method, winner','Eligible participant count and approval status','Print result and download report','Publish member announcement','View draw audit evidence (seed, snapshot, algorithm)'],'Functions'),
 (20,'Distribution Management','Prepare, approve, pay, and confirm a distribution',
  lambda wf,ch,t: r_form(wf,ch,t,[('Beneficiary',['Beneficiary','Scheme','Gross entitlement','Approved deductions','Net payment']),('Payment',['Payment method','Payment reference','Supporting documents'])]),
  ['Gross from scheme entitlement; net = gross minus deductions (generated)','Deductions require per-row approver and configured rule','Verify available funds before payment (server-side)','Actions: Prepare, Submit approval, Approve, Record payment, Confirm receipt','Duplicate distribution payment prevention enforced'],'Actions'),
 (21,'Cash & Bank Management','Account register, deposits, transfers, reconciliation',
  lambda wf,ch,t: r_list(wf,ch,t,['Account','Type','Currency','Balance','Status'],['Type','Branch']),
  ['Multiple cash and bank accounts with opening balances','Deposits, withdrawals, and transfers','Cashier closing balances and reconciliation','Bank reconciliation against statement balance'],'Functions'),
 (22,'Expense Management','Submit, review, approve, and pay expenses',
  lambda wf,ch,t: r_form(wf,ch,t,[('Expense',['Expense date','Category','Amount','Description','Payee']),('Payment',['Cash/Bank account','Supporting document'])]),
  ['Buttons: Submit, Review, Approve, Record payment','Approval routed through maker-checker matrix','Journal entry posted on payment','Supporting document upload required'],'Actions'),
 (23,'Legal & Dispute Management','Agreements, complaints, disputes, settlements',
  lambda wf,ch,t: r_list(wf,ch,t,['Case','Type','Member','Scheme','Assigned','Status'],['Type','Status']),
  ['Upload agreements and legal documents (versioned)','Record complaints and disputes','Assign legal advisor and track recovery','Record settlement and close cases'],'Functions'),
 (24,'Reports Center','Categorized report catalog with PDF / XLSX export',
  lambda wf,ch,t: r_list(wf,ch,t,['Report','Category','Period','Format','Last run'],['Category','Format']),
  ['Categories: Membership, Contribution, Collection, Draw, Distribution, Cash & Bank, Expenses, Financial statements, Audit, Scheme performance','Filters by association, branch, scheme, date range, member, method','Export to PDF, Excel, printable HTML','Large reports run asynchronously'],'Functions'),
 (25,'User & Role Management','Create users, assign roles, set approval limits',
  lambda wf,ch,t: r_list(wf,ch,t,['User','Email','Roles','Branch','Status'],['Search','Role','Branch']),
  ['Create users and assign roles','Assign branches and configure permissions','Set per-role approval limits per transaction type','Suspend users and review access history'],'Functions'),
 (26,'Approval Center','Pending approvals assigned to the caller',
  lambda wf,ch,t: r_list(wf,ch,t,['Type','Txn','Amount','Submitted by','Approver','Status'],['Type','Status']),
  ['Pending requests with transaction type and amount','Required approver and submission date','Actions: Approve, Reject, Return for correction, Escalate','Escalation above the approver limit routes to committee'],'Actions'),
 (27,'Member Portal','Member self-service — own records only',
  lambda wf,ch,t: r_member_portal(wf,ch,t),
  ['Member sees ONLY their own records (RLS-enforced)','My Dashboard, Profile, Schemes, Contributions, Receipts','Draw Status, Distribution, Documents, Complaints, Notifications','No access to other members or association-wide financials'],'Navigation'),
 (28,'System Settings','Association-wide configuration',
  lambda wf,ch,t: r_form(wf,ch,t,[('Profile',['Association profile','Financial year','Currency','Receipt numbering']),('Rules',['Payment methods','Contribution frequency','Draw rules','Approval limits']),('Notifications',['Notification templates','Security settings'])]),
  ['Changes audited via fn_audit_log','Approval-limit changes are themselves approval-gated','Notification templates per channel (SMS / email / push / in-app)','Security settings: MFA, session expiry, lockout policy'],'Configure'),
]

# ---------------------------------------------------------------- build
c = canvasmod.Canvas(OUT, pagesize=A4)
c.setTitle('EAMS UI Wireframes'); c.setAuthor('Z.ai'); c.setCreator('Z.ai')
c.setSubject('Ekub & Association Management System — UI Wireframes (28 screens)')

# Cover
c.setFillColor(NAVY); c.rect(0,0,1.1*cm,PH,fill=1,stroke=0)
c.setFillColor(TEAL); c.rect(1.1*cm,0,0.18*cm,PH,fill=1,stroke=0)
c.setFillColor(EMERALD); c.rect(2.6*cm,PH-4.0*cm,3.4*cm,0.22*cm,fill=1,stroke=0)
c.setFillColor(NAVY); c.setFont('FreeSerif-Bold',26)
c.drawString(2.6*cm, PH-5.2*cm, 'EAMS UI Wireframes')
c.setFillColor(TEAL); c.setFont('FreeSerif',14)
c.drawString(2.6*cm, PH-6.4*cm, 'All 28 screens — SRS Part 7')
c.setStrokeColor(EMERALD); c.setLineWidth(2); c.line(2.6*cm, PH-6.9*cm, 8.6*cm, PH-6.9*cm)
c.setFillColor(MUTED); c.setFont('FreeSerif',10.5)
c.drawString(2.6*cm, PH-7.8*cm, 'Wireframe legend: navy = chrome / sidebar, teal = actions / active,')
c.drawString(2.6*cm, PH-8.2*cm, 'emerald = primary actions, grey = data fields / placeholders.')
c.drawString(2.6*cm, PH-8.8*cm, 'Each page = one screen: layout zones + a field/function list.')
c.setFillColor(MUTED); c.setFont('FreeSerif',10)
c.drawString(2.6*cm, 2.0*cm, 'Document Version 1.0   |   Companion to EAMS_Technical_Design.pdf')
c.showPage()

def screen_header(c, num, title, subtitle):
    c.setFillColor(NAVY); c.setFont('FreeSerif-Bold', 11)
    c.drawString(M, PH-M-6, 'Screen %d: %s' % (num, title))
    c.setFillColor(MUTED); c.setFont('FreeSerif', 8)
    c.drawString(M, PH-M-16, subtitle)
    c.setStrokeColor(EMERALD); c.setLineWidth(1.5)
    c.line(M, PH-M-20, M+40, PH-M-20)

for (num, title, sub, rfn, fields, ftitle) in SCREENS:
    screen_header(c, num, title, sub)
    top = PH - M - 22
    bottom = M + 1.2*cm
    wx, wy, ww, wh = M, bottom, PW-2*M, top-bottom
    wf = WF(c, wx, wy, ww, wh)
    rfn(wf, wh-58, title)
    # field list strip at bottom
    c.setFillColor(STRIPE); c.setStrokeColor(BORDER); c.setLineWidth(0.6)
    c.roundRect(M, M, PW-2*M, 1.05*cm, 2, fill=1, stroke=1)
    c.setFillColor(NAVY_L); c.setFont('FreeSerif-Bold', 8)
    c.drawString(M+6, M+1.05*cm-9, ftitle+':')
    c.setFillColor(TEXT); c.setFont('FreeSerif', 7.2)
    line = '   '.join('\u2022 '+f for f in fields)
    maxw = PW-2*M-12; x=M+6; y=M+1.05*cm-18
    words = line.split(' '); cur=''
    for wd in words:
        t=(cur+' '+wd).strip()
        if c.stringWidth(t,'FreeSerif',7.2) <= maxw or not cur:
            cur=t
        else:
            c.drawString(x,y,cur); y-=8.5; cur=wd
            if y < M+2: break
    if cur and y>=M+2: c.drawString(x,y,cur)
    c.setFillColor(MUTED); c.setFont('FreeSerif',7)
    c.drawString(M, 0.5*cm, 'EAMS UI Wireframes — SRS Part 7')
    c.drawRightString(PW-M, 0.5*cm, 'Page %d' % c.getPageNumber())
    c.showPage()

c.save()
print('Wrote', OUT)
