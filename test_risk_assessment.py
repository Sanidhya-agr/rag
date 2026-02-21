import json
from contract_scanner import scan_contract
from risk_assessment import assess_risk

# Read the test contract
with open("data/ProfessionalServicesAgreement.txt", "r", encoding="utf-8") as f:
    contract_text = f.read()

print(">>> Scanning contract with CUAD model...")
print("-" * 50)

# Step 1: Extract clauses
extracted = scan_contract(contract_text)

print("\n=== EXTRACTED CLAUSES ===")
for category, info in extracted.items():
    status = "✓ FOUND" if info["found"] else "✗ NOT FOUND"
    score = f"{info['score']:.1%}"
    answer = info["answer"][:120] + "…" if len(info["answer"]) > 120 else info["answer"]
    print(f"  [{status}] {category} ({score}): {answer}")

print("\n" + "=" * 80)
print(">>> Running LLM risk assessment...\n")

# Step 2: Risk assessment (now returns a dict, not a generator)
report = assess_risk(extracted)

# Validate structure
assert isinstance(report, dict), "Report should be a dict"
assert "overallRisk" in report, "Missing overallRisk key"
assert "summary" in report, "Missing summary key"
assert "risks" in report, "Missing risks key"
assert report["overallRisk"] in ("Red", "Yellow", "Green"), f"Invalid overallRisk: {report['overallRisk']}"
assert isinstance(report["risks"], list), "risks should be a list"

for r in report["risks"]:
    assert "severity" in r, "Each risk must have a severity"
    assert "title" in r, "Each risk must have a title"
    assert "issue" in r, "Each risk must have an issue"
    assert "suggestion" in r, "Each risk must have a suggestion"

print("=== RISK ASSESSMENT (Structured JSON) ===")
print(json.dumps(report, indent=2))
print("\n" + "=" * 80)
print("✓ All assertions passed — structured output is valid.")
