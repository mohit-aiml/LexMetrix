"""
LexMetrix - Targeted Compliance Mix Image Generator
Generates 4 high-resolution packaging label images representing:
- 100% Statutory Compliance (Himalayan Honey - 8/8 PASS)
- 75% Statutory Compliance (Desi Chai - 6/8 PASS, 2/8 FAIL)
- 50% Statutory Compliance (Nutty Treat - 4/8 PASS, 4/8 FAIL)
- 0% Statutory Compliance (Defective Wrapper - 0/8 PASS, 8/8 FAIL)
"""

import os
from PIL import Image, ImageDraw, ImageFont

SAMPLES_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "uploads", "samples")

def get_fonts():
    font_path = "C:\\Windows\\Fonts\\arial.ttf"
    bold_path = "C:\\Windows\\Fonts\\arialbd.ttf"
    
    if os.path.exists(font_path):
        f_title = ImageFont.truetype(bold_path if os.path.exists(bold_path) else font_path, 26)
        f_header = ImageFont.truetype(bold_path if os.path.exists(bold_path) else font_path, 20)
        f_body = ImageFont.truetype(font_path, 19)
        f_bold = ImageFont.truetype(bold_path if os.path.exists(bold_path) else font_path, 19)
    else:
        f_title = ImageFont.load_default()
        f_header = f_title
        f_body = f_title
        f_bold = f_title
    return f_title, f_header, f_body, f_bold

def generate_mix_images():
    os.makedirs(SAMPLES_DIR, exist_ok=True)
    f_title, f_header, f_body, f_bold = get_fonts()

    # =========================================================================
    # 1. 100% COMPLIANCE: Himalayan Mountain Honey (500g)
    # 8 PASS, 0 FAIL -> 100.0%
    # =========================================================================
    img1 = Image.new("RGB", (900, 620), color="#FFFDF7")
    d1 = ImageDraw.Draw(img1)
    d1.rectangle([(0, 0), (900, 80)], fill="#1E3A8A")
    d1.text((30, 24), "HIMALAYAN PURE MOUNTAIN HONEY", font=f_title, fill="#FFFFFF")
    d1.text((670, 28), "100% ORGANIC", font=f_header, fill="#FBBF24")
    d1.rectangle([(20, 95), (880, 600)], outline="#94A3B8", width=2)

    declarations_1 = [
        ("Product Name: Himalayan Pure Raw Mountain Honey", f_bold, "#0F172A"),
        ("Net Quantity: 500 g", f_bold, "#0F172A"), # 1. PASS Net Qty
        ("MRP: Rs. 290.00 (incl. of all taxes)", f_bold, "#0F172A"), # 2. PASS MRP
        ("Month & Year of Mfg: 08/2026", f_body, "#334155"), # 3. PASS Date
        ("Best Before: 18 Months from Packaging", f_body, "#334155"),
        ("Batch No: HM-2026-N10", f_body, "#334155"), # 4. PASS Batch
        ("Manufactured By: Himalayan Naturals India Pvt Ltd,", f_body, "#334155"),
        ("Plot 14, EPIP Industrial Zone, Dehradun, Uttarakhand - 248001", f_body, "#334155"), # 5. PASS Mfg + PIN
        ("Country of Origin: India", f_bold, "#0F172A"), # 6. PASS Origin
        ("Consumer Grievance Cell: Manager - Customer Care", f_body, "#334155"),
        ("Toll Free: 1800-120-7788  |  Email: care@himalayannaturals.in", f_bold, "#0F172A") # 7. PASS Phone + Email, 8. PASS Font
    ]
    y = 115
    for text, font, color in declarations_1:
        d1.text((45, y), text, font=font, fill=color)
        y += 41
    path_100 = os.path.join(SAMPLES_DIR, "sample_100_compliant.png")
    img1.save(path_100)

    # =========================================================================
    # 2. 75% COMPLIANCE: Desi Chai Premium Assam Tea (250g)
    # 6 PASS, 2 FAIL -> 75.0%
    # - PASS: Mfg & PIN, Origin, Net Qty, Date, MRP, Font
    # - FAIL: Missing Consumer Email (Rule 6(1)(n))
    # - FAIL: Missing Batch Number (Rule 6(1)(f))
    # =========================================================================
    img2 = Image.new("RGB", (900, 620), color="#F0FDF4")
    d2 = ImageDraw.Draw(img2)
    d2.rectangle([(0, 0), (900, 80)], fill="#065F46")
    d2.text((30, 24), "DESI CHAI PREMIUM ASSAM TEA", font=f_title, fill="#FFFFFF")
    d2.text((700, 28), "FRESH HARVEST", font=f_header, fill="#6EE7B7")
    d2.rectangle([(20, 95), (880, 600)], outline="#A7F3D0", width=2)

    declarations_2 = [
        ("Product Name: Desi Chai Premium Assam CTC Tea", f_bold, "#0F172A"),
        ("Net Quantity: 250 g", f_bold, "#0F172A"), # 1. PASS Qty
        ("MRP: Rs. 140.00 (incl. of all taxes)", f_bold, "#0F172A"), # 2. PASS MRP
        ("Month & Year of Mfg: 09/2026", f_body, "#334155"), # 3. PASS Date
        ("Best Before: 12 Months from Packing", f_body, "#334155"),
        # (4. FAIL: Batch Number missing)
        ("Packed By: Desi Chai Blenders Private Limited,", f_body, "#334155"),
        ("Tea Estate Hub, Sector 5, Kolkata, West Bengal - 700091", f_body, "#334155"), # 5. PASS Mfg + PIN
        ("Country of Origin: India", f_bold, "#0F172A"), # 6. PASS Origin
        ("Customer Helpline: 1800-419-3322", f_body, "#DC2626") # 7. FAIL: Missing mandatory Email (Rule 6(1)(n)), 8. PASS Font
    ]
    y = 125
    for text, font, color in declarations_2:
        d2.text((45, y), text, font=font, fill=color)
        y += 45
    path_75 = os.path.join(SAMPLES_DIR, "sample_75_compliance.png")
    img2.save(path_75)

    # =========================================================================
    # 3. 50% COMPLIANCE: Nutty Treat Crunchy Cookies (150g)
    # 4 PASS, 4 FAIL -> 50.0%
    # - PASS: Date, Origin, Batch, Font
    # - FAIL: Net Qty non-standard 'gms' (Rule 6(1)(c))
    # - FAIL: MRP missing '(incl. of all taxes)' (Rule 6(1)(e))
    # - FAIL: Missing Consumer Email (Rule 6(1)(n))
    # - FAIL: Missing Manufacturer Identity (Rule 6(1)(a))
    # =========================================================================
    img3 = Image.new("RGB", (900, 620), color="#FFFBEB")
    d3 = ImageDraw.Draw(img3)
    d3.rectangle([(0, 0), (900, 80)], fill="#B45309")
    d3.text((30, 24), "NUTTY TREAT CRUNCHY CASHEW COOKIES", font=f_title, fill="#FFFFFF")
    d3.rectangle([(20, 95), (880, 600)], outline="#FCD34D", width=2)

    declarations_3 = [
        ("Product Name: Nutty Treat Crispy Cashew Cookies", f_bold, "#0F172A"),
        ("Net Weight: 150 gms", f_bold, "#DC2626"), # 1. FAIL: Prohibited 'gms' (Rule 6(1)(c))
        ("MRP: Rs. 60.00", f_bold, "#DC2626"), # 2. FAIL: Missing '(incl. of all taxes)' (Rule 6(1)(e))
        ("Month & Year of Mfg: 07/2026", f_body, "#334155"), # 1. PASS Date (Rule 6(1)(d))
        ("Best Before: 6 Months from Mfg", f_body, "#334155"),
        ("Batch No: NT-881", f_body, "#334155"), # 2. PASS Batch (Rule 6(1)(f))
        ("Country of Origin: India", f_bold, "#0F172A"), # 3. PASS Origin (Rule 6(1)(b))
        ("Consumer Care Helpline: 020-27419900", f_body, "#DC2626") # 3. FAIL: Missing Email (Rule 6(1)(n))
        # 4. FAIL: Manufacturer missing entirely (Rule 6(1)(a)), 4. PASS Font height (Rule 5)
    ]
    y = 125
    for text, font, color in declarations_3:
        d3.text((45, y), text, font=font, fill=color)
        y += 48
    path_50 = os.path.join(SAMPLES_DIR, "sample_50_compliance.png")
    img3.save(path_50)

    # =========================================================================
    # 4. 0% COMPLIANCE: Defective Commercial Wrapper
    # 0 PASS, 8 FAIL -> 0.0%
    # Entirely lacks all 8 mandatory declarations
    # =========================================================================
    img4 = Image.new("RGB", (900, 620), color="#1E293B")
    d4 = ImageDraw.Draw(img4)
    d4.rectangle([(0, 0), (900, 100)], fill="#0F172A")
    d4.text((30, 32), "VOGUE LUXURY SILK TEXTILES", font=f_title, fill="#E2E8F0")
    d4.rectangle([(20, 120), (880, 590)], outline="#475569", width=3)
    
    bogus_text = [
        ("EXCLUSIVE DESIGNER COLLECTION - EXPORT EDITION", f_bold, "#94A3B8"),
        ("Soft Touch Fabric - Hand Wash Only", f_body, "#64748B"),
        ("Store in a cool dry place", f_body, "#64748B"),
        ("For Commercial Textile Distribution", f_body, "#475569")
    ]
    y = 210
    for text, font, color in bogus_text:
        d4.text((60, y), text, font=font, fill=color)
        y += 50
        
    path_0 = os.path.join(SAMPLES_DIR, "sample_0_compliance.png")
    img4.save(path_0)

    print("Targeted mix images successfully generated:")
    print("  100% Compliance:", path_100)
    print("  75% Compliance: ", path_75)
    print("  50% Compliance: ", path_50)
    print("  0% Compliance:  ", path_0)
    
    return {
        "100": path_100,
        "75": path_75,
        "50": path_50,
        "0": path_0
    }

if __name__ == "__main__":
    generate_mix_images()
