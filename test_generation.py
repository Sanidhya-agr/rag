from generation import generate_contract

test_inputs = [
  """Partnership between Manish and Deepak for 2 years in India. 
Manish will engage in promotional activities on social media. 
Deepak will pay Manish ₹50,000 per month. Governing law: India."""]
for inp in test_inputs:
    print(f"\n>>> Input: {inp}")
    print("-" * 50)
    result = generate_contract(inp)
    print(result)
    print("=" * 80)

