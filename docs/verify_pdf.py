import os
import pymupdf

pdf_path = r"c:\Users\DELL\OneDrive\Desktop\project\RestaurantOps AI\docs\RestaurantOps_AI_SRS_Yohannes_Zewde.pdf"
md_path = r"c:\Users\DELL\OneDrive\Desktop\project\RestaurantOps AI\docs\RestaurantOps_AI_SRS_Yohannes_Zewde.md"
img_dir = r"c:\Users\DELL\OneDrive\Desktop\project\RestaurantOps AI\docs\verification_images"
os.makedirs(img_dir, exist_ok=True)

# 1. Existence
print(f"MD exists: {os.path.exists(md_path)} (Size: {os.path.getsize(md_path)} bytes)")
print(f"PDF exists: {os.path.exists(pdf_path)} (Size: {os.path.getsize(pdf_path)} bytes)")

doc = pymupdf.open(pdf_path)
page_count = len(doc)
print(f"Total PDF Page Count: {page_count}")

# Extract all text
full_text = ""
for idx, page in enumerate(doc):
    text = page.get_text()
    full_text += f"\n--- Page {idx+1} ---\n" + text

# Check 19 sections
sections = [
    "1. Introduction",
    "2. Purpose",
    "3. Problem Statement",
    "4. Proposed Solution",
    "5. Project Objectives",
    "6. Target Users and Stakeholders",
    "7. Functional Requirements",
    "8. Non-Functional Requirements",
    "9. System Architecture",
    "10. Third-Party API Integrations",
    "11. System Workflows",
    "12. API Specifications",
    "13. User Interface and System Components",
    "14. Technology Stack",
    "15. Minimum Viable Product (MVP) Scope",
    "16. Future Enhancements",
    "17. Acceptance Criteria",
    "18. Deployment and Resource Considerations",
    "19. Conclusion",
]

print("\n--- SECTION VERIFICATION IN PDF ---")
missing_sections = []
for sec in sections:
    if sec in full_text:
        print(f"  [OK] {sec}")
    else:
        print(f"  [MISSING] {sec}")
        missing_sections.append(sec)

# Check FR-01 to FR-08
print("\n--- FUNCTIONAL REQUIREMENTS VERIFICATION IN PDF ---")
fr_items = [f"FR-0{i}" for i in range(1, 9)]
missing_fr = []
for fr in fr_items:
    if fr in full_text:
        print(f"  [OK] {fr}")
    else:
        print(f"  [MISSING] {fr}")
        missing_fr.append(fr)

# Check metadata
meta_checks = [
    "RestaurantOps AI",
    "Yohannes Zewde",
    "1.0",
    "Reconstructed Project Specification",
    "FastAPI",
    "React",
    "SQLAlchemy",
    "Google Gemini",
    "google-genai",
    "Telegram",
    "Open-Meteo",
    "APScheduler",
]
print("\n--- METADATA & STACK VERIFICATION IN PDF ---")
for m in meta_checks:
    present = m in full_text
    print(f"  [{'OK' if present else 'MISSING'}] {m}")

# Render all pages to PNG
print("\n--- RENDERING PDF PAGES TO IMAGES ---")
rendered_images = []
for i in range(page_count):
    page = doc.load_page(i)
    pix = page.get_pixmap(dpi=150)
    out_img = os.path.join(img_dir, f"page_{i+1}.png")
    pix.save(out_img)
    rendered_images.append(out_img)
    print(f"  Saved page {i+1} image to: {out_img}")

print(f"\nVerification complete. Missing sections: {len(missing_sections)}, Missing FRs: {len(missing_fr)}")
