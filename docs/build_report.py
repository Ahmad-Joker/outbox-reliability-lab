"""Generate the explanatory report from verified project evidence (optional reportlab dependency)."""
from pathlib import Path
import json
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, KeepTogether
from reportlab.graphics.shapes import Drawing, Rect, String, Line, Polygon

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / 'Outbox_Reliability_Lab_Explanation_2026-11-01.pdf'
DEMO = json.loads((ROOT / 'samples/verified_demo_output.json').read_text())
NAVY = colors.HexColor('#15304A')
TEAL = colors.HexColor('#087E85')
PALE = colors.HexColor('#EAF4F5')
LIGHT = colors.HexColor('#F2F5F9')
INK = colors.HexColor('#243449')
MUTED = colors.HexColor('#556779')

styles = getSampleStyleSheet()
styles.add(ParagraphStyle(name='CoverTitleX', fontName='Helvetica-Bold', fontSize=24, leading=29, textColor=NAVY, spaceAfter=11))
styles.add(ParagraphStyle(name='SubtitleX', fontName='Helvetica', fontSize=12, leading=17, textColor=TEAL, spaceAfter=15))
styles.add(ParagraphStyle(name='H1X', fontName='Helvetica-Bold', fontSize=15, leading=19, textColor=NAVY, spaceBefore=14, spaceAfter=7, keepWithNext=True))
styles.add(ParagraphStyle(name='H2X', fontName='Helvetica-Bold', fontSize=11.5, leading=15, textColor=TEAL, spaceBefore=10, spaceAfter=5, keepWithNext=True))
styles.add(ParagraphStyle(name='BodyX', fontName='Helvetica', fontSize=10.2, leading=15.2, textColor=INK, spaceAfter=7))
styles.add(ParagraphStyle(name='SmallX', fontName='Helvetica', fontSize=9.4, leading=13.6, textColor=INK, spaceAfter=5))
styles.add(ParagraphStyle(name='TinyX', fontName='Helvetica', fontSize=8.8, leading=12, textColor=INK))
styles.add(ParagraphStyle(name='CalloutX', fontName='Helvetica-Bold', fontSize=11.2, leading=16, textColor=NAVY, backColor=PALE, borderPadding=10, spaceBefore=7, spaceAfter=11))
styles.add(ParagraphStyle(name='FooterX', fontName='Helvetica', fontSize=8.2, leading=10, textColor=MUTED, alignment=TA_CENTER))


def P(text, style='BodyX'):
    return Paragraph(text, styles[style])


def tbl(rows, widths, header=True):
    data = [[P(str(cell), 'TinyX') for cell in row] for row in rows]
    t = Table(data, colWidths=widths, repeatRows=1 if header else 0, hAlign='LEFT')
    cmds = [('VALIGN',(0,0),(-1,-1),'TOP'), ('LEFTPADDING',(0,0),(-1,-1),8), ('RIGHTPADDING',(0,0),(-1,-1),8), ('TOPPADDING',(0,0),(-1,-1),7), ('BOTTOMPADDING',(0,0),(-1,-1),7), ('LINEBELOW',(0,-1),(-1,-1),.5,colors.HexColor('#D8E2EA'))]
    if header:
        cmds += [('BACKGROUND',(0,0),(-1,0),NAVY),('TEXTCOLOR',(0,0),(-1,0),colors.white)]
        # Paragraph text uses its own color, so set header cells explicitly
        data[0] = [Paragraph(f'<font color="white"><b>{cell}</b></font>', styles['TinyX']) for cell in rows[0]]
    for i in range(1 if header else 0, len(rows)):
        if i%2==0: cmds.append(('BACKGROUND',(0,i),(-1,i),LIGHT))
    t.setStyle(TableStyle(cmds))
    return t


def diagram():
    d=Drawing(490,210)
    boxes=[(8,142,125,44,'HTTP client','idempotency key'),(178,142,130,44,'FastAPI','order validation'),(358,142,124,44,'SQLite transaction','order + outbox'),
           (358,52,124,44,'Polling worker','claim + lease'),(178,52,130,44,'Idempotent inbox','UNIQUE(event_id)'),(8,52,125,44,'Audit / dashboard','retry + recovery')]
    for x,y,w,h,label,sub in boxes:
        d.add(Rect(x,y,w,h,rx=8,ry=8,fillColor=PALE if 'inbox' in label.lower() else LIGHT,strokeColor=TEAL,strokeWidth=1.2))
        d.add(String(x+w/2,y+26,label,fontName='Helvetica-Bold',fontSize=9.3,textAnchor='middle',fillColor=NAVY))
        d.add(String(x+w/2,y+11,sub,fontName='Helvetica',fontSize=8.3,textAnchor='middle',fillColor=MUTED))
    arrows=[(133,164,178,164),(308,164,358,164),(420,142,420,96),(358,74,308,74),(178,74,133,74)]
    for x1,y1,x2,y2 in arrows:
        d.add(Line(x1,y1,x2,y2,strokeColor=TEAL,strokeWidth=1.7))
        if x1<x2:d.add(Polygon([x2,y2,x2-6,y2+3,x2-6,y2-3],fillColor=TEAL,strokeColor=TEAL))
        elif x1>x2:d.add(Polygon([x2,y2,x2+6,y2+3,x2+6,y2-3],fillColor=TEAL,strokeColor=TEAL))
        else:d.add(Polygon([x2,y2,x2-3,y2+6,x2+3,y2+6],fillColor=TEAL,strokeColor=TEAL))
    d.add(String(245,116,'At-least-once attempt; duplicate suppressed at recipient',fontName='Helvetica',fontSize=8.4,textAnchor='middle',fillColor=MUTED))
    d.add(String(245,15,'All components run locally. Inbox is simulated, not a real external service.',fontName='Helvetica-Oblique',fontSize=8.4,textAnchor='middle',fillColor=MUTED))
    return d


def footer(canvas, doc):
    canvas.saveState()
    w,h=A4
    canvas.setStrokeColor(colors.HexColor('#DDE5EC'))
    canvas.line(18*mm,16*mm,w-18*mm,16*mm)
    canvas.setFont('Helvetica',8)
    canvas.setFillColor(MUTED)
    canvas.drawString(18*mm,11*mm,'Outbox Reliability Lab | Ahmad Essam Abdelaziz | 01 Nov 2026')
    canvas.drawRightString(w-18*mm,11*mm,f'Page {doc.page}')
    canvas.restoreState()

story=[]
story += [Spacer(1,7*mm),P('OUTBOX RELIABILITY LAB','CoverTitleX'),P('From job-market research to a verified backend engineering MVP','SubtitleX')]
story += [P('<b>Prepared for:</b> Ahmad Essam Abdelaziz &nbsp;&nbsp; <b>Date:</b> 1 November 2026 &nbsp;&nbsp; <b>Delivery:</b> local MVP + source archive'),
          P('A simulated order system that survives temporary processing failures and demonstrates why idempotency matters. Built with Python, FastAPI, SQLite, a separate polling worker, tests, and a read-only dashboard.','CalloutX')]
story += [P('1 | Why this project won','H1X'),P('Current employer postings emphasize reliable APIs, asynchronous processing, testing, debugging, databases and operational ownership. Ahmad already has AI evaluation and full-stack experience; a demonstrable failure-tolerant backend closes a different gap.')]
story += [tbl([['Ranked idea','Hiring / gap / feasibility','Editorial score'],['1. Outbox Reliability Lab','Reliability, transactional writes, retries, auditability','97/100'],['2. ReconcileAudit','Finance automation and matching','85/100'],['3. SearchRankBench','Search relevance and evaluation','82/100'],['4. EdgeVisionOps','Computer vision inference and MLOps','75/100']],[175,225,80])]
story += [Spacer(1,7),P('Scoring rubric: hiring demand 25%, gap 20%, usefulness 15%, differentiation 15%, feasibility 15%, low cost 10%. Scores are editorial assessments, not hiring probabilities.','SmallX')]
story += [P('Hiring evidence','H2X'),P('<b>Monzo:</b> Go, Kafka, Docker and shipped code. <b>Amazon:</b> reliable services, CI/CD and code verification. <b>Cloudflare:</b> Go/Python and large-scale engineering. <b>Graphcore:</b> Linux, monitoring and automation. <b>Aleph Cairo:</b> process automation and reconciliation. These are real employer descriptions, not guarantees of eligibility.','SmallX')]
story += [PageBreak(),P('2 | Architecture and data flow','H1X'),diagram(),P('What happens step by step','H2X')]
for n,s in enumerate([
    'The API checks an integer amount and the Idempotency-Key header. It rejects invalid requests and conflicting repeated keys.',
    'A single SQLite transaction inserts the order and an outbox event. If the outbox insert fails, the order rolls back.',
    'A separate worker claims the oldest due event using BEGIN IMMEDIATE, records an attempt and a time-limited lease.',
    'The worker writes the event to a simulated downstream inbox with UNIQUE(event_id). The same event can be retried without a second effect.',
    'Successful delivery is acknowledged. Temporary failures are retried with bounded backoff; repeated failures are dead-lettered.',
    'If a crash occurs after the inbox commit but before acknowledgement, the lease expires, recovery requeues the event and the inbox suppresses the duplicate.'
],1):story.append(P(f'<b>{n}.</b> {s}','SmallX'))
story += [P('Why it matters','H2X'),P('A common bug is saving an order and then crashing before notifying another service. The transactional outbox removes that local gap. At-least-once delivery can still replay messages, so a receiver needs durable idempotency. This lab makes both issues observable and testable.')]
story += [PageBreak(),P('3 | Actual input-to-output walkthrough','H1X'),P('The recorded demo ran on 1 November 2026 against a local SQLite file with synthetic amounts. Its two events followed these paths:')]
story += [tbl([['Event','Injected behavior','Observed result'],['Order A: 1,250 cents','Failure before delivery','retry, then delivered'],['Order B: 2,500 cents','Crash after inbox commit, before ack','lease recovered; duplicate suppressed']],[132,170,178])]
story += [Spacer(1,8),P(f'<b>Recorded demo counts:</b> {DEMO["stats"]["orders"]} orders; {DEMO["stats"]["deliveries"]} unique downstream deliveries; {DEMO["stats"]["audit_records"]} audit entries; all events ended in delivered state.')]
story += [P('Example HTTP request','H2X'),P('<font face="Courier">POST /orders</font> with <font face="Courier">Idempotency-Key: sample-001</font> and JSON <font face="Courier">{"amount_cents":1250}</font>. The response includes a generated order_id and event_id. After one worker run, <font face="Courier">GET /orders/{id}</font> returns <font face="Courier">"status":"delivered"</font>. A duplicate request with the same key and amount reuses the original order; a different amount returns HTTP 409.')]
story += [P('Key source files','H2X'),tbl([['File','Responsibility'],['db.py','SQLite schema, WAL, connection setup'],['service.py','Atomic order/outbox, leases, retries, delivery, audit'],['api.py','Validated REST API and read-only dashboard'],['cli.py','Worker loop, failure injection and deterministic demo'],['tests/','Rollback, concurrency, recovery, dead-letter, HTTP flow'],['MASTER_PROMPT.md','Research-based, pre-code implementation contract']],[135,345])]
story += [PageBreak(),P('4 | Installation, verification and limitations','H1X'),P('How to run locally','H2X')]
for s in ['<font face="Courier">python -m venv .venv</font> and activate it.', '<font face="Courier">python -m pip install -e \'[dev]\'</font>', '<font face="Courier">outbox-lab --db demo.sqlite demo</font>', '<font face="Courier">python -m pytest -q</font>', '<font face="Courier">OUTBOX_DB=demo.sqlite uvicorn outbox_lab.api:app</font>; visit <font face="Courier">/dashboard</font> and <font face="Courier">/docs</font>.']:
    story.append(P('• '+s,'SmallX'))
story += [P('Verification actually performed','H2X'),tbl([['Check','Observed outcome'],['Unit/integration/API tests','16 passed'],['Python compileall','Passed'],['Editable install','Passed with --no-build-isolation --no-deps (offline environment)'],['CLI failure/recovery demo','Passed; 2 orders, 2 unique deliveries'],['HTTP create → worker → read','HTTP 201 create, 200 read, delivered state'],['Docker Compose','Not run; Docker unavailable'],['Remote GitHub CI','Not run; repository creation blocked']],[180,300])]
story += [P('Investigated blocker','H2X'),P('Standard pip editable install initially failed because the isolated build could not resolve PyPI DNS while fetching setuptools. Installed setuptools 82.0.1 was available locally; installing without build isolation and without dependency downloads worked, followed by a successful full test rerun. Normal installation instructions remain valid on a network-enabled machine.','SmallX')]
story += [P('Important limitations','H2X'),P('No authentication, external message broker, real payments, multi-node deployment, cloud monitoring or real external recipient. The inbox shares a SQLite file with the outbox but commits separately. A simulated crash does not kill the OS process. No Docker, GitHub Actions or external performance benchmark was verified. Do not present this as a production banking system.','SmallX')]
story += [PageBreak(),P('5 | GitHub, interview and CV presentation','H1X'),P('GitHub publication status','H2X'),P('<b>Local feature branch:</b> <font face="Courier">feat/outbox-reliability-mvp</font>. <b>Verified local code commit:</b> <font face="Courier">864f5e2</font> (the explanatory PDF is generated afterward). <b>Requested remote:</b> Ahmad-Joker/outbox-reliability-lab. The repository returned 404 and no available connected action can create it; gh CLI is absent. Therefore <b>no remote push or pull request exists</b>. A recoverable source ZIP is supplied. To publish, create the dedicated repository and grant connected GitHub access; then inspect its default branch and open a feature PR.','SmallX')]
story += [P('How to explain it in an interview','H2X'),P('“I built a small fault-injection lab for the transactional outbox pattern. A single transaction saves an order and event; a separate worker claims events, retries temporary failures and records audit history. I simulated a crash after the downstream side effect but before acknowledgement. The event was replayed, yet a unique event ID prevented a second effect. I tested rollback, concurrent workers, retry exhaustion and the HTTP flow. It is a local teaching system, not a production distributed broker.”')]
story += [P('Truthful CV bullet','H2X'),P('Built a Python/FastAPI and SQLite transactional-outbox lab with idempotent event consumption, leased worker recovery, bounded retries, failure injection, automated tests and an audit dashboard; verified crash-after-delivery recovery without duplicate simulated side effects.','CalloutX')]
story += [P('Saved master prompt: key commitments','H2X'),P('The pre-code MASTER_PROMPT.md records the hiring evidence, weighted ranking, target users, user stories, architecture, exact MVP boundary, modules, edge cases, acceptance criteria, implement–test–inspect–fix loop, GitHub publication steps and explanatory PDF requirements. The actual implementation followed the contract; the GitHub stage is explicitly blocked.','SmallX')]
story += [P('Employer and technical sources (official postings unless noted)','H2X')]
sources=[('Monzo internship','https://job-boards.greenhouse.io/monzo/jobs/8156261'),('Amazon ML SDE internship','https://www.amazon.jobs/en/jobs/10588762/2027-software-dev-engineer-intern-machine-learning-uk'),('Cloudflare internship','https://job-boards.greenhouse.io/cloudflare/jobs/8245211'),('Graphcore platform internship','https://job-boards.greenhouse.io/graphcore/jobs/8894965002'),('Aleph Cairo internship','https://jobs.lever.co/aleph/f6da715d-f67e-4c25-bab1-b2e5d14709d0'),('Microservices.io: idempotent consumer (pattern reference)','https://microservices.io/patterns/communication-style/idempotent-consumer.html'),('Temporal design patterns (competing platform)','https://docs.temporal.io/design-patterns')]
for name,url in sources:
    story.append(P(f'• <link href="{url}" color="#087E85"><u>{name}</u></link>','SmallX'))

doc=SimpleDocTemplate(str(OUTPUT),pagesize=A4,leftMargin=18*mm,rightMargin=18*mm,topMargin=17*mm,bottomMargin=21*mm,title='Outbox Reliability Lab — Project Explanation',author='ChatGPT Project Builder')
doc.build(story,onFirstPage=footer,onLaterPages=footer)
print(OUTPUT)
