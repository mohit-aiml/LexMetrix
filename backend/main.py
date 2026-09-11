"""
LexMetrix - Main FastAPI Application
Connects CV Preprocessing, OCR, Legal Metrology Rule Engine,
Database, Reporting Engine, and Static Web UI.
"""

import os
import uuid
import shutil
from datetime import datetime
from typing import Optional, Dict, Any, List

from fastapi import FastAPI, File, UploadFile, Form, HTTPException, Query, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, StreamingResponse, JSONResponse
from pydantic import BaseModel

from backend.database import (
    init_db, save_inspection, get_inspection_by_id,
    get_all_inspections, get_rules, update_rule, get_stats
)
from backend.cv_engine import (
    assess_image_quality, enhance_image, load_image,
    draw_evidence_annotations, estimate_pdp_area
)
from backend.ocr_engine import run_ocr, extract_all_declarations
from backend.rule_engine import LegalMetrologyRuleEngine
from backend.report_engine import generate_pdf_report, export_inspections_to_csv
from backend.sample_generator import create_sample_labels

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STATIC_SAMPLES_DIR = os.path.join(BASE_DIR, "uploads", "samples")

if os.environ.get("VERCEL"):
    UPLOAD_DIR = "/tmp/uploads"
    REPORTS_DIR = "/tmp/reports"
else:
    UPLOAD_DIR = os.path.join(BASE_DIR, "uploads")
    REPORTS_DIR = os.path.join(UPLOAD_DIR, "reports")

FRONTEND_DIR = os.path.join(BASE_DIR, "frontend")

os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(REPORTS_DIR, exist_ok=True)
os.makedirs(FRONTEND_DIR, exist_ok=True)

# Copy static sample images into uploads directory if running on Vercel
if os.environ.get("VERCEL"):
    target_samples = os.path.join(UPLOAD_DIR, "samples")
    os.makedirs(target_samples, exist_ok=True)
    if os.path.exists(STATIC_SAMPLES_DIR):
        for fname in os.listdir(STATIC_SAMPLES_DIR):
            s_src = os.path.join(STATIC_SAMPLES_DIR, fname)
            if os.path.isfile(s_src):
                shutil.copyfile(s_src, os.path.join(target_samples, fname))

# Initialize DB and samples
try:
    init_db()
    create_sample_labels()
except Exception as e:
    print(f"Init warning: {e}")

app = FastAPI(
    title="LexMetrix API",
    description="Automated Legal Metrology Compliance Checking & Enforcement System",
    version="2.0.0"
)

# Enable CORS for local/cross-origin development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

rule_engine = LegalMetrologyRuleEngine()

# Model for Rule update
class RuleUpdateRequest(BaseModel):
    is_mandatory: int
    parameters: Dict[str, Any]

@app.get("/api/health")
def health_check():
    return {
        "status": "healthy",
        "system": "LexMetrix Legal Metrology AI",
        "version": "2.0.0",
        "timestamp": datetime.now().isoformat()
    }

@app.get("/api/dashboard/stats")
def get_dashboard_stats():
    """Returns enforcement statistics, compliance rate, and rule violation breakdown."""
    stats = get_stats()
    return stats

@app.get("/api/rules")
def list_rules():
    """Returns version-controlled statutory rules."""
    return get_rules()

@app.put("/api/rules/{rule_id}")
def modify_rule(rule_id: str, payload: RuleUpdateRequest):
    success = update_rule(rule_id, payload.is_mandatory, payload.parameters)
    if not success:
        raise HTTPException(status_code=404, detail=f"Rule {rule_id} not found")
    return {"status": "success", "message": f"Rule {rule_id} updated successfully"}

@app.get("/api/samples")
def list_sample_products():
    """Returns pre-loaded packaging samples for immediate 1-click evaluation."""
    samples = [
        {
            "id": "sample1",
            "name": "Golden Bake Butter Cookies (200g)",
            "brand": "Golden Treat Foods",
            "category": "Biscuits & Confectionery",
            "image_url": "/uploads/samples/sample1_compliant_cookies.png",
            "expected_verdict": "COMPLIANT",
            "description": "Standard packaged commodity with complete statutory declarations, tax disclaimers, and correct SI unit."
        },
        {
            "id": "sample2",
            "name": "Crunchy Potato Chips (120g)",
            "brand": "Tasty Snacks Ltd",
            "category": "Snacks & Savouries",
            "image_url": "/uploads/samples/sample2_mrp_tax_violation.png",
            "expected_verdict": "NON_COMPLIANT",
            "description": "Violation of Rule 6(1)(e): MRP declared without mandatory '(incl. of all taxes)' phrase."
        },
        {
            "id": "sample3",
            "name": "Super Clean Detergent Powder (500g)",
            "brand": "Hygiene Home Products",
            "category": "Household & Detergents",
            "image_url": "/uploads/samples/sample3_illegal_unit_violation.png",
            "expected_verdict": "NON_COMPLIANT",
            "description": "Violation of Rule 6(1)(c) & Second Schedule: Prohibited unit symbol 'gms' used instead of standard 'g'."
        },
        {
            "id": "sample4",
            "name": "Royal Pure Mustard Oil (1L)",
            "brand": "Royal Agro Mills",
            "category": "Edible Oils & Foods",
            "image_url": "/uploads/samples/sample4_missing_email_and_pin.png",
            "expected_verdict": "NON_COMPLIANT",
            "description": "Violation of Rule 6(1)(n) & 6(1)(a): Consumer care missing mandatory email, address missing PIN code."
        },
        {
            "id": "sample5",
            "name": "Blurry Capture Test Package",
            "brand": "Quality Assurance Demo",
            "category": "Quality Benchmark",
            "image_url": "/uploads/samples/sample5_blurry_scan.png",
            "expected_verdict": "WARNING",
            "description": "Demonstrates automated Laplacian blur detection and evidentiary standard rejection."
        }
    ]
    return samples

@app.post("/api/scan")
async def scan_package(
    file: Optional[UploadFile] = File(None),
    sample_id: Optional[str] = Form(None),
    product_name: str = Form("Packaged Commodity"),
    brand: str = Form("Retail Brand"),
    category: str = Form("General FMCG"),
    inspector_name: str = Form("Inspector Rajesh Sharma"),
    inspector_id: str = Form("DOCA-DL-402"),
    location: str = Form("Retail Store, New Delhi"),
    notes: str = Form("")
):
    """
    Core Compliance Pipeline:
    1. Ingestion (Upload, Camera capture, or Sample ID)
    2. CV Quality Assessment (Laplacian blur & lighting)
    3. CLAHE Image Enhancement
    4. Hardware-Accelerated OCR
    5. Legal Metrology Rule Evaluation
    6. Annotated Visual Evidence Rendering
    7. PDF Inspection Notice Generation
    8. SQLite Persistence & Audit Record
    """
    file_id = str(uuid.uuid4())[:8]
    raw_filename = f"scan_{file_id}.png"
    raw_filepath = os.path.join(UPLOAD_DIR, raw_filename)
    
    # Handle sample selection or uploaded file
    if sample_id:
        sample_map = {
            "sample1": ("sample1_compliant_cookies.png", "Golden Bake Butter Cookies", "Golden Treat Foods", "Biscuits & Confectionery"),
            "sample2": ("sample2_mrp_tax_violation.png", "Crunchy Potato Chips", "Tasty Snacks Ltd", "Snacks & Savouries"),
            "sample3": ("sample3_illegal_unit_violation.png", "Super Clean Detergent", "Hygiene Home Products", "Household & Detergents"),
            "sample4": ("sample4_missing_email_and_pin.png", "Royal Pure Mustard Oil", "Royal Agro Mills", "Edible Oils"),
            "sample5": ("sample5_blurry_scan.png", "Blurry Demo Package", "Quality Assurance", "Testing")
        }
        if sample_id in sample_map:
            s_file, s_prod, s_brand, s_cat = sample_map[sample_id]
            src_path = os.path.join(UPLOAD_DIR, "samples", s_file)
            shutil.copyfile(src_path, raw_filepath)
            product_name = s_prod
            brand = s_brand
            category = s_cat
        else:
            raise HTTPException(status_code=400, detail="Invalid sample_id specified")
    elif file:
        with open(raw_filepath, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    else:
        raise HTTPException(status_code=400, detail="Either file upload or sample_id must be provided")

    # 1. CV Quality Assessment
    cv_img = load_image(raw_filepath)
    quality_metrics = assess_image_quality(cv_img)
    pdp_info = estimate_pdp_area(cv_img)
    
    # 2. Preprocess & Enhance
    enhanced_cv_img = enhance_image(cv_img)
    
    # 3. High-Accuracy OCR
    ocr_result = run_ocr(raw_filepath)
    
    # 4. Parse Declarations
    declarations = extract_all_declarations(ocr_result)
    
    # Update product metadata if detected in OCR
    if declarations.get("manufacturer", {}).get("company_name"):
        pass
        
    # 5. Statutory Rule Evaluation
    compliance_result = rule_engine.evaluate(declarations, pdp_info)
    
    # 6. Render Evidence Annotations
    annotated_filename = f"annotated_{file_id}.png"
    annotated_filepath = os.path.join(UPLOAD_DIR, annotated_filename)
    draw_evidence_annotations(
        raw_filepath,
        compliance_result.get("annotations", []),
        annotated_filepath
    )
    
    # 7. Generate Official PDF Notice / Inspection Report
    inspection_code = f"LM-{datetime.now().strftime('%Y%m%d')}-{file_id.upper()}"
    pdf_filename = f"report_{inspection_code}.pdf"
    pdf_filepath = os.path.join(REPORTS_DIR, pdf_filename)
    
    inspection_record_data = {
        "inspection_code": inspection_code,
        "product_name": product_name,
        "brand": brand,
        "category": category,
        "image_path": raw_filepath,
        "annotated_image_path": annotated_filepath,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "inspector_name": inspector_name,
        "inspector_id": inspector_id,
        "location": location,
        "compliance_status": compliance_result["compliance_status"],
        "compliance_score": compliance_result["compliance_score"],
        "extracted_data": declarations,
        "violations": compliance_result["violations"],
        "blur_score": quality_metrics["blur_score"],
        "notes": notes,
        "legal_recommendation": compliance_result["legal_recommendation"]
    }
    
    try:
        generate_pdf_report(inspection_record_data, pdf_filepath)
    except Exception as e:
        print(f"PDF generation error: {e}")
        
    # 8. Save to SQLite Database
    inspection_id = save_inspection(inspection_record_data)
    
    return {
        "id": inspection_id,
        "inspection_code": inspection_code,
        "product_name": product_name,
        "brand": brand,
        "category": category,
        "compliance_status": compliance_result["compliance_status"],
        "compliance_score": compliance_result["compliance_score"],
        "quality_metrics": quality_metrics,
        "pdp_info": pdp_info,
        "extracted_data": declarations,
        "violations": compliance_result["violations"],
        "rule_evaluations": compliance_result["rule_evaluations"],
        "legal_recommendation": compliance_result["legal_recommendation"],
        "summary": compliance_result["summary"],
        "image_url": f"/uploads/{raw_filename}",
        "annotated_image_url": f"/uploads/{annotated_filename}",
        "pdf_report_url": f"/api/inspections/{inspection_id}/pdf",
        "timestamp": inspection_record_data["timestamp"]
    }

@app.get("/api/inspections")
def list_inspections(
    query: str = Query("", description="Search by product, brand, or code"),
    status: str = Query("ALL", description="Filter by status"),
    category: str = Query("ALL", description="Filter by category"),
    limit: int = Query(100, description="Result limit")
):
    """Search and retrieve past inspection repository."""
    records = get_all_inspections(limit=limit, query=query, status=status, category=category)
    # Add URLs for web consumption
    for r in records:
        if r.get("image_path"):
            r["image_url"] = f"/uploads/{os.path.basename(r['image_path'])}"
        if r.get("annotated_image_path"):
            r["annotated_image_url"] = f"/uploads/{os.path.basename(r['annotated_image_path'])}"
        r["pdf_report_url"] = f"/api/inspections/{r['id']}/pdf"
    return records

@app.get("/api/inspections/{inspection_id}")
def get_inspection_details(inspection_id: int):
    """Retrieve full details of a specific inspection."""
    record = get_inspection_by_id(inspection_id)
    if not record:
        raise HTTPException(status_code=404, detail="Inspection not found")
    if record.get("image_path"):
        record["image_url"] = f"/uploads/{os.path.basename(record['image_path'])}"
    if record.get("annotated_image_path"):
        record["annotated_image_url"] = f"/uploads/{os.path.basename(record['annotated_image_path'])}"
    record["pdf_report_url"] = f"/api/inspections/{record['id']}/pdf"
    return record

@app.get("/api/inspections/{inspection_id}/pdf")
def download_inspection_pdf(inspection_id: int):
    """Download official inspection notice / report PDF."""
    record = get_inspection_by_id(inspection_id)
    if not record:
        raise HTTPException(status_code=404, detail="Inspection not found")
        
    code = record.get("inspection_code", f"LM-{inspection_id}")
    pdf_filename = f"report_{code}.pdf"
    pdf_path = os.path.join(REPORTS_DIR, pdf_filename)
    
    # Regenerate if not existing
    if not os.path.exists(pdf_path):
        generate_pdf_report(record, pdf_path)
        
    return FileResponse(
        pdf_path,
        media_type="application/pdf",
        filename=pdf_filename,
        headers={"Content-Disposition": f"attachment; filename={pdf_filename}"}
    )

@app.get("/api/inspections/export/csv")
def export_csv():
    """Export inspection database to CSV format."""
    records = get_all_inspections(limit=1000)
    csv_content = export_inspections_to_csv(records)
    return Response(
        content=csv_content,
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=lexmetrix_inspections_{datetime.now().strftime('%Y%m%d')}.csv"}
    )

@app.post("/api/seed-demo-data")
def seed_demo_inspections():
    """Pre-populates the database with realistic inspections across Indian retail hubs."""
    demo_items = [
        {
            "inspection_code": "LM-20260901-A101",
            "product_name": "Haldiram's Aloo Bhujia (400g)",
            "brand": "Haldiram's",
            "category": "Snacks & Confectionery",
            "location": "Blinkit Dark Store, Sector 62, Noida",
            "inspector_name": "Amit Sharma",
            "inspector_id": "DOCA-UP-108",
            "compliance_status": "COMPLIANT",
            "compliance_score": 100.0,
            "timestamp": "2026-09-01 10:30:15",
            "extracted_data": {
                "mrp": {"amount": 95.0, "has_inclusive_taxes": True},
                "net_quantity": {"value": 400, "unit": "g", "is_standard_unit": True, "estimated_height_mm": 4.1},
                "manufacturer": {"company_name": "Haldiram Snacks Pvt Ltd", "has_pincode": True},
                "dates": {"mfg_date": "08/2026"},
                "consumer_care": {"has_phone": True, "has_email": True, "phone": "0120-2400500", "email": "care@haldirams.com"},
                "origin": {"country": "India", "is_declared": True}
            },
            "violations": []
        },
        {
            "inspection_code": "LM-20260903-B204",
            "product_name": "Imported Hazelnut Choco Spread (350g)",
            "brand": "SweetChoc Europe",
            "category": "Imported Goods",
            "location": "Nature's Basket, Bandra West, Mumbai",
            "inspector_name": "Pooja Patil",
            "inspector_id": "DOCA-MH-312",
            "compliance_status": "NON_COMPLIANT",
            "compliance_score": 42.0,
            "timestamp": "2026-09-03 14:15:22",
            "extracted_data": {
                "mrp": {"amount": 420.0, "has_inclusive_taxes": False},
                "net_quantity": {"value": 350, "unit": "g", "is_standard_unit": True},
                "manufacturer": {"company_name": "Euro Sweets GmbH", "has_pincode": False},
                "dates": {"mfg_date": "05/2026"},
                "consumer_care": {"has_phone": False, "has_email": False},
                "origin": {"country": "Germany", "is_declared": True}
            },
            "violations": [
                {
                    "rule_id": "RULE_6_1_E_MRP",
                    "legal_citation": "Rule 6(1)(e) of Legal Metrology (PC) Rules, 2011",
                    "issue": "MRP declared without '(incl. of all taxes)'.",
                    "penalty_section": "Section 36(1) of Legal Metrology Act, 2009"
                },
                {
                    "rule_id": "RULE_6_1_N_CONSUMER_CARE",
                    "legal_citation": "Rule 6(1)(n) of Legal Metrology (PC) Rules, 2011",
                    "issue": "Missing Indian importer consumer care telephone helpline and email.",
                    "penalty_section": "Rule 6(1)(n) read with Rule 32"
                }
            ]
        },
        {
            "inspection_code": "LM-20260906-C309",
            "product_name": "Herbal Ayurvedic Hair Cleanser (250ml)",
            "brand": "VedaAura",
            "category": "Cosmetics & Personal Care",
            "location": "Reliance Smart Bazaar, Indiranagar, Bengaluru",
            "inspector_name": "K. R. Murthy",
            "inspector_id": "DOCA-KA-550",
            "compliance_status": "NON_COMPLIANT",
            "compliance_score": 62.0,
            "timestamp": "2026-09-06 11:40:00",
            "extracted_data": {
                "mrp": {"amount": 210.0, "has_inclusive_taxes": True},
                "net_quantity": {"value": 250, "unit": "ml", "is_standard_unit": True},
                "manufacturer": {"company_name": "Veda Organics", "has_pincode": False},
                "dates": {"mfg_date": "07/2026"},
                "consumer_care": {"has_phone": True, "has_email": False, "phone": "1800-333-8899"},
                "origin": {"country": "India", "is_declared": True}
            },
            "violations": [
                {
                    "rule_id": "RULE_6_1_N_CONSUMER_CARE",
                    "legal_citation": "Rule 6(1)(n) of Legal Metrology (PC) Rules, 2011",
                    "issue": "Missing mandatory consumer care email address.",
                    "penalty_section": "Rule 6(1)(n) read with Rule 32"
                }
            ]
        },
        {
            "inspection_code": "LM-20260908-D415",
            "product_name": "Premium Basmati Rice (5kg)",
            "brand": "Royal Harvest",
            "category": "Grains & Pulses",
            "location": "Metro Cash & Carry, Yeshwanthpur, Bengaluru",
            "inspector_name": "K. R. Murthy",
            "inspector_id": "DOCA-KA-550",
            "compliance_status": "COMPLIANT",
            "compliance_score": 100.0,
            "timestamp": "2026-09-08 16:20:10",
            "extracted_data": {
                "mrp": {"amount": 625.0, "has_inclusive_taxes": True, "has_unit_sale_price": True, "unit_sale_price": "₹125.00/kg"},
                "net_quantity": {"value": 5, "unit": "kg", "is_standard_unit": True, "estimated_height_mm": 6.2},
                "manufacturer": {"company_name": "Harvest Agri Mills Ltd", "has_pincode": True},
                "dates": {"mfg_date": "08/2026"},
                "consumer_care": {"has_phone": True, "has_email": True, "phone": "1800-419-5500", "email": "help@royalharvest.in"},
                "origin": {"country": "India", "is_declared": True}
            },
            "violations": []
        }
    ]
    
    inserted_ids = []
    for item in demo_items:
        # Check if already seeded
        existing = get_all_inspections(limit=1, query=item["inspection_code"])
        if not existing:
            item["image_path"] = os.path.join(UPLOAD_DIR, "samples", "sample1_compliant_cookies.png")
            item["annotated_image_path"] = item["image_path"]
            item["blur_score"] = 185.0
            item["notes"] = "Routine field inspection at regional retail outlet."
            item["legal_recommendation"] = rule_engine._generate_legal_recommendation(item["compliance_status"], item["violations"])
            # Generate PDF
            pdf_path = os.path.join(REPORTS_DIR, f"report_{item['inspection_code']}.pdf")
            try:
                generate_pdf_report(item, pdf_path)
            except Exception:
                pass
            iid = save_inspection(item)
            inserted_ids.append(iid)
            
    return {"status": "success", "seeded_count": len(inserted_ids), "ids": inserted_ids}

# Mount static directories
app.mount("/uploads", StaticFiles(directory=UPLOAD_DIR), name="uploads")
app.mount("/", StaticFiles(directory=FRONTEND_DIR, html=True), name="frontend")
