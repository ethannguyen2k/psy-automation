import pandas as pd
import os
from stage4_validation import DataValidator, DataFormatter

def test_data_validator():
    """Test the DataValidator class."""
    print("\n" + "="*50)
    print("TESTING DATA VALIDATOR")
    print("="*50)
    
    validator = DataValidator()
    
    # Test address validation with Wisemind Psychology address
    addresses = [
        "Unit 2/40 Minchinton St, Caloundra QLD 4551",  # Should be corrected
        "40 Minchinton St, Caloundra QLD 4551",        # Already correct
        "Minchinton St Caloundra QLD 4551",            # Missing number
        "40 Minchinton St Caloundra QLD",              # Missing comma and postcode
        "Cnr Queen & Victoria St, Brisbane QLD 4000"   # Corner address
    ]
    
    print("\nAddress Validation:")
    for address in addresses:
        valid, cleaned = validator.validate_address(address)
        print(f"'{address}'")
        print(f"  Valid: {valid}")
        print(f"  Cleaned: '{cleaned}'")
        print()
    
    # Test email validation
    emails = [
        "admin@wisemind.com.au",      # Valid
        "info@psychology.com",        # Valid
        "contact.us@clinic.net.au",   # Valid
        "not-an-email",               # Invalid
        "missing@domain"              # Invalid
    ]
    
    print("\nEmail Validation:")
    for email in emails:
        valid, cleaned = validator.validate_email(email)
        print(f"'{email}' -> Valid: {valid}, Cleaned: '{cleaned}'")
    
    # Test URL validation
    urls = [
        "http://www.wisemind.com.au",          # Valid
        "https://psychology-clinic.com.au",    # Valid
        "www.mindfultherapy.net",              # Missing http, should be fixed
        "psychology-website",                  # Invalid
        "info@domain.com"                      # Not a URL
    ]
    
    print("\nURL Validation:")
    for url in urls:
        valid, cleaned = validator.validate_url(url)
        print(f"'{url}' -> Valid: {valid}, Cleaned: '{cleaned}'")
    
    # Test phone validation
    phones = [
        "0490193347",           # Valid
        "(07) 5432 1098",       # Should be cleaned
        "+61 412 345 678",      # Should be cleaned
        "1800 123 456",         # Valid
        "not-a-phone"           # Invalid
    ]
    
    print("\nPhone Validation:")
    for phone in phones:
        valid, cleaned = validator.validate_phone(phone)
        print(f"'{phone}' -> Valid: {valid}, Cleaned: '{cleaned}'")
    
    # Test psychologist type validation
    types = [
        "C",                      # Valid
        "G",                      # Valid
        "Clinical Psychologist",  # Should be cleaned to "C"
        "General",                # Should be cleaned to "G"
        "Therapist"               # Invalid
    ]
    
    print("\nPsychologist Type Validation:")
    for psych_type in types:
        valid, cleaned = validator.validate_psychologist_type(psych_type)
        print(f"'{psych_type}' -> Valid: {valid}, Cleaned: '{cleaned}'")
    
    # Test price validation
    prices = [
        "$220",           # Valid
        "180.00",         # Valid
        "$195.50",        # Valid
        "about $200",     # Should extract 200
        "not a price"     # Invalid
    ]
    
    print("\nPrice Validation:")
    for price in prices:
        valid, cleaned = validator.validate_price(price)
        print(f"'{price}' -> Valid: {valid}, Cleaned: '{cleaned}'")

def test_data_formatter():
    """Test the DataFormatter class with Wisemind Psychology example."""
    print("\n" + "="*50)
    print("TESTING DATA FORMATTER")
    print("="*50)
    
    # Create a sample DataFrame
    data = {
        "Practice": ["Wisemind Psychology"],
        "Address": ["Unit 2/40 Minchinton St, Caloundra QLD 4551"],
        "Website": ["http://www.wisemind.com.au"],
        "Phone": ["0490193347"],
        "Name": [""],
        "Email": [""],
        "Doctors": [""],
        "Type": [""],
        "Initial Consult": [""],
        "Follow-up Consult": [""],
        "Date": [""],
        "Notes": [""]
    }
    
    df = pd.DataFrame(data)
    
    # Create sample extracted data
    extracted_data = {
        "Wisemind Psychology": {
            "practice_name": "Wisemind Psychology",
            "email": "admin@wisemind.com.au",
            "doctor_page_url": "http://www.wisemind.com.au/our-team/",
            "psychologists": [
                {
                    "name": "Melissa Madden",
                    "type": "C"
                },
                {
                    "name": "Danielle Comerford",
                    "type": "G"
                },
                {
                    "name": "Rachel Hannam",
                    "type": "G"
                }
            ],
            "pricing_info": {
                "initial_consult": "$220",
                "followup_consult": "$180"
            }
        }
    }
    
    # Initialize the formatter
    formatter = DataFormatter()
    
    # Format the data
    updated_df, new_rows, discrepancies = formatter.format_data_for_excel(df, extracted_data)
    
    # Print the results
    print("\nOriginal DataFrame:")
    print(df)
    
    print("\nUpdated DataFrame:")
    print(updated_df)
    
    print(f"\nNew Rows Added: {len(new_rows)}")
    for i, row in enumerate(new_rows):
        print(f"\nNew Row {i+1}:")
        for col, val in row.items():
            print(f"  {col}: {val}")
    
    print(f"\nDiscrepancies Found: {len(discrepancies)}")
    for idx, message in discrepancies:
        print(f"  Row {idx+2}: {message}")
    
    # Save to Excel for inspection
    output_dir = "test_output"
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        
    output_file = os.path.join(output_dir, "formatter_test_output.xlsx")
    
    # Combine the updated DataFrame and new rows
    if new_rows:
        combined_df = pd.concat([updated_df, pd.DataFrame(new_rows)], ignore_index=True)
    else:
        combined_df = updated_df
        
    combined_df.to_excel(output_file, index=False)
    print(f"\nSaved formatted data to {output_file}")

if __name__ == "__main__":
    test_data_validator()
    print("\n" + "="*70 + "\n")
    test_data_formatter()