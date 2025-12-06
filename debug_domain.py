import app

def test_domain_classification(domain):
    print(f"=== Testing domain: {domain} ===")
    
    # Clean the domain like the app does
    cleaned_domain = domain.lower().strip()
    if cleaned_domain.startswith('http://'):
        cleaned_domain = cleaned_domain[7:]
    elif cleaned_domain.startswith('https://'):
        cleaned_domain = cleaned_domain[8:]
    if cleaned_domain.startswith('www.'):
        cleaned_domain = cleaned_domain[4:]
    
    print(f"Cleaned domain: {cleaned_domain}")
    print(f"Is valid domain: {app.is_valid_domain(cleaned_domain)}")
    print(f"Is trusted domain: {app.is_trusted_domain(cleaned_domain)}")
    print(f"Trusted suffixes: {app.TRUSTED_SUFFIXES}")
    
    # Test the suffix matching manually
    d = cleaned_domain.lower().strip().rstrip('.')
    print(f"Domain for matching: '{d}'")
    
    for suf in app.TRUSTED_SUFFIXES:
        if d == suf:
            print(f"✅ Exact match with: {suf}")
        elif d.endswith('.' + suf):
            print(f"✅ Suffix match with: {suf}")
        else:
            print(f"❌ No match with: {suf}")

if __name__ == "__main__":
    test_domain_classification("mail.google.com")
    print()
    test_domain_classification("google.com")
