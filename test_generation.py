from generation import generate_contract

test_inputs = [
    
   " I want to generate a Non-Disclosure Agreement (NDA), between manish (Party A) and deepak (Party B), with the following terms: i want to sign an nda with san for 2 years."
]

for inp in test_inputs:
    print(f"\n>>> Input: {inp}")
    print("-" * 50)
    result = generate_contract(inp)
    print(result)
    print("=" * 80)

