from jsonschema import Draft7Validator

DEFAULT_SCHEMA = {
    "type": "object",
    "properties": {

        "candidate_id": {"type": "string"},

        "full_name": {"type": ["string", "null"]},

        "emails": {
            "type": "array",
            "items": {
                "type": "string",
                "format": "email"
            }
        },

        "phones": {
            "type": "array",
            "items": {
                "type": "string",
                "pattern": "^\\+?[1-9]\\d{1,14}$"
            }
        },

        "location": {
            "type": ["object", "null"],
            "properties": {
                "city": {"type": ["string", "null"]},
                "region": {"type": ["string", "null"]},
                "country": {
                    "type": ["string", "null"],
                    "pattern": "^[A-Z]{2}$"
                }
            },
            "required": ["city", "region", "country"]
        },

        "links": {
            "type": "object",
            "properties": {
                "linkedin": {"type": ["string", "null"]},
                "github": {"type": ["string", "null"]},
                "portfolio": {"type": ["string", "null"]},
                "other": {
                    "type": "array",
                    "items": {"type": "string"}
                }
            },
            "required": ["linkedin", "github", "portfolio", "other"]
        },

        "headline": {"type": ["string", "null"]},

        "years_experience": {
            "type": ["number", "null"],
            "minimum": 0
        },

        "skills": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "confidence": {
                        "type": "number",
                        "minimum": 0,
                        "maximum": 1
                    },
                    "sources": {
                        "type": "array",
                        "items": {"type": "string"}
                    }
                },
                "required": ["name", "confidence", "sources"]
            }
        },

        "experience": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "company": {"type": ["string", "null"]},
                    "title": {"type": ["string", "null"]},
                    "start": {
                        "type": ["string", "null"],
                        "pattern": "^\\d{4}-(0[1-9]|1[0-2])$"
                    },
                   "end": {
    "type": ["string", "null"],
    "pattern": "^(\\d{4}-(0[1-9]|1[0-2])|[Pp]resent)$"
},
                    "summary": {"type": ["string", "null"]}
                },
                "required": ["company", "title", "start", "end", "summary"]
            }
        },

        "education": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "institution": {"type": ["string", "null"]},
                    "degree": {"type": ["string", "null"]},
                    "field": {"type": ["string", "null"]},
                    "end_year": {
                        "type": ["string", "null"],
                        "pattern": "^\\d{4}$"
                    }
                },
                "required": ["institution", "degree", "field", "end_year"]
            }
        },

        "provenance": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "field": {"type": "string"},
                    "source": {"type": "string"},
                    "method": {"type": "string"}
                },
                "required": ["field", "source", "method"]
            }
        },

        "overall_confidence": {
            "type": ["number", "null"],
            "minimum": 0,
            "maximum": 1
        },
    },

    "required": [
        "candidate_id",
        "full_name",
        "emails",
        "phones"
    ]
}


def validate_output(o, c=None):
    s = c if c else DEFAULT_SCHEMA
    v = Draft7Validator(s)
    e = sorted(v.iter_errors(o), key=lambda x: list(x.path))
    return [
        f"{'/'.join(str(p) for p in x.path) or '<root>'}: {x.message}"
        for x in e
    ]