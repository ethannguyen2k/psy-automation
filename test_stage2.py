import pandas as pd
import os
import json
from stage2_web_scraping import WebScraper

def test_web_scraping():
    """Test the web scraper with Wisemind Psychology website."""
    # Create a sample DataFrame with Wisemind Psychology website
    data = {
        "Practice": [
            "Wisemind Psychology"
        ],
        "Address": [
            "Unit 2/40 Minchinton St, Caloundra QLD 4551"
        ],
        "Website": [
            "http://www.wisemind.com.au"
        ],
        "Phone": [
            "0490193347"
        ]
    }
    
    # Create DataFrame and set "green rows"
    df = pd.DataFrame(data)
    green_rows = [0]  # Only one row in this test
    
    print("\n" + "="*50)
    print("TESTING WEB SCRAPING (WISEMIND PSYCHOLOGY)")
    print("="*50)
    
    # Create output directory
    output_dir = "wisemind_scraped_data"
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    # Initialize scraper
    scraper = WebScraper(output_dir=output_dir)
    scraper.load_data(df, green_rows)
    
    # Set to True to actually scrape the website (will contact external site)
    actually_scrape = True
    
    if actually_scrape:
        # Scrape Wisemind Psychology website
        print("\nScraping Wisemind Psychology website...")
        result = scraper.scrape_clinic(0, df.iloc[0])
        
        # Print results
        print("\nScraping Results:")
        print(f"Practice: {result.get('practice_name')}")
        print(f"Website: {result.get('website_url')}")
        print(f"Emails found: {result.get('email', [])}")
        print(f"Doctor pages found: {len(result.get('doctor_pages', []))}")
        
        # Extract specific information
        extracted = scraper.extract_specific_info(result)
        print("\nExtracted Information:")
        print(f"Email: {extracted.get('email')}")
        print(f"Doctor page: {extracted.get('doctor_page_url')}")
        print(f"Psychologists found: {len(extracted.get('psychologists', []))}")
        for psych in extracted.get('psychologists', []):
            print(f"  - {psych.get('name')} ({psych.get('type')})")
        
        # Print pricing information
        pricing = extracted.get('pricing_info', {})
        print(f"Initial consult price: {pricing.get('initial_consult', 'Not found')}")
        print(f"Follow-up consult price: {pricing.get('followup_consult', 'Not found')}")
        
        # Save detailed results to file for inspection
        with open(os.path.join(output_dir, "wisemind_results.json"), "w") as f:
            # Convert sets to lists for JSON serialization
            serializable_result = {}
            for k, v in result.items():
                if isinstance(v, set):
                    serializable_result[k] = list(v)
                else:
                    serializable_result[k] = v
            json.dump(serializable_result, f, indent=2)
        
        print(f"\nDetailed results saved to {os.path.join(output_dir, 'wisemind_results.json')}")
    else:
        print("\nTest mode: Not actually scraping the website.")
        print("To test scraping the real website, set actually_scrape = True")
        
        # Provide information about Wisemind Psychology website
        print("\nWisemind Psychology Website Information:")
        print("URL: http://www.wisemind.com.au")
        print("The website provides information about psychologists practicing at Wisemind Psychology.")
        print("It includes sections on About, Services, Team Members, and Contact information.")
        print("The psychologists at this practice work with various mental health issues including:")
        print("- Anxiety and stress")
        print("- Depression")
        print("- Trauma")
        print("- Relationship issues")
        
        # Provide information about what the scraper would extract
        print("\nWhat the scraper would extract:")
        print("- Practice email addresses like admin@wisemind.com.au")
        print("- URLs to pages with psychologist information")
        print("- Names and types of psychologists working at the practice")
        print("- Consultation pricing information if available")
        
        # Explain what happens when actually_scrape=True
        print("\nWhen actually_scrape=True, the program will:")
        print("1. Visit the Wisemind Psychology website")
        print("2. Download and parse the main page")
        print("3. Find and visit relevant subpages (About, Team, Services, etc.)")
        print("4. Extract all the relevant information")
        print("5. Save the extracted text to files in the wisemind_scraped_data directory")
        print("6. Process the text to identify psychologists, emails, and pricing")

if __name__ == "__main__":
    test_web_scraping()