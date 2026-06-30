from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib import colors

def generate_design_pdf(output_path):
                                     
    c = canvas.Canvas(output_path, pagesize=letter)
    width, height = letter
    
                                    
    c.setStrokeColor(colors.HexColor("#1A365D"))                   
    c.setLineWidth(2)
    c.rect(15, 15, width - 30, height - 30)
    c.setLineWidth(0.5)
    c.rect(18, 18, width - 36, height - 36)
    
                                                          
                    
                                                          
    c.setFillColor(colors.HexColor("#1A365D"))
    c.rect(20, height - 60, width - 40, 40, fill=True, stroke=False)
    
    c.setFillColor(colors.white)
    c.setFont("Helvetica-Bold", 14)
    c.drawString(30, height - 45, "MULTI-SOURCE CANDIDATE DATA TRANSFORMER")
    
    c.setFont("Helvetica", 9)
    c.drawRightString(width - 30, height - 35, "Asvitha B | Engineering Intern Assignment")
    c.drawRightString(width - 30, height - 50, "asvithab.cse2023@citchennai.net")
    
                                                          
                          
                                                          
    col1_left = 30
    col1_width = 260
    col2_left = 320
    col2_width = 260
    
                             
    def draw_section_header(title, x, y):
        c.setFillColor(colors.HexColor("#2B6CB0"))
        c.rect(x, y - 3, col1_width, 14, fill=True, stroke=False)
        c.setFillColor(colors.white)
        c.setFont("Helvetica-Bold", 9)
        c.drawString(x + 5, y, title)
        
                               
    def draw_text_block(lines, x, start_y, font_size=7.5, leading=10, is_bold_headers=True):
        y = start_y
        c.setFillColor(colors.HexColor("#2D3748"))
        for line in lines:
            if not line:
                y -= leading / 2
                continue
            if is_bold_headers and (line.startswith("•") or ":" in line) and not line.startswith("  "):
                parts = line.split(":", 1)
                if len(parts) == 2 and not line.startswith("•"):
                    c.setFont("Helvetica-Bold", font_size)
                    c.drawString(x, y, parts[0] + ":")
                    c.setFont("Helvetica", font_size)
                    c.drawString(x + c.stringWidth(parts[0] + ": ", "Helvetica-Bold", font_size), y, parts[1].strip())
                elif line.startswith("•"):
                    c.setFont("Helvetica", font_size)
                    c.drawString(x, y, line)
                else:
                    c.setFont("Helvetica-Bold", font_size)
                    c.drawString(x, y, line)
            else:
                c.setFont("Helvetica", font_size)
                c.drawString(x, y, line)
            y -= leading
        return y

                                                          
                       
                                                          
    
                                      
    y = 705
    draw_section_header("1. PIPELINE & PROCESS FLOW", col1_left, y)
    y -= 15
    pipeline_text = [
        "The system processes multiple, noisy sources asynchronously:",
        "• INGEST: Point CLI or UI to recruiter CSV, ATS JSON, and PDF resumes.",
        "• EXTRACT: Concrete parsers convert inputs to RawCandidateFields.",
        "  - Structured (CSV/JSON): Extract flat maps, link current job.",
        "  - Unstructured (PDF): Extract email, phone, location, skills, and links.",
        "• NORMALIZE: Clean formats independently of merge logic.",
        "• RECONCILE: Group records by candidate ID and merge overlapping data.",
        "• PROJECT: Apply custom output config templates dynamically.",
        "• VALIDATE: Perform JSON schema compliance verification before exit."
    ]
    y = draw_text_block(pipeline_text, col1_left, y)
    
                                                 
    y -= 10
    draw_section_header("2. CANONICAL SCHEMA & NORMALIZATION", col1_left, y)
    y -= 15
    schema_text = [
        "A standardized output shape provides predictability downstream:",
        "• Phone Numbers: Normalized to E.164 (e.g. +91 98765 43210 -> +919876543210).",
        "• Country Codes: Normalized to ISO 3166-1 alpha-2 (e.g. 'India' -> 'IN').",
        "• Date Fields: Standardized to YYYY-MM format; active roles map to 'present'.",
        "• Skill Taxonomy: Canonicalized via explicit alias map (e.g. JS -> JavaScript).",
        "  Unmapped skills are title-cased and preserved to avoid loss.",
        "• Complex Objects:",
        "  - Location: { city: str, region: str, country: str }",
        "  - Links: { linkedin: str, github: str, portfolio: str, other: str[] }",
        "  - Experience: [ { company, title, start, end, summary } ]",
        "  - Education: [ { institution, degree, field, end_year } ]"
    ]
    y = draw_text_block(schema_text, col1_left, y)

                                                   
    y -= 10
    draw_section_header("3. MERGE & CONFLICT-RESOLUTION POLICY", col1_left, y)
    y -= 15
    merge_text = [
        "To ensure deterministic results, conflict resolution is rule-driven:",
        "• Source-Trust Hierarchy: Custom field-specific trust weights decide winners.",
        "  - Identity (Name/Email/Phone): ATS JSON (0.85) > CSV (0.8) > Resume (0.6).",
        "  - Skills & Experience Details: Resume (0.85) > ATS (0.7) > CSV (0.4).",
        "• Conflict Resolvers:",
        "  - Scalars (Name/Email/Phone): Agreement across sources yields high trust.",
        "    Disagreements select highest-trust source. Tie-breakers pick longest string.",
        "  - Lists (Skills/Links): Taken as union across sources with max trust score.",
        "  - Complex Objects (Jobs/Degrees): Grouped by normalized company or",
        "    institution name. Internal fields resolved via scalar conflict policy.",
        "• Confidence Scoring:",
        "  - Agreement: Sets confidence to 0.95.",
        "  - Conflict Winner: Confidence capped at 0.60.",
        "  - Single-Source: Confidence capped at 0.75.",
        "  - Overall: Computed as average of all populated scalar confidences."
    ]
    y = draw_text_block(merge_text, col1_left, y)

                                                          
                       
                                                          
    
                                      
    y2 = 705
    draw_section_header("4. RUNTIME CONFIG PROJECTION & VALIDATION", col2_left, y2)
    y2 -= 15
    config_text = [
        "Output projection is fully decoupled from extraction and merge engines:",
        "• Path Resolution: Supports dot-paths (location.city), list-index",
        "  resolution (emails[0]), and list-of-objects projection (skills[].name).",
        "• Normalization: Applies E164 phone or skill canonicalization on project.",
        "• Missing Value Policies: Action configurable via 'on_missing' parameter:",
        "  - null (default): Populates missing fields as null.",
        "  - omit: Entirely excludes the key from the output dictionary.",
        "  - error: Raises a ValueError immediately if a required field is missing.",
        "• Toggles: Provenance and confidence metadata can be switched off.",
        "• Validation: The projected object is validated against custom/default",
        "  JSON schemas using Draft7Validator, logging errors without crashing."
    ]
    y2 = draw_text_block(config_text, col2_left, y2)

                                   
    y2 -= 10
    draw_section_header("5. KEY EDGE CASES HANDLED", col2_left, y2)
    y2 -= 15
    edge_text = [
        "• Incomplete Names vs Full Names: Resume has 'Vikram Raghavan' while",
        "  CSV has 'Vikram'. When trust levels are close, the tie-breaker prefers",
        "  the longer string, ensuring completeness is preserved.",
        "• Phone Representation Differences: CSV has '9876543210', ATS JSON has",
        "  '9876543210', and resume has '+91 9876543210'. Normalizing prior to",
        "  comparison ensures these are flagged as 'agreement' rather than 'conflict'.",
        "• Garbage / Unparseable Sources: A corrupted scan PDF with no text",
        "  triggers a logged parse error. The pipeline degrades gracefully,",
        "  merging any remaining sources without raising exceptions.",
        "• Company Alias Matching: Resolves 'TechNova Pvt Ltd' vs 'TechNova Private",
        "  Limited' by stripping legal suffixes and comparing lowercase strings.",
        "• Nested Education Splitting: Parses 'B.E. Computer Science' into",
        "  degree: 'B.E.' and field: 'Computer Science' using specialized regex."
    ]
    y2 = draw_text_block(edge_text, col2_left, y2)

                                                          
    y2 -= 10
    draw_section_header("6. INTENTIONAL SCOPE TRADEOFFS", col2_left, y2)
    y2 -= 15
    scope_text = [
        "• Cross-Candidate Deduplication: Assumes files/records are pre-linked",
        "  via candidate ID. Deduplicating individuals named 'Priya S' vs 'Priya",
        "  Sundaram' without explicit common identifiers is out of scope.",
        "• Dynamic Trust Adaptation: Source trust weights are statically configured.",
        "  A machine-learning model adapting trust based on historical accuracy",
        "  was omitted in favor of explainable, deterministic rules.",
        "• Live API Fetching: GitHub/LinkedIn mock JSON data is processed in-memory.",
        "  Live GraphQL/REST network fetching was excluded under time pressure."
    ]
    y2 = draw_text_block(scope_text, col2_left, y2)

              
    c.showPage()
    c.save()
    print(f"Technical Design PDF successfully generated at {output_path}")

if __name__ == "__main__":
    generate_design_pdf("AsvithaB_asvithab.cse2023@citchennai.net_Eightfold.pdf")
