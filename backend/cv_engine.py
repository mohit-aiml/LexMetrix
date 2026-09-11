"""
LexMetrix - Computer Vision & Preprocessing Engine
Improves image quality, detects blur, handles glare/contrast with CLAHE,
estimates Principal Display Panel (PDP), and renders evidence annotations.
"""

import cv2
import numpy as np
import os
from typing import Dict, Any, List, Tuple
from PIL import Image

def load_image(image_path: str) -> np.ndarray:
    img = cv2.imread(image_path)
    if img is None:
        raise ValueError(f"Could not load image from: {image_path}")
    return img

def assess_image_quality(image: np.ndarray) -> Dict[str, Any]:
    """
    Computes blur score (Laplacian variance) and lighting balance.
    Essential for field inspectors to guarantee evidentiary standard.
    """
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY) if len(image.shape) == 3 else image
    
    # Blur detection via Laplacian Variance
    laplacian_var = float(cv2.Laplacian(gray, cv2.CV_64F).var())
    is_blurry = laplacian_var < 75.0
    
    # Lighting and contrast
    mean_brightness = float(np.mean(gray))
    std_contrast = float(np.std(gray))
    
    lighting_verdict = "Optimal"
    if mean_brightness < 40:
        lighting_verdict = "Under-exposed (Too Dark)"
    elif mean_brightness > 230:
        lighting_verdict = "Over-exposed (Glare Detected)"
        
    quality_verdict = "Good Quality"
    if is_blurry:
        quality_verdict = "Blurry - Re-scan Recommended"
    elif mean_brightness < 40 or mean_brightness > 230:
        quality_verdict = f"Lighting Issue - {lighting_verdict}"
        
    return {
        "blur_score": round(laplacian_var, 2),
        "is_blurry": is_blurry,
        "mean_brightness": round(mean_brightness, 2),
        "contrast": round(std_contrast, 2),
        "quality_verdict": quality_verdict,
        "lighting_verdict": lighting_verdict,
        "width": int(image.shape[1]),
        "height": int(image.shape[0])
    }

def enhance_image(image: np.ndarray) -> np.ndarray:
    """
    Preprocesses package image using CLAHE on L-channel and subtle bilateral filter
    to remove reflections, enhance printed text contrast, and improve OCR yield.
    """
    if len(image.shape) == 2:
        image = cv2.cvtColor(image, cv2.COLOR_GRAY2BGR)
        
    # Convert BGR to LAB
    lab = cv2.cvtColor(image, cv2.COLOR_BGR2LAB)
    l_channel, a_channel, b_channel = cv2.split(lab)
    
    # Apply CLAHE to L-channel
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    cl = clahe.apply(l_channel)
    
    # Merge and convert back
    merged_lab = cv2.merge((cl, a_channel, b_channel))
    enhanced_bgr = cv2.cvtColor(merged_lab, cv2.COLOR_LAB2BGR)
    
    # Preserve sharp edges of characters while suppressing packaging texture
    filtered = cv2.bilateralFilter(enhanced_bgr, d=5, sigmaColor=35, sigmaSpace=35)
    return filtered

def estimate_pdp_area(image: np.ndarray) -> Dict[str, Any]:
    """
    Estimates the Principal Display Panel (PDP) bounding box and area in cm^2
    assuming standard standard capture distance / DPI (approx 96 DPI baseline).
    Under Rule 5, PDP area determines the minimum mandatory numeral height.
    """
    h, w = image.shape[:2]
    # For packaged commodity labels, PDP is typically 40% to 100% of visible front surface
    total_px = h * w
    
    # Estimate dimensions in cm assuming standard 96 DPI (37.8 px/cm)
    px_per_cm = 37.8
    width_cm = w / px_per_cm
    height_cm = h / px_per_cm
    area_cm2 = width_cm * height_cm
    
    return {
        "pdp_width_px": w,
        "pdp_height_px": h,
        "estimated_area_cm2": round(area_cm2, 2),
        "width_cm": round(width_cm, 1),
        "height_cm": round(height_cm, 1)
    }

def draw_evidence_annotations(
    image_path: str,
    annotations: List[Dict[str, Any]],
    output_path: str
) -> str:
    """
    Draws evidentiary visual annotations over the scanned image.
    Green: Rule Passed / Compliant
    Red: Rule Violated / Illegal Declaration
    Amber: Warning / Low Confidence / Font Size concern
    """
    image = cv2.imread(image_path)
    if image is None:
        raise ValueError(f"Unable to read image at: {image_path}")
        
    annotated = image.copy()
    overlay = image.copy()
    
    colors = {
        "COMPLIANT": (46, 125, 50),     # Forest Green (BGR)
        "VIOLATION": (40, 40, 215),      # Crimson Red (BGR)
        "WARNING": (0, 140, 255),        # Amber / Orange (BGR)
        "INFO": (180, 105, 30)           # Blue (BGR)
    }
    
    for ann in annotations:
        bbox = ann.get("bbox") # [x, y, w, h]
        if not bbox or len(bbox) != 4:
            continue
            
        x, y, w, h = [int(v) for v in bbox]
        # Keep within bounds
        x = max(0, min(x, image.shape[1] - 1))
        y = max(0, min(y, image.shape[0] - 1))
        w = max(5, min(w, image.shape[1] - x))
        h = max(5, min(h, image.shape[0] - y))
        
        status = ann.get("status", "INFO").upper()
        color = colors.get(status, colors["INFO"])
        
        # Draw semi-transparent highlight fill
        cv2.rectangle(overlay, (x, y), (x + w, y + h), color, -1)
        
        # Draw crisp border
        thickness = 2
        cv2.rectangle(annotated, (x, y), (x + w, y + h), color, thickness)
        
        # Label badge
        label = ann.get("label", "")
        if label:
            font = cv2.FONT_HERSHEY_SIMPLEX
            font_scale = 0.45
            font_thickness = 1
            (text_w, text_h), baseline = cv2.getTextSize(label, font, font_scale, font_thickness)
            
            badge_y1 = max(0, y - text_h - 6)
            badge_y2 = y
            badge_x2 = min(image.shape[1], x + text_w + 10)
            
            cv2.rectangle(annotated, (x, badge_y1), (badge_x2, badge_y2), color, -1)
            cv2.putText(
                annotated,
                label,
                (x + 5, y - 4),
                font,
                font_scale,
                (255, 255, 255),
                font_thickness,
                cv2.LINE_AA
            )
            
    # Blend overlay with 15% opacity for highlight effect
    cv2.addWeighted(overlay, 0.15, annotated, 0.85, 0, annotated)
    
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    cv2.imwrite(output_path, annotated)
    return output_path
