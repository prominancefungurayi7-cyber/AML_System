"""Build the corrected, evidence-aligned dissertation from verified project records."""
from __future__ import annotations

from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.shared import Inches, Pt, RGBColor
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml import OxmlElement
from docx.oxml.ns import qn


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "Chapters 1-5" / "Revised"
OUT.mkdir(exist_ok=True)
ART = OUT / "figures"
ART.mkdir(exist_ok=True)

FONT_PATH = Path("C:/Windows/Fonts/arial.ttf")
BOLD_PATH = Path("C:/Windows/Fonts/arialbd.ttf")
def font(size=27, bold=False):
    return ImageFont.truetype(str(BOLD_PATH if bold else FONT_PATH), size)

INK = "#20334d"
BLUE = "#2354a1"
LIGHT = "#eaf1fb"
GREEN = "#227857"

def diagram(name, heading, rows, footer=""):
    width = 1500
    step = 142
    height = 140 + len(rows) * step + (85 if footer else 30)
    im = Image.new("RGB", (width, height), "white")
    d = ImageDraw.Draw(im)
    d.text((70, 35), heading, font=font(34, True), fill=INK)
    for i, (label, body) in enumerate(rows):
        y = 105 + i * step
        d.rounded_rectangle((70, y, 1430, y + 103), radius=18, fill=LIGHT, outline=BLUE, width=3)
        d.text((103, y + 13), label, font=font(26, True), fill=BLUE)
        d.text((103, y + 54), body, font=font(23), fill=INK)
        if i + 1 < len(rows):
            d.line((750, y + 104, 750, y + 137), fill=BLUE, width=4)
            d.polygon([(739, y + 125), (761, y + 125), (750, y + 139)], fill=BLUE)
    if footer:
        d.text((70, height - 58), footer, font=font(22), fill=GREEN)
    path = ART / f"{name}.png"
    im.save(path)
    return path

gantt = Image.new("RGB", (1500, 630), "white")
gd = ImageDraw.Draw(gantt)
gd.text((50, 25), "Twelve-week development schedule", font=font(34, True), fill=INK)
for i in range(12):
    x = 425 + i * 85
    gd.text((x + 12, 80), str(i+1), font=font(24, True), fill=INK)
    gd.line((x, 112, x, 572), fill="#d5dfec", width=2)
plan = [
    ("Requirements and design", 1, 2),
    ("Simulation and history", 2, 4),
    ("V4 model integration", 4, 7),
    ("Redis and WebSockets", 6, 8),
    ("Risk and compliance workflow", 8, 10),
    ("Messaging and receipt workflow", 9, 11),
    ("Verification and presentation", 11, 12),
]
for i, (label, start, end) in enumerate(plan):
    y = 122 + i * 65
    gd.text((48, y+10), label, font=font(22), fill=INK)
    gd.rounded_rectangle((425+(start-1)*85, y, 425+end*85-10, y+43), radius=8, fill=BLUE if i < 4 else GREEN)
gd.line((425+12*85, 112, 425+12*85, 572), fill="#d5dfec", width=2)
gantt.save(ART / "figure_1_1_gantt.png")

diagram("figure_3_1_architecture", "Application architecture", [
    ("Clients", "Customer, compliance officer and administrator browsers"),
    ("Flask application", "Authenticated routes, Socket.IO events and access checks"),
    ("Transaction and analysis", "MySQL commit, history attestation, frozen V4 inference, independent rules"),
    ("Persistence and delivery", "MySQL ledger, cases and messages; Redis cross-instance event broker"),
], "Customer payments remain committed even if subsequent analysis fails.")
diagram("figure_3_2_activity", "Customer payment and AML activity", [
    ("1. Authorise", "Check session, CSRF token, request ID, wallet, amount and balance"),
    ("2. Assess rules", "Evaluate independent AML rules in the payment transaction"),
    ("3. Commit once", "Write the payment, balances and canonical capture records atomically"),
    ("4. Attest history", "Verify the source revision including the new payment"),
    ("5. Infer with V4", "Apply the frozen model after the successful commit"),
    ("6. Finalise and notify", "Save separate AI/rule evidence; publish authorised updates"),
], "On analysis failure: keep the payment, record an error and use audited nonfinancial retry.")
diagram("figure_3_3_messages", "Private message and receipt sequence", [
    ("Sender", "Authenticated send; stored in MySQL with status sent"),
    ("Recipient browser", "Receives Socket.IO event and confirms delivery: two grey ticks"),
    ("Recipient opens thread", "Read acknowledgement is stored: two blue ticks"),
    ("Sender browser", "Receives private status updates and renders the current receipt"),
], "Offline history is retained; a browser must be open for direct OS notifications.")

im = Image.new("RGB", (1500, 660), "white")
d = ImageDraw.Draw(im)
d.text((65, 28), "V4 synthetic validation confusion matrix", font=font(35, True), fill=INK)
d.text((510, 130), "Predicted normal", font=font(27, True), fill=INK)
d.text((925, 130), "Predicted suspicious", font=font(27, True), fill=INK)
for y, label in [(255, "Actual normal"), (445, "Actual suspicious")]:
    d.text((70, y), label, font=font(27, True), fill=INK)
for x, y, value, title, color in [
    (480, 203, "11,852", "True negatives", LIGHT),
    (915, 203, "118", "False positives", "#fbe9e6"),
    (480, 393, "292", "False negatives", "#fbe9e6"),
    (915, 393, "2,738", "True positives", "#e4f5eb"),
]:
    d.rounded_rectangle((x, y, x+370, y+150), radius=15, fill=color, outline=BLUE, width=3)
    d.text((x+35, y+25), value, font=font(43, True), fill=INK)
    d.text((x+35, y+89), title, font=font(25), fill=INK)
d.text((65, 605), "Validation n = 15,000; threshold = 0.50. These are synthetic development results.", font=font(23), fill=GREEN)
im.save(ART / "figure_4_1_confusion.png")


doc = Document()
section = doc.sections[0]
section.top_margin = Inches(.75)
section.bottom_margin = Inches(.7)
section.left_margin = Inches(1.1)
section.right_margin = Inches(1.0)
section.different_first_page_header_footer = True
footer = section.footer.paragraphs[0]
footer.alignment = WD_ALIGN_PARAGRAPH.CENTER
page_field = OxmlElement('w:fldSimple')
page_field.set(qn('w:instr'), 'PAGE')
footer._p.append(page_field)
normal = doc.styles["Normal"]
normal.font.name = "Times New Roman"
normal.font.size = Pt(12)
normal.paragraph_format.line_spacing = 1.5
normal.paragraph_format.space_after = Pt(6)
for style_name in ("Title", "Heading 1", "Heading 2", "Heading 3"):
    s = doc.styles[style_name]
    s.font.name = "Times New Roman"
    s.font.bold = True
    s.font.color.rgb = RGBColor(0, 0, 0)
    s.font.size = Pt(14 if style_name in ("Title", "Heading 1") else 12)
    s.paragraph_format.space_before = Pt(11)
    s.paragraph_format.space_after = Pt(5)
    s.paragraph_format.keep_with_next = True

def p(text=""):
    q = doc.add_paragraph(text)
    q.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    return q
def h(text, level=1):
    return doc.add_heading(text, level=level)
def fig(path, caption, width=5.9):
    sources = {
        "Figure 1.1": "Use the twelve-week schedule in Section 1.7; render the Gantt chart from tools/build_revised_dissertation.py (figure_1_1_gantt.png).",
        "Figure 3.1": "Use the Flask/MySQL/Redis architecture in server.py and realtime.py; use figures/figure_3_1_architecture.png, not a dashboard screenshot.",
        "Figure 3.2": "Use the customer payment route, v4_primary.py and v4_history_attestation.py to trace validation, financial commit, history verification and inference; use figure_3_2_activity.png.",
        "Figure 3.3": "Use messaging.py and server.py socket handlers to trace stored, delivered and read states; use figure_3_3_messages.png.",
        "Figure 4.1": "Use ml_v4/evidence/stage18/primary_XGB_metrics.json, the frozen synthetic Validation confusion matrix; use figure_4_1_confusion.png. Do not substitute current simulation counts.",
        "Figure 4.2": "Sign in as the selected customer, open Customer Dashboard > Recent Transactions (and Transactions for earlier pages). Capture wallet identity, dated transactions, amounts, statuses and separate AI/rule findings.",
        "Figure 4.3": "Sign in as Compliance, open the flagged-transactions list, click Review on the demonstrated transaction and capture its transaction ID, AI findings and Rule findings together.",
        "Figure 4.4": "Open Messages as Customer and Compliance in separate browser profiles. Select the matching contact and capture the account number, retained message/reply and small read-receipt ticks; repeat with Compliance and Admin.",
    }
    key = caption.split(":", 1)[0]
    if key in sources:
        p("Image capture/source instructions ? " + key + ": " + sources[key])
    q = doc.add_paragraph()
    q.alignment = WD_ALIGN_PARAGRAPH.CENTER
    q.add_run().add_picture(str(path), width=Inches(width))
    q.paragraph_format.space_after = Pt(2)
    c = doc.add_paragraph(caption)
    c.alignment = WD_ALIGN_PARAGRAPH.CENTER
    c.paragraph_format.line_spacing = 1
    c.paragraph_format.keep_with_next = False
    for run in c.runs: run.italic = True
def table(headers, rows, caption):
    t = doc.add_table(rows=1, cols=len(headers))
    t.style = "Table Grid"
    t.alignment = WD_TABLE_ALIGNMENT.CENTER
    for cell, value in zip(t.rows[0].cells, headers): cell.text = value
    for row in rows:
        for cell, value in zip(t.add_row().cells, row): cell.text = str(value)
    c = doc.add_paragraph(caption)
    c.alignment = WD_ALIGN_PARAGRAPH.CENTER
    c.paragraph_format.line_spacing = 1
    return t

title = doc.add_paragraph()
title.alignment = WD_ALIGN_PARAGRAPH.CENTER
title.add_run("REAL-TIME MOBILE-MONEY ANTI-MONEY LAUNDERING DECISION SUPPORT SYSTEM").bold = True
p("Prominance Fungurayi (R251946T) and Ashton Kahlari (R252989W)")
p("Midlands State University, Department of Computer Science · Revised chapters 1–5 · October 2026")
p("The research system supports human AML review. Its synthetic model score is a suspicious-pattern estimate; it does not establish that a crime occurred.")

h("CHAPTER 1: INTRODUCTION")
h("1.1 Introduction", 2)
p("This chapter introduced the mobile-money AML problem, research aim, five measurable process objectives, scope and twelve-week development plan. The completed system combined wallet transactions, a synthetic scenario generator, frozen V4 XGBoost inference, independent AML rules, analyst review and authenticated real-time communication.")
h("1.2 Background of the Study", 2)
p("Mobile money has expanded access to digital payments in Sub-Saharan Africa [1], while financial inclusion remains an explicit Zimbabwean policy objective [2]. The World Bank documented the role of digital payments and mobile-money accounts in financial inclusion [3]. Rapid wallet transfers and agent activity, however, create patterns that can be difficult to assess from individual payments alone. Mobile-money financial-crime research and regional intelligence reports identify a need for proportionate, evidence-led monitoring [4], [10]–[12].")
p("Machine-learning research has examined transaction monitoring and prioritisation [5], [6], [15]. Synthetic financial data can support controlled experimentation where labelled operational data are unavailable [7]. Such data also limit external validity: a classifier trained on synthetic labels must not be represented as proof of laundering or as a substitute for an analyst. The present system therefore stored AI findings separately from rule findings and retained human review.")
h("1.3 Problem Definition", 2)
p("Mobile-money activity can involve rapid repeated transfers, wallet networks and agent-mediated flows that are difficult to interpret from isolated records. Conventional transaction lists provide limited context for an investigator and may not promptly deliver a coherent explanation to authorised staff. An integrated process was required to simulate test activity, preserve the payment ledger, analyse historical behaviour, combine independent risk signals, and communicate review findings without losing transaction or message history.")
h("1.4 Aim", 2)
p("To develop and evaluate an authenticated mobile-money AML decision-support system that processes wallet transactions, identifies synthetic suspicious-pattern indicators using frozen V4 XGBoost and independent rules, and supports timely human investigation and communication.")
h("1.5 SMART Research Objectives", 2)
p("SMART means Specific, Measurable, Achievable, Relevant and Time-sensitive, as specified in the departmental guidelines. Each objective names a functional process, a measurable acceptance test and a deadline. Achievability must be checked using measured local demonstrations; targets must not be presented as achieved results. The twelve-week schedule measured completion deadlines. The demonstration times below were acceptance targets for a local panel presentation, measured from a prepared signed-in state on the same local network; they were not claims about unmeasured production service levels.")
objectives = [
    "To develop, by the end of week 4, a transaction generation module that simulates real-world mobile-money transaction patterns using existing customer histories, and to demonstrate the saving of ten valid transactions with a 70% routine and 30% suspicious-scenario mix within three minutes, while preserving wallet-balance reconciliation and unique transaction identities.",
    "To implement, by the end of week 8, a real-time engine using Redis and WebSockets that delivers an authorised transaction or alert update across two application instances within five seconds during the panel demonstration, while excluding unauthorised users.",
    "To develop, by the end of week 9, a compliance dashboard through which an authorised compliance officer can review a flagged transaction, examine its recorded AI reasoning and separate rule findings, and record an investigation outcome within two minutes during the panel demonstration.",
    "To develop, by the end of week 10, a risk-scoring mechanism that incorporates a trained and evaluated XGBoost model and independent AML rules; evaluate the model using precision, recall, F1-score and a confusion matrix on the held-out development validation partition, and demonstrate the combined risk assessment and separately identified AI and rule findings for one committed transaction within thirty seconds.",
    "To develop, by the end of week 11, a real-time professional messaging dashboard that enables bidirectional customer-compliance and compliance-administrator communication, and to demonstrate one persisted message and reply for each authorised pair, with sent, delivered and read receipts, within two minutes per pair.",
]

for i, item in enumerate(objectives, 1): p(f"{i}. {item}")
h("1.6 Limitations and Delimitations", 2)
p("Evaluation used synthetic mobile-money behaviour; neither the research labels nor the validation metrics establish performance on operational Zimbabwean transactions. The local application did not connect to a mobile-money operator, regulator or national identity system. Direct operating-system message notifications required an open authenticated browser tab and granted notification permission. The study covered Cash-In, Cash-Out and wallet-to-wallet activity, the existing wallet and agent population, and the frozen V4 feature contract. These limits were kept visible in the results rather than interpreted as negative evidence about operational transactions.")
h("1.7 Development Instruments", 2)
p("The implementation used Python and Flask for authenticated routes, Flask-SocketIO for browser events, Redis for cross-instance event publication, MySQL for committed transactions and messaging history, and the frozen XGBoost model for behavioural classification. The browser interface used HTML, CSS, JavaScript and React. The local development environment supplied controlled, non-operational test data.")
h("1.8 Work Plan", 2)
p("Table 1.1 and Figure 1.1 retained the approved twelve-week plan. The final week was reserved for verification and presentation rather than model retraining.")
table(["Weeks", "Process", "Demonstrable output"], [(f"{a}–{b}", label, "Reviewed implementation and evidence") for label,a,b in plan], "Table 1.1: Twelve-week project work plan")
fig(ART / "figure_1_1_gantt.png", "Figure 1.1: Twelve-week development Gantt chart")
h("1.9 Justification and Summary", 2)
p("A joined workflow is useful because transaction processing, model findings, independent rules and communication have different evidence and access requirements. The system makes these relationships visible to customers and analysts. Chapter 2 evaluates the supporting literature; Chapter 3 explains the methods, architecture and safeguards; Chapter 4 presents measured results; and Chapter 5 evaluates the objectives and remaining limitations.")

doc.add_page_break()
h("CHAPTER 2: LITERATURE REVIEW")
h("2.1 Introduction", 2)
p("This chapter followed an international-to-Zimbabwean review of mobile money, AML monitoring, machine learning, synthetic transaction generation and investigator communication. Sources were selected from official organisations and identifiable research publications dated within the university's ten-year limit.")
h("2.2 International and Regional Context", 2)
p("GSMA and World Bank publications describe widespread mobile-money use and its relevance to financial inclusion [1], [3]. FATF discussed opportunities and limitations of technology-assisted AML/CFT, while its work with the Egmont Group addressed digital transformation of suspicious-activity analysis [8], [9]. These sources support technology as an aid to analysts, not automatic criminal determination. INTERPOL and the Basel Institute described financial-crime exposure in African mobile-money environments [11], [12].")
h("2.3 Zimbabwean Context", 2)
p("Zimbabwe's National Financial Inclusion Strategy II set policy goals for financial service access [2]. ESAAMLG's 2024 follow-up report documented the national AML/CFT context [10]. Chitimira and Torerai analysed mobile-money regulation and financial inclusion in Zimbabwe in 2021 and 2023 [13], [14]. These works justify a local decision-support workflow while limiting claims about direct operator or regulator integration.")
h("2.4 Transaction Monitoring and Behaviour", 2)
p("Whisker and Lokanan identified risks posed by mobile-money features [4]. Jullum and colleagues examined how machine learning can reduce the volume of transactions sent for manual investigation [15]. Research on graph-based AML in Zimbabwe illustrated the value of relationships among financial entities [16]. The present system uses historical behavioural features that include structuring, network and agent context, but keeps actual source records and review decisions accessible. The model result and rule result remain separate because similar alerts can have different causes.")
h("2.4.1 Temporal and Relational Evidence", 3)
p("A transfer amount can look unremarkable when viewed alone while the sequence of related payments, recipients or agent interactions warrants review. Time-aware monitoring research therefore motivates retaining earlier transaction context and the order in which events became available [6]. Graph-oriented studies motivate examining wallet relationships rather than only the fields of an isolated payment [16]. The research system used a causal historical feature service: a transaction was analysed against a verified source revision, and model input could not include future records or private scenario labels. This matters because including subsequent transactions in an earlier prediction would give the model information unavailable at the decision time and overstate measured performance.")
p("The three research dimensions—structuring, network behaviour and agent behaviour—were analytical families rather than three separate primary models. An alert could reflect more than one dimension. Family recall therefore described how often the model predicted the positive class for members of a family; it did not prove that the model had identified the distinctive causal feature of that family. The separate rule engine supplied named rule indicators, while V4 supplied a probability and, where available, model evidence for review. The distinction helped an officer inspect a decision without presenting a rule match as an AI attribution.")
h("2.4.2 Human Review and Alert Interpretation", 3)
p("Technology-assisted AML has to balance missed suspicious activity with excessive alerts. The FATF and Egmont material describes the potential role of advanced analytics in prioritising investigation [8], [9]. A high model score is therefore a request for attention under the model's synthetic target definition, not a legal conclusion about a customer. This distinction influenced the interface: the customer history shows the operational transaction state, and the compliance interface exposes separate AI and rule findings and allows an officer to record a review outcome. A stored inference error is not recoded as a normal prediction. This design preserves the difference between a financial event, an automated indicator and a human decision.")
table(["Source", "Contribution", "Limit for this study"], [
    ("Whisker and Lokanan [4]", "Mobile-money AML threat context", "Does not validate this classifier"),
    ("Tertychnyi et al. [6]", "Timely, interpretable monitoring", "Different data and workflow"),
    ("Altman et al. [7]", "Synthetic AML benchmark method", "Synthetic labels remain constructed"),
    ("Jullum et al. [15]", "Machine-learning review prioritisation", "Banking context differs from wallets"),
    ("Ndlovu et al. [16]", "Zimbabwean graph-based AML example", "Not this local wallet population"),
], "Table 2.1: Critical comparison of the main analytical literature")
h("2.5 Synthetic Data and Real-Time Communication", 2)
p("Altman and colleagues presented a synthetic AML transaction benchmark [7]. Synthetic scenarios allow controlled comparisons but may encode assumptions that do not hold in a live payment network. The simulation module therefore distinguishes its declared 70/30 scenario mix from V4's actual prediction ratio. Socket.IO's Redis adapter demonstrates the general mechanism for cross-server event delivery [18], while browser notification permission and tab lifetime constrain device notifications [19].")
h("2.5.1 Synthetic Validity and Class Balance", 3)
p("The proportion of scenarios selected for a simulation batch is a design input. It is neither a model accuracy measure nor the proportion of transactions an independent rule engine will flag. For example, repeated routine transactions generated within a short time window can legitimately activate velocity rules even if their scenario label is routine. Conversely, an intentionally suspicious synthetic scenario might not cross the frozen V4 threshold. Evaluation must record the constructed scenario mix, the actual model predictions, the independent rule alerts and their overlap as four different quantities. The dissertation reports model metrics from the controlled development Validation set and avoids transferring its class prevalence to the local application.")
h("2.5.2 Event Delivery, Receipts and Device Notifications", 3)
p("A WebSocket event is a fast notification mechanism but is not a substitute for database persistence. Redis publication distributes private and staff events between application instances, while MySQL remains the source of message history. Receipt semantics also require care: saving a message permits a single sent tick; emitting to a socket room does not establish that a browser received it. The recipient browser must acknowledge receipt before the second grey tick is stored. Opening a visible thread is a separate event that changes the receipt to two blue ticks. The browser Notifications API requires permission and a secure context; mobile notification support also depends on service-worker notification capability [19]. These conditions shaped the implemented communication workflow.")
h("2.6 Gaps, Feasibility and Proposed Work", 2)
p("The literature does not establish that a synthetic classifier alone is sufficient for a Zimbabwean mobile-money investigation. The practical gap addressed here is the coordination of an immutable payment history, causal feature generation, separate AI and rule findings, analyst access and persistent private messages. The existing local Flask/MySQL deployment and reproducible frozen model made implementation technically feasible within the twelve-week scope. No external operator interface or production prevalence estimate was claimed.")
h("2.7 Summary", 2)
p("The reviewed work supported historical behavioural analysis, controlled synthetic testing and human review while highlighting data and deployment limits. Chapter 3 explains the implemented system and verification method.")

doc.add_page_break()
h("CHAPTER 3: METHODOLOGY")
h("3.1 Introduction and Research Design", 2)
p("The project followed an iterative implementation and verification method. Each financial payment committed once under a client request identifier; subsequent inference was a separate, auditable activity. Read-only checks established model integrity, database history authority and protected row counts before application observations. Tests used disposable stores or read-only local requests unless a financial action was explicitly controlled.")
h("3.2 System Requirements and Architecture", 2)
p("The application required customer, compliance and administrator roles; preserved balances and transaction history; separate model and rule evidence; authorised alerts and reports; and private, persistent messaging. MySQL stored financial and communication records. Flask-SocketIO carried browser events. Redis supported cross-instance event publication. Figure 3.1 records the implemented component relationship, including the post-commit analysis boundary.")
fig(ART / "figure_3_1_architecture.png", "Figure 3.1: Application architecture")
h("3.3 Transaction and History Process", 2)
p("The customer route validated authentication, request data, wallet balance and a unique client request ID. It evaluated independent AML rules before committing the payment, balances, rule evidence and canonical capture records together. The authorised canonical-history verifier then attested the new source revision before V4 inference. If the revision changed concurrently, analysis failed closed or repeated only nonfinancial verification. The committed payment was never replayed to solve an inference error. The stored failure could be revisited through the existing audited retry workflow. Figure 3.2 presents this order.")
fig(ART / "figure_3_2_activity.png", "Figure 3.2: Post-commit transaction and AML activity")
h("3.4 Simulation and Preprocessing", 2)
p("The simulator generated controlled Cash-In, Cash-Out and wallet-transfer scenarios using existing wallets. Its 70% routine and 30% suspicious target described scenario construction, not a guaranteed alert ratio or model accuracy. Each generated event had to obey the same financial and canonical-history controls as an ordinary customer transaction. The frozen V4 input contract used forty semantic fields, expanded to forty-two estimator columns by categorical encoding. Features used causal thirty-five-day history and excluded private scenario labels or future events. Train-only imputation and scaling were part of the frozen pipeline [17].")
h("3.4.1 Research Population and Partitioning", 3)
p("The V4 development record used 60,000 scored training transactions with 14,400 warm-up events and 15,000 scored Validation transactions with 3,600 warm-up events. Training contained 1,200 wallets and 96 agents across twelve synthetic communities; Validation contained 300 wallets and 24 agents across three disjoint communities. Warm-up records supplied prior history but were not scored as Validation targets. The partitions had separate entities and histories. This arrangement limited direct entity memorisation between the two development partitions, although it did not establish generalisation to real operators or to a later independent population.")
p("The forty semantic inputs included thirty-nine numeric fields and one transaction-type field. The categorical order was wallet-to-wallet, cash-in and cash-out; one-hot expansion produced forty-two numeric estimator columns. The pipeline converted declared missing sentinels to missing values and applied medians fitted only on Train. Standardisation used Train-fitted parameters. Neither account identifiers, private scenario provenance nor future transaction records entered the estimator matrix. In the application, the same frozen field order was required before inference; a missing, re-ordered or malformed vector could not be treated as a valid prediction.")
h("3.4.2 Simulation Controls", 3)
p("The V4 generator produced an explicit plan before writing events and constrained its size to supported batch counts. Its mixed mode used seven routine and three suspicious scenario assignments for a ten-event panel batch. The assignments were inputs to simulation and were not passed to the model as labels. Each payment was bound to a batch identity so a retry of an uncertain response could report a prior commit rather than creating an extra payment. The generated transactions affected demonstration-wallet balances, and committed records remained in the canonical history. This made a short controlled batch useful for panel observation while preventing a reset-and-repeat shortcut that would weaken the audit trail.")
h("3.5 Frozen Model and Risk Assessment", 2)
p("The primary classifier was the hash-verified V4 XGBoost pipeline (SHA-256 555bf1606bf0af97361e3f187575b7229645d5979a43e4c812db259dbfd2bf18). It applied a fixed suspicious-pattern score threshold of 0.50. The older Stage14 model remained as an archived asset but was bypassed in active V4 transaction inference. Independent rules continued to run. The operational risk state combined their results under the application's existing policy, while storing separate AI and rule levels and reasons. A missing or failed V4 result remained explicit rather than becoming a fabricated prediction.")
h("3.5.1 Candidate Comparison and Freeze", 3)
p("The controlled V4 development compared Logistic Regression, Random Forest, HistGradientBoosting and XGBoost under a fixed 0.50 threshold. The predeclared selection rule required minimum macro F1, suspicious recall, false-positive and domain performance gates, then preferred the best macro F1 unless an eligible model fell within a 0.005 tolerance; among close candidates, lower false-positive rate took priority. XGBoost was within that tolerance of HistGradientBoosting and had fewer false positives, though more false negatives. The decision was a documented synthetic development trade-off. The pipeline, feature architecture and threshold were frozen after this selection and were not tuned to later application outcomes.")
h("3.5.2 Post-Commit Failure Handling", 3)
p("The process separated financial finality from analytical availability. Independent rules ran inside the financial transaction and were committed with the payment. The V4 coordinator then requested a fresh canonical-history attestation and checked that the revision remained stable through feature construction and inference. An attestation failure, incompatible feature vector or model error left the payment intact and recorded an explicit analytical error or pending state. The existing audited retry mechanism could repeat history verification and inference, but it could not debit or credit a wallet again. This protects both the money trail and the credibility of the model record.")
h("3.5.3 History-Aware Transaction Generation", 3)
p("The transaction generation module includes existing and newly registered customer wallets. Before a new request, it snapshots up to one hundred recent outgoing transfers classified normal or low risk per wallet, their amount quartiles and median, and up to five preferred customer recipients. Five observations are the minimum used to describe an established sample; smaller samples remain explicitly limited. This is an empirical baseline, not a legitimacy label. Previously simulated payments can be included in this observed history and must be disclosed during interpretation. Routine senders rotate over all customers; short batches cannot cover every wallet. The mixed schedule retains 70% routine and 30% suspicious-scenario intentions. Suspicious scenarios remain deliberate stress patterns; their intended category never supplies the V4 prediction. Plans retain signed request identities and balance checks. New payments use current timestamps; immediate execution can therefore depart from historical frequency even where amounts resemble the baseline.")
h("3.6 Messaging and Notification Process", 2)
p("A role-aware contact query restricted conversations to customer–compliance and compliance–administrator pairs. A send stored message content and an unread count in MySQL before notifying the recipient's private socket room. A sent receipt represented committed storage, a delivered receipt required an authenticated recipient-browser acknowledgement, and read required opening the visible thread. Stored messages loaded by cursor pagination. Browser notifications required permission and an open application tab; Figure 3.3 depicts the receipt sequence.")
fig(ART / "figure_3_3_messages.png", "Figure 3.3: Authenticated message and receipt sequence")
h("3.6.1 Access, Persistence and Privacy", 3)
p("The contact API obtained recipients from registered user records rather than accepting arbitrary usernames from a message form. Customer contacts were limited to the assigned compliance role; compliance officers could converse with customer and administrator accounts. Every history request and socket receipt checked that the requester belonged to the conversation or was the actual message receiver. Socket events were sent to private user rooms, and the Redis broker relayed the private envelope to the matching room on each instance. The event did not replace the stored conversation: a disconnected browser could retrieve messages and current statuses after reconnecting. A recipient's browser acknowledged delivery only for messages addressed to that user, preventing a third party from falsely marking someone else's message as received.")
h("3.7 Verification Method", 2)
p("Verification checked the frozen artifact hash, feature order, threshold, canonical-history status, role restrictions, absence of financial duplicates, and separate risk evidence. Controlled browser tests exercised responsive pages and message receipt transitions without live messages. A read-only application review fingerprinted protected MySQL tables before and after page requests. Development model metrics came only from the recorded synthetic Validation partition; no sealed independent evaluation or operational performance was inferred from those results.")
h("3.8 Summary", 2)
p("The method preserved financial writes, historical authority and role boundaries while enabling V4 classification, separate rules and real-time communication. Chapter 4 reports actual observations and their limitations.")

doc.add_page_break()
h("CHAPTER 4: RESULTS AND DISCUSSION")
h("4.1 Introduction", 2)
p("This chapter reports the frozen model's recorded synthetic development results and the local application's read-only integration observations. It separates measured results from panel demonstration targets and does not present a sealed independent test as completed.")
h("4.2 Frozen V4 Development Validation", 2)
p("The V4 development comparison used 60,000 scored training transactions and 15,000 scored validation transactions, with disjoint wallet histories. XGBoost was selected under the predeclared comparison rule because its macro F1 was within 0.005 of the highest eligible candidate and its false-positive rate was lower. The chosen threshold was 0.50. These results describe a synthetic Validation population only.")
table(["Candidate", "Macro F1", "Suspicious recall", "False-positive rate"], [
    ("Logistic Regression", "0.8105", "0.5977", "0.0357"),
    ("Random Forest", "0.9461", "0.8825", "0.0127"),
    ("HistGradientBoosting", "0.9616", "0.9248", "0.0116"),
    ("V4 XGBoost", "0.9567", "0.9036", "0.0099"),
], "Table 4.1: Synthetic Validation candidate comparison at threshold 0.50")
p("For the selected V4 model, Validation accuracy was 0.9727, balanced accuracy 0.9469, suspicious precision 0.9587, ROC-AUC 0.9960 and average precision 0.9860. The confusion matrix had 11,852 true negatives, 118 false positives, 292 false negatives and 2,738 true positives (Figure 4.1). The comparatively low support and recall for some structuring families prevented a claim that all behaviours were reliably detected; S2 recall was 11/23 and S4 recall 4/16. The synthetic prevalence must not be used as an operational positive predictive value.")
fig(ART / "figure_4_1_confusion.png", "Figure 4.1: Frozen V4 synthetic Validation confusion matrix")
h("4.2.1 Behavioural-Family Diagnostics", 3)
p("Aggregate accuracy concealed material variation in family support. The frozen development card recorded the following positive predictions and denominators for selected overlapping families. Membership overlap means these counts must not be summed to obtain total true positives. Sparse families are especially uncertain because a small number of additional errors would move the observed rate considerably.")
table(["Family", "Detected / support", "Recall", "Interpretive limit"], [
    ("Structuring S1", "126 / 132", "0.955", "Support below planned minimum"),
    ("Structuring S2", "11 / 23", "0.478", "Seven subjects and seven clusters"),
    ("Structuring S3", "492 / 546", "0.901", "Support minimum met"),
    ("Structuring S4", "4 / 16", "0.250", "Sparse and weak detection"),
    ("Network N1", "77 / 101", "0.762", "Support below planned minimum"),
    ("Network N2", "381 / 429", "0.888", "Support minimum met"),
    ("Agent A1", "1,467 / 1,467", "1.000", "Dominant family; not universal evidence"),
    ("Agent A4", "151 / 222", "0.680", "Support below planned minimum"),
], "Table 4.2: Selected frozen V4 synthetic Validation family results")
p("A perfect A1 result did not cancel weaker S2 or S4 behaviour. In particular, the original development evidence recorded only four detections among sixteen S4 examples. The selection remained the frozen primary model for the local application, but the appropriate conclusion was limited: the model identified many synthetic review patterns and showed uneven family coverage. The dissertation did not claim that the weak families were corrected by later local simulation or that a high aggregate score guaranteed operational AML effectiveness.")
h("4.3 Local Application Review", 2)
p("The read-only local review identified MySQL database aml, authenticated principal aml@127.0.0.1 and server UUID d441b7bb-43f6-11f1-a2d8-0a0027000005. It observed 8,402 existing transactions, 20 users, 627 alerts and a COMPLETE_VERIFIED canonical-history gate. The before/after fingerprint of protected records was unchanged. This observation supported integrity of the local review; it did not test a new payment in this chapter.")
p("Anonymous socket access was denied, staff events stayed within staff rooms, and a private wallet-balance update reached the correct customer socket. Customer, administrator, compliance, report and messaging pages returned successfully in the checked read-only session. Both 1440-pixel and 390-pixel browser widths rendered the sampled pages without a JavaScript exception or horizontal overflow. These observations establish page and access behaviour under the tested local configuration; they are not a throughput benchmark or a production certification.")
h("4.3.1 Customer History and Operational Status", 3)
p("The customer overview presented recent payments and exposed subsequent history pages in groups of twenty-five. A transaction was included when the customer's wallet was either sender or receiver, allowing incoming transfers to appear alongside outgoing payments. The visible status grouped stored normal and low operational levels as Normal, suspicious as Suspicious, and critical, high-risk or super-suspicious levels as Super suspicious. Pending or failed analysis remained a distinct visible state. The interface also displayed transaction identity, time, type, amount, counterparty, AI finding and independent rule finding. This was a display mapping, not a modification of stored risk scores or the frozen model threshold. A disposable database test verified that twenty-seven inserted records appeared across two pages exactly once and retained separate reasons.")
h("4.3.2 Communication and Redis Verification", 3)
p("Targeted offline tests confirmed that sending stored a message before delivery, an unrelated user could not acknowledge receipt, the intended recipient could transition a sent message to delivered, and opening the thread transitioned it to read. A browser test checked that one tick was shown for sent, two grey ticks for delivered and two blue ticks for read in the time/status area. A second broker instance received a private Redis event addressed to its local user room in a nonfinancial probe. These tests verified event routing and receipt semantics without creating live customer messages. They did not measure notification success on every phone operating system or guarantee delivery after the browser was closed.")
shots = [
    ("customer-customer-1440.png", "Figure 4.2: Customer recent transaction history"),
    ("compliance-v4-alert.png", "Figure 4.3: V4 compliance alert with separate AI and rule findings"),
    ("customer-messages-1440.png", "Figure 4.4: Authenticated messaging interface"),
]
for name, caption in shots:
    src = ART / name if name == "compliance-v4-alert.png" else ROOT / ".pytest_cache" / "ui-review" / name
    if src.exists():
        original = Image.open(src).convert("RGB")
        if name == "customer-customer-1440.png":
            cropped = original.crop((0, 955, original.width, min(original.height, 1740)))
        else:
            cropped = original.crop((0, 0, original.width, min(original.height, 1050)))
        target = ART / name
        cropped.save(target)
        fig(target, caption)
h("4.3.3 Required Panel Evidence Images", 3)
p("Figure 4.5 ? insert screenshot here: sign in as Admin, open Transaction Generation and expand Customer simulation baselines. Capture wallet identities, sample counts, typical amounts and limited-history indicators before selecting Mixed scenarios. After completion, capture Latest Batch showing saved, normal, suspicious, pending and error counts. Record the elapsed time; do not describe pending analysis as complete.")
p("Figure 4.6 ? insert screenshot here: run two authorised application instances using the configured Redis broker; open staff dashboards in separate browser profiles. Capture the same transaction or alert ID on both instances with the measured delivery interval. A single dashboard does not establish cross-instance delivery.")
p("Figure 4.7 ? insert screenshot here: open the selected transaction's Compliance Review page and capture its combined operational risk score alongside the separately named V4 probability/decision and rule findings. Match the transaction ID to Figure 4.2. Do not label the combined score as the model probability.")
h("4.4 Evaluation Against the Five Objectives", 2)
table(["Objective", "Verified evidence", "Panel acceptance still required"], [
    ("1 Simulation", "Generator and canonical controls present", "Time a 10-event 70/30 scenario batch"),
    ("2 Real time", "Redis broker and staff socket isolation checked", "Time two-instance delivery under 5 s"),
    ("3 Compliance", "Alert detail and access check passed", "Record a review within 2 min"),
    ("4 Risk assessment", "Frozen V4 selected; history gate verified", "Time one committed payment under 30 s"),
    ("5 Messaging", "Stored history and receipt tests passed", "Time two-role exchange under 2 min"),
], "Table 4.3: Objective evidence and remaining panel timing checks")
p("The source code and targeted offline tests establish the message status transitions, but a device notification depends on browser permission and operating-system settings. Panel timings in Table 4.3 are acceptance criteria and should be measured live with a stopwatch. No precise timing was invented from the functional tests. The 70/30 generator composition is an input scenario target; V4 predictions and independent rule alerts may have a different distribution.")
h("4.5 Discussion and Summary", 2)
p("The strongest evidence is the reproducible synthetic Validation result and local read-only integration review. The weakest evidence is external validity: some feature families had sparse support, the model was not evaluated on operational transaction labels, and the specified panel timings have not all been observed. Chapter 5 evaluates the completed processes and recommends controlled follow-up measurement without changing the frozen model during this dissertation.")

doc.add_page_break()
h("CHAPTER 5: CONCLUSION AND RECOMMENDATIONS")
h("5.1 Summary of Results", 2)
p("The system joined wallet transaction processing with post-commit canonical-history verification, a frozen V4 XGBoost decision, independent AML rules, compliance review and stored private messaging. The selected model achieved 0.9567 macro F1 and 0.9036 suspicious-pattern recall on the synthetic Validation set; some structuring-family results remained weak. The local read-only application review showed V4 selected, canonical history verified and protected records unchanged.")
h("5.2 Conclusions by Objective", 2)
p("Objective 1 was implemented as a transaction generation module. The latest planner includes all customer wallets, samples routine amounts and preferred recipients from up to one hundred recent outgoing transfers classified normal or low risk, and identifies histories with fewer than five observations as limited. Immediate generation preserves current timestamps rather than pretending to reproduce historical timing. The new planner must be distinguished from earlier implementation measurements. Its 70/30 split described generated scenario types, while the resulting alert ratio remained a measured output of independent model and rule processes. Objective 2 was implemented through WebSocket updates and Redis-backed publication; the five-second, two-instance criterion remains a panel timing check. Objective 3 was implemented through authorised alert investigation with separate AI and rule findings. Objective 4 incorporated the previously completed XGBoost training and evaluation and was implemented through the frozen V4 plus independent-rule risk process, with failures retained as errors rather than invented predictions. Objective 5 was implemented through stored, role-restricted messaging with sent, delivered and read receipts. Exact panel execution times remain acceptance targets until timed live.")
h("5.3 Significance and Limitations", 2)
p("The contribution was an integrated decision-support workflow with clear financial and analytical boundaries. A customer can inspect the complete paged transaction history and recorded status, while an officer can examine alerts and supporting reasons. Local tests and synthetic model evaluation do not establish production AML effectiveness, and the application has no direct operator or regulator connection. Device notifications require the authenticated browser tab to remain open and permission to be granted; closed-browser push delivery requires a separate service-worker deployment.")
h("5.4 Recommendations and Future Work", 2)
p("Before operational adoption, evaluate the frozen approach against independently labelled, representative data under appropriate governance; measure family-specific errors, calibration, response time and alert burden; and conduct security, accessibility and two-instance deployment testing. A controlled panel run should time each SMART objective and record actual values beside the limits specified in Chapter 1. Future notification work may add service-worker push if background delivery is required. Model changes should follow a new validation protocol rather than altering the frozen dissertation artifact silently.")
h("5.5 Final Conclusion", 2)
p("The developed local system met the functional integration aim in its controlled environment and kept model findings, rules and analyst decisions distinct. Its research evidence supports demonstration of the five processes, subject to the stated live timing checks and synthetic-data limitations.")

doc.add_page_break()
h("REFERENCES")
refs = [
    "[1] GSMA, The State of the Industry Report on Mobile Money 2025, 2025. https://www.gsma.com/solutions-and-impact/connectivity-for-good/mobile-for-development/gsma_resources/the-state-of-the-industry-report-on-mobile-money-2025/",
    "[2] Reserve Bank of Zimbabwe, National Financial Inclusion Strategy II 2022–2026, 2022. https://www.rbz.co.zw/documents/BLSS/FinancialInclusion/Zimbabwe_National_Financial_Inclusion_Strategy_II_2022-2026.pdf",
    "[3] A. Demirgüç-Kunt, L. Klapper, D. Singer and S. Ansar, The Global Findex Database 2021, World Bank, 2022. https://microdata.worldbank.org/collections/global-findex",
    "[4] J. Whisker and M. E. Lokanan, ‘Anti-money laundering and counter-terrorist financing threats posed by mobile money,’ Journal of Money Laundering Control, vol. 22, no. 1, pp. 158–172, 2019, doi: 10.1108/JMLC-10-2017-0061.",
    "[5] R. I. T. Jensen and A. Iosifidis, ‘Fighting money laundering with statistics and machine learning,’ IEEE Access, vol. 11, 2023, doi: 10.1109/ACCESS.2023.3239549.",
    "[6] P. Tertychnyi, M. Godgildieva, M. Dumas and M. Ollikainen, ‘Time-aware and interpretable predictive monitoring system for anti-money laundering,’ Machine Learning with Applications, vol. 8, 100306, 2022, doi: 10.1016/j.mlwa.2022.100306.",
    "[7] E. R. Altman et al., ‘Realistic synthetic financial transactions for anti-money laundering models,’ Advances in Neural Information Processing Systems, vol. 36, 2023. https://proceedings.neurips.cc/paper_files/paper/2023/hash/5f38404edff6f3f642d6fa5892479c42-Abstract-Datasets_and_Benchmarks.html",
    "[8] Financial Action Task Force, Opportunities and Challenges of New Technologies for AML/CFT, 2021. https://www.fatf-gafi.org/en/publications/Digitaltransformation/Digital-transformation.html",
    "[9] Financial Action Task Force and Egmont Group, Digital Transformation of AML/CFT for Operational Agencies, 2021. https://www.fatf-gafi.org/content/dam/fatf-gafi/guidance/Digital-Transformation-executive-summary.pdf.coredownload.pdf",
    "[10] ESAAMLG, Zimbabwe: 10th Enhanced Follow-Up Report and 4th Technical Compliance Re-Rating, Apr. 2024. https://www.esaamlg.org/reports/Zimbabwe_FUR-April%202024.pdf",
    "[11] A. Dornbierer, Quick Guide 18: Mobile Money and Financial Crime, Basel Institute on Governance, 2020. https://baselgovernance.org/resources/publications/quick-guide-18-mobile-money-and-financial-crime/",
    "[12] INTERPOL, Mobile Money and Organised Crime in Africa, 2020. https://www.interpol.int/content/download/15457/file/2020%252007%252015%2520PUBLIC%2520VERSION%2520-%2520Strategic%2520Analysis%2520Report%2520-Mobile%2520Money%2520in%2520Africa%25202020.pdf",
    "[13] H. Chitimira and E. Torerai, ‘The nexus between mobile money regulation, innovative technology and the promotion of financial inclusion in Zimbabwe,’ Potchefstroom Electronic Law Journal, vol. 24, 2021, doi: 10.17159/1727-3781/2021/v24i0a10739.",
    "[14] H. Chitimira and E. Torerai, ‘Policy implications and mobile money regulatory approaches to promote financial inclusion of the poor in Zimbabwe after the COVID-19 pandemic,’ De Jure Law Journal, vol. 56, pp. 241–260, 2023, doi: 10.17159/2225-7160/2023/v56a17.",
    "[15] M. Jullum, A. Løland, R. B. Huseby, G. Ånonsen and J. Lorentzen, ‘Detecting money laundering transactions with machine learning,’ Journal of Money Laundering Control, 2020, doi: 10.1108/JMLC-07-2019-0055.",
    "[16] B. Ndlovu et al., ‘Developing a graph-based machine learning model for identifying money laundering networks associated with sanctioned entities in a bank in Zimbabwe,’ Indonesian Journal of Innovation and Applied Sciences, vol. 6, no. 1, pp. 35–59, 2026, doi: 10.47540/ijias.v6i1.2306.",
    "[17] XGBoost Developers, XGBoost Python API Reference, accessed Oct. 2026. https://xgboost.readthedocs.io/en/stable/python/python_api.html",
    "[18] Socket.IO, Redis Adapter Documentation, accessed Oct. 2026. https://socket.io/docs/v4/redis-adapter/",
    "[19] Mozilla, Notifications API, accessed Oct. 2026. https://developer.mozilla.org/en-US/docs/Web/API/Notifications_API",
]
for ref in refs: p(ref)

doc.save(OUT / "Revised Dissertation Chapters 1-5.docx")
print(OUT / "Revised Dissertation Chapters 1-5.docx")
