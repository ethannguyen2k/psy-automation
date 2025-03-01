import os
import json
from stage3_llm_extraction import GeminiExtractor

def test_llm_extraction():
    """Test the LLM-based information extraction with Wisemind Psychology example."""
    print("\n" + "="*50)
    print("TESTING LLM-BASED EXTRACTION WITH WISEMIND PSYCHOLOGY")
    print("="*50)
    
    # Check if API key is set
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print("\nGEMINI_API_KEY not found in environment variables.")
        print("Please set your API key to run this test:")
        print("  export GEMINI_API_KEY='your-api-key'")
        
        # Create a mock sample of what the output would look like for Wisemind Psychology
        print("\nDemo mode: Showing example output without calling the API.")
        
        sample_result = {
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
                "initial_consult": "220",
                "followup_consult": "180"
            }
        }
        
        print("\nSample extraction result for Wisemind Psychology:")
        print(json.dumps(sample_result, indent=2))
        return
    
    # Create sample text file for Wisemind Psychology if it doesn't exist
    sample_dir = "wisemind_sample_data"
    if not os.path.exists(sample_dir):
        os.makedirs(sample_dir)
        
    sample_file = os.path.join(sample_dir, "wisemind_psychology.txt")
    
    if not os.path.exists(sample_file):
        # Create a sample Wisemind Psychology data file based on their real website structure
        sample_content = """Practice: Wisemind Psychology
Website: http://www.wisemind.com.au
Emails: admin@wisemind.com.au
Doctor Pages: http://www.wisemind.com.au/our-team/

--- MAIN PAGE CONTENT ---

<h1>Welcome to Wisemind Psychology</h1>
<p>We are a team of dedicated psychologists providing mental health care and psychological services on the Sunshine Coast, Queensland.</p>
<p>Our clinic offers evidence-based psychological therapy for children, adolescents, and adults.</p>

<h2>Our Services</h2>
<ul>
<li>Individual therapy</li>
<li>Depression and anxiety treatment</li>
<li>Trauma therapy</li>
<li>Stress management</li>
<li>Relationship counseling</li>
</ul>

<h2>Contact Us</h2>
<p>Phone: 0490 193 347</p>
<p>Email: admin@wisemind.com.au</p>
<p>Address: Unit 2/40 Minchinton St, Caloundra QLD 4551</p>

--- DOCTOR PAGE: http://www.wisemind.com.au/our-team/ ---

<h1>Our Team</h1>
<p>Our clinic has a team of experienced and qualified psychologists.</p>

<h2>Melissa Madden</h2>
<p>Clinical Psychologist</p>
<p>Melissa is the principal psychologist at Wisemind Psychology with extensive experience in treating depression, anxiety, and trauma-related conditions.</p>

<h2>Danielle Comerford</h2>
<p>General Psychologist</p>
<p>Danielle specializes in working with adults experiencing anxiety, depression, and relationship difficulties.</p>

<h2>Rachel Hannam</h2>
<p>General Psychologist</p>
<p>Rachel works with children, adolescents, and adults, offering support for anxiety, depression, and stress management.</p>

--- OTHER PAGE: http://www.wisemind.com.au/fees/ ---

<h1>Fees and Rebates</h1>
<p>We aim to provide accessible psychological services to our community.</p>

<h2>Consultation Fees</h2>
<p>Initial Consultation (50 minutes): $220</p>
<p>Follow-up Sessions (50 minutes): $180</p>

<h2>Medicare Rebates</h2>
<p>With a Mental Health Treatment Plan from your GP, you may be eligible for Medicare rebates for psychology sessions.</p>

<h2>Private Health Insurance</h2>
<p>Clients with private health insurance may be eligible for rebates depending on their level of cover.</p>
"""
        
        with open(sample_file, 'w', encoding='utf-8') as f:
            f.write(sample_content)
        
    # Initialize the extractor
    try:
        extractor = GeminiExtractor()
        
        # Extract information from the Wisemind Psychology sample file
        print(f"\nExtracting information from {sample_file}...")
        
        with open(sample_file, 'r', encoding='utf-8') as f:
            content = f.read()
            
        result = extractor.extract_info_from_text("Wisemind Psychology", content)
        
        # Output the extraction results
        print("\nExtraction Results for Wisemind Psychology:")
        print(json.dumps(result, indent=2))
        
        # Process all files in the directory
        all_results = extractor.process_scraped_data(sample_dir, 
                                                   output_file=os.path.join(sample_dir, "wisemind_extraction_results.json"))
        
        print(f"\nProcessed all files in {sample_dir}. Results saved to wisemind_extraction_results.json")
        
        # Show how this would update an Excel file
        print("\nExample of how this data would update an Excel file:")
        print("1. Email: admin@wisemind.com.au would be added to the Email column")
        print("2. Doctor page URL: http://www.wisemind.com.au/our-team/ would be added to the Doctors column")
        print("3. Three psychologists would be added in separate rows:")
        print("   - Melissa Madden (Clinical Psychologist)")
        print("   - Danielle Comerford (General Psychologist)")
        print("   - Rachel Hannam (General Psychologist)")
        print("4. Pricing information would be added:")
        print("   - Initial Consult: $220")
        print("   - Follow-up Consult: $180")
        
    except Exception as e:
        print(f"Error during extraction: {str(e)}")
        print("You can still examine the sample file to understand how the extraction would work.")

if __name__ == "__main__":
    test_llm_extraction()