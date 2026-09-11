"""
LexMetrix - Statutory Legal Metrology Rule Engine
Evaluates compliance against Legal Metrology (Packaged Commodities) Rules, 2011,
incorporating 2017 and 2021 amendments, the First Schedule (Font Heights),
and Second Schedule (Standard Metric Units).
"""

from typing import Dict, Any, List, Tuple
import json

class LegalMetrologyRuleEngine:
    """
    Automated statutory compliance evaluator under Legal Metrology Act, 2009.
    """
    
    def __init__(self, rules_config: List[Dict[str, Any]] = None):
        self.rules_config = {r["rule_id"]: r for r in (rules_config or [])}

    def evaluate(self, declarations: Dict[str, Any], image_meta: Dict[str, Any]) -> Dict[str, Any]:
        violations: List[Dict[str, Any]] = []
        rule_evaluations: List[Dict[str, Any]] = []
        annotations: List[Dict[str, Any]] = []
        
        # 1. Rule 6(1)(a): Manufacturer / Packer / Importer Name & Complete Address
        mfg = declarations.get("manufacturer", {})
        mfg_has_name = bool(mfg.get("company_name"))
        mfg_has_pin = bool(mfg.get("has_pincode"))
        mfg_bbox = mfg.get("bbox")
        
        if not mfg_has_name:
            v = {
                "rule_id": "RULE_6_1_A_MFG",
                "rule_title": "Manufacturer / Packer Identity & Address",
                "legal_citation": "Rule 6(1)(a) of Legal Metrology (PC) Rules, 2011",
                "severity": "CRITICAL",
                "issue": "Missing declaration of Manufacturer, Packer, or Importer name and address.",
                "penalty_section": "Section 36(1) of Legal Metrology Act, 2009 (Fine up to ₹25,000 for 1st offence)",
                "found_value": None,
                "required_format": "Name and complete postal address with PIN code"
            }
            violations.append(v)
            rule_evaluations.append({"rule_id": "RULE_6_1_A_MFG", "status": "FAIL", "reason": v["issue"]})
        elif not mfg_has_pin:
            v = {
                "rule_id": "RULE_6_1_A_MFG",
                "rule_title": "Incomplete Address (Missing PIN Code)",
                "legal_citation": "Rule 6(1)(a) of Legal Metrology (PC) Rules, 2011",
                "severity": "MEDIUM",
                "issue": "Address declared without 6-digit postal PIN code, violating complete address requirement.",
                "penalty_section": "Rule 6(1)(a) read with Rule 32",
                "found_value": mfg.get("raw_text"),
                "required_format": "Address must contain 6-digit PIN code"
            }
            violations.append(v)
            rule_evaluations.append({"rule_id": "RULE_6_1_A_MFG", "status": "WARN", "reason": v["issue"]})
            if mfg_bbox:
                annotations.append({"bbox": mfg_bbox, "status": "WARNING", "label": "Address (Missing PIN)"})
        else:
            rule_evaluations.append({"rule_id": "RULE_6_1_A_MFG", "status": "PASS", "details": mfg.get("company_name")})
            if mfg_bbox:
                annotations.append({"bbox": mfg_bbox, "status": "COMPLIANT", "label": "Manufacturer Details OK"})

        # 2. Rule 6(1)(b): Country of Origin
        origin = declarations.get("origin", {})
        origin_bbox = origin.get("bbox")
        if not origin.get("is_declared"):
            v = {
                "rule_id": "RULE_6_1_B_ORIGIN",
                "rule_title": "Country of Origin Declaration",
                "legal_citation": "Rule 6(1)(b) of Legal Metrology (PC) Rules, 2011",
                "severity": "HIGH",
                "issue": "Country of Origin or 'Made in India' declaration not conspicuously found on packaging.",
                "penalty_section": "Rule 6(1)(b) read with Section 36",
                "found_value": None,
                "required_format": "Explicit 'Country of Origin: [Country]' or 'Made in [Country]'"
            }
            violations.append(v)
            rule_evaluations.append({"rule_id": "RULE_6_1_B_ORIGIN", "status": "FAIL", "reason": v["issue"]})
        else:
            rule_evaluations.append({"rule_id": "RULE_6_1_B_ORIGIN", "status": "PASS", "details": origin.get("country")})
            if origin_bbox:
                annotations.append({"bbox": origin_bbox, "status": "COMPLIANT", "label": f"Origin: {origin.get('country')}"})

        # 3. Rule 6(1)(c) & Second Schedule: Net Quantity & Metric Symbols
        qty = declarations.get("net_quantity", {})
        qty_bbox = qty.get("bbox")
        qty_val = qty.get("value")
        qty_unit = qty.get("unit")
        
        if qty_val is None:
            v = {
                "rule_id": "RULE_6_1_C_NET_QTY",
                "rule_title": "Net Quantity Declaration Missing",
                "legal_citation": "Rule 6(1)(c) of Legal Metrology (PC) Rules, 2011",
                "severity": "CRITICAL",
                "issue": "Net quantity is completely missing or illegible on packaging.",
                "penalty_section": "Section 36(1) of Legal Metrology Act, 2009",
                "found_value": None,
                "required_format": "Net Qty: [Number] [g/kg/ml/l/N]"
            }
            violations.append(v)
            rule_evaluations.append({"rule_id": "RULE_6_1_C_NET_QTY", "status": "FAIL", "reason": v["issue"]})
        elif not qty.get("is_standard_unit"):
            forbidden = qty.get("forbidden_unit_found", "non-standard")
            v = {
                "rule_id": "RULE_6_1_C_NET_QTY",
                "rule_title": "Non-Standard / Prohibited Metric Unit",
                "legal_citation": "Rule 6(1)(c) & Second Schedule of Legal Metrology (PC) Rules, 2011",
                "severity": "HIGH",
                "issue": f"Illegal unit symbol '{forbidden}' used. Second Schedule permits only standard symbols ('g', 'kg', 'ml', 'l', 'm', 'N', 'U'). Words like 'gms', 'grm', 'ltrs', 'kilos' are explicitly unlawful.",
                "penalty_section": "Section 36 & Rule 32 of Legal Metrology (PC) Rules, 2011",
                "found_value": f"{qty_val} {forbidden}",
                "required_format": f"Standard symbol (e.g. '{'g' if 'gm' in forbidden else 'l' if 'ltr' in forbidden else 'kg'}')"
            }
            violations.append(v)
            rule_evaluations.append({"rule_id": "RULE_6_1_C_NET_QTY", "status": "FAIL", "reason": v["issue"]})
            if qty_bbox:
                annotations.append({"bbox": qty_bbox, "status": "VIOLATION", "label": f"Illegal Unit: '{forbidden}'"})
        else:
            rule_evaluations.append({"rule_id": "RULE_6_1_C_NET_QTY", "status": "PASS", "details": f"{qty_val} {qty_unit}"})
            if qty_bbox:
                annotations.append({"bbox": qty_bbox, "status": "COMPLIANT", "label": f"Net Qty: {qty_val}{qty_unit}"})

        # 4. Rule 6(1)(d): Month & Year of Manufacture / Packing
        dates = declarations.get("dates", {})
        dates_bbox = dates.get("bbox")
        if not dates.get("mfg_date"):
            v = {
                "rule_id": "RULE_6_1_D_DATE",
                "rule_title": "Month & Year of Manufacture / Packing Missing",
                "legal_citation": "Rule 6(1)(d) of Legal Metrology (PC) Rules, 2011",
                "severity": "CRITICAL",
                "issue": "No manufacturing or pre-packing date declared on package.",
                "penalty_section": "Section 36(1) of Legal Metrology Act, 2009",
                "found_value": None,
                "required_format": "Month and Year (MM/YYYY or Month YYYY)"
            }
            violations.append(v)
            rule_evaluations.append({"rule_id": "RULE_6_1_D_DATE", "status": "FAIL", "reason": v["issue"]})
        else:
            rule_evaluations.append({"rule_id": "RULE_6_1_D_DATE", "status": "PASS", "details": dates.get("mfg_date")})
            if dates_bbox:
                annotations.append({"bbox": dates_bbox, "status": "COMPLIANT", "label": f"Mfg: {dates.get('mfg_date')}"})

        # 5. Rule 6(1)(e): Maximum Retail Price (MRP) & Tax Disclaimer
        mrp = declarations.get("mrp", {})
        mrp_bbox = mrp.get("bbox")
        mrp_amt = mrp.get("amount")
        has_taxes = mrp.get("has_inclusive_taxes", False)
        
        if mrp_amt is None:
            v = {
                "rule_id": "RULE_6_1_E_MRP",
                "rule_title": "Maximum Retail Price (MRP) Declaration Missing",
                "legal_citation": "Rule 6(1)(e) of Legal Metrology (PC) Rules, 2011",
                "severity": "CRITICAL",
                "issue": "Retail sale price / MRP not declared on package.",
                "penalty_section": "Section 36(1) of Legal Metrology Act, 2009",
                "found_value": None,
                "required_format": "MRP ₹ XX.XX (incl. of all taxes)"
            }
            violations.append(v)
            rule_evaluations.append({"rule_id": "RULE_6_1_E_MRP", "status": "FAIL", "reason": v["issue"]})
        elif not has_taxes:
            v = {
                "rule_id": "RULE_6_1_E_MRP",
                "rule_title": "Missing Mandatory '(incl. of all taxes)' Disclaimer",
                "legal_citation": "Rule 6(1)(e) of Legal Metrology (PC) Rules, 2011 (as amended 2021)",
                "severity": "CRITICAL",
                "issue": f"MRP declared as ₹{mrp_amt} without the mandatory statutory phrase '(incl. of all taxes)'. Consumers cannot be charged extra taxes.",
                "penalty_section": "Section 36(1) of Legal Metrology Act, 2009",
                "found_value": mrp.get("raw_text"),
                "required_format": "MRP ₹ XX.XX (incl. of all taxes)"
            }
            violations.append(v)
            rule_evaluations.append({"rule_id": "RULE_6_1_E_MRP", "status": "FAIL", "reason": v["issue"]})
            if mrp_bbox:
                annotations.append({"bbox": mrp_bbox, "status": "VIOLATION", "label": "MRP: Missing '(incl. of all taxes)'"})
        else:
            rule_evaluations.append({"rule_id": "RULE_6_1_E_MRP", "status": "PASS", "details": f"₹{mrp_amt} (incl. of all taxes)"})
            if mrp_bbox:
                annotations.append({"bbox": mrp_bbox, "status": "COMPLIANT", "label": f"MRP ₹{mrp_amt} (Taxes Incl.)"})

        # Unit Sale Price check for packages > 1kg / 1L
        if qty_val and qty_unit in ["kg", "l"] and qty_val > 1.0:
            if not mrp.get("has_unit_sale_price"):
                v = {
                    "rule_id": "RULE_6_1_E_USP",
                    "rule_title": "Missing Unit Sale Price (USP) for Large Package",
                    "legal_citation": "Rule 6(1)(e) Amendment Rules, 2021",
                    "severity": "MEDIUM",
                    "issue": f"Package net quantity is {qty_val}{qty_unit} (> 1{qty_unit}). Declaration of Unit Sale Price (₹ per {qty_unit} or per g/ml) is mandatory since 2022.",
                    "penalty_section": "Rule 6(1)(e) Second Proviso",
                    "found_value": None,
                    "required_format": f"Unit Sale Price: ₹ XX.XX / {qty_unit}"
                }
                violations.append(v)
                rule_evaluations.append({"rule_id": "RULE_6_1_E_USP", "status": "WARN", "reason": v["issue"]})

        # 6. Rule 6(1)(n): Consumer Care Details (4 Pillars)
        cc = declarations.get("consumer_care", {})
        cc_bbox = cc.get("bbox")
        has_phone = cc.get("has_phone", False)
        has_email = cc.get("has_email", False)
        
        if not has_phone and not has_email:
            v = {
                "rule_id": "RULE_6_1_N_CONSUMER_CARE",
                "rule_title": "Consumer Care Details Missing Entirely",
                "legal_citation": "Rule 6(1)(n) of Legal Metrology (PC) Rules, 2011",
                "severity": "CRITICAL",
                "issue": "Package lacks both telephone helpline and email address for consumer grievance redressal.",
                "penalty_section": "Section 36(1) of Legal Metrology Act, 2009",
                "found_value": None,
                "required_format": "Designation, Postal Address, Phone/Toll-Free & Email ID"
            }
            violations.append(v)
            rule_evaluations.append({"rule_id": "RULE_6_1_N_CONSUMER_CARE", "status": "FAIL", "reason": v["issue"]})
        elif not has_email:
            v = {
                "rule_id": "RULE_6_1_N_CONSUMER_CARE",
                "rule_title": "Missing Consumer Care Email Address",
                "legal_citation": "Rule 6(1)(n) of Legal Metrology (PC) Rules, 2011",
                "severity": "HIGH",
                "issue": "Consumer care telephone is provided but mandatory email address is missing.",
                "penalty_section": "Rule 6(1)(n) read with Rule 32",
                "found_value": f"Phone: {cc.get('phone')}",
                "required_format": "Mandatory Email ID (e.g. care@brand.com)"
            }
            violations.append(v)
            rule_evaluations.append({"rule_id": "RULE_6_1_N_CONSUMER_CARE", "status": "FAIL", "reason": v["issue"]})
            if cc_bbox:
                annotations.append({"bbox": cc_bbox, "status": "WARNING", "label": "Consumer Care (Missing Email)"})
        elif not has_phone:
            v = {
                "rule_id": "RULE_6_1_N_CONSUMER_CARE",
                "rule_title": "Missing Consumer Care Telephone / Toll-Free",
                "legal_citation": "Rule 6(1)(n) of Legal Metrology (PC) Rules, 2011",
                "severity": "HIGH",
                "issue": "Email is provided but mandatory contact telephone / toll-free number is missing.",
                "penalty_section": "Rule 6(1)(n) read with Rule 32",
                "found_value": f"Email: {cc.get('email')}",
                "required_format": "Mandatory Helpline / Toll-free number"
            }
            violations.append(v)
            rule_evaluations.append({"rule_id": "RULE_6_1_N_CONSUMER_CARE", "status": "FAIL", "reason": v["issue"]})
            if cc_bbox:
                annotations.append({"bbox": cc_bbox, "status": "WARNING", "label": "Consumer Care (Missing Phone)"})
        else:
            rule_evaluations.append({"rule_id": "RULE_6_1_N_CONSUMER_CARE", "status": "PASS", "details": f"Phone: {cc.get('phone')}, Email: {cc.get('email')}"})
            if cc_bbox:
                annotations.append({"bbox": cc_bbox, "status": "COMPLIANT", "label": "Consumer Care Complete"})

        # 7. Rule 6(1)(f): Batch / Lot Number
        batch = declarations.get("batch", {})
        batch_bbox = batch.get("bbox")
        if not batch.get("batch_number"):
            v = {
                "rule_id": "RULE_6_1_F_BATCH",
                "rule_title": "Missing Batch / Lot / Code Number",
                "legal_citation": "Rule 6(1)(f) of Legal Metrology (PC) Rules, 2011",
                "severity": "MEDIUM",
                "issue": "Batch or lot identification code missing, preventing product traceability.",
                "penalty_section": "Rule 6(1)(f) read with Rule 32",
                "found_value": None,
                "required_format": "Batch No. / Lot No. / B.No."
            }
            violations.append(v)
            rule_evaluations.append({"rule_id": "RULE_6_1_F_BATCH", "status": "WARN", "reason": v["issue"]})
        else:
            rule_evaluations.append({"rule_id": "RULE_6_1_F_BATCH", "status": "PASS", "details": batch.get("batch_number")})
            if batch_bbox:
                annotations.append({"bbox": batch_bbox, "status": "COMPLIANT", "label": f"Batch: {batch.get('batch_number')}"})

        # 8. Rule 5 & First Schedule: Font Size / Numeral Height Compliance
        est_height_mm = qty.get("estimated_height_mm", 0.0)
        numeral_height_px = qty.get("numeral_height_px", 0.0)
        
        # Determine prescribed minimum height under First Schedule Table
        prescribed_min_mm = 2.0  # default baseline
        if qty_val:
            normalized_g = qty_val
            if qty_unit in ["kg", "l"]:
                normalized_g = qty_val * 1000
            elif qty_unit in ["mg"]:
                normalized_g = qty_val / 1000
                
            if normalized_g <= 50:
                prescribed_min_mm = 1.0
            elif normalized_g <= 200:
                prescribed_min_mm = 2.0
            elif normalized_g <= 1000:
                prescribed_min_mm = 4.0
            else:
                prescribed_min_mm = 6.0
                
        font_check_passed = True
        if est_height_mm > 0 and est_height_mm < (prescribed_min_mm * 0.7):
            font_check_passed = False
            v = {
                "rule_id": "RULE_5_FONT_SIZE",
                "rule_title": "Non-Compliant Font Size / Numeral Height",
                "legal_citation": "Rule 5 & First Schedule of Legal Metrology (PC) Rules, 2011",
                "severity": "HIGH",
                "issue": f"Measured numeral height (~{est_height_mm}mm) is below the statutory minimum ({prescribed_min_mm}mm) mandated for net quantity of {qty_val}{qty_unit}.",
                "penalty_section": "Rule 5 read with Section 36",
                "found_value": f"Approx. {est_height_mm}mm ({numeral_height_px}px)",
                "required_format": f"Minimum {prescribed_min_mm}mm height"
            }
            violations.append(v)
            rule_evaluations.append({"rule_id": "RULE_5_FONT_SIZE", "status": "FAIL", "reason": v["issue"]})
            if qty_bbox:
                annotations.append({"bbox": qty_bbox, "status": "WARNING", "label": f"Font too small (<{prescribed_min_mm}mm)"})
        else:
            rule_evaluations.append({"rule_id": "RULE_5_FONT_SIZE", "status": "PASS", "details": f"Height ~{est_height_mm}mm >= {prescribed_min_mm}mm required"})

        # Scoring Logic
        total_rules = len(rule_evaluations)
        passed_rules = sum(1 for r in rule_evaluations if r["status"] == "PASS")
        warn_rules = sum(1 for r in rule_evaluations if r["status"] == "WARN")
        fail_rules = sum(1 for r in rule_evaluations if r["status"] == "FAIL")
        
        # Calculate weighted compliance score
        raw_score = ((passed_rules * 1.0 + warn_rules * 0.5) / max(total_rules, 1)) * 100.0
        
        # If critical failure exists, cap score
        has_critical = any(v.get("severity") == "CRITICAL" for v in violations)
        if has_critical:
            compliance_score = min(round(raw_score, 1), 48.0)
            status = "NON_COMPLIANT"
        elif fail_rules > 0:
            compliance_score = min(round(raw_score, 1), 68.0)
            status = "NON_COMPLIANT"
        elif warn_rules > 0:
            compliance_score = round(raw_score, 1)
            status = "REVIEW_RECOMMENDED"
        else:
            compliance_score = 100.0
            status = "COMPLIANT"

        # Generate Official Legal Recommendation for Inspector
        legal_recommendation = self._generate_legal_recommendation(status, violations)
        
        return {
            "compliance_status": status,
            "compliance_score": compliance_score,
            "violations": violations,
            "rule_evaluations": rule_evaluations,
            "annotations": annotations,
            "legal_recommendation": legal_recommendation,
            "summary": {
                "total_checked": total_rules,
                "passed": passed_rules,
                "warnings": warn_rules,
                "failures": fail_rules,
                "prescribed_min_font_mm": prescribed_min_mm,
                "measured_font_mm": est_height_mm
            }
        }

    def _generate_legal_recommendation(self, status: str, violations: List[Dict[str, Any]]) -> Dict[str, Any]:
        if status == "COMPLIANT":
            return {
                "action": "CLEARANCE_GRANTED",
                "title": "Package Compliant - No Legal Action Required",
                "statutory_order": "The scanned packaging bears all mandatory declarations in compliance with the Legal Metrology (Packaged Commodities) Rules, 2011. Clearance certificate generated.",
                "notice_type": "None"
            }
        elif status == "REVIEW_RECOMMENDED":
            return {
                "action": "SCRUTINY_NOTICE",
                "title": "Advisory / Rectification Notice Recommended",
                "statutory_order": "Minor packaging defects detected (e.g. missing PIN code or traceability batch number). Issue Form VII Scrutiny & Advisory Notice to the Packer/Manufacturer for rectification within 15 days.",
                "notice_type": "Advisory Notice under Rule 32"
            }
        else:
            # Non-compliant
            reasons = [f"{v['rule_id']} ({v['issue']})" for v in violations[:2]]
            return {
                "action": "ENFORCEMENT_NOTICE",
                "title": "Show Cause & Seizure Notice Recommended",
                "statutory_order": f"Substantive contravention of Legal Metrology (PC) Rules detected: {', '.join(reasons)}. Recommend issuing Statutory Notice under Section 36(1) of the Legal Metrology Act, 2009 with compounded compounding penalty under Section 48.",
                "notice_type": "Statutory Notice under Section 36(1)"
            }
