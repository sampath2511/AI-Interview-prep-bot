import json
from ai.gemini_service import generate_prep_material

try:
    res = generate_prep_material("Binary Trees", "beginner", [], [])
    print(json.dumps(res, indent=2))
except Exception as e:
    print(f"Error: {e}")
