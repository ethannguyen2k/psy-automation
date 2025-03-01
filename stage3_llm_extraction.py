from google import genai
import os
import json
import time
import logging
import re
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
import pandas as pd
import random

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("log/llm_extraction.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Define data models for structured output
class Psychologist(BaseModel):
    name: str
    type: str = Field(description="Type of psychologist: 'C' for Clinical, 'G' for General")

class PricingInfo(BaseModel):
    initial_consult: Optional[str] = None
    followup_consult: Optional[str] = None

class ClinicInfo(BaseModel):
    practice_name: str
    email: Optional[str] = None
    doctor_page_url: Optional[str] = None
    psychologists: List[Psychologist] = []
    pricing_info: PricingInfo = PricingInfo()

class GeminiExtractor:
    def __init__(self, api_key=None, model_name="gemini-2.0-flash"):
        """
        Initialize the Gemini API extractor.
        
        Args:
            api_key (str): Gemini API key
            model_name (str): Gemini model name
        """
        self.api_key = api_key or os.environ.get("GEMINI_API_KEY")
        if not self.api_key:
            raise ValueError("Gemini API key is required. Set GEMINI_API_KEY environment variable or pass as parameter.")
            
        self.model_name = model_name
        self.client = genai.Client(api_key=self.api_key)
        
        logger.info(f"Initialized Gemini Extractor with model: {model_name}")
        
        # Set up extraction prompts
        self._setup_prompts()
        
        # Track rate limiting
        self.last_request_time = 0
        self.min_request_interval = 4  # seconds between requests (to respect the 15 RPM limit)
        
    def _setup_prompts(self):
        """Set up extraction prompts."""
        self.base_prompt = """
        You are a specialized data extraction assistant for psychology clinics in Australia. Your task is to extract specific structured information from website content with high precision and recall.
        
        I'll provide you with text scraped from a psychology clinic website. Extract ONLY the following information:
        
        1. Email address(es) for the clinic (primary contact email preferred)
        2. URL for the doctor/team page (look for pages about staff, team, our psychologists, practitioners)
        3. List of psychologists with their full names and specific types:
        - Use 'C' for Clinical Psychologists (identified by terms like 'Clinical Psychologist', 'Clinical Registration', 'Clinical Endorsement', 'Clinical Registar')
        - Use 'G' for General Psychologists (identified by terms like 'Registered Psychologist', 'General Psychologist', 'Psychologist')
        - Include ALL psychologists you can identify from the content
        4. Pricing information:
        - Initial consultation price (look for terms like 'initial', 'first appointment', 'new patient')
        - Follow-up consultation price (look for terms like 'follow-up', 'standard', 'subsequent', 'return')
        
        Important guidelines:
        - For each field, provide ONLY the extracted information without explanation
        - If multiple options exist (e.g., multiple emails), choose the most likely primary contact
        - For prices, extract numerical values with dollar signs if present
        - If information is not found, leave that field empty or null
        - ONLY return psychologists, not other staff like admin, reception, or other health practitioners
        - Ensure each psychologist's name is a full name (first and last name)
        """
        
        self.page_structure_prompt = """
        The text provided has the following structure:
        - Begins with metadata like Practice name, Website, Emails, and Doctor Pages
        - Contains multiple sections marked with "---" separators (MAIN PAGE, DOCTOR PAGE, OTHER PAGE)
        - Each section has HTML-like elements including headings (<h1>, <h2>), paragraphs (<p>), and lists (<ul>, <li>)
        - Key information like psychologist names often appears in headings
        - Contact information is typically found in the MAIN PAGE section
        - Psychologist details are most likely in the DOCTOR PAGE sections
        - Pricing information might appear in sections about fees, services, or FAQs
        
        Analyze ALL sections thoroughly before making your determination.
        """
    
    def _respect_rate_limit(self):
        """Ensure we respect the rate limit by sleeping if necessary."""
        now = time.time()
        time_since_last_request = now - self.last_request_time
        
        if time_since_last_request < self.min_request_interval:
            sleep_time = self.min_request_interval - time_since_last_request
            logger.info(f"Rate limiting: Sleeping for {sleep_time:.2f} seconds")
            time.sleep(sleep_time)
            
        self.last_request_time = time.time()
    
    def extract_info_from_text(self, practice_name, website_text, structured_output=True):
        """
        Extract clinic information from website text using Gemini API.
        
        Args:
            practice_name (str): Name of the practice
            website_text (str): Text content scraped from the website
            structured_output (bool): Whether to return structured output
            
        Returns:
            dict: Extracted information
        """
        self._respect_rate_limit()
        
        # Prepare the prompt
        prompt = f"{self.base_prompt}\n\n{self.page_structure_prompt}\n\nPractice Name: {practice_name}\n\nWebsite Content:\n\n"
        
        # Trim the website content if it's too long (Gemini has token limits)
        if len(website_text) > 80000:  # Arbitrary limit to avoid token issues
            website_text = website_text[:40000] + "\n...[Content truncated]...\n" + website_text[-40000:]
            
        prompt += website_text

        # Retry parameters
        max_retries = 3
        retry_count = 0
        
        while retry_count < max_retries:
            try:
                if structured_output:
                    response = self.client.models.generate_content(
                        model=self.model_name,
                        contents=prompt,
                        config={
                            'response_mime_type': 'application/json',
                        },
                    )
                    
                    try:
                        import json
                        result_text = response.text
                        result = json.loads(result_text)
                        return result
                    except Exception as e:
                        logger.error(f"Error parsing JSON response: {str(e)}")
                        return {"raw_response": response.text}
                else:
                    response = self.client.models.generate_content(
                        model=self.model_name,
                        contents=prompt
                    )
                    return {"raw_response": response.text}
                    
            except Exception as e:
                retry_count += 1
                logger.warning(f"API call failed (attempt {retry_count}/{max_retries}): {str(e)}")
                
                if retry_count < max_retries:
                    # Exponential backoff with jitter
                    sleep_time = (2 ** retry_count) + random.uniform(0, 1)
                    logger.info(f"Retrying in {sleep_time:.2f} seconds...")
                    time.sleep(sleep_time)
                else:
                    logger.error(f"Error calling Gemini API after {max_retries} attempts: {str(e)}")
                    return {"error": str(e)}
    
    def process_scraped_data(self, scraped_data_dir, output_file=None, max_files=None):
        all_results = {}
        practice_to_results = {}  # This will map Excel practice names to results
        
        # Try to load practice mapping if it exists
        practice_mapping = {}
        mapping_file = os.path.join(scraped_data_dir, "practice_mapping.txt")
        if os.path.exists(mapping_file):
            try:
                with open(mapping_file, 'r', encoding='utf-8') as f:
                    for line in f:
                        if line.strip():
                            parts = line.strip().split('\t')
                            if len(parts) == 2:
                                filename, practice = parts
                                practice_mapping[filename] = practice
                logger.info(f"Loaded practice mapping with {len(practice_mapping)} entries")
            except Exception as e:
                logger.error(f"Error loading practice mapping: {str(e)}")
        
        # List all text files in the directory
        files = [f for f in os.listdir(scraped_data_dir) if f.endswith('.txt') and f != "practice_mapping.txt"]
        
        if max_files:
            files = files[:max_files]
            
        logger.info(f"Processing {len(files)} files from {scraped_data_dir}")
        
        for file_idx, filename in enumerate(files):
            file_path = os.path.join(scraped_data_dir, filename)
            logger.info(f"Processing file {file_idx+1}/{len(files)}: {filename}")
            
            try:
                # Read the file content first - this was missing in the previous code
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # First try to get practice name from mapping
                practice_name = practice_mapping.get(filename)
                
                # If not in mapping, extract from file content
                if not practice_name:
                    # Extract the exact practice name from the first line
                    first_line = content.split('\n', 1)[0]
                    if first_line.startswith('Practice:'):
                        practice_name = first_line[len('Practice:'):].strip()
                    else:
                        # Fallback to filename-based extraction
                        practice_name = filename.rsplit('_', 1)[0].replace('_', ' ')
                
                # Extract information using Gemini
                try:
                    result = self.extract_info_from_text(practice_name, content)
                    all_results[filename] = result
                    
                    # Store using the EXACT practice name for Excel matching
                    practice_to_results[practice_name] = result
                    logger.info(f"Extracted data for practice: '{practice_name}'")
                except Exception as e:
                    logger.error(f"Error extracting information from {filename}: {str(e)}")
                    all_results[filename] = {"error": str(e)}
                
                # Sleep between requests to respect rate limits
                if file_idx < len(files) - 1:
                    time.sleep(1)  # Additional small delay between files
                    
            except Exception as e:
                logger.error(f"Error processing {filename}: {str(e)}")
                all_results[filename] = {"error": str(e)}
        
        # Save results to file if specified
        if output_file:
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(all_results, f, indent=2)
            logger.info(f"Saved extraction results to {output_file}")
            
            # Also save the practice-to-results mapping for easier Excel matching
            practice_mapping_file = os.path.splitext(output_file)[0] + "_by_practice.json"
            with open(practice_mapping_file, 'w', encoding='utf-8') as f:
                json.dump(practice_to_results, f, indent=2)
            logger.info(f"Saved practice-based results to {practice_mapping_file}")
        
        # Return the practice-to-results mapping instead of filename-to-results
        return practice_to_results
    
    def update_excel_with_results(self, df, green_rows, extraction_results, file_mapping=None):
        """
        Update the Excel DataFrame with extracted information.
        
        Args:
            df (pandas.DataFrame): DataFrame to update
            green_rows (list): List of indices for green rows
            extraction_results (dict): Extracted information
            file_mapping (dict): Mapping between DataFrame indices and filenames
            
        Returns:
            pandas.DataFrame: Updated DataFrame
        """
        # Create a copy of the DataFrame to modify
        updated_df = df.copy()
        
        # Ensure required columns exist
        required_columns = ['Name', 'Email', 'Doctors', 'Type', 'Initial Consult', 'Follow-up Consult', 'Date', 'Notes']
        for col in required_columns:
            if col not in updated_df.columns:
                updated_df[col] = ""
        
        # Track new rows to add
        new_rows = []
        
        # Update existing rows and prepare new rows
        for idx in green_rows:
            if idx >= len(updated_df):
                continue
                
            # Get the filename associated with this row
            if file_mapping and idx in file_mapping:
                filename = file_mapping[idx]
            else:
                # No explicit mapping, try to find a match based on practice name
                practice_name = updated_df.iloc[idx].get('Practice', '')
                possible_matches = [
                    fname for fname in extraction_results.keys() 
                    if practice_name.lower() in fname.lower()
                ]
                
                if possible_matches:
                    filename = possible_matches[0]
                else:
                    # No matching file found
                    updated_df.loc[idx, 'Notes'] = "No extraction data found"
                    continue
            
            # Get extraction results for this file
            if filename not in extraction_results:
                updated_df.loc[idx, 'Notes'] = "No extraction data found"
                continue
                
            result = extraction_results[filename]
            
            # Check for errors
            if "error" in result:
                updated_df.loc[idx, 'Notes'] = f"Extraction error: {result['error']}"
                continue
            
            # Update email
            if result.get('email'):
                updated_df.loc[idx, 'Email'] = result['email']
                
            # Update doctor page URL
            if result.get('doctor_page_url'):
                updated_df.loc[idx, 'Doctors'] = result['doctor_page_url']
                
            # Update pricing information
            pricing_info = result.get('pricing_info', {})
            if pricing_info.get('initial_consult'):
                updated_df.loc[idx, 'Initial Consult'] = pricing_info['initial_consult']
                
            if pricing_info.get('followup_consult'):
                updated_df.loc[idx, 'Follow-up Consult'] = pricing_info['followup_consult']
            
            # Get today's date for the Date column
            import datetime
            today = datetime.datetime.now().strftime('%Y-%m-%d')
            updated_df.loc[idx, 'Date'] = today
            
            # Process psychologists
            psychologists = result.get('psychologists', [])
            
            if not psychologists:
                updated_df.loc[idx, 'Notes'] = "No psychologists found"
                continue
                
            # Update the first psychologist in the current row
            if psychologists:
                first_psych = psychologists[0]
                updated_df.loc[idx, 'Name'] = first_psych.get('name', '')
                updated_df.loc[idx, 'Type'] = first_psych.get('type', '')
                
                # Create new rows for additional psychologists
                for psych in psychologists[1:]:
                    new_row = updated_df.iloc[idx].copy()
                    new_row['Name'] = psych.get('name', '')
                    new_row['Type'] = psych.get('type', '')
                    new_rows.append(new_row)
        
        # Add new rows for additional psychologists
        if new_rows:
            updated_df = pd.concat([updated_df, pd.DataFrame(new_rows)], ignore_index=True)
            
        return updated_df

# Example usage
if __name__ == "__main__":
    # For testing, you would need to set the API key
    # os.environ["GEMINI_API_KEY"] = "your-api-key"
    
    print("This module provides LLM-based information extraction using the Gemini API.")
    print("To use it, you need to set the GEMINI_API_KEY environment variable.")
    print("Example:")
    print("extractor = GeminiExtractor()")
    print("results = extractor.process_scraped_data('scraped_data')")