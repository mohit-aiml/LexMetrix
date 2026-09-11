"""
LexMetrix - Automated Test Suite
Verifies Computer Vision assessment, OCR extraction, Rule Engine enforcement,
and PDF report generation across standard and violating packaging samples.
"""

import os
import sys
import unittest

# Add root directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.cv_engine import assess_image_quality, enhance_image, load_image, draw_evidence_annotations
from backend.ocr_engine import run_ocr, extract_all_declarations
from backend.rule_engine import LegalMetrologyRuleEngine
from backend.report_engine import generate_pdf_report
from backend.database import init_db, save_inspection, get_inspection_by_id, get_all_inspections

class TestLexMetrixCompliance(unittest.TestCase):
    
    @classmethod
    def setUpClass(cls):
        init_db()
        cls.samples_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "uploads", "samples")
        cls.engine = LegalMetrologyRuleEngine()

    def test_01_cv_blur_detection(self):
        sharp_path = os.path.join(self.samples_dir, "sample1_compliant_cookies.png")
        blurry_path = os.path.join(self.samples_dir, "sample5_blurry_scan.png")
        
        sharp_img = load_image(sharp_path)
        blurry_img = load_image(blurry_path)
        
        sharp_qual = assess_image_quality(sharp_img)
        blurry_qual = assess_image_quality(blurry_img)
        
        self.assertFalse(sharp_qual["is_blurry"], "Sharp image should not be flagged as blurry")
        self.assertTrue(blurry_qual["is_blurry"], "Blurry image must be flagged with is_blurry=True")
        self.assertGreater(sharp_qual["blur_score"], blurry_qual["blur_score"])

    def test_02_sample1_fully_compliant(self):
        img_path = os.path.join(self.samples_dir, "sample1_compliant_cookies.png")
        ocr_res = run_ocr(img_path)
        declarations = extract_all_declarations(ocr_res)
        
        # Check extracted fields
        self.assertIsNotNone(declarations["mrp"]["amount"])
        self.assertTrue(declarations["mrp"]["has_inclusive_taxes"])
        self.assertEqual(declarations["net_quantity"]["unit"], "g")
        self.assertTrue(declarations["net_quantity"]["is_standard_unit"])
        self.assertTrue(declarations["manufacturer"]["has_pincode"])
        self.assertTrue(declarations["consumer_care"]["has_email"])
        self.assertTrue(declarations["consumer_care"]["has_phone"])
        
        # Evaluate rules
        eval_result = self.engine.evaluate(declarations, {})
        self.assertEqual(eval_result["compliance_status"], "COMPLIANT")
        self.assertEqual(eval_result["compliance_score"], 100.0)
        self.assertEqual(len(eval_result["violations"]), 0)

    def test_03_sample2_mrp_tax_violation(self):
        img_path = os.path.join(self.samples_dir, "sample2_mrp_tax_violation.png")
        ocr_res = run_ocr(img_path)
        declarations = extract_all_declarations(ocr_res)
        
        self.assertIsNotNone(declarations["mrp"]["amount"])
        self.assertFalse(declarations["mrp"]["has_inclusive_taxes"], "Sample 2 deliberately omitted taxes text")
        
        eval_result = self.engine.evaluate(declarations, {})
        self.assertEqual(eval_result["compliance_status"], "NON_COMPLIANT")
        
        violated_rules = [v["rule_id"] for v in eval_result["violations"]]
        self.assertIn("RULE_6_1_E_MRP", violated_rules, "Must flag Rule 6(1)(e) MRP violation")

    def test_04_sample3_prohibited_unit_violation(self):
        img_path = os.path.join(self.samples_dir, "sample3_illegal_unit_violation.png")
        ocr_res = run_ocr(img_path)
        declarations = extract_all_declarations(ocr_res)
        
        self.assertFalse(declarations["net_quantity"]["is_standard_unit"])
        self.assertEqual(declarations["net_quantity"]["forbidden_unit_found"], "gms")
        
        eval_result = self.engine.evaluate(declarations, {})
        self.assertEqual(eval_result["compliance_status"], "NON_COMPLIANT")
        
        violated_rules = [v["rule_id"] for v in eval_result["violations"]]
        self.assertIn("RULE_6_1_C_NET_QTY", violated_rules, "Must flag illegal unit symbol 'gms'")

    def test_05_sample4_consumer_care_missing_email_and_pin(self):
        img_path = os.path.join(self.samples_dir, "sample4_missing_email_and_pin.png")
        ocr_res = run_ocr(img_path)
        declarations = extract_all_declarations(ocr_res)
        
        self.assertFalse(declarations["consumer_care"]["has_email"], "Missing email should be caught")
        self.assertFalse(declarations["manufacturer"]["has_pincode"], "Missing PIN code should be caught")
        
        eval_result = self.engine.evaluate(declarations, {})
        self.assertNotEqual(eval_result["compliance_status"], "COMPLIANT")
        violated_rules = [v["rule_id"] for v in eval_result["violations"]]
        self.assertIn("RULE_6_1_N_CONSUMER_CARE", violated_rules)

    def test_06_pdf_report_generation(self):
        test_data = {
            "inspection_code": "LM-TEST-2026-999",
            "timestamp": "2026-09-11 21:55:00",
            "product_name": "Sample Test Product",
            "brand": "BrandX",
            "category": "Snacks & Confectionery",
            "inspector_name": "Senior Inspector S. K. Verma",
            "inspector_id": "DOCA-INSP-101",
            "location": "Central Mart, Connaught Place, New Delhi",
            "compliance_status": "NON_COMPLIANT",
            "compliance_score": 45.0,
            "image_path": os.path.join(self.samples_dir, "sample2_mrp_tax_violation.png"),
            "extracted_data": {
                "mrp": {"amount": 35.0, "has_inclusive_taxes": False},
                "net_quantity": {"value": 120, "unit": "g", "is_standard_unit": True, "estimated_height_mm": 3.2},
                "manufacturer": {"company_name": "Tasty Snacks Ltd", "has_pincode": True},
                "dates": {"mfg_date": "09/2026"},
                "consumer_care": {"has_phone": True, "has_email": True, "phone": "1800-444-5566"},
                "origin": {"is_declared": True, "country": "India"}
            },
            "violations": [
                {
                    "rule_id": "RULE_6_1_E_MRP",
                    "legal_citation": "Rule 6(1)(e) of Legal Metrology (PC) Rules, 2011",
                    "issue": "MRP declared without mandatory '(incl. of all taxes)' phrase.",
                    "penalty_section": "Section 36(1) of Legal Metrology Act, 2009"
                }
            ],
            "legal_recommendation": {
                "action": "ENFORCEMENT_NOTICE",
                "title": "Statutory Notice Recommended",
                "statutory_order": "Issue notice under Section 36(1) for missing tax disclaimer."
            }
        }
        
        pdf_out = os.path.join(self.samples_dir, "test_output_report.pdf")
        gen_path = generate_pdf_report(test_data, pdf_out)
        self.assertTrue(os.path.exists(gen_path))
        self.assertGreater(os.path.getsize(gen_path), 500)

if __name__ == "__main__":
    unittest.main()
