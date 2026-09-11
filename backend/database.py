"""
LexMetrix - Database Layer
Provides SQLite persistence for inspections, versioned Legal Metrology rules, and audit trails.
"""

import sqlite3
import json
import os
from datetime import datetime
from typing import Dict, Any, List, Optional

if os.environ.get("VERCEL"):
    DB_PATH = "/tmp/lexmetrix.db"
else:
    DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "lexmetrix.db")

DEFAULT_RULES = [
    {
        "rule_id": "RULE_6_1_A_MFG",
        "rule_name": "Manufacturer / Packer / Importer Name & Address",
        "legal_citation": "Rule 6(1)(a) of Legal Metrology (PC) Rules, 2011",
        "is_mandatory": 1,
        "description": "Every package shall bear the name and complete address of the manufacturer or packer or importer, including PIN code.",
        "parameters": json.dumps({"require_pincode": True, "min_address_len": 15})
    },
    {
        "rule_id": "RULE_6_1_B_ORIGIN",
        "rule_name": "Country of Origin",
        "legal_citation": "Rule 6(1)(b) of Legal Metrology (PC) Rules, 2011",
        "is_mandatory": 1,
        "description": "Declaration of Country of Origin or 'Made in India' / country of manufacture is mandatory.",
        "parameters": json.dumps({"mandatory_for_all": True})
    },
    {
        "rule_id": "RULE_6_1_C_NET_QTY",
        "rule_name": "Net Quantity & Standard Metric Units",
        "legal_citation": "Rule 6(1)(c) & Second Schedule of Legal Metrology (PC) Rules, 2011",
        "is_mandatory": 1,
        "description": "Net quantity must be declared in standard SI metric units (g, kg, ml, l, m, cm, mm, N, U). Non-standard units (gms, grm, ltrs, kilos) are strictly prohibited.",
        "parameters": json.dumps({
            "allowed_units": ["g", "kg", "ml", "l", "m", "cm", "mm", "N", "U"],
            "prohibited_units": ["gms", "grm", "gm", "kilo", "kilos", "ltr", "ltrs", "cc", "cu.cm"]
        })
    },
    {
        "rule_id": "RULE_6_1_D_DATE",
        "rule_name": "Month and Year of Manufacture / Packing",
        "legal_citation": "Rule 6(1)(d) of Legal Metrology (PC) Rules, 2011",
        "is_mandatory": 1,
        "description": "The month and year in which the commodity is manufactured or pre-packed or imported shall be declared.",
        "parameters": json.dumps({"allowed_formats": ["MM/YYYY", "Month YYYY", "MM/YY"]})
    },
    {
        "rule_id": "RULE_6_1_E_MRP",
        "rule_name": "Maximum Retail Price (MRP) & Tax Disclaimer",
        "legal_citation": "Rule 6(1)(e) of Legal Metrology (PC) Rules, 2011 (as amended 2021)",
        "is_mandatory": 1,
        "description": "MRP must be declared in Indian Currency with explicit words 'incl. of all taxes' or 'inclusive of all taxes'. Unit Sale Price (USP) required for packages > 1kg/1L.",
        "parameters": json.dumps({
            "require_inclusive_taxes": True,
            "currency_symbols": ["₹", "Rs.", "Rs", "INR"],
            "require_unit_sale_price": True
        })
    },
    {
        "rule_id": "RULE_6_1_N_CONSUMER_CARE",
        "rule_name": "Consumer Care Details (4 Mandatory Pillars)",
        "legal_citation": "Rule 6(1)(n) of Legal Metrology (PC) Rules, 2011",
        "is_mandatory": 1,
        "description": "Name and designation of contact person, address, telephone/toll-free number, and email ID must be declared.",
        "parameters": json.dumps({"require_phone": True, "require_email": True, "require_address": True})
    },
    {
        "rule_id": "RULE_6_1_F_BATCH",
        "rule_name": "Batch / Lot / Code Number",
        "legal_citation": "Rule 6(1)(f) of Legal Metrology (PC) Rules, 2011",
        "is_mandatory": 1,
        "description": "A batch number or code number enables traceability of the packaged product.",
        "parameters": json.dumps({"min_length": 3})
    },
    {
        "rule_id": "RULE_5_FONT_SIZE",
        "rule_name": "Font Size & Numeral Height Compliance",
        "legal_citation": "Rule 5 & First Schedule of Legal Metrology (PC) Rules, 2011",
        "is_mandatory": 1,
        "description": "Minimum numeral and letter height must comply with prescribed tables according to net quantity.",
        "parameters": json.dumps({
            "thresholds_weight": [
                {"max_g": 50, "min_height_mm": 1.0},
                {"max_g": 200, "min_height_mm": 2.0},
                {"max_g": 1000, "min_height_mm": 4.0},
                {"max_g": 999999, "min_height_mm": 6.0}
            ]
        })
    }
]

def get_connection():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_connection()
    cursor = conn.cursor()
    
    # Create inspections table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS inspections (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        inspection_code TEXT UNIQUE,
        product_name TEXT,
        brand TEXT,
        category TEXT,
        image_path TEXT,
        annotated_image_path TEXT,
        timestamp TEXT,
        inspector_name TEXT,
        inspector_id TEXT,
        location TEXT,
        compliance_status TEXT,
        compliance_score REAL,
        extracted_data TEXT,
        violations TEXT,
        blur_score REAL,
        notes TEXT
    )
    """)
    
    # Create rules table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS rules_config (
        rule_id TEXT PRIMARY KEY,
        rule_name TEXT,
        legal_citation TEXT,
        is_mandatory INTEGER,
        description TEXT,
        parameters TEXT,
        updated_at TEXT
    )
    """)
    
    # Create audit_logs table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS audit_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp TEXT,
        action TEXT,
        details TEXT,
        user TEXT
    )
    """)
    
    # Seed default rules if empty
    cursor.execute("SELECT COUNT(*) FROM rules_config")
    if cursor.fetchone()[0] == 0:
        now = datetime.now().isoformat()
        for r in DEFAULT_RULES:
            cursor.execute("""
            INSERT INTO rules_config (rule_id, rule_name, legal_citation, is_mandatory, description, parameters, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (r["rule_id"], r["rule_name"], r["legal_citation"], r["is_mandatory"], r["description"], r["parameters"], now))
            
    conn.commit()
    conn.close()

def save_inspection(data: Dict[str, Any]) -> int:
    conn = get_connection()
    cursor = conn.cursor()
    
    extracted_json = json.dumps(data.get("extracted_data", {}))
    violations_json = json.dumps(data.get("violations", []))
    
    cursor.execute("""
    INSERT INTO inspections (
        inspection_code, product_name, brand, category, image_path,
        annotated_image_path, timestamp, inspector_name, inspector_id,
        location, compliance_status, compliance_score, extracted_data,
        violations, blur_score, notes
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        data.get("inspection_code"),
        data.get("product_name", "Unknown Commodity"),
        data.get("brand", "Unknown Brand"),
        data.get("category", "General Food / FMCG"),
        data.get("image_path", ""),
        data.get("annotated_image_path", ""),
        data.get("timestamp", datetime.now().strftime("%Y-%m-%d %H:%M:%S")),
        data.get("inspector_name", "Inspector Rajesh Sharma"),
        data.get("inspector_id", "DOCA-DL-402"),
        data.get("location", "Supermarket Retail Hub, New Delhi"),
        data.get("compliance_status", "NON_COMPLIANT"),
        float(data.get("compliance_score", 0.0)),
        extracted_json,
        violations_json,
        float(data.get("blur_score", 0.0)),
        data.get("notes", "")
    ))
    
    inspection_id = cursor.lastrowid
    
    # Audit log entry
    cursor.execute("""
    INSERT INTO audit_logs (timestamp, action, details, user)
    VALUES (?, ?, ?, ?)
    """, (
        datetime.now().isoformat(),
        "INSPECTION_RECORDED",
        f"Inspection {data.get('inspection_code')} recorded with status {data.get('compliance_status')}",
        data.get("inspector_name", "Officer")
    ))
    
    conn.commit()
    conn.close()
    return inspection_id

def get_inspection_by_id(inspection_id: int) -> Optional[Dict[str, Any]]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM inspections WHERE id = ?", (inspection_id,))
    row = cursor.fetchone()
    conn.close()
    if not row:
        return None
    item = dict(row)
    item["extracted_data"] = json.loads(item["extracted_data"] or "{}")
    item["violations"] = json.loads(item["violations"] or "[]")
    return item

def get_all_inspections(limit: int = 100, query: str = "", status: str = "", category: str = "") -> List[Dict[str, Any]]:
    conn = get_connection()
    cursor = conn.cursor()
    
    sql = "SELECT * FROM inspections WHERE 1=1"
    params = []
    
    if query:
        sql += " AND (product_name LIKE ? OR brand LIKE ? OR inspection_code LIKE ?)"
        q = f"%{query}%"
        params.extend([q, q, q])
    if status and status != "ALL":
        sql += " AND compliance_status = ?"
        params.append(status)
    if category and category != "ALL":
        sql += " AND category = ?"
        params.append(category)
        
    sql += " ORDER BY id DESC LIMIT ?"
    params.append(limit)
    
    cursor.execute(sql, tuple(params))
    rows = cursor.fetchall()
    conn.close()
    
    results = []
    for r in rows:
        item = dict(r)
        item["extracted_data"] = json.loads(item["extracted_data"] or "{}")
        item["violations"] = json.loads(item["violations"] or "[]")
        results.append(item)
    return results

def get_rules() -> List[Dict[str, Any]]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM rules_config ORDER BY rule_id ASC")
    rows = cursor.fetchall()
    conn.close()
    
    rules = []
    for r in rows:
        item = dict(r)
        item["parameters"] = json.loads(item["parameters"] or "{}")
        rules.append(item)
    return rules

def update_rule(rule_id: str, is_mandatory: int, parameters: Dict[str, Any]) -> bool:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
    UPDATE rules_config
    SET is_mandatory = ?, parameters = ?, updated_at = ?
    WHERE rule_id = ?
    """, (is_mandatory, json.dumps(parameters), datetime.now().isoformat(), rule_id))
    affected = cursor.rowcount > 0
    conn.commit()
    conn.close()
    return affected

def get_stats() -> Dict[str, Any]:
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT COUNT(*) FROM inspections")
    total = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM inspections WHERE compliance_status = 'COMPLIANT'")
    compliant = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM inspections WHERE compliance_status = 'NON_COMPLIANT'")
    violations = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM inspections WHERE compliance_status = 'REVIEW_RECOMMENDED'")
    reviews = cursor.fetchone()[0]
    
    # Category breakdown
    cursor.execute("SELECT category, COUNT(*) as count FROM inspections GROUP BY category")
    categories = {row["category"]: row["count"] for row in cursor.fetchall()}
    
    # Top violated rules by parsing violations JSON
    cursor.execute("SELECT violations FROM inspections WHERE compliance_status != 'COMPLIANT'")
    all_violations_rows = cursor.fetchall()
    conn.close()
    
    violation_counts = {}
    for row in all_violations_rows:
        try:
            viols = json.loads(row["violations"] or "[]")
            for v in viols:
                r_id = v.get("rule_id", "OTHER")
                violation_counts[r_id] = violation_counts.get(r_id, 0) + 1
        except Exception:
            pass
            
    compliance_rate = round((compliant / total * 100), 1) if total > 0 else 0.0
    
    return {
        "total_inspections": total,
        "compliant_count": compliant,
        "violation_count": violations,
        "review_count": reviews,
        "compliance_rate": compliance_rate,
        "category_breakdown": categories,
        "violation_by_rule": violation_counts
    }

if __name__ == "__main__":
    init_db()
    print("Database initialized successfully at:", DB_PATH)
