"""
LexMetrix - Synthetic Package Sample Generator
Generates realistic packaging label images using high-resolution TrueType typography:
- Sample 1: 100% Fully Compliant FMCG Product
- Sample 2: Violation - Missing Tax Disclaimer in MRP
- Sample 3: Violation - Illegal Prohibited Unit ('gms' instead of 'g')
- Sample 4: Violation - Missing Consumer Care Email & PIN code
- Sample 5: Warning - Blurry Low-Quality Photo
"""

import os
import cv2
import numpy as np
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

def create_sample_labels():
    os.makedirs(SAMPLES_DIR, exist_ok=True)
    f_title, f_header, f_body, f_bold = get_fonts()
    
    # 1. Sample 1: Fully Compliant Butter Cookies Label
    img1 = Image.new("RGB", (900, 600), color="#FFFDF7")
    d1 = ImageDraw.Draw(img1)
    
    # Brand banner
    d1.rectangle([(0, 0), (900, 80)], fill="#1E3A8A")
    d1.text((30, 24), "GOLDEN BAKE BUTTER COOKIES", font=f_title, fill="#FFFFFF")
    d1.text((650, 28), "100% VEG", font=f_header, fill="#4ADE80")
    
    # Packaging border
    d1.rectangle([(20, 95), (880, 580)], outline="#94A3B8", width=2)
    
    declarations_1 = [
        ("Product Name: Golden Bake Rich Butter Cookies", f_bold, "#0F172A"),
        ("Net Quantity: 200 g", f_bold, "#0F172A"),
        ("MRP: Rs. 45.00 (incl. of all taxes)", f_bold, "#0F172A"),
        ("Month & Year of Mfg: 08/2026", f_body, "#334155"),
        ("Best Before: 6 Months from Packaging", f_body, "#334155"),
        ("Batch No: GB-2026-X89", f_body, "#334155"),
        ("Manufactured By: Golden Treat Confectionery Pvt Ltd,", f_body, "#334155"),
        ("Plot 42, Okhla Industrial Area, Phase-III, New Delhi - 110020", f_body, "#334155"),
        ("Country of Origin: India", f_bold, "#0F172A"),
        ("Customer Care Cell: Manager - Consumer Grievances", f_body, "#334155"),
        ("Helpline: 1800-222-3344  |  Email: customercare@goldentreat.in", f_bold, "#0F172A")
    ]
    
    y = 115
    for text, font, color in declarations_1:
        d1.text((45, y), text, font=font, fill=color)
        y += 39
        
    path1 = os.path.join(SAMPLES_DIR, "sample1_compliant_cookies.png")
    img1.save(path1)
    
    # 2. Sample 2: Non-compliant - Missing Taxes in MRP
    img2 = Image.new("RGB", (900, 600), color="#FFFBEB")
    d2 = ImageDraw.Draw(img2)
    d2.rectangle([(0, 0), (900, 80)], fill="#B91C1C")
    d2.text((30, 24), "CRUNCHY POTATO CHIPS - TANGY MASALA", font=f_title, fill="#FFFFFF")
    d2.rectangle([(20, 95), (880, 580)], outline="#F59E0B", width=2)
    
    declarations_2 = [
        ("Product Name: Crunchy Potato Wafers", f_bold, "#0F172A"),
        ("Net Quantity: 120 g", f_bold, "#0F172A"),
        ("MRP: Rs. 35.00", f_bold, "#DC2626"), # VIOLATION: Missing (incl. of all taxes)
        ("Month & Year of Mfg: 09/2026", f_body, "#334155"),
        ("Best Before: 4 Months from Packing", f_body, "#334155"),
        ("Batch No: CP-9921", f_body, "#334155"),
        ("Manufactured By: Tasty Snacks India Limited,", f_body, "#334155"),
        ("Sector 18, Udyog Vihar, Gurugram, Haryana - 122015", f_body, "#334155"),
        ("Country of Origin: India", f_bold, "#0F172A"),
        ("Consumer Care Helpline: 1800-444-5566", f_body, "#334155"),
        ("Email: support@tastysnacks.co.in", f_body, "#334155")
    ]
    
    y = 115
    for text, font, color in declarations_2:
        d2.text((45, y), text, font=font, fill=color)
        y += 40
    path2 = os.path.join(SAMPLES_DIR, "sample2_mrp_tax_violation.png")
    img2.save(path2)
    
    # 3. Sample 3: Non-compliant - Prohibited Unit 'gms'
    img3 = Image.new("RGB", (900, 600), color="#F0FDF4")
    d3 = ImageDraw.Draw(img3)
    d3.rectangle([(0, 0), (900, 80)], fill="#047857")
    d3.text((30, 24), "SUPER CLEAN DETERGENT POWDER", font=f_title, fill="#FFFFFF")
    d3.rectangle([(20, 95), (880, 580)], outline="#10B981", width=2)
    
    declarations_3 = [
        ("Product Name: Super Clean Active Detergent", f_bold, "#0F172A"),
        ("Net Weight: 500 gms", f_bold, "#DC2626"), # VIOLATION: 'gms' is strictly prohibited
        ("MRP: Rs. 85.00 (incl. of all taxes)", f_bold, "#0F172A"),
        ("Month of Pkd: 07/2026", f_body, "#334155"),
        ("Batch No: SC-2026-D12", f_body, "#334155"),
        ("Packed By: Hygiene Home Products Ltd,", f_body, "#334155"),
        ("MIDC Industrial Area, Andheri East, Mumbai - 400093", f_body, "#334155"),
        ("Country of Origin: India", f_bold, "#0F172A"),
        ("Consumer Care Helpline: 022-28394455", f_body, "#334155"),
        ("Email: care@superclean.in", f_body, "#334155")
    ]
    y = 115
    for text, font, color in declarations_3:
        d3.text((45, y), text, font=font, fill=color)
        y += 40
    path3 = os.path.join(SAMPLES_DIR, "sample3_illegal_unit_violation.png")
    img3.save(path3)
    
    # 4. Sample 4: Missing Consumer Care Email & Incomplete Address (Missing PIN)
    img4 = Image.new("RGB", (900, 600), color="#F8FAFC")
    d4 = ImageDraw.Draw(img4)
    d4.rectangle([(0, 0), (900, 80)], fill="#334155")
    d4.text((30, 24), "ROYAL KACHI GHANI MUSTARD OIL", font=f_title, fill="#FFFFFF")
    d4.rectangle([(20, 95), (880, 580)], outline="#94A3B8", width=2)
    
    declarations_4 = [
        ("Product Name: Royal Pure Mustard Oil", f_bold, "#0F172A"),
        ("Net Volume: 1 l", f_bold, "#0F172A"),
        ("MRP: Rs. 175.00 (inclusive of all taxes)", f_bold, "#0F172A"),
        ("Month & Year of Mfg: 08/2026", f_body, "#334155"),
        ("Batch No: KO-801", f_body, "#334155"),
        ("Packed By: Royal Agro Mills, Station Road, Jaipur", f_body, "#DC2626"), # VIOLATION: Missing PIN!
        ("Country of Origin: India", f_bold, "#0F172A"),
        ("Consumer Helpline: 1800-999-0011", f_body, "#DC2626") # VIOLATION: Missing Email!
    ]
    y = 120
    for text, font, color in declarations_4:
        d4.text((45, y), text, font=font, fill=color)
        y += 45
    path4 = os.path.join(SAMPLES_DIR, "sample4_missing_email_and_pin.png")
    img4.save(path4)
    
    # 5. Sample 5: Blurry Photo for Laplacian Blur Detector Test
    cv_img1 = cv2.imread(path1)
    blurred = cv2.GaussianBlur(cv_img1, (35, 35), 20)
    path5 = os.path.join(SAMPLES_DIR, "sample5_blurry_scan.png")
    cv2.imwrite(path5, blurred)
    
    print("TrueType samples regenerated successfully in:", SAMPLES_DIR)
    return {
        "sample1": path1,
        "sample2": path2,
        "sample3": path3,
        "sample4": path4,
        "sample5": path5
    }

if __name__ == "__main__":
    create_sample_labels()
