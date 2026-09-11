import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.cv_engine import estimate_pdp_area, load_image
from backend.ocr_engine import run_ocr, extract_all_declarations
from backend.rule_engine import LegalMetrologyRuleEngine

engine = LegalMetrologyRuleEngine()
samples = [
    "sample_100_compliant.png",
    "sample_75_compliance.png",
    "sample_50_compliance.png",
    "sample_0_compliance.png"
]

for fname in samples:
    path = os.path.join("uploads", "samples", fname)
    ocr = run_ocr(path)
    decl = extract_all_declarations(ocr)
    ev = engine.evaluate(decl, estimate_pdp_area(load_image(path)))
    print(f"File: {fname}")
    print(f"  Score:  {ev['compliance_score']}%")
    print(f"  Status: {ev['compliance_status']}")
    print(f"  Passed: {ev['summary']['passed']}, Warn: {ev['summary']['warnings']}, Fail: {ev['summary']['failures']}")
    if ev['violations']:
        print("  Violations:")
        for v in ev['violations']:
            issue_clean = v['issue'].encode('ascii', 'ignore').decode('ascii')
            print(f"    - [{v['rule_id']}] {issue_clean}")
    print("-" * 50)
