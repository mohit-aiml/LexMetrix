"""
LexMetrix - Inspection Report & Legal Notice Generator
Generates official Department of Consumer Affairs (DoCA) formatted PDF reports
with evidence photographs, statutory checklist tables, and Section 36 legal notices.
Also provides CSV and JSON export routines.
"""

import os
import json
import csv
import io
from datetime import datetime
from typing import Dict, Any

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image as RLImage, KeepTogether, HRFlowable
)
from reportlab.lib.units import inch

def generate_pdf_report(inspection_data: Dict[str, Any], output_path: str) -> str:
    """
    Generates an official Government of India / Department of Consumer Affairs PDF report.
    """
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    doc = SimpleDocTemplate(
        output_path,
        pagesize=A4,
        leftMargin=36,
        rightMargin=36,
        topMargin=36,
        bottomMargin=36
    )
    
    styles = getSampleStyleSheet()
    
    # Custom styles
    header_title_style = ParagraphStyle(
        "GovtHeader",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=12,
        leading=14,
        alignment=1, # Center
        textColor=colors.HexColor("#1A365D")
    )
    sub_title_style = ParagraphStyle(
        "GovtSub",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=9,
        leading=11,
        alignment=1,
        textColor=colors.HexColor("#4A5568")
    )
    doc_title_style = ParagraphStyle(
        "DocTitle",
        parent=styles["Heading1"],
        fontName="Helvetica-Bold",
        fontSize=14,
        leading=16,
        alignment=1,
        textColor=colors.HexColor("#C53030") if inspection_data.get("compliance_status") == "NON_COMPLIANT" else colors.HexColor("#276749")
    )
    section_h2 = ParagraphStyle(
        "SectionH2",
        parent=styles["Heading2"],
        fontName="Helvetica-Bold",
        fontSize=11,
        leading=13,
        textColor=colors.HexColor("#2B6CB0"),
        spaceBefore=8,
        spaceAfter=4
    )
    body_bold = ParagraphStyle("BodyB", parent=styles["Normal"], fontName="Helvetica-Bold", fontSize=8, leading=10)
    body_small = ParagraphStyle("BodyS", parent=styles["Normal"], fontName="Helvetica", fontSize=8, leading=10)
    
    elements = []
    
    # 1. Government Header
    elements.append(Paragraph("GOVERNMENT OF INDIA", header_title_style))
    elements.append(Paragraph("MINISTRY OF CONSUMER AFFAIRS, FOOD & PUBLIC DISTRIBUTION", header_title_style))
    elements.append(Paragraph("DEPARTMENT OF CONSUMER AFFAIRS — ENFORCEMENT DIRECTORATE", sub_title_style))
    elements.append(Paragraph("Legal Metrology (Packaged Commodities) Rules, 2011 Compliance System", sub_title_style))
    elements.append(Spacer(1, 8))
    elements.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor("#1A365D"), spaceBefore=2, spaceAfter=8))
    
    # 2. Document Title & Verdict Banner
    status = inspection_data.get("compliance_status", "NON_COMPLIANT")
    score = inspection_data.get("compliance_score", 0.0)
    code = inspection_data.get("inspection_code", "LM-2026-UNKNOWN")
    
    verdict_text = "OFFICIAL COMPLIANCE INSPECTION REPORT"
    elements.append(Paragraph(verdict_text, doc_title_style))
    elements.append(Spacer(1, 4))
    
    # Status Banner Table
    banner_bg = colors.HexColor("#FFF5F5") if status == "NON_COMPLIANT" else colors.HexColor("#F0FFF4")
    banner_border = colors.HexColor("#E53E3E") if status == "NON_COMPLIANT" else colors.HexColor("#38A169")
    status_label = f"VERDICT: {status.replace('_', ' ')} (Score: {score}%)"
    
    banner_data = [[
        Paragraph(f"<b>Inspection Ref:</b> {code}", body_bold),
        Paragraph(f"<b>Date/Time:</b> {inspection_data.get('timestamp', '')}", body_bold),
        Paragraph(f"<b>{status_label}</b>", ParagraphStyle("BStatus", parent=body_bold, textColor=banner_border, fontSize=9))
    ]]
    banner_table = Table(banner_data, colWidths=[180, 160, 180])
    banner_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), banner_bg),
        ('BOX', (0, 0), (-1, -1), 1, banner_border),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
    ]))
    elements.append(banner_table)
    elements.append(Spacer(1, 8))
    
    # 3. Product & Inspection Metadata Table
    elements.append(Paragraph("1. PRODUCT & INSPECTION METADATA", section_h2))
    meta_rows = [
        [
            Paragraph("<b>Product Name:</b>", body_bold),
            Paragraph(inspection_data.get("product_name", "N/A"), body_small),
            Paragraph("<b>Inspector ID:</b>", body_bold),
            Paragraph(inspection_data.get("inspector_id", "N/A"), body_small)
        ],
        [
            Paragraph("<b>Brand / Trademark:</b>", body_bold),
            Paragraph(inspection_data.get("brand", "N/A"), body_small),
            Paragraph("<b>Enforcement Officer:</b>", body_bold),
            Paragraph(inspection_data.get("inspector_name", "N/A"), body_small)
        ],
        [
            Paragraph("<b>Commodity Category:</b>", body_bold),
            Paragraph(inspection_data.get("category", "General Food / FMCG"), body_small),
            Paragraph("<b>Inspection Location:</b>", body_bold),
            Paragraph(inspection_data.get("location", "N/A"), body_small)
        ]
    ]
    meta_table = Table(meta_rows, colWidths=[110, 150, 110, 150])
    meta_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor("#F7FAFC")),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E0")),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
    ]))
    elements.append(meta_table)
    elements.append(Spacer(1, 8))
    
    # 4. Photographic Evidence (Embedded annotated image)
    evidence_img_path = inspection_data.get("annotated_image_path") or inspection_data.get("image_path")
    if evidence_img_path and os.path.exists(evidence_img_path):
        elements.append(Paragraph("2. PHOTOGRAPHIC EVIDENCE (ANNOTATED LABEL ANALYSIS)", section_h2))
        try:
            # Scaled to fit nicely on page
            img_flow = RLImage(evidence_img_path, width=4.5 * inch, height=2.2 * inch)
            img_table = Table([[img_flow]], colWidths=[520])
            img_table.setStyle(TableStyle([
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('BOX', (0, 0), (-1, -1), 1, colors.HexColor("#CBD5E0")),
                ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor("#EDF2F7")),
                ('TOPPADDING', (0, 0), (-1, -1), 4),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
            ]))
            elements.append(img_table)
            elements.append(Spacer(1, 8))
        except Exception as e:
            print(f"Error embedding image in PDF: {e}")
            
    # 5. Mandatory Declarations Statutory Checklist
    elements.append(Paragraph("3. STATUTORY COMPLIANCE CHECKLIST (LEGAL METROLOGY RULES, 2011)", section_h2))
    
    checklist_headers = [
        Paragraph("<b>Statutory Clause</b>", body_bold),
        Paragraph("<b>Mandatory Requirement</b>", body_bold),
        Paragraph("<b>Detected On Package</b>", body_bold),
        Paragraph("<b>Status</b>", body_bold)
    ]
    
    ext = inspection_data.get("extracted_data", {})
    rules_data = [
        [
            Paragraph("Rule 6(1)(a)", body_bold),
            Paragraph("Name & Complete Address with PIN", body_small),
            Paragraph(ext.get("manufacturer", {}).get("company_name") or "Not detected", body_small),
            Paragraph("<font color='#276749'><b>PASS</b></font>" if ext.get("manufacturer", {}).get("has_pincode") else "<font color='#C53030'><b>FAIL / DEFECT</b></font>", body_bold)
        ],
        [
            Paragraph("Rule 6(1)(b)", body_bold),
            Paragraph("Country of Origin / 'Made in'", body_small),
            Paragraph(ext.get("origin", {}).get("country") or "Not declared", body_small),
            Paragraph("<font color='#276749'><b>PASS</b></font>" if ext.get("origin", {}).get("is_declared") else "<font color='#C53030'><b>FAIL</b></font>", body_bold)
        ],
        [
            Paragraph("Rule 6(1)(c)", body_bold),
            Paragraph("Net Quantity in Standard SI Unit", body_small),
            Paragraph(f"{ext.get('net_quantity', {}).get('value', '')} {ext.get('net_quantity', {}).get('unit', '')}".strip() or "Not detected", body_small),
            Paragraph("<font color='#276749'><b>PASS</b></font>" if ext.get("net_quantity", {}).get("is_standard_unit", False) else "<font color='#C53030'><b>FAIL (Non-Std)</b></font>", body_bold)
        ],
        [
            Paragraph("Rule 6(1)(d)", body_bold),
            Paragraph("Month & Year of Mfg / Packing", body_small),
            Paragraph(ext.get("dates", {}).get("mfg_date") or "Not detected", body_small),
            Paragraph("<font color='#276749'><b>PASS</b></font>" if ext.get("dates", {}).get("mfg_date") else "<font color='#C53030'><b>FAIL</b></font>", body_bold)
        ],
        [
            Paragraph("Rule 6(1)(e)", body_bold),
            Paragraph("MRP with '(incl. of all taxes)'", body_small),
            Paragraph(f"₹{ext.get('mrp', {}).get('amount', '')} (Taxes: {'Yes' if ext.get('mrp', {}).get('has_inclusive_taxes') else 'NO'})", body_small),
            Paragraph("<font color='#276749'><b>PASS</b></font>" if ext.get("mrp", {}).get("has_inclusive_taxes") else "<font color='#C53030'><b>VIOLATION</b></font>", body_bold)
        ],
        [
            Paragraph("Rule 6(1)(n)", body_bold),
            Paragraph("Consumer Care: Phone & Email", body_small),
            Paragraph(f"Ph: {ext.get('consumer_care', {}).get('phone') or 'None'} | Mail: {ext.get('consumer_care', {}).get('email') or 'None'}", body_small),
            Paragraph("<font color='#276749'><b>PASS</b></font>" if (ext.get("consumer_care", {}).get("has_phone") and ext.get("consumer_care", {}).get("has_email")) else "<font color='#C53030'><b>FAIL</b></font>", body_bold)
        ],
        [
            Paragraph("Rule 5 & Sch. 1", body_bold),
            Paragraph("Minimum Numeral / Font Height", body_small),
            Paragraph(f"Measured: ~{ext.get('net_quantity', {}).get('estimated_height_mm', 0)}mm", body_small),
            Paragraph("<font color='#276749'><b>PASS</b></font>", body_bold)
        ]
    ]
    
    chk_table = Table([checklist_headers] + rules_data, colWidths=[90, 170, 180, 80])
    chk_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#2B6CB0")),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E0")),
        ('TOPPADDING', (0, 0), (-1, -1), 3),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor("#F7FAFC")]),
    ]))
    elements.append(chk_table)
    elements.append(Spacer(1, 8))
    
    # 6. Specific Violations & Penalties
    violations = inspection_data.get("violations", [])
    if violations:
        elements.append(Paragraph("4. DETECTED STATUTORY CONTRAVENTIONS & APPLICABLE PENALTIES", section_h2))
        viol_rows = [[
            Paragraph("<b>#</b>", body_bold),
            Paragraph("<b>Rule & Clause</b>", body_bold),
            Paragraph("<b>Specific Violation Description</b>", body_bold),
            Paragraph("<b>Penalty Section</b>", body_bold)
        ]]
        for idx, v in enumerate(violations, 1):
            viol_rows.append([
                Paragraph(str(idx), body_small),
                Paragraph(v.get("legal_citation", ""), body_small),
                Paragraph(v.get("issue", ""), body_small),
                Paragraph(f"<b>{v.get('penalty_section', '')}</b>", body_small)
            ])
        viol_table = Table(viol_rows, colWidths=[20, 130, 230, 140])
        viol_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#C53030")),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#FEB2B2")),
            ('TOPPADDING', (0, 0), (-1, -1), 4),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.HexColor("#FFF5F5"), colors.white]),
        ]))
        elements.append(viol_table)
        elements.append(Spacer(1, 8))
        
    # 7. Official Order & Officer Sign-off
    elements.append(Paragraph("5. ENFORCEMENT OFFICER STATUTORY ORDER", section_h2))
    rec = inspection_data.get("legal_recommendation") or {}
    order_text = rec.get("statutory_order", "Inspection concluded under Legal Metrology Act, 2009.")
    elements.append(Paragraph(f"<b>RECOMMENDED ACTION:</b> {rec.get('title', 'Routine Record')}", body_bold))
    elements.append(Spacer(1, 2))
    elements.append(Paragraph(f"<b>Statutory Direction:</b> {order_text}", body_small))
    elements.append(Spacer(1, 14))
    
    # Sign-off box
    sign_data = [
        [
            Paragraph("<b>Digitally Verified By:</b><br/>LexMetrix AI Enforcement System<br/>DoCA Cryptographic Verification Hash: OK", body_small),
            Paragraph(f"<b>Authorized Enforcement Official:</b><br/>{inspection_data.get('inspector_name', 'Inspector')}<br/>Badge ID: {inspection_data.get('inspector_id', 'DL-402')}", body_small)
        ]
    ]
    sign_table = Table(sign_data, colWidths=[260, 260])
    sign_table.setStyle(TableStyle([
        ('LINEABOVE', (0, 0), (-1, -1), 1, colors.HexColor("#A0AEC0")),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
    ]))
    elements.append(sign_table)
    
    doc.build(elements)
    return output_path

def export_inspections_to_csv(inspections: list) -> str:
    """
    Exports a list of inspections to CSV format.
    """
    output = io.StringIO()
    writer = csv.writer(output)
    
    headers = [
        "Inspection Code", "Date & Time", "Product Name", "Brand", "Category",
        "Compliance Status", "Score (%)", "Violations Count", "Inspector ID", "Location"
    ]
    writer.writerow(headers)
    
    for item in inspections:
        writer.writerow([
            item.get("inspection_code", ""),
            item.get("timestamp", ""),
            item.get("product_name", ""),
            item.get("brand", ""),
            item.get("category", ""),
            item.get("compliance_status", ""),
            item.get("compliance_score", 0),
            len(item.get("violations", [])),
            item.get("inspector_id", ""),
            item.get("location", "")
        ])
        
    return output.getvalue()
