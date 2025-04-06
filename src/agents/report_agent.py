import matplotlib.pyplot as plt
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    PageBreak,
    Image,
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import inch
from io import BytesIO
import pandas as pd

import matplotlib.pyplot as plt
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    Image,
    ListFlowable,
    ListItem,
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import inch
from io import BytesIO
import pandas as pd
from textwrap import wrap


def wrap_text(text, width=60):
    return "\n".join(wrap(str(text), width=width))


import matplotlib.pyplot as plt
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    Image,
    ListFlowable,
    ListItem,
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import inch
from io import BytesIO
import pandas as pd


def generate_pdf_report(data, filename="rfp_report.pdf"):
    doc = SimpleDocTemplate(
        filename,
        pagesize=A4,
        rightMargin=30,
        leftMargin=30,
        topMargin=30,
        bottomMargin=18,
    )
    styles = getSampleStyleSheet()
    story = []

    # Custom styles
    title_style = ParagraphStyle(
        name="Title", fontSize=20, textColor=colors.HexColor("#2E86C1"), spaceAfter=20
    )
    h2_style = ParagraphStyle(
        name="Heading2",
        fontSize=14,
        textColor=colors.HexColor("#1ABC9C"),
        spaceAfter=10,
    )
    normal_style = styles["BodyText"]

    story.append(Paragraph("RFP Compliance Report", title_style))
    story.append(Spacer(1, 6))

    # 1️⃣ Eligibility Section
    story.append(Paragraph("1. Eligibility Assessment", h2_style))

    eligibility_data = [
        ["Criteria", "Required", "Current", "Matches", "Corrective Steps"]
    ]
    match_count = mismatch_count = 0
    for item in data["eligibility"]["compliance_criteria"]:
        if item["matches"]:
            match_count += 1
        else:
            mismatch_count += 1
        eligibility_data.append(
            [
                Paragraph(item["criteria"], normal_style),
                Paragraph(item["required"], normal_style),
                Paragraph(item["current"], normal_style),
                "✔" if item["matches"] else "✗",
                Paragraph(str(item.get("corrective_steps", "-")), normal_style),
            ]
        )

    eligibility_table = Table(eligibility_data, colWidths=[90, 130, 80, 40, 120])
    eligibility_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#3498DB")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.black),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("FONTSIZE", (0, 0), (-1, -1), 9),
            ]
        )
    )
    story.append(eligibility_table)
    story.append(Spacer(1, 6))
    story.append(
        Paragraph(
            f"<b>Summary:</b> {data['eligibility']['overall_eligibility_assessment']}",
            normal_style,
        )
    )

    # Eligibility donut chart
    story.append(Spacer(1, 10))
    story.append(Paragraph("    Eligibility Match Overview", h2_style))
    plt.figure(figsize=(3.5, 3.5))
    plt.pie(
        [match_count, mismatch_count],
        labels=["Match", "Mismatch"],
        colors=["#2ECC71", "#E74C3C"],
        autopct="%1.1f%%",
        startangle=140,
        wedgeprops={"width": 0.4},
    )
    plt.title("Eligibility Match Ratio")
    buffer = BytesIO()
    plt.savefig(buffer, format="PNG")
    plt.close()
    buffer.seek(0)
    story.append(Image(buffer, width=3.5 * inch, height=3.5 * inch))

    story.append(Spacer(1, 14))

    # 2️⃣ Checklist Section
    story.append(Paragraph("2. Submission Checklist", h2_style))
    checklist_data = [["Task", "Priority", "Deadline"]]

    print(data)
    for item in data["checklist"]["items"]:
        checklist_data.append(
            [
                Paragraph(item["task"], normal_style),
                Paragraph(item["priority"], normal_style),
                Paragraph(item["deadline"], normal_style),
            ]
        )

    checklist_table = Table(checklist_data, colWidths=[250, 80, 80])
    checklist_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#16A085")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("BACKGROUND", (0, 1), (-1, -1), colors.HexColor("#ECF0F1")),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.black),
                ("FONTSIZE", (0, 0), (-1, -1), 9),
            ]
        )
    )
    story.append(checklist_table)

    # Checklist pie chart
    story.append(Spacer(1, 10))
    story.append(Paragraph("    Task Priority Distribution", h2_style))
    checklist_df = pd.DataFrame(data["checklist"]["items"])
    plt.figure(figsize=(4, 4))
    checklist_df["priority"].value_counts().plot(
        kind="pie", autopct="%1.1f%%", colors=["#F1C40F", "#E74C3C", "#2ECC71"]
    )
    plt.ylabel("")
    plt.title("Checklist Priorities")
    pie_buffer = BytesIO()
    plt.savefig(pie_buffer, format="PNG")
    plt.close()
    pie_buffer.seek(0)
    story.append(Image(pie_buffer, width=3.5 * inch, height=3.5 * inch))

    story.append(Spacer(1, 14))

    # 3️⃣ Risk Analysis
    story.append(Paragraph("3. Risk Analysis", h2_style))
    risk_data = [["Description", "Severity", "Mitigation Strategy"]]
    for risk in data["risk_analysis"]["identified_risks"]:
        risk_data.append(
            [
                Paragraph(risk["risk_description"], normal_style),
                Paragraph(risk["severity"], normal_style),
                Paragraph(risk["mitigation_strategy"], normal_style),
            ]
        )

    risk_table = Table(risk_data, colWidths=[180, 80, 180])
    risk_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#8E44AD")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("BACKGROUND", (0, 1), (-1, -1), colors.HexColor("#F2F3F4")),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.black),
                ("FONTSIZE", (0, 0), (-1, -1), 9),
            ]
        )
    )
    story.append(risk_table)

    # Risk bar chart
    story.append(Spacer(1, 10))
    story.append(Paragraph("    Risk Severity Overview", h2_style))
    risk_df = pd.DataFrame(data["risk_analysis"]["identified_risks"])
    severity_count = risk_df["severity"].value_counts()
    plt.figure(figsize=(5, 3))
    severity_count.plot(kind="bar", color="#E67E22")
    plt.title("Risk Severity Levels")
    plt.ylabel("Count")
    plt.xticks(rotation=0)
    bar_buffer = BytesIO()
    plt.savefig(bar_buffer, format="PNG")
    plt.close()
    bar_buffer.seek(0)
    story.append(Image(bar_buffer, width=4 * inch, height=3 * inch))

    story.append(Spacer(1, 14))

    # 4️⃣ References
    story.append(Paragraph("4. Relevant References", h2_style))
    references = data["references"]
    bullet_list = ListFlowable(
        [ListItem(Paragraph(link, normal_style)) for link in references],
        bulletType="bullet",
    )
    story.append(bullet_list)

    # Build the document
    doc.build(story)
    print(f"✅ PDF successfully generated: {filename}")


if __name__ == "__main__":
    input_data = {
        "eligibility": {
            "compliance_criteria": [
                {
                    "criteria": "Minimum Years of Experience in Temporary Staffing",
                    "required": "minimum of three (3) years of business in Temporary Staffing Services at time of bid due date",
                    "current": "7 years",
                    "matches": True,
                },
                {
                    "criteria": "HUB Certification",
                    "required": "Submit proof of HUB certificate",
                    "current": "Not certified.",
                    "matches": False,
                    "corrective_steps": "Steps here",
                },
            ],
            "overall_eligibility_assessment": "Ineligible due to lack of HUB certification.",
        },
        "checklist": {
            "items": [
                {
                    "task": "Submit questions",
                    "priority": "Medium",
                    "deadline": "2025-02-18",
                },
                {
                    "task": "Submit proposal",
                    "priority": "High",
                    "deadline": "2025-02-25",
                },
                {
                    "task": "Include HSD Form A",
                    "priority": "High",
                    "deadline": "2025-02-25",
                },
            ]
        },
        "risk_analysis": {
            "identified_risks": [
                {
                    "risk_description": "RFP requires E&O insurance, not listed in profile.",
                    "severity": "High",
                    "mitigation_strategy": "Obtain required E&O insurance before bid.",
                },
                {
                    "risk_description": "Company may lack specific MHMR experience.",
                    "severity": "Medium",
                    "mitigation_strategy": "Highlight specific personnel experience.",
                },
            ]
        },
        "references": ["https://example.com/link1", "https://example.com/link2"],
    }

    generate_pdf_report(input_data)
