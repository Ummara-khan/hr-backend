"""
generate_policies.py
--------------------
Creates all 12 company policy documents as:
  • .txt  — plain text with structured formatting
  • .pdf  — formatted PDF with headers, numbered lists, tables, contact directories

Run: python generate_policies.py
Output: writes into ../data/  (relative to this script's location)
"""

import os
import sys
from pathlib import Path
from datetime import date

from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    HRFlowable, PageBreak, ListFlowable, ListItem,
)
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT

# ── Paths ──────────────────────────────────────────────────────────────────
SCRIPT_DIR = Path(__file__).parent
DATA_DIR   = SCRIPT_DIR.parent / "data"
TODAY      = date.today().strftime("%B %d, %Y")

# ── Colour palette ─────────────────────────────────────────────────────────
C_NAVY   = colors.HexColor("#1e3a5f")
C_INDIGO = colors.HexColor("#4f46e5")
C_TEAL   = colors.HexColor("#0d9488")
C_AMBER  = colors.HexColor("#d97706")
C_LIGHT  = colors.HexColor("#f1f5f9")
C_BORDER = colors.HexColor("#cbd5e1")
C_WHITE  = colors.white
C_BLACK  = colors.HexColor("#1e293b")
C_MUTED  = colors.HexColor("#64748b")
C_RED    = colors.HexColor("#dc2626")
C_GREEN  = colors.HexColor("#16a34a")

DEPT_COLORS = {
    "garment":   C_INDIGO,
    "denim":     C_TEAL,
    "corporate": C_AMBER,
}

# ══════════════════════════════════════════════════════════════════════════════
#  STYLES
# ══════════════════════════════════════════════════════════════════════════════

def make_styles(accent):
    s = getSampleStyleSheet()

    def add(name, **kw):
        s.add(ParagraphStyle(name=name, **kw))

    add("DocTitle",
        fontSize=22, leading=28, textColor=C_WHITE,
        fontName="Helvetica-Bold", alignment=TA_CENTER, spaceAfter=4)
    add("DocSub",
        fontSize=10, leading=14, textColor=colors.HexColor("#cbd5e1"),
        fontName="Helvetica", alignment=TA_CENTER, spaceAfter=2)
    add("SectionHead",
        fontSize=13, leading=18, textColor=C_WHITE,
        fontName="Helvetica-Bold", alignment=TA_LEFT,
        spaceBefore=14, spaceAfter=4,
        backColor=accent, leftIndent=-12, rightIndent=-12,
        borderPad=6)
    add("SubHead",
        fontSize=10, leading=14, textColor=accent,
        fontName="Helvetica-Bold", spaceBefore=8, spaceAfter=3)
    add("Body",
        fontSize=9, leading=14, textColor=C_BLACK,
        fontName="Helvetica", spaceAfter=4)
    add("BulletItem",
        fontSize=9, leading=14, textColor=C_BLACK,
        fontName="Helvetica", leftIndent=16, spaceAfter=2,
        bulletIndent=4)
    add("Note",
        fontSize=8.5, leading=13, textColor=C_MUTED,
        fontName="Helvetica-Oblique", spaceAfter=4)
    add("ContactName",
        fontSize=9, leading=13, textColor=C_BLACK,
        fontName="Helvetica-Bold")
    add("ContactInfo",
        fontSize=8.5, leading=13, textColor=C_MUTED,
        fontName="Helvetica")
    add("Warning",
        fontSize=9, leading=13, textColor=C_RED,
        fontName="Helvetica-Bold", spaceAfter=4)
    add("Footer",
        fontSize=7.5, leading=11, textColor=C_MUTED,
        fontName="Helvetica", alignment=TA_CENTER)
    return s


# ══════════════════════════════════════════════════════════════════════════════
#  PDF HELPERS
# ══════════════════════════════════════════════════════════════════════════════

def header_banner(title, subtitle, accent, styles):
    """Coloured header block at top of document."""
    data = [[
        Paragraph(title, styles["DocTitle"]),
        Paragraph(subtitle, styles["DocSub"]),
    ]]
    t = Table(data, colWidths=["100%"])
    t.setStyle(TableStyle([
        ("BACKGROUND",  (0,0), (-1,-1), accent),
        ("TOPPADDING",  (0,0), (-1,-1), 18),
        ("BOTTOMPADDING",(0,0),(-1,-1), 14),
        ("LEFTPADDING", (0,0), (-1,-1), 20),
        ("RIGHTPADDING",(0,0), (-1,-1), 20),
        ("BOX",         (0,0), (-1,-1), 0.5, colors.HexColor("#334155")),
    ]))
    return t


def section_header(text, styles):
    return Paragraph(f"&nbsp;&nbsp;{text}", styles["SectionHead"])


def numbered_list(items, styles, start=1):
    """Properly numbered list."""
    els = []
    for i, item in enumerate(items, start):
        els.append(Paragraph(f"<b>{i}.</b>&nbsp;&nbsp;{item}", styles["BulletItem"]))
    return els


def bullet_list(items, styles, symbol="•"):
    els = []
    for item in items:
        els.append(Paragraph(f"{symbol}&nbsp;&nbsp;{item}", styles["BulletItem"]))
    return els


def contact_table(contacts, styles, accent):
    """
    contacts = list of dicts with keys:
      role, name, phone, ext, email (all optional except role)
    """
    header = [
        Paragraph("<b>Role / Department</b>", styles["Body"]),
        Paragraph("<b>Name</b>", styles["Body"]),
        Paragraph("<b>Phone / Ext</b>", styles["Body"]),
        Paragraph("<b>Email</b>", styles["Body"]),
    ]
    rows = [header]
    for c in contacts:
        rows.append([
            Paragraph(c.get("role", ""), styles["Body"]),
            Paragraph(c.get("name", "—"), styles["Body"]),
            Paragraph(c.get("phone", "") + (" (Ext. " + c["ext"] + ")" if c.get("ext") else ""), styles["Body"]),
            Paragraph(c.get("email", "—"), styles["Body"]),
        ])
    t = Table(rows, colWidths=[4.5*cm, 4*cm, 4.5*cm, 5.5*cm])
    t.setStyle(TableStyle([
        ("BACKGROUND",    (0,0), (-1,0), accent),
        ("TEXTCOLOR",     (0,0), (-1,0), C_WHITE),
        ("ROWBACKGROUNDS",(0,1), (-1,-1), [C_WHITE, C_LIGHT]),
        ("GRID",          (0,0), (-1,-1), 0.4, C_BORDER),
        ("TOPPADDING",    (0,0), (-1,-1), 5),
        ("BOTTOMPADDING", (0,0), (-1,-1), 5),
        ("LEFTPADDING",   (0,0), (-1,-1), 6),
        ("RIGHTPADDING",  (0,0), (-1,-1), 6),
        ("FONTSIZE",      (0,0), (-1,-1), 8.5),
    ]))
    return t


def penalty_table(rows_data, styles, accent):
    """Two-column table for violation → penalty mapping."""
    header = [Paragraph("<b>Violation / Offence</b>", styles["Body"]),
              Paragraph("<b>Penalty / Action</b>", styles["Body"])]
    rows = [header] + [[Paragraph(a, styles["Body"]), Paragraph(b, styles["Body"])] for a,b in rows_data]
    t = Table(rows, colWidths=[9*cm, 9.5*cm])
    t.setStyle(TableStyle([
        ("BACKGROUND",    (0,0), (-1,0), accent),
        ("TEXTCOLOR",     (0,0), (-1,0), C_WHITE),
        ("ROWBACKGROUNDS",(0,1), (-1,-1), [C_WHITE, C_LIGHT]),
        ("GRID",          (0,0), (-1,-1), 0.4, C_BORDER),
        ("TOPPADDING",    (0,0), (-1,-1), 5),
        ("BOTTOMPADDING", (0,0), (-1,-1), 5),
        ("LEFTPADDING",   (0,0), (-1,-1), 6),
        ("RIGHTPADDING",  (0,0), (-1,-1), 6),
        ("FONTSIZE",      (0,0), (-1,-1), 8.5),
    ]))
    return t


def info_box(text, styles, color=None):
    """Lightly shaded info/note box."""
    bg = color or C_LIGHT
    t = Table([[Paragraph(text, styles["Body"])]], colWidths=["100%"])
    t.setStyle(TableStyle([
        ("BACKGROUND",    (0,0), (-1,-1), bg),
        ("BOX",           (0,0), (-1,-1), 0.5, C_BORDER),
        ("TOPPADDING",    (0,0), (-1,-1), 8),
        ("BOTTOMPADDING", (0,0), (-1,-1), 8),
        ("LEFTPADDING",   (0,0), (-1,-1), 10),
        ("RIGHTPADDING",  (0,0), (-1,-1), 10),
    ]))
    return t


def build_pdf(path, story_fn, dept, doc_title, doc_subtitle):
    accent = DEPT_COLORS.get(dept, C_NAVY)
    styles = make_styles(accent)
    out    = Path(path)
    out.parent.mkdir(parents=True, exist_ok=True)

    doc = SimpleDocTemplate(
        str(out),
        pagesize=A4,
        leftMargin=2*cm, rightMargin=2*cm,
        topMargin=1.5*cm, bottomMargin=2*cm,
        title=doc_title,
        author="HR Department",
    )

    story = []
    story.append(header_banner(doc_title, doc_subtitle, accent, styles))
    story.append(Spacer(1, 16))
    story_fn(story, styles, accent)

    # Footer note
    story.append(Spacer(1, 20))
    story.append(HRFlowable(width="100%", thickness=0.5, color=C_BORDER))
    story.append(Spacer(1, 4))
    story.append(Paragraph(
        f"CONFIDENTIAL — For internal use only. &nbsp;|&nbsp; Generated: {TODAY} &nbsp;|&nbsp; "
        f"HR Department, {dept.title()} Division",
        styles["Footer"]
    ))

    doc.build(story)
    print(f"  ✓ PDF: {out.relative_to(DATA_DIR.parent)}")


# ══════════════════════════════════════════════════════════════════════════════
#  TXT WRITER
# ══════════════════════════════════════════════════════════════════════════════

def write_txt(path, content):
    out = Path(path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(content, encoding="utf-8")
    print(f"  ✓ TXT: {out.relative_to(DATA_DIR.parent)}")


# ══════════════════════════════════════════════════════════════════════════════
#  POLICY DEFINITIONS  (12 policies)
# ══════════════════════════════════════════════════════════════════════════════

# ────────────────────────────────────────────────────
#  GARMENT  HR
# ────────────────────────────────────────────────────

GARMENT_HR_TXT = """
================================================================================
  GARMENT DEPARTMENT — HUMAN RESOURCES POLICY
  Document No.: GRM-HR-001 | Version: 3.0 | Effective: January 1, 2024
================================================================================

1. WORKING HOURS & SHIFTS
   1.1  Standard production shift: 08:00 – 17:00 (Monday to Saturday)
   1.2  Night shift (bonus-eligible): 22:00 – 06:00 (+20% of basic salary)
   1.3  Break schedule:
        • Lunch: 30 minutes (13:00 – 13:30)
        • Tea break: 10 minutes each (10:30 and 15:30)
   1.4  Grace period: 10 minutes after shift start
   1.5  Late arrivals beyond grace period × 3 in any month = ½-day leave deduction

2. ATTENDANCE & TIMEKEEPING
   2.1  Biometric punch-in/out mandatory at every shift start and end.
   2.2  Failure to punch = "absent" unless manager overrides with written memo.
   2.3  Habitual absenteeism defined as ≥ 6 unauthorised absences per quarter.
   2.4  Employees must notify line supervisor at least 1 hour before shift if unable to attend.
   2.5  Emergency notifications accepted via:
        • SMS to supervisor's mobile
        • WhatsApp to departmental group
        • Phone call to Production Control Room: +92-21-3456-7000 (Ext. 101)

3. DRESS CODE & PERSONAL PROTECTIVE EQUIPMENT
   3.1  All production floor staff must wear:
        (a) Company-issued uniform (2 sets provided annually)
        (b) Steel-toed safety shoes (replaced every 18 months at company cost)
        (c) Hairnet when within 3 metres of sewing machinery
   3.2  Jewellery, rings, bracelets, and loose accessories are PROHIBITED on the floor.
   3.3  Office-based garment staff: business casual; no open-toed footwear.

4. PERFORMANCE APPRAISAL
   4.1  Annual review cycle: November 1 – November 30 each year.
   4.2  Rating scale:
        5 – Outstanding    | Bonus: 20% of annual basic
        4 – Exceeds        | Bonus: 15%
        3 – Meets          | Bonus: 10%
        2 – Needs Improvement | Bonus: 5%
        1 – Unsatisfactory | No bonus; PIP initiated
   4.3  KPIs measured:
        • Output quantity vs. daily target
        • Defect / rejection rate
        • Attendance percentage
        • Safety compliance score
        • Teamwork (peer + supervisor rating)
   4.4  Employees rated 1 for two consecutive years may be reassigned or terminated.

5. TRAINING & DEVELOPMENT
   5.1  Minimum 40 hours of training per employee per calendar year.
   5.2  Mandatory courses (all floor staff):
        (a) Workplace Safety & First Aid — 8 hours (January each year)
        (b) Quality Standards — 4 hours (April and October)
        (c) Machinery Safety — 4 hours (on joining; refresher every 2 years)
   5.3  External training bond: employees sponsored for courses costing > PKR 20,000
        must serve a minimum of 12 months post-training.

6. GRIEVANCE PROCEDURE
   6.1  Step 1: Raise with Line Supervisor (resolution within 5 working days)
   6.2  Step 2: Escalate to HR Business Partner (resolution within 10 working days)
   6.3  Step 3: Final appeal to General Manager – Garment (decision within 15 working days)
   6.4  Grievances may be submitted in writing on Form GRM-HR-GRV-01 or verbally.
   6.5  No retaliation against any employee who raises a legitimate grievance.

7. DISCIPLINARY PROCEDURE
   7.1  Minor offences (e.g., repeated tardiness, dress code violation):
        Step A → Verbal Warning (documented)
        Step B → Written Warning (valid 12 months)
        Step C → Final Written Warning
        Step D → Termination with notice
   7.2  Major offences (e.g., theft, workplace violence, fraud) → Immediate suspension
        pending inquiry; may result in summary dismissal.
   7.3  Disciplinary hearings must be held within 7 working days of alleged offence.

8. KEY CONTACTS — GARMENT HR
   ┌─────────────────────────────┬──────────────────┬─────────────────────────────┐
   │ Role                        │ Phone            │ Email                       │
   ├─────────────────────────────┼──────────────────┼─────────────────────────────┤
   │ HR Manager – Garment        │ +92-21-3456-7010 │ hr.garment@company.com      │
   │ HR Officer (Recruitment)    │ +92-21-3456-7011 │ recruit.garment@company.com │
   │ Payroll Officer             │ Ext. 205         │ payroll@company.com         │
   │ Production Control Room     │ +92-21-3456-7000 │ pcr@company.com             │
   │ Security Gate (Main)        │ Ext. 100         │ security@company.com        │
   │ Employee Helpline (24/7)    │ 0800-12345       │ helpline@company.com        │
   └─────────────────────────────┴──────────────────┴─────────────────────────────┘

================================================================================
  CONFIDENTIAL — For internal use only. HR Dept, Garment Division. v3.0 2024
================================================================================
""".strip()


def garment_hr_pdf(story, styles, accent):
    S = styles
    story += [
        section_header("1. WORKING HOURS & SHIFTS", S),
        Spacer(1,4),
        *numbered_list([
            "Standard production shift: <b>08:00 – 17:00</b> (Monday to Saturday)",
            "Night shift (bonus-eligible): <b>22:00 – 06:00</b> — employees receive +20% shift allowance on basic salary",
            "Break schedule: Lunch 30 min (13:00–13:30) | Tea break 10 min at 10:30 and 15:30",
            "Grace period: 10 minutes after shift start before late arrival is recorded",
            "Late arrivals beyond grace period occurring <b>3× in any month</b> = half-day leave deduction",
        ], S),
        Spacer(1,8),

        section_header("2. ATTENDANCE & TIMEKEEPING", S),
        Spacer(1,4),
        Paragraph("<b>2.1</b> Biometric punch-in/out is mandatory at every shift start and end.", S["Body"]),
        Paragraph("<b>2.2</b> Failure to punch = 'absent' unless line manager overrides with written memo.", S["Body"]),
        Paragraph("<b>2.3</b> Habitual absenteeism = ≥ 6 unauthorised absences per quarter.", S["Body"]),
        Paragraph("<b>2.4</b> Emergency absence notifications accepted via:", S["Body"]),
        *bullet_list([
            "SMS to your Line Supervisor's mobile",
            "WhatsApp to departmental group",
            "Phone call — Production Control Room: <b>+92-21-3456-7000 (Ext. 101)</b>",
        ], S),
        Spacer(1,8),

        section_header("3. PERFORMANCE APPRAISAL", S),
        Spacer(1,4),
        Paragraph("Annual review cycle: <b>November 1 – 30</b> each year. Bonus structure:", S["Body"]),
        Spacer(1,4),
    ]

    rating_data = [
        [Paragraph("<b>Rating</b>", S["Body"]), Paragraph("<b>Description</b>", S["Body"]), Paragraph("<b>Bonus</b>", S["Body"])],
        [Paragraph("5", S["Body"]), Paragraph("Outstanding", S["Body"]), Paragraph("20% of annual basic", S["Body"])],
        [Paragraph("4", S["Body"]), Paragraph("Exceeds Expectations", S["Body"]), Paragraph("15%", S["Body"])],
        [Paragraph("3", S["Body"]), Paragraph("Meets Expectations", S["Body"]), Paragraph("10%", S["Body"])],
        [Paragraph("2", S["Body"]), Paragraph("Needs Improvement", S["Body"]), Paragraph("5%", S["Body"])],
        [Paragraph("1", S["Body"]), Paragraph("Unsatisfactory", S["Body"]), Paragraph("No bonus; PIP initiated", S["Body"])],
    ]
    rt = Table(rating_data, colWidths=[2*cm, 8*cm, 8.5*cm])
    rt.setStyle(TableStyle([
        ("BACKGROUND",    (0,0), (-1,0), accent),
        ("TEXTCOLOR",     (0,0), (-1,0), C_WHITE),
        ("ROWBACKGROUNDS",(0,1), (-1,-1), [C_WHITE, C_LIGHT]),
        ("GRID",          (0,0), (-1,-1), 0.4, C_BORDER),
        ("TOPPADDING",    (0,0), (-1,-1), 5),
        ("BOTTOMPADDING", (0,0), (-1,-1), 5),
        ("LEFTPADDING",   (0,0), (-1,-1), 6),
        ("ALIGN",         (0,0), (0,-1), "CENTER"),
    ]))
    story += [rt, Spacer(1,8)]

    story += [
        section_header("4. GRIEVANCE PROCEDURE", S),
        Spacer(1,4),
        *numbered_list([
            "<b>Step 1:</b> Raise with Line Supervisor — resolution within 5 working days",
            "<b>Step 2:</b> Escalate to HR Business Partner — resolution within 10 working days",
            "<b>Step 3:</b> Final appeal to General Manager, Garment — decision within 15 working days",
        ], S),
        info_box("⚠ No retaliation is permitted against any employee who raises a legitimate grievance. "
                 "Violations of this rule are treated as major misconduct.", S),
        Spacer(1,8),

        section_header("5. KEY CONTACTS — GARMENT HR DEPARTMENT", S),
        Spacer(1,6),
        contact_table([
            {"role": "HR Manager – Garment",      "name": "Ms. Amna Siddiqui",  "phone": "+92-21-3456-7010", "email": "hr.garment@company.com"},
            {"role": "HR Officer (Recruitment)",  "name": "Mr. Usman Ali",       "phone": "+92-21-3456-7011", "email": "recruit.garment@company.com"},
            {"role": "Payroll Officer",            "name": "Ms. Rabia Khan",      "phone": "", "ext": "205",   "email": "payroll@company.com"},
            {"role": "Production Control Room",   "name": "Duty Officer",         "phone": "+92-21-3456-7000","ext": "101", "email": "pcr@company.com"},
            {"role": "Security Gate (Main)",      "name": "Security Desk",        "phone": "", "ext": "100",   "email": "security@company.com"},
            {"role": "Employee Helpline (24/7)",  "name": "Helpline",             "phone": "0800-12345",       "email": "helpline@company.com"},
        ], S, accent),
    ]


# ────────────────────────────────────────────────────
#  GARMENT  MEDICAL
# ────────────────────────────────────────────────────

GARMENT_MED_TXT = """
================================================================================
  GARMENT DEPARTMENT — MEDICAL & HEALTH POLICY
  Document No.: GRM-MED-001 | Version: 3.1 | Effective: January 1, 2024
================================================================================

1. MEDICAL COVERAGE LIMITS
   ┌─────────────────────────────────────┬─────────────────────┐
   │ Category                            │ Annual Limit (PKR)  │
   ├─────────────────────────────────────┼─────────────────────┤
   │ Employee (Inpatient)                │ 150,000             │
   │ Spouse                              │  75,000             │
   │ Each Child (max 2)                  │  50,000             │
   │ Maternity (per delivery, max 2)     │  50,000             │
   │ Dental (Employee)                   │  15,000             │
   │ Optical (Employee)                  │   8,000             │
   └─────────────────────────────────────┴─────────────────────┘

2. PANEL HOSPITALS & CLINICS
   2.1  Karachi
        (a) City Hospital                 — 021-3580-1234
        (b) Al-Khidmat Medical Centre     — 021-3480-5678
        (c) Aga Khan University Hospital  — 021-3486-4527
        (d) South City Hospital           — 021-3431-0000
   2.2  Lahore
        (a) Shaukat Khanum Cancer Centre  — 042-3590-5000
        (b) Doctors Hospital              — 042-3591-0000
   2.3  Islamabad
        (a) Shifa International Hospital  — 051-846-3000
   2.4  Approved Dental Clinics
        • SmilePlus Dental Care           — 021-3542-2222
        • DentaCare Clinics               — 021-3512-3456

3. REIMBURSEMENT PROCESS
   3.1  Claims must be submitted within 30 days of treatment date.
   3.2  Required documents (ALL must be original):
        (a) Completed Reimbursement Form GRM-MED-01 (available from HR)
        (b) Doctor's prescription / referral letter
        (c) All original receipts (pharmacy, lab, hospital)
        (d) Lab / radiology reports (where applicable)
        (e) Discharge summary for inpatient claims
   3.3  Processing timelines:
        • Standard claims (< PKR 20,000): 15 working days
        • Large claims (≥ PKR 20,000): requires HR Manager approval; 20 working days
        • Emergency / occupational claims: 7 working days
   3.4  Payment credited directly to employee's registered bank account.
   3.5  Incomplete submissions are returned within 5 working days with a deficiency list.

4. SICK LEAVE PROCEDURE
   4.1  Notify line supervisor within the first hour of shift.
   4.2  Medical certificate required for > 2 consecutive sick days.
   4.3  > 10 sick days in a calendar year triggers mandatory HR review meeting.

5. EMERGENCY CONTACTS — MEDICAL
   ┌──────────────────────────────┬──────────────────┬───────────────┐
   │ Service                      │ Number           │ Available     │
   ├──────────────────────────────┼──────────────────┼───────────────┤
   │ Company Doctor (On-site)     │ Ext. 300         │ 08:00 – 18:00 │
   │ First Aid Room               │ Ext. 301         │ 24 / 7        │
   │ Ambulance (Company)          │ +92-21-3456-7999 │ 24 / 7        │
   │ Emergency (Edhi)             │ 115              │ 24 / 7        │
   │ Rescue 1122                  │ 1122             │ 24 / 7        │
   │ Aga Khan Hospital ER         │ 021-3486-4545    │ 24 / 7        │
   │ Medical HR Officer           │ +92-21-3456-7012 │ 09:00 – 17:00 │
   └──────────────────────────────┴──────────────────┴───────────────┘

6. EXCLUSIONS
   6.1  Cosmetic or elective procedures (unless medically certified as necessary)
   6.2  Self-inflicted injuries
   6.3  Treatment outside Pakistan without prior written company approval
   6.4  Experimental treatments not approved by PMDC
   6.5  Outpatient psychiatric treatment beyond 6 approved sessions per year

================================================================================
  CONFIDENTIAL. HR Dept, Garment Division. Doc No. GRM-MED-001 v3.1 (2024)
================================================================================
""".strip()


def garment_med_pdf(story, styles, accent):
    S = styles
    story += [
        section_header("1. MEDICAL COVERAGE LIMITS", S),
        Spacer(1,4),
    ]
    cov_data = [
        [Paragraph("<b>Category</b>", S["Body"]), Paragraph("<b>Annual Limit (PKR)</b>", S["Body"])],
        ["Employee (Inpatient)", "150,000"],
        ["Spouse", "75,000"],
        ["Each Child (max 2 children)", "50,000"],
        ["Maternity (per delivery, max 2 in service)", "50,000"],
        ["Dental (Employee only)", "15,000"],
        ["Optical (Employee only)", "8,000"],
    ]
    cov_data = [[Paragraph(str(r[0]), S["Body"]), Paragraph(str(r[1]), S["Body"])] for r in cov_data]
    ct = Table(cov_data, colWidths=[12*cm, 6.5*cm])
    ct.setStyle(TableStyle([
        ("BACKGROUND",    (0,0), (-1,0), accent),
        ("TEXTCOLOR",     (0,0), (-1,0), C_WHITE),
        ("ROWBACKGROUNDS",(0,1), (-1,-1), [C_WHITE, C_LIGHT]),
        ("GRID",          (0,0), (-1,-1), 0.4, C_BORDER),
        ("TOPPADDING",    (0,0), (-1,-1), 5),
        ("BOTTOMPADDING", (0,0), (-1,-1), 5),
        ("LEFTPADDING",   (0,0), (-1,-1), 6),
        ("ALIGN",         (1,0), (1,-1), "RIGHT"),
    ]))
    story += [ct, Spacer(1,8)]

    story += [
        section_header("2. APPROVED PANEL HOSPITALS", S),
        Spacer(1,4),
        Paragraph("<b>Karachi</b>", S["SubHead"]),
        *numbered_list([
            "City Hospital &nbsp;&mdash;&nbsp; <b>021-3580-1234</b>",
            "Al-Khidmat Medical Centre &nbsp;&mdash;&nbsp; <b>021-3480-5678</b>",
            "Aga Khan University Hospital &nbsp;&mdash;&nbsp; <b>021-3486-4527</b>",
            "South City Hospital &nbsp;&mdash;&nbsp; <b>021-3431-0000</b>",
        ], S),
        Paragraph("<b>Lahore</b>", S["SubHead"]),
        *numbered_list([
            "Shaukat Khanum Cancer Centre &nbsp;&mdash;&nbsp; <b>042-3590-5000</b>",
            "Doctors Hospital &nbsp;&mdash;&nbsp; <b>042-3591-0000</b>",
        ], S),
        Spacer(1,8),

        section_header("3. REIMBURSEMENT PROCESS", S),
        Spacer(1,4),
        info_box("Claims must be submitted within <b>30 days</b> of treatment date. Late claims are NOT processed.", S),
        Spacer(1,6),
        Paragraph("<b>Required documents (ALL originals):</b>", S["Body"]),
        *numbered_list([
            "Completed Reimbursement Form <b>GRM-MED-01</b> (collect from HR office or HR portal)",
            "Doctor's prescription / specialist referral letter",
            "All original receipts — pharmacy, laboratory, hospital",
            "Lab / radiology reports (where applicable)",
            "Hospital discharge summary (for inpatient / admitted cases)",
        ], S),
        Spacer(1,6),
        Paragraph("<b>Processing Timelines:</b>", S["Body"]),
        *bullet_list([
            "Standard claims (under PKR 20,000): <b>15 working days</b>",
            "Large claims (PKR 20,000 and above): requires HR Manager approval — <b>20 working days</b>",
            "Emergency / occupational health claims: <b>7 working days</b> (priority track)",
        ], S, "→"),
        Spacer(1,8),

        section_header("4. EMERGENCY MEDICAL CONTACTS", S),
        Spacer(1,6),
        contact_table([
            {"role": "Company Doctor (On-site)",  "name": "Dr. Sana Mirza",     "phone": "", "ext": "300",        "email": "doctor@company.com"},
            {"role": "First Aid Room",             "name": "First Aider on Duty","phone": "", "ext": "301",        "email": "firstaid@company.com"},
            {"role": "Company Ambulance (24/7)",  "name": "Dispatch",            "phone": "+92-21-3456-7999",      "email": "ambulance@company.com"},
            {"role": "Edhi Ambulance",             "name": "National",            "phone": "115",                   "email": "—"},
            {"role": "Rescue 1122",                "name": "National",            "phone": "1122",                  "email": "—"},
            {"role": "Aga Khan Hospital ER",      "name": "Emergency Dept",      "phone": "021-3486-4545",         "email": "—"},
            {"role": "Medical HR Officer",        "name": "Mr. Farhan Qureshi",  "phone": "+92-21-3456-7012",      "email": "medical.hr@company.com"},
        ], S, accent),
    ]


# ────────────────────────────────────────────────────
#  GARMENT  LEAVE
# ────────────────────────────────────────────────────

GARMENT_LEAVE_TXT = """
================================================================================
  GARMENT DEPARTMENT — LEAVE POLICY
  Document No.: GRM-LV-001 | Version: 2.5 | Effective: January 1, 2024
================================================================================

1. LEAVE ENTITLEMENT SUMMARY
   ┌────────────────────────┬──────────┬────────────────────────────────────────┐
   │ Leave Type             │ Days/Yr  │ Notes                                  │
   ├────────────────────────┼──────────┼────────────────────────────────────────┤
   │ Casual Leave           │    14    │ Cannot carry forward; up to 7 encashable│
   │ Sick Leave             │    10    │ Medical cert needed after day 2         │
   │ Earned / Annual Leave  │    18    │ Accrues after 1 year; max 30-day hold   │
   │ Maternity Leave        │    84    │ 12 weeks paid; max 2 in service         │
   │ Paternity Leave        │     7    │ Within 30 days of birth                 │
   │ Bereavement (Spouse)   │     5    │ Death certificate required              │
   │ Bereavement (Parent)   │     3    │ Death certificate required              │
   │ Hajj Leave (once)      │    30    │ Unpaid; apply 2 months in advance       │
   │ Study / Exam Leave     │     5    │ Enrolment proof required                │
   └────────────────────────┴──────────┴────────────────────────────────────────┘

2. CASUAL LEAVE
   2.1  14 days credited on January 1 each year (pro-rated for new joiners at 1.17 days/month).
   2.2  Maximum 3 consecutive casual days without department head approval.
   2.3  Unused balance LAPSES on December 31; cannot be carried forward.
   2.4  Encashment: Up to 7 unused days may be encashed at year-end at daily basic rate.

3. EARNED / ANNUAL LEAVE
   3.1  Accrual: 1.5 days per completed calendar month of service (18 days per year).
   3.2  Eligibility: After completing 12 months of continuous service.
   3.3  Application: Minimum 15 days advance notice required.
   3.4  Minimum usage: At least 10 consecutive days must be taken per year.
   3.5  Maximum accumulation: 30 days; any balance above 30 lapses at year-end.
   3.6  Encashment: Full balance encashable at resignation, retirement, or death.

4. MATERNITY & PATERNITY LEAVE
   4.1  Maternity: 84 days (12 weeks) paid leave.
        • May commence 4 weeks before expected delivery date.
        • Available after completing 6 months of continuous service.
        • Maximum 2 maternity benefits in entire employment.
   4.2  Paternity: 7 days paid leave.
        • Must be taken within 30 days of child's birth.
        • Maximum 2 times during employment.
        • Proof required: Birth certificate or hospital document.
   4.3  Nursing mothers: 2 × 30-minute nursing breaks per shift for 6 months post-delivery.

5. PUBLIC HOLIDAYS (2024)
   5.1  The following gazetted holidays are observed:
        No.  Holiday                          Date(s)
        1    Kashmir Day                      February 5
        2    Pakistan Day                     March 23
        3    Labour Day                       May 1
        4    Eid ul Fitr                      3 days (as per moon sighting)
        5    Independence Day                 August 14
        6    Eid ul Adha                      3 days (as per moon sighting)
        7    Ashura                           2 days (as per moon sighting)
        8    Eid Milad un Nabi               1 day (as per moon sighting)
        9    Quaid-e-Azam Day                December 25
        10   Christmas                        December 25 (for Christian employees)
   5.2  If production requirements mandate work on a public holiday, compensation = double pay + 1 substitute holiday.

6. LEAVE APPLICATION PROCEDURE
   6.1  All applications via Form GRM-LV-01 or the online HR portal.
   6.2  Emergency leave: Notify supervisor by phone/SMS immediately; submit form next working day.
   6.3  Unapproved absence for > 3 consecutive days may be treated as voluntary abandonment.
   6.4  Leave status queries: hr.garment@company.com | Ext. 205

================================================================================
  CONFIDENTIAL. HR Dept, Garment Division. Doc No. GRM-LV-001 v2.5 (2024)
================================================================================
""".strip()


def garment_leave_pdf(story, styles, accent):
    S = styles
    story += [
        section_header("1. LEAVE ENTITLEMENT SUMMARY TABLE", S),
        Spacer(1,6),
    ]
    lt_data = [
        [Paragraph("<b>Leave Type</b>", S["Body"]), Paragraph("<b>Days / Year</b>", S["Body"]), Paragraph("<b>Key Conditions</b>", S["Body"])],
        ["Casual Leave",         "14", "Cannot carry forward; up to 7 days encashable"],
        ["Sick Leave",           "10", "Medical cert required after 2 consecutive days"],
        ["Earned / Annual Leave","18", "Accrues after 1 yr; max 30-day accumulation"],
        ["Maternity Leave",      "84", "12 weeks paid; max 2 in entire service"],
        ["Paternity Leave",       "7", "Within 30 days of child's birth; max 2 times"],
        ["Bereavement (Spouse/Child)", "5", "Death certificate required"],
        ["Bereavement (Parent/Sibling)","3","Death certificate required"],
        ["Hajj Leave (once)",    "30", "Unpaid; apply 2 months in advance"],
        ["Study / Exam Leave",    "5", "Enrolment or exam admission proof required"],
    ]
    lt_data = [[Paragraph(str(r[0]), S["Body"]), Paragraph(str(r[1]), S["Body"]), Paragraph(str(r[2]), S["Body"])] for r in lt_data]
    lt = Table(lt_data, colWidths=[5.5*cm, 3*cm, 10*cm])
    lt.setStyle(TableStyle([
        ("BACKGROUND",    (0,0), (-1,0), accent),
        ("TEXTCOLOR",     (0,0), (-1,0), C_WHITE),
        ("ROWBACKGROUNDS",(0,1), (-1,-1), [C_WHITE, C_LIGHT]),
        ("GRID",          (0,0), (-1,-1), 0.4, C_BORDER),
        ("TOPPADDING",    (0,0), (-1,-1), 5),
        ("BOTTOMPADDING", (0,0), (-1,-1), 5),
        ("LEFTPADDING",   (0,0), (-1,-1), 6),
        ("ALIGN",         (1,0), (1,-1), "CENTER"),
    ]))
    story += [lt, Spacer(1,10)]

    story += [
        section_header("2. PUBLIC HOLIDAYS 2024", S),
        Spacer(1,4),
    ]
    ph_data = [
        [Paragraph("<b>No.</b>", S["Body"]), Paragraph("<b>Holiday</b>", S["Body"]), Paragraph("<b>Date / Period</b>", S["Body"])],
        ["1","Kashmir Day","February 5"],
        ["2","Pakistan Day","March 23"],
        ["3","Labour Day","May 1"],
        ["4","Eid ul Fitr (3 days)","As per moon sighting (approx. April 9–11)"],
        ["5","Independence Day","August 14"],
        ["6","Eid ul Adha (3 days)","As per moon sighting (approx. June 16–18)"],
        ["7","Ashura (2 days)","As per moon sighting"],
        ["8","Eid Milad un Nabi","As per moon sighting"],
        ["9","Quaid-e-Azam Day","December 25"],
        ["10","Christmas","December 25 (for Christian employees)"],
    ]
    ph_data = [[Paragraph(str(r[0]), S["Body"]), Paragraph(str(r[1]), S["Body"]), Paragraph(str(r[2]), S["Body"])] for r in ph_data]
    ph = Table(ph_data, colWidths=[1.5*cm, 7*cm, 10*cm])
    ph.setStyle(TableStyle([
        ("BACKGROUND",    (0,0), (-1,0), accent),
        ("TEXTCOLOR",     (0,0), (-1,0), C_WHITE),
        ("ROWBACKGROUNDS",(0,1), (-1,-1), [C_WHITE, C_LIGHT]),
        ("GRID",          (0,0), (-1,-1), 0.4, C_BORDER),
        ("TOPPADDING",    (0,0), (-1,-1), 5),
        ("BOTTOMPADDING", (0,0), (-1,-1), 5),
        ("LEFTPADDING",   (0,0), (-1,-1), 6),
    ]))
    story += [ph, Spacer(1,8)]

    story += [
        section_header("3. MATERNITY & PATERNITY LEAVE", S),
        Spacer(1,4),
        Paragraph("<b>Maternity Leave (Female Employees):</b>", S["SubHead"]),
        *numbered_list([
            "84 days (12 weeks) of paid maternity leave",
            "Leave may commence 4 weeks before expected delivery date",
            "Available after completing 6 months of continuous service",
            "Maximum 2 maternity benefits during entire period of employment",
            "Nursing mothers entitled to 2 × 30-minute breaks per shift for 6 months post-delivery",
        ], S),
        Paragraph("<b>Paternity Leave (Male Employees):</b>", S["SubHead"]),
        *numbered_list([
            "7 days paid paternity leave upon birth of child",
            "Must be taken within 30 days of child's birth",
            "Available maximum 2 times during employment",
            "Required proof: Birth certificate or hospital birth notification document",
        ], S),
    ]


# ────────────────────────────────────────────────────
#  GARMENT  SECURITY
# ────────────────────────────────────────────────────

GARMENT_SEC_TXT = """
================================================================================
  GARMENT DEPARTMENT — SECURITY POLICY
  Document No.: GRM-SEC-001 | Version: 2.0 | Effective: January 1, 2024
================================================================================

1. ACCESS CONTROL
   1.1  All employees must display company ID badges visibly at all times on premises.
   1.2  Sharing of access cards or IDs is strictly prohibited.
   1.3  Lost ID cards must be reported within 1 hour to Security Desk (Ext. 100).
   1.4  Replacement card fee: PKR 200; issued within 24 hours.
   1.5  Zone classifications:
        Zone A — Office & Admin (Green badge)
        Zone B — General Production Floor (Blue badge)
        Zone C — Cutting & Pattern Area (Yellow badge)
        Zone D — Sample & Design Room (Red badge — restricted)

2. VISITOR MANAGEMENT
   2.1  All visitors must register at Main Gate and collect a visitor pass.
   2.2  Original CNIC or passport required for visitor registration.
   2.3  Visitors must be escorted by a host employee at all times.
   2.4  Visitor pass must be surrendered on exit.
   2.5  Photography and video recording by visitors: PROHIBITED without written approval.
   2.6  Pre-approved vendor visits only; approval from Procurement department required.

3. MATERIAL MOVEMENT GATE PASS PROCEDURE
   3.1  No material, fabric, or finished goods may leave premises without an approved Gate Pass.
   3.2  Gate Pass requirements:
        (a) Description and quantity of material
        (b) Signature of Department Head
        (c) Co-signature of Security Supervisor
        (d) Reference to Purchase Order or Delivery Challan
   3.3  Material found exiting without a Gate Pass will be confiscated; employee responsible will face disciplinary action.
   3.4  Gate Pass request form: GRM-SEC-GP-01 (available at Security Desk)

4. EMERGENCY CONTACTS — SECURITY & SAFETY
   ┌──────────────────────────────┬──────────────────┬───────────────┐
   │ Service                      │ Number           │ Available     │
   ├──────────────────────────────┼──────────────────┼───────────────┤
   │ Security Gate (Main)         │ Ext. 100         │ 24 / 7        │
   │ Security Gate (Back)         │ Ext. 102         │ 24 / 7        │
   │ Security Manager             │ +92-21-3456-7050 │ 08:00 – 22:00 │
   │ Security Manager (Emer.)     │ +92-331-1234567  │ 24 / 7        │
   │ Fire Brigade (Karachi)       │ 16               │ 24 / 7        │
   │ Police (Emergency)           │ 15               │ 24 / 7        │
   │ Rescue 1122                  │ 1122             │ 24 / 7        │
   │ Factory Manager (On-call)    │ +92-300-9876543  │ After hours   │
   └──────────────────────────────┴──────────────────┴───────────────┘

5. PROHIBITED ITEMS ON PREMISES
   5.1  The following are STRICTLY PROHIBITED:
        (a) Weapons of any kind (firearms, bladed weapons, etc.)
        (b) Alcohol or narcotics
        (c) Gambling materials
        (d) Personal mobile phones on the production floor during working hours
        (e) Outside food in production areas
        (f) Unauthorised recording equipment
   5.2  Security may conduct random checks of personal belongings.

6. DISCIPLINARY ACTIONS FOR SECURITY VIOLATIONS
   ┌─────────────────────────────────────────┬─────────────────────────────────┐
   │ Violation                               │ Action                          │
   ├─────────────────────────────────────────┼─────────────────────────────────┤
   │ Sharing access card                     │ Written warning + card suspended│
   │ Allowing tailgating                     │ Written warning                 │
   │ Material removal without Gate Pass      │ Final warning or termination    │
   │ Theft of company property               │ Immediate termination + FIR     │
   │ Assault on security personnel           │ Immediate termination + FIR     │
   │ Tampering with CCTV or alarms           │ Final warning or termination    │
   │ Bringing prohibited items               │ Written warning (1st offence)   │
   └─────────────────────────────────────────┴─────────────────────────────────┘

================================================================================
  CONFIDENTIAL. HR Dept, Garment Division. Doc No. GRM-SEC-001 v2.0 (2024)
================================================================================
""".strip()


def garment_sec_pdf(story, styles, accent):
    S = styles
    story += [
        section_header("1. ACCESS CONTROL & ZONE CLASSIFICATION", S),
        Spacer(1,4),
        *numbered_list([
            "All employees must display company ID badges <b>visibly</b> at all times on premises",
            "Sharing of access cards or IDs is <b>strictly prohibited</b>",
            "Lost ID cards must be reported within <b>1 hour</b> to Security Desk (Ext. 100)",
            "Replacement card fee: PKR 200 | Issued within 24 hours",
        ], S),
        Spacer(1,4),
    ]
    zone_data = [
        [Paragraph("<b>Zone</b>", S["Body"]), Paragraph("<b>Badge Colour</b>", S["Body"]), Paragraph("<b>Access Area</b>", S["Body"])],
        ["Zone A", "Green",  "Office & Administration"],
        ["Zone B", "Blue",   "General Production Floor"],
        ["Zone C", "Yellow", "Cutting & Pattern Area"],
        ["Zone D", "Red",    "Sample & Design Room (Restricted)"],
    ]
    zone_data = [[Paragraph(str(r[0]), S["Body"]), Paragraph(str(r[1]), S["Body"]), Paragraph(str(r[2]), S["Body"])] for r in zone_data]
    zt = Table(zone_data, colWidths=[3*cm, 4*cm, 11.5*cm])
    zt.setStyle(TableStyle([
        ("BACKGROUND",    (0,0), (-1,0), accent),
        ("TEXTCOLOR",     (0,0), (-1,0), C_WHITE),
        ("ROWBACKGROUNDS",(0,1), (-1,-1), [C_WHITE, C_LIGHT]),
        ("GRID",          (0,0), (-1,-1), 0.4, C_BORDER),
        ("TOPPADDING",    (0,0), (-1,-1), 5),
        ("BOTTOMPADDING", (0,0), (-1,-1), 5),
        ("LEFTPADDING",   (0,0), (-1,-1), 6),
    ]))
    story += [zt, Spacer(1,8)]

    story += [
        section_header("2. MATERIAL MOVEMENT — GATE PASS PROCEDURE", S),
        Spacer(1,4),
        info_box("⚠ No material, fabric, or finished goods may leave the premises without an approved Gate Pass. "
                 "Use Form <b>GRM-SEC-GP-01</b> (available at Security Desk, Ext. 100).", S),
        Spacer(1,6),
        Paragraph("<b>Required information on every Gate Pass:</b>", S["Body"]),
        *numbered_list([
            "Description and quantity of material / goods",
            "Signature of Department Head",
            "Co-signature of Security Supervisor",
            "Reference Purchase Order number or Delivery Challan number",
        ], S),
        Spacer(1,8),

        section_header("3. SECURITY VIOLATIONS & PENALTIES", S),
        Spacer(1,6),
        penalty_table([
            ("Sharing access card with another person",       "Written warning + card temporarily suspended"),
            ("Allowing tailgating through access door",       "Written warning"),
            ("Removing material without Gate Pass",           "Final warning or termination (value-dependent)"),
            ("Theft of company property",                     "Immediate termination + FIR filed with police"),
            ("Assault on security or any employee",           "Immediate termination + FIR filed with police"),
            ("Tampering with CCTV cameras or alarms",         "Final warning or termination"),
            ("Bringing prohibited items onto premises",       "Written warning (1st offence); Final warning (repeat)"),
            ("Unauthorised photography / video recording",    "Written warning + device confiscated pending review"),
        ], S, accent),
        Spacer(1,8),

        section_header("4. EMERGENCY CONTACTS — SECURITY & SAFETY", S),
        Spacer(1,6),
        contact_table([
            {"role": "Security Gate (Main)",       "name": "Duty Guard",            "phone": "", "ext": "100",        "email": "security@company.com"},
            {"role": "Security Gate (Back)",       "name": "Duty Guard",            "phone": "", "ext": "102",        "email": "security@company.com"},
            {"role": "Security Manager",           "name": "Mr. Tariq Mehmood",    "phone": "+92-21-3456-7050",      "email": "security.mgr@company.com"},
            {"role": "Security Manager (After hrs)","name": "Mr. Tariq Mehmood",   "phone": "+92-331-1234567",       "email": "—"},
            {"role": "Fire Brigade (Karachi)",     "name": "National",              "phone": "16",                    "email": "—"},
            {"role": "Police (Emergency)",         "name": "National",              "phone": "15",                    "email": "—"},
            {"role": "Rescue 1122",                "name": "National",              "phone": "1122",                  "email": "—"},
            {"role": "Factory Manager (On-call)",  "name": "Mr. Imran Hassan",      "phone": "+92-300-9876543",       "email": "factory.mgr@company.com"},
        ], S, accent),
    ]


# ────────────────────────────────────────────────────
#  DENIM  HR  (shorter but still rich)
# ────────────────────────────────────────────────────

DENIM_HR_TXT = """
================================================================================
  DENIM DEPARTMENT — HUMAN RESOURCES POLICY
  Document No.: DNM-HR-001 | Version: 2.1 | Effective: January 1, 2024
================================================================================

1. WORKING HOURS & SHIFTS
   1.1  Shift A (Washing & Finishing):  07:00 – 16:00
   1.2  Shift B (Chemical Processing): 16:00 – 00:00
   1.3  Overtime: 1.5× hourly for first 2 hours; 2.0× beyond 2 hours.
   1.4  Maximum overtime: 12 hours/week, 48 hours/month.

2. GRADING STRUCTURE
   Grade A — Master Washer, Laser Operator, Senior QC Inspector
   Grade B — Machine Operator, Dyer, Fabric Cutter
   Grade C — Helper, Ironing Operator, Packing Staff

   Skill premiums (monthly, in addition to basic salary):
   • Laser operation:    PKR 5,000
   • Chemical mixing:    PKR 4,000
   • QC Inspection:      PKR 3,000
   • General skill:      PKR 2,000

3. CHEMICAL SAFETY TRAINING (MANDATORY)
   3.1  All chemical-handling employees must complete:
        (a) Hazmat Handling Certification — 16 hours (on joining)
        (b) MSDS (Material Safety Data Sheet) Workshop — 4 hours (every 6 months)
        (c) Respiratory Protection Training — 8 hours (sandblasting & laser staff only)
   3.2  Employees CANNOT operate chemical stations until 2-week supervised training is completed and signed off by the Safety Officer.
   3.3  Training records maintained in personnel file and available to employee on request.

4. KEY CONTACTS — DENIM HR
   ┌────────────────────────────┬──────────────────┬──────────────────────────────┐
   │ Role                       │ Phone            │ Email                        │
   ├────────────────────────────┼──────────────────┼──────────────────────────────┤
   │ HR Manager – Denim         │ +92-21-3456-7020 │ hr.denim@company.com         │
   │ Safety Officer (EHS)       │ +92-21-3456-7021 │ ehs@company.com              │
   │ Chemical Store In-charge   │ Ext. 400         │ chemstore@company.com        │
   │ Training Coordinator       │ Ext. 401         │ training@company.com         │
   │ Employee Helpline (24/7)   │ 0800-12345       │ helpline@company.com         │
   └────────────────────────────┴──────────────────┴──────────────────────────────┘

================================================================================
  CONFIDENTIAL. HR Dept, Denim Division. Doc No. DNM-HR-001 v2.1 (2024)
================================================================================
""".strip()


def denim_hr_pdf(story, styles, accent):
    S = styles
    story += [
        section_header("1. GRADE STRUCTURE & SKILL PREMIUMS", S),
        Spacer(1,4),
    ]
    gd = [
        [Paragraph("<b>Grade</b>", S["Body"]), Paragraph("<b>Roles</b>", S["Body"]), Paragraph("<b>Skill Premium (PKR/month)</b>", S["Body"])],
        ["Grade A", "Master Washer, Laser Operator, Senior QC Inspector", "3,000 – 5,000"],
        ["Grade B", "Machine Operator, Dyer, Fabric Cutter",              "2,000 – 4,000"],
        ["Grade C", "Helper, Ironing Operator, Packing Staff",            "—"],
    ]
    gd = [[Paragraph(str(r[0]), S["Body"]), Paragraph(str(r[1]), S["Body"]), Paragraph(str(r[2]), S["Body"])] for r in gd]
    gt = Table(gd, colWidths=[3*cm, 9*cm, 6.5*cm])
    gt.setStyle(TableStyle([
        ("BACKGROUND",    (0,0), (-1,0), accent),
        ("TEXTCOLOR",     (0,0), (-1,0), C_WHITE),
        ("ROWBACKGROUNDS",(0,1), (-1,-1), [C_WHITE, C_LIGHT]),
        ("GRID",          (0,0), (-1,-1), 0.4, C_BORDER),
        ("TOPPADDING",    (0,0), (-1,-1), 5),
        ("BOTTOMPADDING", (0,0), (-1,-1), 5),
        ("LEFTPADDING",   (0,0), (-1,-1), 6),
    ]))
    story += [gt, Spacer(1,8)]

    story += [
        section_header("2. MANDATORY CHEMICAL SAFETY TRAINING", S),
        Spacer(1,4),
        info_box("⚠ <b>IMPORTANT:</b> Employees may NOT operate chemical stations until a 2-week supervised "
                 "training is completed and signed off by the Safety Officer.", S),
        Spacer(1,6),
        *numbered_list([
            "<b>Hazmat Handling Certification</b> — 16 hours (completed on joining)",
            "<b>MSDS Workshop</b> — 4 hours every 6 months (Material Safety Data Sheets)",
            "<b>Respiratory Protection Training</b> — 8 hours (sandblasting & laser operators only)",
        ], S),
        Spacer(1,8),

        section_header("3. KEY CONTACTS — DENIM HR & SAFETY", S),
        Spacer(1,6),
        contact_table([
            {"role": "HR Manager – Denim",        "name": "Ms. Zara Hussain",     "phone": "+92-21-3456-7020",   "email": "hr.denim@company.com"},
            {"role": "Safety Officer (EHS)",       "name": "Mr. Ali Rehman",       "phone": "+92-21-3456-7021",   "email": "ehs@company.com"},
            {"role": "Chemical Store In-charge",  "name": "Mr. Saeed Khan",       "phone": "", "ext": "400",     "email": "chemstore@company.com"},
            {"role": "Training Coordinator",      "name": "Ms. Nadia Bashir",     "phone": "", "ext": "401",     "email": "training@company.com"},
            {"role": "Employee Helpline (24/7)",  "name": "Helpline",              "phone": "0800-12345",         "email": "helpline@company.com"},
        ], S, accent),
    ]


# ────────────────────────────────────────────────────
#  DENIM  MEDICAL
# ────────────────────────────────────────────────────

DENIM_MED_TXT = """
================================================================================
  DENIM DEPARTMENT — MEDICAL & HEALTH POLICY
  Document No.: DNM-MED-001 | Version: 2.3 | Effective: January 1, 2024
================================================================================

1. ENHANCED MEDICAL COVERAGE (Chemical Exposure Risk)
   Coverage limit per employee: PKR 200,000/year (vs standard PKR 150,000)
   Dependents: Spouse PKR 100,000 | Each child (max 2): PKR 60,000
   Chemical-exposure illnesses: NO sub-limit (fully covered)
   Cancer screening (annual, high-risk roles): Fully covered

2. QUARTERLY HEALTH MONITORING — MANDATORY
   All chemical-handling staff must attend quarterly health monitoring.
   Tests included:
     (a) Lung function test (spirometry)
     (b) Skin allergy screening (patch test)
     (c) Complete blood count (CBC)
     (d) Liver function tests (LFTs)
     (e) Vision and hearing assessment
   Employees with abnormal results are automatically reassigned pending specialist review.

3. CHEMICAL EMERGENCY PROTOCOL
   3.1  In case of chemical splash to skin or eyes:
        STEP 1: Flush affected area with running water for minimum 15 minutes.
        STEP 2: Proceed immediately to First Aid Room (Ext. 501).
        STEP 3: Notify supervisor and complete Exposure Report within 2 hours (Form DNM-EHS-01).
        STEP 4: Medical follow-up appointment mandatory within 24 hours.
   3.2  All chemical exposures are logged in the Exposure Registry maintained by EHS.
   3.3  Repeat exposures trigger mandatory workstation risk assessment.

4. EMERGENCY CONTACTS — DENIM MEDICAL & EHS
   ┌──────────────────────────────┬──────────────────┬───────────────┐
   │ Service                      │ Number           │ Available     │
   ├──────────────────────────────┼──────────────────┼───────────────┤
   │ First Aid Room               │ Ext. 501         │ 24 / 7        │
   │ EHS Officer (Chemical)       │ +92-21-3456-7021 │ 07:00 – 00:00 │
   │ EHS Officer (Emergency)      │ +92-333-9876543  │ 24 / 7        │
   │ Company Ambulance            │ +92-21-3456-7999 │ 24 / 7        │
   │ Occupational Health Doctor   │ Ext. 502         │ 08:00 – 17:00 │
   │ Dermatology Panel — JPMC     │ 021-9921-5740    │ Office hours  │
   │ Pulmonology — AKU Hospital   │ 021-3486-4527    │ Office hours  │
   │ Edhi Ambulance               │ 115              │ 24 / 7        │
   └──────────────────────────────┴──────────────────┴───────────────┘

================================================================================
  CONFIDENTIAL. HR Dept, Denim Division. Doc No. DNM-MED-001 v2.3 (2024)
================================================================================
""".strip()


def denim_med_pdf(story, styles, accent):
    S = styles
    story += [
        section_header("1. ENHANCED MEDICAL COVERAGE LIMITS", S),
        Spacer(1,4),
    ]
    cov = [
        [Paragraph("<b>Category</b>", S["Body"]), Paragraph("<b>Annual Limit (PKR)</b>", S["Body"])],
        ["Employee (all conditions incl. chemical-related)", "200,000"],
        ["Chemical-exposure illnesses", "NO sub-limit (fully covered)"],
        ["Spouse", "100,000"],
        ["Each Child (max 2)", "60,000"],
        ["Cancer screening – high-risk roles (annual)", "Fully covered"],
        ["Dermatological treatment (work-related)", "Fully covered"],
    ]
    cov = [[Paragraph(str(r[0]), S["Body"]), Paragraph(str(r[1]), S["Body"])] for r in cov]
    ct = Table(cov, colWidths=[12*cm, 6.5*cm])
    ct.setStyle(TableStyle([
        ("BACKGROUND",    (0,0), (-1,0), accent),
        ("TEXTCOLOR",     (0,0), (-1,0), C_WHITE),
        ("ROWBACKGROUNDS",(0,1), (-1,-1), [C_WHITE, C_LIGHT]),
        ("GRID",          (0,0), (-1,-1), 0.4, C_BORDER),
        ("TOPPADDING",    (0,0), (-1,-1), 5),
        ("BOTTOMPADDING", (0,0), (-1,-1), 5),
        ("LEFTPADDING",   (0,0), (-1,-1), 6),
    ]))
    story += [ct, Spacer(1,8)]

    story += [
        section_header("2. CHEMICAL EMERGENCY PROTOCOL", S),
        Spacer(1,4),
        info_box("⚠ <b>In case of chemical splash to skin or eyes — act IMMEDIATELY:</b>", S),
        Spacer(1,4),
        *numbered_list([
            "<b>FLUSH</b> affected area with running water for a <b>minimum of 15 minutes</b>",
            "<b>PROCEED</b> immediately to First Aid Room (Ext. 501) — do not delay",
            "<b>NOTIFY</b> supervisor and complete Exposure Report within 2 hours using <b>Form DNM-EHS-01</b>",
            "<b>FOLLOW UP</b> — mandatory medical appointment within 24 hours of exposure",
        ], S),
        Spacer(1,8),

        section_header("3. EMERGENCY CONTACTS — DENIM MEDICAL & EHS", S),
        Spacer(1,6),
        contact_table([
            {"role": "First Aid Room",              "name": "First Aider on Duty",  "phone": "", "ext": "501",        "email": "firstaid@company.com"},
            {"role": "EHS Officer (Chemical)",      "name": "Mr. Ali Rehman",       "phone": "+92-21-3456-7021",      "email": "ehs@company.com"},
            {"role": "EHS Officer (After Hours)",   "name": "Mr. Ali Rehman",       "phone": "+92-333-9876543",       "email": "ehs@company.com"},
            {"role": "Company Ambulance (24/7)",   "name": "Dispatch",              "phone": "+92-21-3456-7999",      "email": "ambulance@company.com"},
            {"role": "Occupational Health Doctor", "name": "Dr. Sameer Javed",      "phone": "", "ext": "502",        "email": "occ.health@company.com"},
            {"role": "Dermatology — JPMC",         "name": "Panel Clinic",          "phone": "021-9921-5740",         "email": "—"},
            {"role": "Pulmonology — AKU Hospital", "name": "Panel Clinic",          "phone": "021-3486-4527",         "email": "—"},
            {"role": "Edhi Ambulance (National)",  "name": "Edhi Foundation",       "phone": "115",                   "email": "—"},
        ], S, accent),
    ]


# ────────────────────────────────────────────────────
#  DENIM  LEAVE + SECURITY  (condensed for brevity but still rich)
# ────────────────────────────────────────────────────

DENIM_LEAVE_TXT = """
================================================================================
  DENIM DEPARTMENT — LEAVE POLICY
  Document No.: DNM-LV-001 | Version: 2.2 | Effective: January 1, 2024
================================================================================

1. LEAVE SUMMARY
   ┌──────────────────────────┬──────────┬─────────────────────────────────┐
   │ Leave Type               │ Days/Yr  │ Notes                           │
   ├──────────────────────────┼──────────┼─────────────────────────────────┤
   │ Casual Leave             │    14    │ Cannot carry forward             │
   │ Sick Leave               │    10    │ Unlimited for chemical illness   │
   │ Earned Leave             │    18    │ Accrues after 1 yr              │
   │ Hazardous Duty Leave     │     4    │ Extra 1 day/quarter for chem.   │
   │ Maternity Leave          │    84    │ 12 weeks paid                   │
   │ Paternity Leave          │     7    │ Within 30 days of birth         │
   │ Bereavement (Spouse)     │     5    │                                 │
   │ Bereavement (Parent)     │     3    │                                 │
   │ Bereavement (In-laws)    │     2    │                                 │
   │ Hajj Leave (once)        │    30    │ Unpaid                          │
   └──────────────────────────┴──────────┴─────────────────────────────────┘

2. HAZARDOUS DUTY LEAVE (DENIM-SPECIFIC)
   2.1  Employees working in sandblasting, laser, or heavy chemical areas earn 1 additional leave day per quarter.
   2.2  Total: 4 extra hazard leave days per year.
   2.3  Hazard leave must be taken within the same quarter; it is NOT encashable and does NOT carry forward.

3. SICK LEAVE — SPECIAL PROVISION
   3.1  For chemical-related occupational illness: sick leave is unlimited pending medical specialist review.
   3.2  First 3 months at full pay; next 3 months at 50% pay.
   3.3  Employee must submit specialist medical report to HR every 4 weeks during extended sick leave.

4. LEAVE APPLICATION CONTACTS
   HR System email: denim.hr@company.com
   HR Extension:    Ext. 203
   HR Office:       Room 8, Admin Block, Denim Division

================================================================================
  CONFIDENTIAL. HR Dept, Denim Division. Doc No. DNM-LV-001 v2.2 (2024)
================================================================================
""".strip()


def denim_leave_pdf(story, styles, accent):
    S = styles
    story += [section_header("1. LEAVE ENTITLEMENT TABLE", S), Spacer(1,4)]
    lt = [
        [Paragraph("<b>Leave Type</b>", S["Body"]), Paragraph("<b>Days/Yr</b>", S["Body"]), Paragraph("<b>Notes</b>", S["Body"])],
        ["Casual Leave",           "14", "Cannot carry forward; max 7 days encashable at year end"],
        ["Sick Leave",             "10", "Unlimited for chemical-related occupational illness"],
        ["Earned / Annual Leave",  "18", "Accrues after 1 year; max 30-day accumulation"],
        ["Hazardous Duty Leave",    "4", "Extra 1 day/quarter for chem/laser/sandblast roles; not encashable"],
        ["Maternity Leave",        "84", "12 weeks paid; max 2 in service"],
        ["Paternity Leave",         "7", "Within 30 days of birth; max 2 times"],
        ["Bereavement (Spouse/Child)", "5", "Death cert required"],
        ["Bereavement (Parent/Sibling)", "3", "Death cert required"],
        ["Bereavement (In-laws)", "2", "Death cert required"],
        ["Hajj Leave (once only)", "30", "Unpaid; 2 months advance application"],
    ]
    lt = [[Paragraph(str(r[0]), S["Body"]), Paragraph(str(r[1]), S["Body"]), Paragraph(str(r[2]), S["Body"])] for r in lt]
    t = Table(lt, colWidths=[5.5*cm, 2.5*cm, 10.5*cm])
    t.setStyle(TableStyle([
        ("BACKGROUND",(0,0),(-1,0),accent),("TEXTCOLOR",(0,0),(-1,0),C_WHITE),
        ("ROWBACKGROUNDS",(0,1),(-1,-1),[C_WHITE,C_LIGHT]),
        ("GRID",(0,0),(-1,-1),0.4,C_BORDER),
        ("TOPPADDING",(0,0),(-1,-1),5),("BOTTOMPADDING",(0,0),(-1,-1),5),
        ("LEFTPADDING",(0,0),(-1,-1),6),("ALIGN",(1,0),(1,-1),"CENTER"),
    ]))
    story += [t, Spacer(1,8),
        section_header("2. HAZARDOUS DUTY LEAVE (DENIM-SPECIFIC)", S), Spacer(1,4),
        *numbered_list([
            "Employees in sandblasting, laser, or heavy chemical areas earn <b>1 extra leave day per quarter</b>",
            "Total hazard leave: <b>4 additional days per year</b>",
            "Hazard leave must be taken within the same quarter — it does NOT carry forward",
            "Hazard leave is <b>NOT encashable</b> in any circumstance",
        ], S),
        Spacer(1,8),
        section_header("3. SICK LEAVE — CHEMICAL ILLNESS PROVISION", S), Spacer(1,4),
        info_box("For occupational chemical illness, sick leave is <b>unlimited</b> pending specialist medical review. "
                 "First 3 months: full pay. Next 3 months: 50% pay.", S),
    ]


DENIM_SEC_TXT = """
================================================================================
  DENIM DEPARTMENT — SECURITY POLICY
  Document No.: DNM-SEC-001 | Version: 1.6 | Effective: January 1, 2024
================================================================================

1. CHEMICAL STORE ACCESS
   1.1  Chemical stores accessible only to Grade B and above with valid chemical certification.
   1.2  Daily stock reconciliation mandatory; discrepancies reported to Security within 1 hour.
   1.3  Double-locked and alarm-armed during night hours.
   1.4  100% CCTV coverage in chemical storage and dispensing areas; footage retained 60 days.

2. ZONE ACCESS BADGES
   Red Zone:    Chemical mixing area — Grade B+, hazmat certified only
   Blue Zone:   Laser room — trained laser operators only
   Yellow Zone: Washing area — Grade B and above
   White Zone:  General production & admin

3. PROHIBITED ACTIONS — DENIM SPECIFIC
   3.1  Tampering with chemical measurements or labels → Immediate termination
   3.2  Using mobile phone in chemical areas → Written warning
   3.3  Removing wash recipes or formula sheets from premises → Final warning / FIR
   3.4  Smoking within 50 metres of chemical storage → Final warning

4. HOT WORK PERMIT
   Any welding, grinding, or cutting work near chemical areas requires:
   (a) Written Hot Work Permit from Safety Officer
   (b) Fire watch personnel on standby
   (c) Chemical stores secured and ventilated before work begins
   Hot Work Permit form: DNM-SEC-HWP-01

5. EMERGENCY CONTACTS — DENIM SECURITY
   ┌──────────────────────────────┬──────────────────┬───────────────┐
   │ Service                      │ Number           │ Available     │
   ├──────────────────────────────┼──────────────────┼───────────────┤
   │ Security Desk – Denim Gate   │ Ext. 200         │ 24 / 7        │
   │ EHS Emergency                │ +92-333-9876543  │ 24 / 7        │
   │ Chemical Spill Hotline       │ Ext. 510         │ 24 / 7        │
   │ Fire Brigade                 │ 16               │ 24 / 7        │
   │ Police                       │ 15               │ 24 / 7        │
   └──────────────────────────────┴──────────────────┴───────────────┘

================================================================================
  CONFIDENTIAL. HR Dept, Denim Division. Doc No. DNM-SEC-001 v1.6 (2024)
================================================================================
""".strip()


def denim_sec_pdf(story, styles, accent):
    S = styles
    story += [
        section_header("1. CHEMICAL STORE ACCESS CONTROL", S), Spacer(1,4),
        *numbered_list([
            "Accessible only to <b>Grade B and above</b> with valid chemical handling certification",
            "Daily stock reconciliation mandatory; discrepancies reported to Security within <b>1 hour</b>",
            "Chemical stores are double-locked and alarm-armed during all night hours",
            "100% CCTV coverage in storage and dispensing areas — footage retained for <b>60 days</b>",
        ], S), Spacer(1,8),

        section_header("2. PROHIBITED ACTIONS & PENALTIES — DENIM SPECIFIC", S), Spacer(1,6),
        penalty_table([
            ("Tampering with chemical measurements or labels", "Immediate termination"),
            ("Using mobile phone inside chemical areas",       "Written warning"),
            ("Removing wash recipes / formula sheets from premises", "Final warning or FIR depending on severity"),
            ("Smoking within 50 metres of chemical storage",  "Final written warning"),
            ("Unauthorised access to chemical store",         "Final warning or termination"),
            ("Disabling safety alarms or CCTV",               "Immediate termination"),
        ], S, accent), Spacer(1,8),

        section_header("3. EMERGENCY CONTACTS — DENIM SECURITY", S), Spacer(1,6),
        contact_table([
            {"role": "Security Desk – Denim Gate", "name": "Duty Guard",        "phone": "", "ext": "200",       "email": "security@company.com"},
            {"role": "EHS Emergency (24/7)",       "name": "Mr. Ali Rehman",    "phone": "+92-333-9876543",      "email": "ehs@company.com"},
            {"role": "Chemical Spill Hotline",     "name": "Control Room",      "phone": "", "ext": "510",       "email": "chemspill@company.com"},
            {"role": "Fire Brigade",               "name": "National",           "phone": "16",                   "email": "—"},
            {"role": "Police (Emergency)",         "name": "National",           "phone": "15",                   "email": "—"},
        ], S, accent),
    ]


# ────────────────────────────────────────────────────
#  CORPORATE  HR  +  MEDICAL  +  LEAVE  +  SECURITY
# ────────────────────────────────────────────────────

CORP_HR_TXT = """
================================================================================
  CORPORATE DEPARTMENT — HUMAN RESOURCES POLICY
  Document No.: CORP-HR-001 | Version: 3.2 | Effective: January 1, 2024
================================================================================

1. WORKING HOURS & FLEXIBLE WORK
   1.1  Standard hours: 09:00 – 18:00, Monday to Friday.
   1.2  Core hours (mandatory presence): 10:00 – 16:00.
   1.3  Flex start: 08:00 – 10:00 (adjust end time accordingly).
   1.4  Work from Home (WFH): Up to 2 days/week for Grade 3 and above with manager approval.
   1.5  WFH conditions: VPN connected, available on Teams during core hours, professional background for video calls.

2. CORPORATE GRADE STRUCTURE & COMPENSATION
   ┌───────┬──────────────────────────────────┬─────────────────────────────────────────┐
   │ Grade │ Roles                            │ Key Benefits                            │
   ├───────┼──────────────────────────────────┼─────────────────────────────────────────┤
   │  1    │ Assistant / Junior Officer        │ Base salary, medical, leave             │
   │  2    │ Officer / Executive               │ Grade 1 + mobile PKR 2,500/month        │
   │  3    │ Senior Officer / Asst. Manager    │ Grade 2 + WFH eligible                  │
   │  4    │ Manager / Deputy Manager          │ Grade 3 + car allowance PKR 30,000/month│
   │  5    │ Senior Manager / General Manager  │ Grade 4 + fuel + driver + PKR 80,000 CA │
   │  6    │ Director / C-Suite                │ Grade 5 + executive perks + Board access│
   └───────┴──────────────────────────────────┴─────────────────────────────────────────┘

3. TRAVEL POLICY
   3.1  All travel requires pre-approval on Form CORP-HR-T-01 (available on HR portal).
   3.2  Per diem rates:
        • Domestic travel:        PKR 5,000 per day
        • International (Asia):   USD 120 per day
        • International (Europe/US): USD 180 per day
   3.3  Air travel:
        Grade 1–3: Economy class
        Grade 4+:  Business class for flights over 4 hours
   3.4  Hotel bookings: Must be made through company travel desk (traveldesk@company.com).
   3.5  Expense reports must be submitted within 5 working days of return with all original receipts.

4. KEY CONTACTS — CORPORATE HR
   ┌────────────────────────────────┬──────────────────┬────────────────────────────────┐
   │ Role                           │ Phone            │ Email                          │
   ├────────────────────────────────┼──────────────────┼────────────────────────────────┤
   │ HR Director                    │ +92-21-3456-7001 │ hrd@company.com                │
   │ HR Manager – Corporate         │ +92-21-3456-7002 │ hr.corporate@company.com       │
   │ Payroll Manager                │ +92-21-3456-7003 │ payroll.corp@company.com       │
   │ Recruitment Lead               │ +92-21-3456-7004 │ recruit.corp@company.com       │
   │ L&D Manager                    │ +92-21-3456-7005 │ ld@company.com                 │
   │ Travel Desk                    │ Ext. 150         │ traveldesk@company.com         │
   │ Employee Helpline (24/7)       │ 0800-12345       │ helpline@company.com           │
   │ CEO Office                     │ +92-21-3456-7000 │ ceo.office@company.com         │
   └────────────────────────────────┴──────────────────┴────────────────────────────────┘

================================================================================
  CONFIDENTIAL. HR Dept, Corporate Division. Doc No. CORP-HR-001 v3.2 (2024)
================================================================================
""".strip()


def corp_hr_pdf(story, styles, accent):
    S = styles
    story += [section_header("1. CORPORATE GRADE STRUCTURE & BENEFITS", S), Spacer(1,4)]
    gd = [
        [Paragraph("<b>Grade</b>", S["Body"]), Paragraph("<b>Typical Roles</b>", S["Body"]), Paragraph("<b>Key Benefits</b>", S["Body"])],
        ["1","Assistant / Junior Officer","Base salary + medical + leave entitlements"],
        ["2","Officer / Executive","Grade 1 + mobile allowance PKR 2,500/month"],
        ["3","Senior Officer / Asst. Manager","Grade 2 + WFH eligible (2 days/week)"],
        ["4","Manager / Deputy Manager","Grade 3 + car allowance PKR 30,000/month"],
        ["5","Senior Manager / General Manager","Grade 4 + fuel allowance + driver + PKR 80,000 CA"],
        ["6","Director / C-Suite","Grade 5 + executive perks + Board access"],
    ]
    gd = [[Paragraph(str(r[0]), S["Body"]), Paragraph(str(r[1]), S["Body"]), Paragraph(str(r[2]), S["Body"])] for r in gd]
    t = Table(gd, colWidths=[2*cm, 6*cm, 10.5*cm])
    t.setStyle(TableStyle([
        ("BACKGROUND",(0,0),(-1,0),accent),("TEXTCOLOR",(0,0),(-1,0),C_WHITE),
        ("ROWBACKGROUNDS",(0,1),(-1,-1),[C_WHITE,C_LIGHT]),
        ("GRID",(0,0),(-1,-1),0.4,C_BORDER),
        ("TOPPADDING",(0,0),(-1,-1),5),("BOTTOMPADDING",(0,0),(-1,-1),5),
        ("LEFTPADDING",(0,0),(-1,-1),6),("ALIGN",(0,0),(0,-1),"CENTER"),
    ]))
    story += [t, Spacer(1,8),
        section_header("2. BUSINESS TRAVEL POLICY", S), Spacer(1,4),
        info_box("All travel requires pre-approval on Form <b>CORP-HR-T-01</b> before booking. "
                 "Submit expense reports within <b>5 working days</b> of return with all original receipts.", S),
        Spacer(1,6),
    ]
    td = [
        [Paragraph("<b>Destination</b>", S["Body"]), Paragraph("<b>Grade 1–3</b>", S["Body"]), Paragraph("<b>Grade 4+</b>", S["Body"])],
        ["Domestic","Economy | PKR 5,000/day per diem","Economy | PKR 5,000/day per diem"],
        ["International (Asia)","Economy | USD 120/day per diem","Business (flights >4hr) | USD 120/day"],
        ["International (Europe/US)","Economy | USD 180/day per diem","Business (all flights) | USD 180/day"],
    ]
    td = [[Paragraph(str(r[0]), S["Body"]), Paragraph(str(r[1]), S["Body"]), Paragraph(str(r[2]), S["Body"])] for r in td]
    tt = Table(td, colWidths=[4.5*cm, 7*cm, 7*cm])
    tt.setStyle(TableStyle([
        ("BACKGROUND",(0,0),(-1,0),accent),("TEXTCOLOR",(0,0),(-1,0),C_WHITE),
        ("ROWBACKGROUNDS",(0,1),(-1,-1),[C_WHITE,C_LIGHT]),
        ("GRID",(0,0),(-1,-1),0.4,C_BORDER),
        ("TOPPADDING",(0,0),(-1,-1),5),("BOTTOMPADDING",(0,0),(-1,-1),5),
        ("LEFTPADDING",(0,0),(-1,-1),6),
    ]))
    story += [tt, Spacer(1,8),
        section_header("3. KEY CONTACTS — CORPORATE HR", S), Spacer(1,6),
        contact_table([
            {"role":"HR Director",              "name":"Mr. Hassan Zuberi",     "phone":"+92-21-3456-7001","email":"hrd@company.com"},
            {"role":"HR Manager – Corporate",   "name":"Ms. Sadia Naeem",       "phone":"+92-21-3456-7002","email":"hr.corporate@company.com"},
            {"role":"Payroll Manager",          "name":"Mr. Bilal Chaudhry",    "phone":"+92-21-3456-7003","email":"payroll.corp@company.com"},
            {"role":"Recruitment Lead",         "name":"Ms. Aisha Malik",       "phone":"+92-21-3456-7004","email":"recruit.corp@company.com"},
            {"role":"L&D Manager",              "name":"Mr. Saad Farooqi",      "phone":"+92-21-3456-7005","email":"ld@company.com"},
            {"role":"Travel Desk",              "name":"Travel Coordinator",    "phone":"","ext":"150",     "email":"traveldesk@company.com"},
            {"role":"Employee Helpline (24/7)", "name":"Helpline",               "phone":"0800-12345",      "email":"helpline@company.com"},
        ], S, accent),
    ]


CORP_MED_TXT = """
================================================================================
  CORPORATE DEPARTMENT — MEDICAL & HEALTH POLICY
  Document No.: CORP-MED-001 | Version: 2.9 | Effective: January 1, 2024
================================================================================

1. COVERAGE LIMITS BY GRADE
   ┌──────────┬──────────────────┬──────────────────────────────────────┐
   │ Grade    │ Employee (PKR)   │ Dependents                           │
   ├──────────┼──────────────────┼──────────────────────────────────────┤
   │ 1 – 3    │ 200,000          │ Spouse 80K | Each child (max 3) 50K  │
   │ 4 – 5    │ 350,000          │ Spouse 150K | Each child (max 3) 80K │
   │ 6 (Dir+) │ 500,000          │ Spouse 200K | Each child (max 3) 100K│
   └──────────┴──────────────────┴──────────────────────────────────────┘

2. WELLNESS BENEFITS
   2.1  Annual comprehensive health checkup at partner diagnostic centres — all grades (covered 100%).
   2.2  Executive health screening for Grade 4+:
        (a) Cardiac stress test
        (b) Full abdominal ultrasound
        (c) Bone density scan
        (d) Complete hormonal panel
   2.3  Gym membership reimbursement: Grade 3+ up to PKR 3,000/month.
   2.4  On-site flu vaccination: Every October, offered to all corporate staff free of charge.
   2.5  Vision checkup + spectacles: PKR 8,000/year per employee.
   2.6  Telehealth: Unlimited 24/7 virtual doctor consultations for employee + immediate family.

3. REIMBURSEMENT — CORPORATE PROCESS
   3.1  Submit online via HR portal: hr.portal.company.com
   3.2  Grade 1–3: Processed within 15 working days.
   3.3  Grade 4+: Priority processing within 7 working days.
   3.4  Grade 4+ employees: Direct billing available at all panel hospitals (no out-of-pocket first).
   3.5  Emergency advance: Up to PKR 50,000 as interest-free loan for medical emergencies.

4. EMERGENCY CONTACTS — CORPORATE MEDICAL
   ┌────────────────────────────────┬──────────────────┬─────────────────┐
   │ Service                        │ Number           │ Available       │
   ├────────────────────────────────┼──────────────────┼─────────────────┤
   │ Corporate Medical Officer      │ Ext. 600         │ 09:00 – 18:00   │
   │ Telehealth Platform            │ App: HealthNow   │ 24 / 7          │
   │ Mental Health EAP Hotline      │ 0800-54321       │ 24 / 7          │
   │ Ambulance (Company)            │ +92-21-3456-7999 │ 24 / 7          │
   │ Insurance Claims — Jubilee     │ 021-111-234-567  │ 09:00 – 17:00   │
   │ Insurance Claims — EFU         │ 021-111-338-820  │ 09:00 – 17:00   │
   │ AKU Hospital ER                │ 021-3486-4545    │ 24 / 7          │
   └────────────────────────────────┴──────────────────┴─────────────────┘

================================================================================
  CONFIDENTIAL. HR Dept, Corporate Division. Doc No. CORP-MED-001 v2.9 (2024)
================================================================================
""".strip()


def corp_med_pdf(story, styles, accent):
    S = styles
    story += [section_header("1. MEDICAL COVERAGE BY GRADE", S), Spacer(1,4)]
    cov = [
        [Paragraph("<b>Grade</b>", S["Body"]), Paragraph("<b>Employee Limit (PKR)</b>", S["Body"]), Paragraph("<b>Dependents</b>", S["Body"])],
        ["1 – 3","200,000","Spouse PKR 80K | Each child (max 3): PKR 50K"],
        ["4 – 5","350,000","Spouse PKR 150K | Each child (max 3): PKR 80K"],
        ["6 (Dir+)","500,000","Spouse PKR 200K | Each child (max 3): PKR 100K"],
    ]
    cov = [[Paragraph(str(r[0]), S["Body"]), Paragraph(str(r[1]), S["Body"]), Paragraph(str(r[2]), S["Body"])] for r in cov]
    ct = Table(cov, colWidths=[3*cm, 5.5*cm, 10*cm])
    ct.setStyle(TableStyle([
        ("BACKGROUND",(0,0),(-1,0),accent),("TEXTCOLOR",(0,0),(-1,0),C_WHITE),
        ("ROWBACKGROUNDS",(0,1),(-1,-1),[C_WHITE,C_LIGHT]),
        ("GRID",(0,0),(-1,-1),0.4,C_BORDER),
        ("TOPPADDING",(0,0),(-1,-1),5),("BOTTOMPADDING",(0,0),(-1,-1),5),
        ("LEFTPADDING",(0,0),(-1,-1),6),
    ]))
    story += [ct, Spacer(1,8),
        section_header("2. WELLNESS & EXECUTIVE HEALTH BENEFITS", S), Spacer(1,4),
        *numbered_list([
            "Annual comprehensive health checkup — all grades (100% covered at partner diagnostic centres)",
            "Executive screening for Grade 4+: Cardiac stress test, abdominal ultrasound, bone density, hormonal panel",
            "Gym membership reimbursement: <b>PKR 3,000/month</b> for Grade 3 and above",
            "Annual flu vaccination: Offered on-site every October, free of charge for all corporate staff",
            "Vision checkup + spectacles: <b>PKR 8,000/year</b> per employee",
            "Telehealth: Unlimited 24/7 virtual doctor consultations for employee and immediate family",
        ], S), Spacer(1,8),
        section_header("3. EMERGENCY CONTACTS — CORPORATE MEDICAL", S), Spacer(1,6),
        contact_table([
            {"role":"Corporate Medical Officer","name":"Dr. Nida Waheed",    "phone":"","ext":"600",         "email":"medical@company.com"},
            {"role":"Telehealth Platform",      "name":"HealthNow App",      "phone":"App / 0800-99999",     "email":"support@healthnow.pk"},
            {"role":"Mental Health EAP Hotline","name":"Counselling Desk",   "phone":"0800-54321",           "email":"eap@company.com"},
            {"role":"Company Ambulance (24/7)", "name":"Dispatch",           "phone":"+92-21-3456-7999",     "email":"ambulance@company.com"},
            {"role":"Insurance — Jubilee Life", "name":"Claims Dept",        "phone":"021-111-234-567",      "email":"claims@jubileelife.com"},
            {"role":"Insurance — EFU General",  "name":"Claims Dept",        "phone":"021-111-338-820",      "email":"claims@efu.com.pk"},
            {"role":"AKU Hospital Emergency",   "name":"Emergency Dept",     "phone":"021-3486-4545",        "email":"—"},
        ], S, accent),
    ]


CORP_LEAVE_TXT = """
================================================================================
  CORPORATE DEPARTMENT — LEAVE POLICY
  Document No.: CORP-LV-001 | Version: 3.1 | Effective: January 1, 2024
================================================================================

1. LEAVE ENTITLEMENT BY GRADE
   ┌────────────────────┬─────────────┬─────────────────────────────────────────────┐
   │ Leave Type         │ Days / Year │ Grade-specific variation                    │
   ├────────────────────┼─────────────┼─────────────────────────────────────────────┤
   │ Casual Leave       │  14 – 21    │ Grade 1–3: 14 | Grade 4–5: 18 | Grade 6: 21│
   │ Earned Leave       │  18 – 25    │ 0–2 yrs: 18 | 3–5 yrs: 21 | 6+ yrs: 25    │
   │ Sick Leave         │     12      │ All grades; up to 6 months extended (serious)│
   │ Maternity Leave    │  84 – 112   │ Standard: 84 days | Corporate: 112 days     │
   │ Paternity Leave    │     14      │ Corporate-enhanced (vs standard 7 days)      │
   │ Study / Exam Leave │     10      │ Paid if company-sponsored course            │
   │ Sabbatical         │     90      │ Unpaid; after 7 years of service; once      │
   │ Bereavement        │   3 – 7     │ Spouse/Child: 7 | Parent/Sibling: 5 | Other: 3│
   │ Hajj Leave         │     30      │ Unpaid; apply 3 months in advance           │
   └────────────────────┴─────────────┴─────────────────────────────────────────────┘

2. MATERNITY LEAVE — CORPORATE ENHANCED
   2.1  Corporate female employees receive 16 weeks (112 days) paid maternity leave.
   2.2  Maternity medical expenses covered up to PKR 75,000 per delivery.
   2.3  Maximum 3 maternity benefits during entire employment.
   2.4  Flexible return-to-work: Part-time for first 3 months post-return (with approval).
   2.5  On-site creche available at Head Office for children aged 3 months to 3 years.

3. SABBATICAL POLICY
   3.1  Available to employees with 7+ years of continuous service.
   3.2  Duration: Up to 3 months (90 days) unpaid leave.
   3.3  May only be used once in entire service.
   3.4  Purpose must be declared: travel, personal development, academic, or volunteer work.
   3.5  Health insurance coverage continues during sabbatical; all other benefits suspended.
   3.6  Job reinstatement at same grade guaranteed on return (subject to business needs).
   3.7  Application: Submit to HR Director at least 3 months in advance.

4. LEAVE WITHOUT PAY — APPROVAL MATRIX
   Duration            Approved By
   Up to 7 days        Line Manager
   8 – 30 days         Department Head
   31 – 60 days        HR Director
   61 – 90 days        CEO
   Beyond 90 days      Board HR Committee

5. LEAVE HR CONTACTS — CORPORATE
   HR Portal:        hr.portal.company.com
   HR Manager:       +92-21-3456-7002 | hr.corporate@company.com
   Payroll Queries:  +92-21-3456-7003 | payroll.corp@company.com

================================================================================
  CONFIDENTIAL. HR Dept, Corporate Division. Doc No. CORP-LV-001 v3.1 (2024)
================================================================================
""".strip()


def corp_leave_pdf(story, styles, accent):
    S = styles
    story += [section_header("1. LEAVE ENTITLEMENT BY GRADE", S), Spacer(1,4)]
    lt = [
        [Paragraph("<b>Leave Type</b>", S["Body"]), Paragraph("<b>Days/Year</b>", S["Body"]), Paragraph("<b>Grade Variation</b>", S["Body"])],
        ["Casual Leave","14 – 21","Grade 1–3: 14 | Grade 4–5: 18 | Grade 6: 21"],
        ["Earned Leave","18 – 25","0–2 yrs: 18 | 3–5 yrs: 21 | 6+ yrs: 25"],
        ["Sick Leave","12","All grades; up to 6 months extended (serious illness)"],
        ["Maternity Leave","84 – 112","Standard: 84 days | Corporate Enhanced: 112 days"],
        ["Paternity Leave","14","Corporate-enhanced (vs standard 7 days)"],
        ["Study / Exam Leave","10","Paid if company-sponsored course; 5 days for personal"],
        ["Sabbatical","90","Unpaid; after 7 years service; once in employment"],
        ["Bereavement","3 – 7","Spouse/Child: 7 | Parent/Sibling: 5 | Extended family: 3"],
        ["Hajj Leave","30","Unpaid; apply 3 months in advance"],
    ]
    lt = [[Paragraph(str(r[0]), S["Body"]), Paragraph(str(r[1]), S["Body"]), Paragraph(str(r[2]), S["Body"])] for r in lt]
    t = Table(lt, colWidths=[5*cm, 2.5*cm, 11*cm])
    t.setStyle(TableStyle([
        ("BACKGROUND",(0,0),(-1,0),accent),("TEXTCOLOR",(0,0),(-1,0),C_WHITE),
        ("ROWBACKGROUNDS",(0,1),(-1,-1),[C_WHITE,C_LIGHT]),
        ("GRID",(0,0),(-1,-1),0.4,C_BORDER),
        ("TOPPADDING",(0,0),(-1,-1),5),("BOTTOMPADDING",(0,0),(-1,-1),5),
        ("LEFTPADDING",(0,0),(-1,-1),6),("ALIGN",(1,0),(1,-1),"CENTER"),
    ]))
    story += [t, Spacer(1,8),
        section_header("2. LEAVE WITHOUT PAY — APPROVAL MATRIX", S), Spacer(1,4),
    ]
    ap = [
        [Paragraph("<b>Duration</b>", S["Body"]), Paragraph("<b>Approved By</b>", S["Body"])],
        ["Up to 7 days","Line Manager"],
        ["8 – 30 days","Department Head"],
        ["31 – 60 days","HR Director"],
        ["61 – 90 days","CEO"],
        ["Beyond 90 days","Board HR Committee"],
    ]
    ap = [[Paragraph(str(r[0]), S["Body"]), Paragraph(str(r[1]), S["Body"])] for r in ap]
    at = Table(ap, colWidths=[7*cm, 11.5*cm])
    at.setStyle(TableStyle([
        ("BACKGROUND",(0,0),(-1,0),accent),("TEXTCOLOR",(0,0),(-1,0),C_WHITE),
        ("ROWBACKGROUNDS",(0,1),(-1,-1),[C_WHITE,C_LIGHT]),
        ("GRID",(0,0),(-1,-1),0.4,C_BORDER),
        ("TOPPADDING",(0,0),(-1,-1),5),("BOTTOMPADDING",(0,0),(-1,-1),5),
        ("LEFTPADDING",(0,0),(-1,-1),6),
    ]))
    story += [at]


CORP_SEC_TXT = """
================================================================================
  CORPORATE DEPARTMENT — INFORMATION & PHYSICAL SECURITY POLICY
  Document No.: CORP-SEC-001 | Version: 2.5 | Effective: January 1, 2024
================================================================================

1. PASSWORD & AUTHENTICATION STANDARDS
   1.1  Minimum password length: 12 characters.
   1.2  Must contain: uppercase, lowercase, number, and special character.
   1.3  Password must be changed every 90 days.
   1.4  Last 10 passwords cannot be reused.
   1.5  Multi-Factor Authentication (MFA): Mandatory for ALL corporate systems.
   1.6  Shared passwords: STRICTLY PROHIBITED.

2. DATA CLASSIFICATION
   Level 1 — Public:       Marketing materials, approved press releases
   Level 2 — Internal:     General company information, non-sensitive procedures
   Level 3 — Confidential: Client data, financials, HR records, product pricing
   Level 4 — Restricted:   Board papers, M&A data, personal data (PDPA-sensitive)

   Handling rules:
   • Level 3: Must be encrypted when emailed; no sharing without business need.
   • Level 4: Printed copies require secure handling; shred after use; share only with named recipients on need-to-know basis.

3. CFO FRAUD / PAYMENT FRAUD PREVENTION
   3.1  No financial transfer may be actioned based on email-only instruction, even from C-suite.
   3.2  All transfer instructions above PKR 100,000 must be verified via direct phone call to requester.
   3.3  New vendor bank account details must be confirmed by phone with the vendor before any payment.
   3.4  Suspicious payment request? Contact IT Security immediately: itsecurity@company.com | Ext. 700.

4. INCIDENT RESPONSE — CRITICAL TIMELINES
   Incident Type                         Report Within
   Suspected data breach                 1 hour to IT Security
   Confirmed personal data breach        72 hours to regulatory authority (PDPA)
   Lost/stolen company device            1 hour to IT Security for remote wipe
   Phishing email received               Immediately to itsecurity@company.com
   Physical security incident            Immediately to Security Desk (Ext. 600)

5. EMERGENCY CONTACTS — CORPORATE SECURITY
   ┌────────────────────────────────┬──────────────────┬─────────────────┐
   │ Service                        │ Number           │ Available       │
   ├────────────────────────────────┼──────────────────┼─────────────────┤
   │ IT Security Team               │ Ext. 700         │ 09:00 – 18:00   │
   │ IT Security Emergency (24/7)   │ +92-21-3456-7070 │ 24 / 7          │
   │ IT Security Email              │ itsecurity@co.   │ Monitored 24/7  │
   │ Security Desk (Reception)      │ Ext. 600         │ 24 / 7          │
   │ Security Manager               │ +92-21-3456-7060 │ 08:00 – 20:00   │
   │ DRP / Business Continuity      │ Ext. 701         │ 09:00 – 18:00   │
   │ Police Emergency               │ 15               │ 24 / 7          │
   │ Cyber Crime Reporting (FIA)    │ 1991             │ 09:00 – 17:00   │
   └────────────────────────────────┴──────────────────┴─────────────────┘

================================================================================
  CONFIDENTIAL. HR Dept, Corporate Division. Doc No. CORP-SEC-001 v2.5 (2024)
================================================================================
""".strip()


def corp_sec_pdf(story, styles, accent):
    S = styles
    story += [
        section_header("1. DATA CLASSIFICATION LEVELS", S), Spacer(1,4),
    ]
    dc = [
        [Paragraph("<b>Level</b>", S["Body"]), Paragraph("<b>Classification</b>", S["Body"]), Paragraph("<b>Examples & Handling</b>", S["Body"])],
        ["1","Public","Marketing materials, approved press releases — share freely"],
        ["2","Internal","General procedures, org charts — share internally only"],
        ["3","Confidential","Client data, financials, HR records — encrypt when emailed"],
        ["4","Restricted","Board papers, M&A data, PDPA-sensitive personal data — named recipients only; shred after use"],
    ]
    dc = [[Paragraph(str(r[0]), S["Body"]), Paragraph(str(r[1]), S["Body"]), Paragraph(str(r[2]), S["Body"])] for r in dc]
    dt = Table(dc, colWidths=[2*cm, 4*cm, 12.5*cm])
    dt.setStyle(TableStyle([
        ("BACKGROUND",(0,0),(-1,0),accent),("TEXTCOLOR",(0,0),(-1,0),C_WHITE),
        ("ROWBACKGROUNDS",(0,1),(-1,-1),[C_WHITE,C_LIGHT]),
        ("GRID",(0,0),(-1,-1),0.4,C_BORDER),
        ("TOPPADDING",(0,0),(-1,-1),5),("BOTTOMPADDING",(0,0),(-1,-1),5),
        ("LEFTPADDING",(0,0),(-1,-1),6),("ALIGN",(0,0),(0,-1),"CENTER"),
    ]))
    story += [dt, Spacer(1,8),
        section_header("2. CFO / PAYMENT FRAUD PREVENTION", S), Spacer(1,4),
        info_box("⚠ <b>CRITICAL:</b> No financial transfer may be actioned based on email-only instruction, "
                 "even if it appears to come from C-suite executives. This is the #1 social engineering attack vector.", S),
        Spacer(1,6),
        *numbered_list([
            "All transfers above <b>PKR 100,000</b> must be verified via direct phone call to the requester",
            "New vendor bank account details must be confirmed by phone with the vendor before first payment",
            "Suspicious payment requests: Contact IT Security immediately — <b>itsecurity@company.com</b> | <b>Ext. 700</b>",
        ], S), Spacer(1,8),

        section_header("3. INCIDENT RESPONSE TIMELINES", S), Spacer(1,4),
    ]
    it = [
        [Paragraph("<b>Incident Type</b>", S["Body"]), Paragraph("<b>Report Within</b>", S["Body"]), Paragraph("<b>Report To</b>", S["Body"])],
        ["Suspected data breach","1 hour","IT Security (Ext. 700 / itsecurity@company.com)"],
        ["Confirmed personal data breach (PDPA)","72 hours","Regulatory authority + IT Security"],
        ["Lost or stolen company device","1 hour","IT Security for immediate remote wipe"],
        ["Phishing email received","Immediately","itsecurity@company.com"],
        ["Physical security incident","Immediately","Security Desk (Ext. 600)"],
    ]
    it = [[Paragraph(str(r[0]), S["Body"]), Paragraph(str(r[1]), S["Body"]), Paragraph(str(r[2]), S["Body"])] for r in it]
    itt = Table(it, colWidths=[6.5*cm, 3.5*cm, 8.5*cm])
    itt.setStyle(TableStyle([
        ("BACKGROUND",(0,0),(-1,0),accent),("TEXTCOLOR",(0,0),(-1,0),C_WHITE),
        ("ROWBACKGROUNDS",(0,1),(-1,-1),[C_WHITE,C_LIGHT]),
        ("GRID",(0,0),(-1,-1),0.4,C_BORDER),
        ("TOPPADDING",(0,0),(-1,-1),5),("BOTTOMPADDING",(0,0),(-1,-1),5),
        ("LEFTPADDING",(0,0),(-1,-1),6),
    ]))
    story += [itt, Spacer(1,8),
        section_header("4. EMERGENCY CONTACTS — CORPORATE IT & PHYSICAL SECURITY", S), Spacer(1,6),
        contact_table([
            {"role":"IT Security Team",              "name":"IT Security Desk",   "phone":"","ext":"700",         "email":"itsecurity@company.com"},
            {"role":"IT Security Emergency (24/7)", "name":"On-call Engineer",   "phone":"+92-21-3456-7070",     "email":"itsecurity@company.com"},
            {"role":"Security Desk (Reception)",    "name":"Security Guard",     "phone":"","ext":"600",         "email":"security@company.com"},
            {"role":"Security Manager",             "name":"Mr. Osman Faruqui",  "phone":"+92-21-3456-7060",     "email":"security.mgr@company.com"},
            {"role":"Business Continuity / DRP",   "name":"BCP Coordinator",    "phone":"","ext":"701",         "email":"bcp@company.com"},
            {"role":"Police Emergency",             "name":"National",           "phone":"15",                   "email":"—"},
            {"role":"Cyber Crime (FIA)",            "name":"FIA Cybercrime Wing","phone":"1991",                 "email":"—"},
        ], S, accent),
    ]


# ══════════════════════════════════════════════════════════════════════════════
#  MAIN — Build all 12 policies
# ══════════════════════════════════════════════════════════════════════════════

POLICIES = [
    # (dept, policy_type, txt_content, pdf_story_fn, pdf_title, pdf_subtitle)
    ("garment","hr",    GARMENT_HR_TXT,    garment_hr_pdf,
     "Garment Department\nHuman Resources Policy",
     "Document No.: GRM-HR-001  |  Version 3.0  |  Effective January 1, 2024"),

    ("garment","medical", GARMENT_MED_TXT, garment_med_pdf,
     "Garment Department\nMedical & Health Policy",
     "Document No.: GRM-MED-001  |  Version 3.1  |  Effective January 1, 2024"),

    ("garment","leave",   GARMENT_LEAVE_TXT, garment_leave_pdf,
     "Garment Department\nLeave Policy",
     "Document No.: GRM-LV-001  |  Version 2.5  |  Effective January 1, 2024"),

    ("garment","security", GARMENT_SEC_TXT, garment_sec_pdf,
     "Garment Department\nSecurity Policy",
     "Document No.: GRM-SEC-001  |  Version 2.0  |  Effective January 1, 2024"),

    ("denim","hr",        DENIM_HR_TXT,     denim_hr_pdf,
     "Denim Department\nHuman Resources Policy",
     "Document No.: DNM-HR-001  |  Version 2.1  |  Effective January 1, 2024"),

    ("denim","medical",   DENIM_MED_TXT,    denim_med_pdf,
     "Denim Department\nMedical & Health Policy",
     "Document No.: DNM-MED-001  |  Version 2.3  |  Effective January 1, 2024"),

    ("denim","leave",     DENIM_LEAVE_TXT,  denim_leave_pdf,
     "Denim Department\nLeave Policy",
     "Document No.: DNM-LV-001  |  Version 2.2  |  Effective January 1, 2024"),

    ("denim","security",  DENIM_SEC_TXT,    denim_sec_pdf,
     "Denim Department\nSecurity Policy",
     "Document No.: DNM-SEC-001  |  Version 1.6  |  Effective January 1, 2024"),

    ("corporate","hr",      CORP_HR_TXT,    corp_hr_pdf,
     "Corporate Department\nHuman Resources Policy",
     "Document No.: CORP-HR-001  |  Version 3.2  |  Effective January 1, 2024"),

    ("corporate","medical",  CORP_MED_TXT,  corp_med_pdf,
     "Corporate Department\nMedical & Health Policy",
     "Document No.: CORP-MED-001  |  Version 2.9  |  Effective January 1, 2024"),

    ("corporate","leave",    CORP_LEAVE_TXT, corp_leave_pdf,
     "Corporate Department\nLeave Policy",
     "Document No.: CORP-LV-001  |  Version 3.1  |  Effective January 1, 2024"),

    ("corporate","security", CORP_SEC_TXT,  corp_sec_pdf,
     "Corporate Department\nInformation & Physical Security Policy",
     "Document No.: CORP-SEC-001  |  Version 2.5  |  Effective January 1, 2024"),
]


def main():
    print(f"\n{'='*60}")
    print(f"  Generating 12 policy documents (TXT + PDF)")
    print(f"{'='*60}\n")

    for dept, ptype, txt, pdf_fn, pdf_title, pdf_sub in POLICIES:
        print(f"\n[{dept.upper()} / {ptype.upper()}]")
        base = DATA_DIR / dept / ptype

        # Write TXT
        write_txt(base / f"{ptype}_policy.txt", txt)

        # Write PDF
        pdf_title_clean = pdf_title.replace("\n", " — ")
        build_pdf(
            path=base / f"{ptype}_policy.pdf",
            story_fn=pdf_fn,
            dept=dept,
            doc_title=pdf_title.replace("\n", "\n"),
            doc_subtitle=pdf_sub,
        )

    total = len(POLICIES)
    print(f"\n{'='*60}")
    print(f"  Done! {total} TXT + {total} PDF = {total*2} files generated.")
    print(f"  All saved under: {DATA_DIR}")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    main()
