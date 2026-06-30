"""
extract/base.py
Shared contract every extractor must satisfy, so merge.py never needs
to know which concrete source type produced a record.
"""

from dataclasses import dataclass, field


@dataclass
class RawCandidateFields:
    """
    Common, un-normalized output of any extractor for ONE candidate
    from ONE source. Field values are whatever the source gave us,
    untouched -- normalization happens later, in normalize.py.

    source_type    -- e.g. "recruiter_csv", "ats_json", "resume_pdf"
    source_id      -- a human-traceable identifier for this exact source
                       record (e.g. file name + row number), used in provenance.
    candidate_key  -- best-effort key to align this record with the same
                       candidate across sources (e.g. the CSV/ATS id, or a
                       filename-derived key for unstructured sources).
    fields         -- flat dict of raw field name -> raw value. Missing
                       fields are simply absent (not None) so downstream
                       code can distinguish "not provided" from "empty".
    parse_errors   -- non-fatal issues encountered while extracting,
                       surfaced for provenance/debugging, never raised.
    """
    source_type: str
    source_id: str
    candidate_key: str | None
    fields: dict = field(default_factory=dict)
    parse_errors: list = field(default_factory=list)