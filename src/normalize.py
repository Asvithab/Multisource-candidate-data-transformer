"""
normalize.py
Pure, independently-testable normalizers for each field type. None of
these know about "sources" or "merging" -- they take a raw value and
return a normalized value (or None if it can't be normalized), plus
optionally an error string for provenance/debugging.
"""

import re
from datetime import datetime

import phonenumbers
import pycountry
from dateutil import parser as date_parser

                                                                             
                
                                                                             
DEFAULT_REGION = "IN"                                                               


def normalize_phone(raw: str, default_region: str = DEFAULT_REGION) -> str | None:
    """Normalize a raw phone string to E.164 (e.g. '+919876543210')."""
    if not raw:
        return None
    try:
        parsed = phonenumbers.parse(raw, default_region)
        if not phonenumbers.is_valid_number(parsed):
            return None
        return phonenumbers.format_number(parsed, phonenumbers.PhoneNumberFormat.E164)
    except phonenumbers.NumberParseException:
        return None



def normalize_date(raw: str) -> str | None:
    """Normalize a loosely-formatted date string to YYYY-MM."""
    if not raw:
        return None

    if raw.strip().lower() in {"present", "current","PRESENT", "now"}:
        return "present"

    try:
        parsed = date_parser.parse(raw, default=datetime(1900, 1, 1))
        return parsed.strftime("%Y-%m")
    except (date_parser.ParserError, ValueError, OverflowError):
        return None

def normalize_country(raw: str) -> str | None:
    """Normalize a country name to its ISO 3166-1 alpha-2 code (e.g. 'IN')."""
    if not raw:
        return None
    try:
        match = pycountry.countries.search_fuzzy(raw)
        return match[0].alpha_2 if match else None
    except LookupError:
        return None


                                                                             
                           
                                                                             
                                                                 
                                                                      
                                                                
SKILL_ALIASES = {
    "js": "JavaScript",
    "javascript": "JavaScript",
    "reactjs": "React",
    "react.js": "React",
    "react": "React",
    "py": "Python",
    "python": "Python",
    "django": "Django",
    "postgres": "PostgreSQL",
    "postgresql": "PostgreSQL",
    "sql": "SQL",
    "powerbi": "Power BI",
    "power bi": "Power BI",
    "excel": "Excel",
    "ts": "TypeScript",
    "typescript": "TypeScript",
    "css": "CSS",
    "docker": "Docker",
    "aws": "AWS",
}


def normalize_skill(raw: str) -> str:
    """
    Normalize a raw skill string to its canonical name. Unknown skills
    are title-cased and passed through unchanged rather than dropped --
    we never silently discard a candidate's stated skill.
    """
    key = raw.strip().lower()
    return SKILL_ALIASES.get(key, raw.strip())


                                                                             
                                                    
                                                                             
LEGAL_SUFFIXES_RE = re.compile(
    r"\b(pvt\.?\s*ltd\.?|private\s+limited|inc\.?|incorporated|llc|ltd\.?)\b",
    re.IGNORECASE,
)


def normalize_company_for_comparison(raw: str) -> str:
    """
    Returns a normalized-for-COMPARISON version of a company name (strips
    legal suffixes, lowercases, collapses whitespace) -- used only to
    decide whether two sources actually agree, NOT used as the stored
    output value (the original, source-provided string is kept for display).
    """
    if not raw:
        return ""
    cleaned = LEGAL_SUFFIXES_RE.sub("", raw)
    cleaned = re.sub(r"[^\w\s]", "", cleaned)
    cleaned = re.sub(r"\s+", " ", cleaned).strip().lower()
    return cleaned