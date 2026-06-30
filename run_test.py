from src.pipeline import run_pipeline
from src.project import project
import json

results = run_pipeline(
    csv_path='data/samples/recruiter_export.csv',
    json_path='data/samples/ats_blob.json',
    resume_paths=[
        'data/samples/resume_C001.pdf',
        'data/samples/resume_C004.pdf',
        'data/samples/resume_C005_garbage.pdf',
    ],
)

print("=== DEFAULT OUTPUT (C001) ===")
print(json.dumps(results[0], indent=2))

config = json.load(open('configs/example_config.json'))
print("\n=== CUSTOM CONFIG OUTPUT (C001) ===")
print(json.dumps(project(results[0], config), indent=2))