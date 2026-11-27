#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
EAMS Deployment Guide PDF generator.
Output: /home/z/my-project/download/EAMS_Deployment_Guide.pdf
Docker-based hosting, environment, migrations, backups, security, monitoring.
"""
import os, sys, hashlib
sys.path.insert(0, '/home/z/my-project/skills/pdf/scripts')
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm, inch, cm
from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT, TA_JUSTIFY
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer, PageBreak,
    Table, TableStyle, KeepTogether, CondPageBreak, HRFlowable, Preformatted)
from reportlab.platypus.tableofcontents import TableOfContents
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase.pdfmetrics import registerFontFamily

FD = '/usr/share/fonts'
pdfmetrics.registerFont(TTFont('NotoSerifSC', f'{FD}/truetype/noto-serif-sc/NotoSerifSC-Regular.ttf'))
pdfmetrics.registerFont(TTFont('NotoSerifSC-Bold', f'{FD}/truetype/noto-serif-sc/NotoSerifSC-Bold.ttf'))
registerFontFamily('NotoSerifSC', normal='NotoSerifSC', bold='NotoSerifSC-Bold')
pdfmetrics.registerFont(TTFont('FreeSerif', f'{FD}/truetype/freefont/FreeSerif.ttf'))
pdfmetrics.registerFont(TTFont('FreeSerif-Bold', f'{FD}/truetype/freefont/FreeSerifBold.ttf'))
pdfmetrics.registerFont(TTFont('FreeSerif-Italic', f'{FD}/truetype/freefont/FreeSerifItalic.ttf'))
pdfmetrics.registerFont(TTFont('FreeSerif-BoldItalic', f'{FD}/truetype/freefont/FreeSerifBoldItalic.ttf'))
pdfmetrics.registerFont(TTFont('DejaVuSans', f'{FD}/truetype/dejavu/DejaVuSansMono.ttf'))
registerFontFamily('FreeSerif', normal='FreeSerif', bold='FreeSerif-Bold',
                   italic='FreeSerif-Italic', boldItalic='FreeSerif-BoldItalic')
try:
    from pdf import install_font_fallback; install_font_fallback()
except Exception: pass

NAVY=colors.HexColor('#0F2A43'); NAVY_L=colors.HexColor('#1B3A57')
TEAL=colors.HexColor('#1F7A8C'); EMERALD=colors.HexColor('#2F9E6B')
BG=colors.HexColor('#F4F6F8'); BORDER=colors.HexColor('#CBD5E0')
TEXT=colors.HexColor('#1A2230'); MUTED=colors.HexColor('#6B7785'); STRIPE=colors.HexColor('#EEF2F6')

BODY=ParagraphStyle('B',fontName='FreeSerif',fontSize=10.5,leading=16,alignment=TA_JUSTIFY,textColor=TEXT,spaceAfter=8)
BULLET=ParagraphStyle('BU',parent=BODY,leftIndent=14,spaceAfter=4,alignment=TA_LEFT)
H1=ParagraphStyle('H1',fontName='FreeSerif-Bold',fontSize=17,leading=23,textColor=NAVY,spaceBefore=16,spaceAfter=8)
H2=ParagraphStyle('H2',fontName='FreeSerif-Bold',fontSize=12.5,leading=18,textColor=NAVY_L,spaceBefore=10,spaceAfter=5)
H3=ParagraphStyle('H3',fontName='FreeSerif-Bold',fontSize=11,leading=15,textColor=TEAL,spaceBefore=7,spaceAfter=3)
CODE=ParagraphStyle('C',fontName='DejaVuSans',fontSize=8,leading=11.5,textColor=TEXT,backColor=STRIPE,
    leftIndent=6,rightIndent=6,spaceBefore=3,spaceAfter=7)
CAP=ParagraphStyle('Cap',fontName='FreeSerif-Italic',fontSize=8.5,textColor=MUTED,alignment=TA_CENTER,spaceBefore=2,spaceAfter=8)
TH=ParagraphStyle('TH',fontName='FreeSerif-Bold',fontSize=9, textColor=colors.white, alignment=TA_LEFT, leading=12)
TC=ParagraphStyle('TC',fontName='FreeSerif',fontSize=9, textColor=TEXT, alignment=TA_LEFT, leading=12)
TC_C=ParagraphStyle('TCc',parent=TC,alignment=TA_CENTER)
TC_M=ParagraphStyle('TCm',fontName='DejaVuSans',fontSize=8.2,textColor=TEXT,alignment=TA_LEFT,leading=11)
COVER_T=ParagraphStyle('CT',fontName='FreeSerif-Bold',fontSize=28,leading=34,textColor=NAVY,alignment=TA_LEFT)
COVER_S=ParagraphStyle('CS',fontName='FreeSerif',fontSize=14,leading=20,textColor=TEAL,alignment=TA_LEFT)
COVER_M=ParagraphStyle('CM',fontName='FreeSerif',fontSize=10.5,leading=16,textColor=MUTED,alignment=TA_LEFT)
TOC_L0=ParagraphStyle('TL0',fontName='FreeSerif-Bold',fontSize=11,leading=18,leftIndent=4,textColor=NAVY)
TOC_L1=ParagraphStyle('TL1',fontName='FreeSerif',fontSize=10,leading=16,leftIndent=22,textColor=TEXT)

OUT='/home/z/my-project/download/EAMS_Deployment_Guide.pdf'
AVAIL=A4[0]-2*0.85*inch

def H(t,s,level=0):
    k='h_'+hashlib.md5(t.encode()).hexdigest()[:8]
    p=Paragraph(f'<a name="{k}"/>{t}',s); p.bookmark_name=k; p.bookmark_level=level
    p.bookmark_text=t; p.bookmark_key=k; return p
def para(t,s=BODY): return Paragraph(t,s)
def bullets(items): return [Paragraph(f'<bullet>•</bullet> {t}',BULLET) for t in items]
def code(t): return Paragraph(t.replace('<','<').replace('>','>'),CODE)
def tbl(data,ratios,cap=None):
    cw=[r*AVAIL for r in ratios]
    t=Table(data,colWidths=cw,hAlign='CENTER',repeatRows=1)
    sty=[('GRID',(0,0),(-1,-1),0.5,BORDER),('VALIGN',(0,0),(-1,-1),'MIDDLE'),
         ('LEFTPADDING',(0,0),(-1,-1),5),('RIGHTPADDING',(0,0),(-1,-1),5),
         ('TOPPADDING',(0,0),(-1,-1),4),('BOTTOMPADDING',(0,0),(-1,-1),4),
         ('BACKGROUND',(0,0),(-1,0),NAVY),('TEXTCOLOR',(0,0),(-1,0),colors.white)]
    for r in range(1,len(data)):
        if r%2==0: sty.append(('BACKGROUND',(0,r),(-1,r),STRIPE))
    t.setStyle(TableStyle(sty))
    out=[t]
    if cap: out+=[Spacer(1,3),Paragraph(cap,CAP)]
    out+=[Spacer(1,8)]; return out

class TocDoc(SimpleDocTemplate):
    def afterFlowable(self,f):
        if hasattr(f,'bookmark_name'):
            self.notify('TOCEntry',(getattr(f,'bookmark_level',0),getattr(f,'bookmark_text',''),self.page,getattr(f,'bookmark_key','')))

def hf(canvas,doc):
    canvas.saveState(); canvas.setStrokeColor(BORDER); canvas.setLineWidth(0.5)
    canvas.line(0.85*inch,A4[1]-0.55*inch,A4[0]-0.85*inch,A4[1]-0.55*inch)
    canvas.setFont('FreeSerif',7.5); canvas.setFillColor(MUTED)
    canvas.drawString(0.85*inch,A4[1]-0.48*inch,'EAMS — Deployment Guide')
    canvas.drawRightString(A4[0]-0.85*inch,A4[1]-0.48*inch,'Version 1.0')
    canvas.line(0.85*inch,0.55*inch,A4[0]-0.85*inch,0.55*inch)
    canvas.drawString(0.85*inch,0.4*inch,'Ekub & Association Management System')
    canvas.drawRightString(A4[0]-0.85*inch,0.4*inch,f'Page {doc.page}'); canvas.restoreState()

def cover_page(canvas,doc):
    canvas.saveState()
    canvas.setFillColor(NAVY); canvas.rect(0,0,1.1*cm,A4[1],fill=1,stroke=0)
    canvas.setFillColor(TEAL); canvas.rect(1.1*cm,0,0.18*cm,A4[1],fill=1,stroke=0)
    canvas.setFillColor(EMERALD); canvas.rect(2.6*cm,A4[1]-4.2*cm,3.4*cm,0.22*cm,fill=1,stroke=0)
    canvas.restoreState()

story=[]
# Cover
story.append(Spacer(1,5.0*cm))
story.append(Paragraph('EAMS<br/>Deployment Guide',COVER_T))
story.append(Spacer(1,0.4*cm))
story.append(Paragraph('Docker-based hosting, configuration & operations',COVER_S))
story.append(Spacer(1,0.3*cm))
story.append(HRFlowable(width=6*cm,color=EMERALD,thickness=2,spaceBefore=0,spaceAfter=10))
story.append(Paragraph('Production deployment instructions for the Ekub & Association Management '
 'System — environment, database migrations with Row-Level Security, backups, security '
 'hardening, monitoring, and the go-live checklist.',COVER_M))
story.append(Spacer(1,7.0*cm))
story.append(Paragraph('Document Version 1.0',COVER_M))
story.append(Paragraph('Initial Market: Ethiopia  |  Currency: ETB',COVER_M))
story.append(Paragraph('Companion files: eams_database_schema.sql, eams_seed_data.sql, eams_api_spec.yaml',COVER_M))
story.append(PageBreak())

# TOC
story.append(Paragraph('Table of Contents',H1))
toc=TableOfContents(); toc.levelStyles=[TOC_L0,TOC_L1]; story.append(toc); story.append(PageBreak())

# 1. Overview
story.append(H('1. Overview & Prerequisites',H1,0))
story.append(para('This guide deploys the EAMS platform as a Docker-based stack: a Django REST API, '
 'a Next.js frontend and PWA, a PostgreSQL 15+ database with Row-Level Security, a Redis cache, '
 'and a Celery worker for asynchronous jobs. All services run behind an Nginx reverse proxy that '
 'terminates TLS. The deployment is tenant-aware by design: a single database holds every '
 'association, isolated at the row level, so horizontal scaling of the application tier does not '
 'compromise tenant separation.'))
story.append(para('Before starting, provision a Linux host (Ubuntu 22.04 LTS or equivalent) with at '
 'least 4 vCPU, 8 GB RAM, and 100 GB SSD for a pilot of up to 10,000 members per '
 'association. Install Docker Engine 24+, Docker Compose v2, and OpenSSL. Obtain a domain name '
 'with valid DNS A/AAAA records and a TLS certificate (Let&apos;s Encrypt via Certbot, or a '
 'commercial CA). Configure an SMTP endpoint for email and an SMS gateway account for '
 'notifications. Payment-provider credentials (Telebirr, CBE Birr, M-Pesa Ethiopia) are required '
 'only when digital collections go live; the platform can operate on cash and bank transfer first.'))

# 2. Topology
story.append(H('2. Deployment Topology',H1,0))
story.append(para('The reference stack is defined in a single docker-compose.yml. Six services form '
 'the production topology: nginx (edge), web (Django API + gunicorn), worker (Celery), beat '
 '(Celery scheduler), db (PostgreSQL), and redis (broker/cache). Static and media assets are '
 'served by nginx from a shared volume; the database and Redis persist data to named volumes; '
 'backups are written to a dedicated volume that an external job ships to object storage.'))
story += tbl([
 [Paragraph('Service',TH),Paragraph('Image',TH),Paragraph('Port',TH),Paragraph('Purpose',TH)],
 [para('nginx',TC),para('nginx:1.27',TC),para('80, 443',TC_C),para('TLS termination, static + media, reverse proxy',TC)],
 [para('web',TC),para('eams/api:1.0',TC),para('8000 (internal)',TC_C),para('Django REST API via gunicorn',TC)],
 [para('worker',TC),para('eams/api:1.0',TC),para('-',TC_C),para('Celery worker (receipts, reports, notifications)',TC)],
 [para('beat',TC),para('eams/api:1.0',TC),para('-',TC_C),para('Celery beat (schedule generation, reminders)',TC)],
 [para('db',TC),para('postgres:15',TC),para('5432 (internal)',TC_C),para('PostgreSQL with RLS + audit triggers',TC)],
 [para('redis',TC),para('redis:7',TC),para('6379 (internal)',TC_C),para('Celery broker + cache',TC)],
],[0.14,0.20,0.18,0.48],cap='Table 1. Production service topology.')
story.append(para('The minimal docker-compose excerpt below shows the service wiring. Internal '
 'ports are never published to the host; only nginx exposes 80/443.'))
story.append(code(
 'services:\n'
 '  db:\n'
 '    image: postgres:15\n'
 '    environment:\n'
 '      POSTGRES_DB: eams\n'
 '      POSTGRES_USER: eams_app\n'
 '      POSTGRES_PASSWORD_FILE: /run/secrets/db_password\n'
 '    volumes: [ db_data:/var/lib/postgresql/data ]\n'
 '    secrets: [ db_password ]\n'
 '    restart: unless-stopped\n'
 '  web:\n'
 '    image: eams/api:1.0\n'
 '    command: gunicorn eams.wsgi:application -b 0.0.0.0:8000 -w 4\n'
 '    env_file: .env\n'
 '    depends_on: [ db, redis ]\n'
 '    restart: unless-stopped\n'
 '  nginx:\n'
 '    image: nginx:1.27\n'
 '    ports: [ "80:80", "443:443" ]\n'
 '    volumes:\n'
 '      - ./nginx.conf:/etc/nginx/conf.d/default.conf:ro\n'
 '      - certs:/etc/nginx/certs:ro\n'
 '      - static:/usr/share/nginx/html/static:ro\n'
 '    depends_on: [ web ]\n'
 '    restart: unless-stopped'))

# 3. Environment
story.append(H('3. Environment Configuration',H1,0))
story.append(para('All runtime configuration is supplied through environment variables loaded from '
 'a .env file that is never committed to source control. Secrets (database password, JWT signing '
 'key, payment-provider keys, SMTP password) are injected via Docker secrets or a secrets manager '
 'rather than plain env vars where possible. Monetary and tenant settings are per-association in '
 'the database; the variables below are platform-wide.'))
story += tbl([
 [Paragraph('Variable',TH),Paragraph('Required',TH),Paragraph('Purpose',TH)],
 [para('DATABASE_URL',TC_M),para('Yes',TC_C),para('postgres://user:pass@db:5432/eams',TC)],
 [para('REDIS_URL',TC_M),para('Yes',TC_C),para('redis://redis:6379/0 — broker and cache',TC)],
 [para('DJANGO_SECRET_KEY',TC_M),para('Yes',TC_C),para('Cryptographic signing key (50+ random chars)',TC)],
 [para('JWT_SIGNING_KEY',TC_M),para('Yes',TC_C),para('Token signing key (separate from Django secret)',TC)],
 [para('ALLOWED_HOSTS',TC_M),para('Yes',TC_C),para('Comma-separated FQDNs served by the API',TC)],
 [para('CORS_ALLOWED_ORIGINS',TC_M),para('Yes',TC_C),para('Frontend origin(s) for CORS',TC)],
 [para('DB_TENANT_GUC',TC_M),para('Yes',TC_C),para('Set to 1 — enables app.current_association_id scoping',TC)],
 [para('SMS_GATEWAY_URL / SMS_API_KEY',TC_M),para('No',TC_C),para('SMS provider endpoint and key',TC)],
 [para('EMAIL_HOST / EMAIL_HOST_USER / EMAIL_HOST_PASSWORD',TC_M),para('No',TC_C),para('SMTP relay for email notifications',TC)],
 [para('TELEBIRR_* / CBE_BIRR_* / MPESA_*',TC_M),para('No',TC_C),para('Payment-provider credentials (digital collections)',TC)],
 [para('BACKUP_S3_BUCKET / BACKUP_S3_KEY',TC_M),para('Yes',TC_C),para('Off-site backup target',TC)],
 [para('SENTRY_DSN',TC_M),para('No',TC_C),para('Error tracking',TC)],
],[0.30,0.12,0.58],cap='Table 2. Platform environment variables.')

# 4. Database
story.append(H('4. Database Setup & Migrations',H1,0))
story.append(para('The database is the trust boundary for tenant isolation and financial integrity, '
 'so its setup is the most carefully scripted step. Load the schema, run application migrations, '
 'enable RLS, then seed the demonstration environment only in non-production. The application '
 'connection role must NOT be a superuser and must be subject to RLS via the FORCE clause on the '
 'six sensitive tables.'))
story.append(H('4.1 Initial Schema & RLS',H2,1))
story.append(para('The schema file creates extensions, enums, all tables, constraints, indexes, the '
 'audit trigger, and the full RLS policy set. Load it once into the empty database:'))
story.append(code(
 'psql -h db -U eams_app -d eams -f eams_database_schema.sql'))
story.append(para('Verify RLS is enabled and forced on the sensitive tables before any application '
 'data is written:'))
story.append(code(
 "SELECT relname, relrowsecurity, relforcerowsecurity\n"
 "FROM pg_class WHERE relname IN\n"
 "('members','contributions','distributions','journal_entries','journal_lines','receipts');\n"
 "-- Every row must show relrowsecurity = t and relforcerowsecurity = t."))
story.append(H('4.2 Tenant GUCs on Every Connection',H2,1))
story.append(para('Every authenticated request must set two session GUCs before issuing any query, '
 'so RLS can scope rows to the caller association. The API middleware does this inside a '
 'transaction; the seed script sets <font name="DejaVuSans">app.is_platform_admin</font> to '
 'bypass scoping for seeding only.'))
story.append(code(
 "SET LOCAL app.current_association_id = '<uuid>';\n"
 "SET LOCAL app.current_user_id       = '<uuid>';\n"
 "SET LOCAL app.is_platform_admin     = 'off';"))
story.append(H('4.3 Seed (Demonstration Only)',H2,1))
story.append(para('The seed dataset demonstrates both Ekub models and the balanced double-entry '
 'ledger. Load it only in a clearly identified demonstration environment, never in production:'))
story.append(code(
 'psql -h db -U eams_app -d eams -f eams_seed_data.sql\n'
 '-- verify the books balance:\n'
 "SELECT * FROM v_journal_balance_check;  -- every balance_difference must be 0"))
story.append(para('After loading, the cash account should hold ETB 440,000 (2,400,000 collected '
 'minus 1,000,000 Model A distribution minus 1,960,000 Model B net distribution), the balance '
 'sheet should balance (Assets 440,000 = Liabilities 400,000 + Income 40,000), and the remaining '
 'targets of both winners should be zero. If any of these fail, do not proceed.'))

# 5. Application
story.append(H('5. Application Deployment',H1,0))
story.append(para('Build the API image once and push it to your registry. The same image serves '
 'the web, worker, and beat containers — the entrypoint selects the role from the COMMAND. '
 'Collect static files into the shared volume that nginx mounts read-only.'))
story.append(code(
 'docker compose build web\n'
 'docker compose run --rm web python manage.py migrate\n'
 'docker compose run --rm web python manage.py collectstatic --noinput\n'
 'docker compose up -d\n'
 'docker compose exec web python manage.py createsuperuser'))
story.append(para('Health checks: nginx exposes <font name="DejaVuSans">/healthz</font> (returns '
 '200 when the web container responds) and the API exposes '
 '<font name="DejaVuSans">/api/health/</font> (checks database and Redis connectivity). Wire '
 'these into the container healthcheck and your load balancer. A rolling deploy replaces the web '
 'containers one at a time; migrations run as a discrete pre-deploy step so they are never run '
 'concurrently by two containers.'))

# 6. PWA
story.append(H('6. PWA Configuration',H1,0))
story.append(para('The frontend ships a web app manifest and a service worker so it is installable '
 'on Android, iOS-supported browsers, and desktop. Cache static assets aggressively; never cache '
 'financial responses. Offline, the app may queue permitted records (e.g., a draft receipt) but '
 'must label them unconfirmed until the server validates them on reconnection. Financial posting, '
 'draw execution, and approvals remain strictly server-authoritative.'))
story += bullets([
 'Serve <font name="DejaVuSans">manifest.webmanifest</font> from the frontend origin with valid icons (192px and 512px).',
 'Register the service worker on first navigation; use a stale-while-revalidate strategy for the app shell only.',
 'Display online/offline status in the top bar; grey out action buttons that require the server when offline.',
 'Use an idempotency key on every queued write so a duplicated sync cannot create a second payment.',
 'Require HTTPS for service worker registration (provided by nginx TLS).',
])

# 7. Integrations
story.append(H('7. Integrations',H1,0))
story.append(para('Payment and communication integrations are configured per environment and '
 'activated only after provider approval and API access are granted. Digital payments must be '
 'verified through an authenticated provider response or reconciliation — never marked completed '
 'on client-reported success alone. Configure webhook endpoints under '
 '<font name="DejaVuSans">/api/webhooks/<provider>/</font> with signature verification; '
 'reject any webhook whose signature does not validate.'))
story += tbl([
 [Paragraph('Integration',TH),Paragraph('Type',TH),Paragraph('Verification',TH)],
 [para('Telebirr',TC),para('Digital payment',TC),para('Provider callback + signature check',TC)],
 [para('CBE Birr',TC),para('Digital payment',TC),para('Provider callback + signature check',TC)],
 [para('M-Pesa Ethiopia',TC),para('Digital payment',TC),para('Provider callback + signature check',TC)],
 [para('SMS gateway',TC),para('Notification',TC),para('Delivery receipt from gateway',TC)],
 [para('SMTP relay',TC),para('Notification',TC),para('SMTP delivery status',TC)],
 [para('Push (FCM/APNs)',TC),para('Notification',TC),para('Token-based, per-device',TC)],
],[0.24,0.20,0.56],cap='Table 3. Integration verification requirements.')

# 8. Backups
story.append(H('8. Backups & Disaster Recovery',H1,0))
story.append(para('Backups are the last line of defense for a financial system. Take automated '
 'daily logical backups (pg_dump) plus continuous WAL archiving for point-in-time recovery. '
 'Encrypt backups at rest with a key held outside the database host. Test restoration regularly '
 '— an untested backup is assumed broken. Configure RPO and RTO targets with the association and '
 'verify them in a quarterly restore drill.'))
story.append(H('8.1 Backup Script',H2,1))
story.append(code(
 '# daily, via cron or Celery beat\n'
 'pg_dump -h db -U eams_app -Fc eams | openssl enc -aes-256-cbc -salt -pass file:/run/secrets/backup_key \\\n'
 '  | aws s3 cp - s3://$BACKUP_S3_BUCKET/eams_$(date +%F).dump.enc\n'
 '# retain 30 daily + 12 monthly + 7 yearly; prune older objects.'))
story.append(H('8.2 Restore Procedure',H2,1))
story.append(code(
 'aws s3 cp s3://$BACKUP_S3_BUCKET/eams_YYYY-MM-DD.dump.enc - | openssl enc -d -aes-256-cbc -pass file:/run/secrets/backup_key \\\n'
 '  > /tmp/restore.dump\n'
 'pg_restore -h db -U eams_app -d eams --clean --if-exists /tmp/restore.dump\n'
 'psql -h db -U eams_app -d eams -c "SELECT * FROM v_journal_balance_check;"  -- confirm integrity'))
story.append(para('After any restore, immediately verify that every posted journal entry still '
 'balances, that RLS policies are intact, and that no association can see another&apos;s rows. '
 'Document the restore in the operations log with the RPO actually achieved.'))

# 9. Security
story.append(H('9. Security Hardening',H1,0))
story.append(para('Security for a financial platform is layered: transport, authentication, '
 'authorization, database, and audit. TLS is mandatory end to end; the API rejects plain HTTP. '
 'Passwords are hashed with argon2id; MFA (TOTP) is enforced for all staff roles and available '
 'to members. Sessions expire; failed-login monitoring locks accounts after the configured '
 'threshold. The application role is least-privilege and subject to FORCE RLS.'))
story += bullets([
 '<b>TLS:</b> terminate at nginx with modern ciphers; HSTS; redirect 80 to 443.',
 '<b>Secrets:</b> Docker secrets or a vault; never bake credentials into images or env files in git.',
 '<b>AuthN:</b> argon2id password hashing, JWT with short access lifetime + refresh rotation, MFA for staff.',
 '<b>AuthZ:</b> permission codes enforced in the API; maker-checker on all financial mutations.',
 '<b>Database:</b> least-privilege role, FORCE RLS on six sensitive tables, audit trigger on 30 tables.',
 '<b>App defense:</b> parameterized queries (no SQL injection), output escaping (no XSS), CSRF tokens, rate limiting on auth endpoints.',
 '<b>Documents:</b> identification documents stored in private object storage with restricted access.',
 '<b>Audit:</b> immutable audit_logs; ship to a write-once log sink; review platform-level events.',
])

# 10. Monitoring
story.append(H('10. Monitoring & Alerting',H1,0))
story.append(para('Monitor four signal classes: infrastructure (CPU, memory, disk, DB connections), '
 'application (error rate, latency, queue depth), business (collection rate, overdue amount, '
 'pending approvals age), and integrity (journal balance drift, RLS policy presence). The '
 'integrity checks are the most important — a financial system that silently drifts is worse than '
 'one that is down.'))
story += tbl([
 [Paragraph('Check',TH),Paragraph('Frequency',TH),Paragraph('Alert if',TH)],
 [para('v_journal_balance_check',TC),para('Hourly',TC_C),para('Any balance_difference != 0',TC)],
 [para('RLS enabled + forced',TC),para('Daily',TC_C),para('Any sensitive table missing RLS or FORCE',TC)],
 [para('Cash vs ledger reconciliation',TC),para('Daily',TC_C),para('Cash account != ledger Cash balance',TC)],
 [para('Backup success',TC),para('Daily',TC_C),para('Backup missing or not encrypted',TC)],
 [para('API error rate',TC),para('Continuous',TC_C),para('5xx rate > 1% over 5 min',TC)],
 [para('Pending approvals age',TC),para('Daily',TC_C),para('Any approval pending > 48h',TC)],
],[0.30,0.16,0.54],cap='Table 4. Integrity and operations monitoring checks.')

# 11. Runbook
story.append(H('11. Operations Runbook',H1,0))
story.append(para('Common operational tasks with their exact commands. Run all financial commands '
 'with the tenant GUCs set so the action is scoped and audited.'))
story += tbl([
 [Paragraph('Task',TH),Paragraph('Command',TH)],
 [para('Tail API logs',TC),para('docker compose logs -f web',TC_M)],
 [para('Run a migration',TC),para('docker compose run --rm web python manage.py migrate',TC_M)],
 [para('Inspect queue',TC),para('docker compose exec web celery -A eams inspect active',TC_M)],
 [para('Take an ad-hoc backup',TC),para('scripts/backup.sh',TC_M)],
 [para('Verify ledger balance',TC),para('psql -c "SELECT * FROM v_journal_balance_check;"',TC_M)],
 [para('Reconcile cash',TC),para('psql -c "SELECT account_name, current_balance FROM cash_accounts;"',TC_M)],
 [para('Rotate JWT signing key',TC),para('Update JWT_SIGNING_KEY; restart web + worker',TC_M)],
 [para('Suspend an association',TC),para('PATCH /platform/associations/{id}/status {status:suspended}',TC_M)],
],[0.26,0.74],cap='Table 5. Operations runbook.')

# 12. Go-live checklist
story.append(H('12. Go-Live Checklist',H1,0))
story.append(para('Do not go live until every item below is verified. The platform should also '
 'undergo legal and regulatory review in Ethiopia before handling funds commercially.'))
story += bullets([
 'Schema loaded; RLS enabled and forced on the six sensitive tables; audit triggers attached.',
 'All migrations applied; smoke tests pass against the OpenAPI specification.',
 'TLS certificate valid; HSTS enabled; HTTP redirects to HTTPS.',
 'Secrets injected via Docker secrets; no credentials in git or images.',
 'Backups running daily, encrypted, and a restore drill completed within RTO.',
 'Monitoring and alerting wired; integrity checks green for 24h.',
 'Payment integrations verified end to end (if digital collections enabled).',
 'MFA enforced for all staff accounts; first General Manager account created per association.',
 'Distribution mode and round_value approved per scheme by the association.',
 'Legal and regulatory review completed; data-retention policy documented.',
])
story.append(para('With the checklist complete, activate the first association, register its '
 'members and schemes, and begin with cash and bank-transfer collections before enabling digital '
 'payments. Monitor the integrity checks closely for the first two weeks; any journal-balance '
 'drift is a stop-the-line event.'))

doc=TocDoc(OUT,pagesize=A4,leftMargin=0.85*inch,rightMargin=0.85*inch,
           topMargin=0.8*inch,bottomMargin=0.8*inch,
           title='EAMS Deployment Guide',author='Z.ai',creator='Z.ai',
           subject='Ekub & Association Management System — Deployment Guide')
doc.multiBuild(story,onFirstPage=cover_page,onLaterPages=hf)
print('Wrote',OUT)
