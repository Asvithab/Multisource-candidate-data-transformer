"""
merge.py
Core conflict-resolution engine. Takes all RawCandidateFields records
for ONE candidate (across all sources) and produces a single canonical
record with per-field confidence and provenance.
"""

from dataclasses import dataclass, field
from datetime import datetime

from .normalize import (
    normalize_phone,
    normalize_skill,
    normalize_country,
    normalize_date,
    normalize_company_for_comparison,
)

TRUST_WEIGHTS = {
    ("full_name", "recruiter_csv"): 0.8,
    ("full_name", "ats_json"): 0.85,
    ("full_name", "resume_pdf"): 0.7,
    ("email", "recruiter_csv"): 0.85,
    ("email", "ats_json"): 0.85,
    ("email", "resume_pdf"): 0.6,
    ("phone", "recruiter_csv"): 0.85,
    ("phone", "ats_json"): 0.85,
    ("phone", "resume_pdf"): 0.6,
    ("company", "recruiter_csv"): 0.8,
    ("company", "ats_json"): 0.85,
    ("company", "resume_pdf"): 0.65,
    ("title", "recruiter_csv"): 0.8,
    ("title", "ats_json"): 0.85,
    ("title", "resume_pdf"): 0.65,
    ("skills", "resume_pdf"): 0.85,
    ("skills", "ats_json"): 0.7,
    ("skills", "recruiter_csv"): 0.4,
              
    ("location.city", "ats_json"): 0.85,
    ("location.city", "resume_pdf"): 0.75,
    ("location.country", "ats_json"): 0.85,
    ("location.country", "resume_pdf"): 0.75,
              
    ("headline", "ats_json"): 0.8,
    ("headline", "resume_pdf"): 0.85,
                       
    ("experience.company", "ats_json"): 0.85,
    ("experience.company", "recruiter_csv"): 0.8,
    ("experience.company", "resume_pdf"): 0.75,
    ("experience.title", "ats_json"): 0.85,
    ("experience.title", "recruiter_csv"): 0.8,
    ("experience.title", "resume_pdf"): 0.75,
    ("experience.start", "resume_pdf"): 0.8,
    ("experience.end", "resume_pdf"): 0.8,
    ("experience.summary", "resume_pdf"): 0.85,
                      
    ("education.institution", "resume_pdf"): 0.85,
    ("education.degree", "resume_pdf"): 0.85,
    ("education.field", "resume_pdf"): 0.85,
    ("education.end_year", "resume_pdf"): 0.85,
           
    ("links.linkedin", "resume_pdf"): 0.85,
    ("links.github", "resume_pdf"): 0.85,
}

DEFAULT_TRUST = 0.5

AGREEMENT_CONFIDENCE = 0.95
CONFLICT_CONFIDENCE_CAP = 0.6
SINGLE_SOURCE_CONFIDENCE_CAP = 0.75

TRUST_CLOSENESS_THRESHOLD = 0.1


@dataclass
class FieldResult:
    value: object
    confidence: float
    provenance: list = field(default_factory=list)


def _trust(field_name: str, source_type: str) -> float:
    return TRUST_WEIGHTS.get((field_name, source_type), DEFAULT_TRUST)


def _resolve_scalar_field(field_name: str, candidates: list, comparison_fn=None) -> FieldResult:
    if not candidates:
        return FieldResult(value=None, confidence=0.0, provenance=[])

    cmp = comparison_fn or (lambda v: v)

    grouped = {}
    for raw_value, source_type, source_id in candidates:
        key = cmp(raw_value)
        grouped.setdefault(key, []).append((raw_value, source_type, source_id))

    if len(grouped) == 1:
        group = list(grouped.values())[0]
        winner_value = group[0][0]

        if len(group) > 1:
            confidence = AGREEMENT_CONFIDENCE
            provenance = [
                {
                    "field": field_name,
                    "source": source_id,
                    "method": "agreement",
                }
                for _, _, source_id in group
            ]
        else:
            _, source_type, source_id = group[0]
            confidence = min(
                _trust(field_name, source_type),
                SINGLE_SOURCE_CONFIDENCE_CAP,
            )
            provenance = [
                {
                    "field": field_name,
                    "source": source_id,
                    "method": "single-source",
                }
            ]

        return FieldResult(
            value=winner_value,
            confidence=confidence,
            provenance=provenance,
        )

    ranked = sorted(
        candidates,
        key=lambda c: _trust(field_name, c[1]),
        reverse=True,
    )

    top_trust = _trust(field_name, ranked[0][1])

    close_contenders = [
        c
        for c in ranked
        if top_trust - _trust(field_name, c[1])
        <= TRUST_CLOSENESS_THRESHOLD + 1e-9
    ]

    if len(close_contenders) > 1:
        best = max(
            close_contenders,
            key=lambda c: len(str(c[0])) if c[0] is not None else 0,
        )
    else:
        best = ranked[0]

    winner_value, winner_source_type, winner_source_id = best

    rejected = [
        value
        for value, _, source_id in candidates
        if source_id != winner_source_id
    ]

    confidence = min(
        _trust(field_name, winner_source_type),
        CONFLICT_CONFIDENCE_CAP,
    )

    provenance = [
        {
            "field": field_name,
            "source": winner_source_id,
            "method": "conflict-resolved",
            "rejected_values": rejected,
        }
    ]

    return FieldResult(
        value=winner_value,
        confidence=confidence,
        provenance=provenance,
    )


def parse_date_to_float(d_str: str) -> float:
    if not d_str:
        return 0.0
    if d_str == "present":
        return 2026.5                                                          
    try:
        parts = d_str.split("-")
        y = int(parts[0])
        m = int(parts[1]) if len(parts) > 1 else 1
        return y + (m - 1) / 12.0
    except Exception:
        return 0.0


def merge_candidate(records: list) -> dict:
    candidate_id = next(
        (r.candidate_key for r in records if r.candidate_key),
        "UNKNOWN",
    )

    provenance = []

                           
    name_candidates = [
        (r.fields["full_name"], r.source_type, r.source_id)
        for r in records
        if "full_name" in r.fields
    ]
    email_candidates = [
        (r.fields["email"], r.source_type, r.source_id)
        for r in records
        if "email" in r.fields
    ]
    phone_candidates = [
        (
            normalize_phone(r.fields["phone"]),
            r.source_type,
            r.source_id,
        )
        for r in records
        if "phone" in r.fields and normalize_phone(r.fields["phone"])
    ]

    name_result = _resolve_scalar_field("full_name", name_candidates)
    email_result = _resolve_scalar_field("email", email_candidates)
    phone_result = _resolve_scalar_field("phone", phone_candidates)

    provenance.extend(name_result.provenance + email_result.provenance + phone_result.provenance)

                                                    
    city_candidates = [
        (r.fields["city"], r.source_type, r.source_id)
        for r in records
        if "city" in r.fields
    ]
    country_candidates = []
    for r in records:
        if "country" in r.fields:
            norm_c = normalize_country(r.fields["country"])
            if norm_c:
                country_candidates.append((norm_c, r.source_type, r.source_id))

    city_res = _resolve_scalar_field("location.city", city_candidates)
    country_res = _resolve_scalar_field("location.country", country_candidates)

    provenance.extend(city_res.provenance + country_res.provenance)

    location = {
    "city": city_res.value if city_res.value else None,
    "region": None,
    "country": country_res.value if country_res.value else None,
}

              
    linkedin_candidates = [
        (r.fields["linkedin"], r.source_type, r.source_id)
        for r in records
        if "linkedin" in r.fields
    ]
    github_candidates = [
        (r.fields["github"], r.source_type, r.source_id)
        for r in records
        if "github" in r.fields
    ]
    portfolio_candidates = [
        (r.fields["portfolio"], r.source_type, r.source_id)
        for r in records
        if "portfolio" in r.fields
    ]

    linkedin_res = _resolve_scalar_field("links.linkedin", linkedin_candidates)
    github_res = _resolve_scalar_field("links.github", github_candidates)
    portfolio_res = _resolve_scalar_field("links.portfolio", portfolio_candidates)

    provenance.extend(linkedin_res.provenance + github_res.provenance + portfolio_res.provenance)

    links = {
        "linkedin": linkedin_res.value,
        "github": github_res.value,
        "portfolio": portfolio_res.value,
        "other": [],
    }

                 
    headline_candidates = []
    for r in records:
        if "headline" in r.fields:
            headline_candidates.append((r.fields["headline"], r.source_type, r.source_id))
        elif "title" in r.fields:
            headline_candidates.append((r.fields["title"], r.source_type, r.source_id))

    headline_res = _resolve_scalar_field("headline", headline_candidates)
    provenance.extend(headline_res.provenance)
    headline = headline_res.value

                                
    company_candidates = [
        (r.fields["company"], r.source_type, r.source_id)
        for r in records
        if "company" in r.fields
    ]
    title_candidates = [
        (r.fields["title"], r.source_type, r.source_id)
        for r in records
        if "title" in r.fields
    ]
    company_result = _resolve_scalar_field(
        "company",
        company_candidates,
        comparison_fn=normalize_company_for_comparison,
    )
    title_result = _resolve_scalar_field("title", title_candidates)
    provenance.extend(company_result.provenance + title_result.provenance)

                                    
    raw_exp_entries = []
    for r in records:
        if "experience_entries" in r.fields:
            for entry in r.fields["experience_entries"]:
                raw_exp_entries.append((entry, r.source_type, r.source_id))

    grouped_exp = {}
    for entry, source_type, source_id in raw_exp_entries:
        comp = entry.get("company") or ""
        norm_comp = normalize_company_for_comparison(comp)
        grouped_exp.setdefault(norm_comp, []).append((entry, source_type, source_id))

    experience = []
    for norm_comp, group in grouped_exp.items():
        comp_c = [(e.get("company"), st, sid) for e, st, sid in group if e.get("company")]
        title_c = [(e.get("title"), st, sid) for e, st, sid in group if e.get("title")]
        start_c = [
            (normalize_date(e.get("start")), st, sid)
            for e, st, sid in group
            if e.get("start") and normalize_date(e.get("start"))
        ]
        end_c = [
            (normalize_date(e.get("end")), st, sid)
            for e, st, sid in group
            if e.get("end") and normalize_date(e.get("end"))
        ]
        summary_c = [(e.get("summary"), st, sid) for e, st, sid in group if e.get("summary")]

        comp_res = _resolve_scalar_field("experience.company", comp_c)
        title_res = _resolve_scalar_field("experience.title", title_c)
        start_res = _resolve_scalar_field("experience.start", start_c)
        end_res = _resolve_scalar_field("experience.end", end_c)
        summary_res = _resolve_scalar_field("experience.summary", summary_c)

        provenance.extend(
            comp_res.provenance
            + title_res.provenance
            + start_res.provenance
            + end_res.provenance
            + summary_res.provenance
        )

        experience.append(
            {
                "company": comp_res.value,
                "title": title_res.value,
                "start": start_res.value,
                "end": end_res.value,
                "summary": summary_res.value,
            }
        )

                                      
    total_years = 0.0
    for exp_entry in experience:
        if exp_entry["start"]:
            start_f = float(parse_date_to_float(exp_entry["start"]))

            if exp_entry["end"]:
                end_f = float(parse_date_to_float(exp_entry["end"]))
            else:
                end_f = float(datetime.now().year)

            if end_f > start_f:
                total_years += end_f - start_f
    years_experience = round(total_years, 1) if total_years > 0.0 else None

                                   
    raw_edu_entries = []
    for r in records:
        if "education_entries" in r.fields:
            for entry in r.fields["education_entries"]:
                raw_edu_entries.append((entry, r.source_type, r.source_id))

    grouped_edu = {}
    for entry, source_type, source_id in raw_edu_entries:
        inst = entry.get("institution") or ""
        norm_inst = inst.strip().lower()
        grouped_edu.setdefault(norm_inst, []).append((entry, source_type, source_id))

    education = []
    for norm_inst, group in grouped_edu.items():
        inst_c = [(e.get("institution"), st, sid) for e, st, sid in group if e.get("institution")]
        degree_c = [(e.get("degree"), st, sid) for e, st, sid in group if e.get("degree")]
        field_c = [(e.get("field"), st, sid) for e, st, sid in group if e.get("field")]
        end_year_c = [(e.get("end_year"), st, sid) for e, st, sid in group if e.get("end_year")]

        inst_res = _resolve_scalar_field("education.institution", inst_c)
        degree_res = _resolve_scalar_field("education.degree", degree_c)
        field_res = _resolve_scalar_field("education.field", field_c)
        end_year_res = _resolve_scalar_field("education.end_year", end_year_c)

        provenance.extend(
            inst_res.provenance
            + degree_res.provenance
            + field_res.provenance
            + end_year_res.provenance
        )

        education.append(
            {
                "institution": inst_res.value,
                "degree": degree_res.value,
                "field": field_res.value,
                "end_year": end_year_res.value,
            }
        )

               
    skills_map = {}
    for r in records:
        for raw_skill in r.fields.get("skills", []):
            canonical = normalize_skill(raw_skill)
            trust = _trust("skills", r.source_type)

            entry = skills_map.setdefault(
                canonical,
                {
                    "sources": [],
                    "confidence": 0.0,
                },
            )

            entry["sources"].append(r.source_id)
            entry["confidence"] = max(entry["confidence"], trust)

    skills_output = [
        {
            "name": name,
            "confidence": round(data["confidence"], 2),
            "sources": data["sources"],
        }
        for name, data in skills_map.items()
    ]

                                  
    field_confidences = [
        r.confidence
        for r in [
            name_result,
            email_result,
            phone_result,
            city_res,
            country_res,
            linkedin_res,
            github_res,
            headline_res,
        ]
        if r.value is not None
    ]

    overall_confidence = (
        round(sum(field_confidences) / len(field_confidences), 2)
        if field_confidences
        else 0.0
    )

    return {
        "candidate_id": candidate_id,
        "full_name": name_result.value,
        "emails": [email_result.value] if email_result.value else [],
        "phones": [phone_result.value] if phone_result.value else [],
        "location": location,
        "links": links,
        "headline": headline,
        "years_experience": years_experience,
        "skills": skills_output,
        "experience": experience,
        "education": education,
        "provenance": provenance,
        "overall_confidence": overall_confidence,
    }
