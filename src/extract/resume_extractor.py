import re
from pathlib import Path

import pdfplumber

from .base import RawCandidateFields

EMAIL_RE = re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+")
PHONE_RE = re.compile(r"(\+?\d[\d\s-]{8,}\d)")
SKILLS_LINE_RE = re.compile(r"skills\s*:\s*(.+)", re.IGNORECASE)
LINKEDIN_RE = re.compile(r"(linkedin\.com/in/[\w\-]+)", re.IGNORECASE)
GITHUB_RE = re.compile(r"(github\.com/[\w\-]+)", re.IGNORECASE)

                                                                        
                                                                     
                                 
PLAUSIBLE_NAME_RE = re.compile(r"^[A-Za-z][A-Za-z.'\- ]{1,60}$")

CITY_COUNTRY_RE = re.compile(r"^([A-Za-z\s]+),\s*(India|USA|UK|Canada|Australia|Germany|Singapore)$")
EXPERIENCE_RE = re.compile(r"^(.*?)\s+at\s+(.*?)\s*\((.*?)\s*-\s*(.*?)\)$")
EDUCATION_RE = re.compile(r"^Education:\s*(.*?),\s*(.*?),\s*(\d{4})$")


def _candidate_key_from_filename(file_path: Path) -> str | None:
    match = re.search(r"resume_([A-Za-z0-9]+)", file_path.stem)
    return match.group(1) if match else None


def _split_degree_field(degree_field_str: str):
    val = degree_field_str.strip()
                          
    for prefix in ["B.E.", "B.Tech", "B.S.", "B.Sc.", "M.S.", "M.Tech", "Ph.D.", "M.B.A.", "B.A.", "M.A."]:
        if val.lower().startswith(prefix.lower()):
            degree = val[:len(prefix)].strip()
            field = val[len(prefix):].strip()
            if field.lower().startswith("in "):
                field = field[3:].strip()
            return degree, field or None
                                    
    parts = re.split(r"\s+", val, maxsplit=1)
    if len(parts) == 2:
        return parts[0], parts[1]
    return val, None


def extract_resume(path: str) -> RawCandidateFields:
    """
    Reads one resume PDF and returns a single RawCandidateFields.
    Never raises: an unreadable or garbage PDF yields a record with
    no fields and a parse_error, so the pipeline can keep going using
    whatever other sources exist for that candidate.
    """
    file_path = Path(path)
    candidate_key = _candidate_key_from_filename(file_path)
    record = RawCandidateFields(
        source_type="resume_pdf",
        source_id=file_path.name,
        candidate_key=candidate_key,
    )

    try:
        with pdfplumber.open(file_path) as pdf:
            text = "\n".join(page.extract_text() or "" for page in pdf.pages)
    except Exception as e:                                                
        record.parse_errors.append(f"failed to read PDF: {e}")
        return record

    if not text.strip():
        record.parse_errors.append("no extractable text in PDF")
        return record

    lines = [line.strip() for line in text.splitlines() if line.strip()]

                                                           
    if lines:
        if PLAUSIBLE_NAME_RE.match(lines[0]):
            record.fields["full_name"] = lines[0]
        else:
            record.parse_errors.append(
                f"first line did not look like a name, skipped: {lines[0]!r}"
            )

                           
    email_match = EMAIL_RE.search(text)
    if email_match:
        record.fields["email"] = email_match.group(0)

    phone_match = PHONE_RE.search(text)
    if phone_match:
        record.fields["phone"] = phone_match.group(0).strip()

                   
    li_match = LINKEDIN_RE.search(text)
    if li_match:
        record.fields["linkedin"] = "https://" + li_match.group(1)

    gh_match = GITHUB_RE.search(text)
    if gh_match:
        record.fields["github"] = "https://" + gh_match.group(1)

                    
    skills_match = SKILLS_LINE_RE.search(text)
    if skills_match:
        skills = [s.strip() for s in skills_match.group(1).split(",") if s.strip()]
        if skills:
            record.fields["skills"] = skills

                                                
    for line in lines:
        city_match = CITY_COUNTRY_RE.match(line)
        if city_match:
            record.fields["city"] = city_match.group(1).strip()
            record.fields["country"] = city_match.group(2).strip()
            break                    

                                                                                                        
    experience_entries = []
    for i, line in enumerate(lines):
        exp_match = EXPERIENCE_RE.match(line)
        if exp_match:
            title, company, start, end = exp_match.groups()
            entry = {
                "title": title.strip(),
                "company": company.strip(),
                "start": start.strip(),
                "end": end.strip(),
                "summary": None,
            }
                                                                              
                                                 
            if i + 1 < len(lines):
                next_line = lines[i + 1]
                is_other_section = (
                    EXPERIENCE_RE.match(next_line)
                    or EDUCATION_RE.match(next_line)
                    or SKILLS_LINE_RE.match(next_line)
                    or CITY_COUNTRY_RE.match(next_line)
                )
                if not is_other_section:
                    entry["summary"] = next_line
            experience_entries.append(entry)
    if experience_entries:
        record.fields["experience_entries"] = experience_entries

                                                                                                
    education_entries = []
    for line in lines:
        edu_match = EDUCATION_RE.match(line)
        if edu_match:
            degree_field, institution, end_year = edu_match.groups()
            degree, field = _split_degree_field(degree_field)
            education_entries.append({
                "institution": institution.strip(),
                "degree": degree,
                "field": field,
                "end_year": end_year.strip(),
            })
    if education_entries:
        record.fields["education_entries"] = education_entries

    if not record.fields:
        record.parse_errors.append("text extracted but no recognizable fields found")

    return record