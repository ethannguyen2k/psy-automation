import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
import random
import os
import re
import logging
from urllib.parse import urlparse, urljoin
from concurrent.futures import ThreadPoolExecutor, as_completed

# Set up logging
os.makedirs("log", exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("log/webscraper.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class WebScraper:
    def __init__(self, df=None, green_rows=None, output_dir="scraped_data"):
        """
        Initialize the web scraper.
        
        Args:
            df (pandas.DataFrame): DataFrame containing clinic data
            green_rows (list): List of indices for green rows
            output_dir (str): Directory to save scraped data
        """
        self.df = df
        self.green_rows = green_rows
        self.output_dir = output_dir
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
        }
        self.session = requests.Session()
        self.session.headers.update(self.headers)
        
        # Create output directory if it doesn't exist
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
            
        # Pages that are likely to contain psychologist information
        self.target_pages = [
            "about", "about-us", "our-team", "our-doctors", "our-psychologists", 
            "team", "staff", "practitioners", "doctors", "psychologists", "clinicians",
            "our-services", "services", "fees", "pricing"
        ]
    
    def load_data(self, df, green_rows):
        """Load DataFrame and green rows."""
        self.df = df
        self.green_rows = green_rows
        logger.info(f"Loaded data with {len(green_rows)} green rows to process")
    
    def clean_url(self, url):
        """Clean and normalize URL."""
        if not url:
            return None
            
        url = url.strip()
        
        # Add scheme if missing
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url
            
        # Remove trailing slash
        if url.endswith('/'):
            url = url[:-1]
            
        return url
    
    def is_valid_url(self, url):
        """Check if URL is valid."""
        if not url:
            return False
            
        try:
            result = urlparse(url)
            return all([result.scheme, result.netloc])
        except:
            return False
    
    def fetch_url(self, url, max_retries=3):
        """
        Fetch content from URL with retries.
        
        Args:
            url (str): URL to fetch
            max_retries (int): Maximum number of retries
            
        Returns:
            tuple: (success, content)
        """
        if not self.is_valid_url(url):
            logger.warning(f"Invalid URL: {url}")
            return False, None
            
        retries = 0
        while retries < max_retries:
            try:
                response = self.session.get(url, timeout=30)
                if response.status_code == 200:
                    return True, response
                elif response.status_code == 404:
                    logger.warning(f"Page not found: {url}")
                    return False, None
                else:
                    logger.warning(f"Failed to fetch {url}: Status code {response.status_code}")
                    retries += 1
                    time.sleep(2 * retries)  # Exponential backoff
            except requests.RequestException as e:
                logger.warning(f"Error fetching {url}: {str(e)}")
                retries += 1
                time.sleep(2 * retries)
                
        return False, None
    
    def extract_text_with_structure(self, html_content):
        """
        Extract text while preserving structural information.
        
        Args:
            html_content: HTML content to parse
            
        Returns:
            str: Structured text
        """
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Remove script and style elements
        for script in soup(["script", "style"]):
            script.decompose()
            
        # Extract text with structure
        structured_text = []
        
        # Handle headings
        for i in range(1, 7):
            for heading in soup.find_all(f'h{i}'):
                text = heading.get_text().strip()
                if text:
                    structured_text.append(f"<h{i}>{text}</h{i}>")
        
        # Handle paragraphs
        for p in soup.find_all('p'):
            text = p.get_text().strip()
            if text:
                structured_text.append(f"<p>{text}</p>")
        
        # Handle lists
        for ul in soup.find_all('ul'):
            list_items = []
            for li in ul.find_all('li'):
                text = li.get_text().strip()
                if text:
                    list_items.append(f"<li>{text}</li>")
            if list_items:
                structured_text.append("<ul>" + "".join(list_items) + "</ul>")
        
        for ol in soup.find_all('ol'):
            list_items = []
            for li in ol.find_all('li'):
                text = li.get_text().strip()
                if text:
                    list_items.append(f"<li>{text}</li>")
            if list_items:
                structured_text.append("<ol>" + "".join(list_items) + "</ol>")
        
        # Handle divs with content
        for div in soup.find_all('div'):
            # Skip divs that contain headings, paragraphs, or lists that we've already processed
            if div.find(['h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'p', 'ul', 'ol']):
                continue
            
            text = div.get_text().strip()
            if text:
                structured_text.append(f"<div>{text}</div>")
        
        return "\n".join(structured_text)
    
    def find_email(self, text):
        """Extract email addresses from text."""
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        emails = re.findall(email_pattern, text)
        return emails
    
    def extract_all_links(self, soup, base_url):
        """Extract all links from a soup object."""
        links = []
        for a in soup.find_all('a', href=True):
            href = a['href']
            # Convert relative URLs to absolute
            if not href.startswith(('http://', 'https://')):
                href = urljoin(base_url, href)
            links.append(href)
        return links
    
    def is_same_domain(self, url1, url2):
        """Check if two URLs belong to the same domain."""
        domain1 = urlparse(url1).netloc
        domain2 = urlparse(url2).netloc
        
        # Remove www prefix for comparison
        domain1 = domain1.replace('www.', '')
        domain2 = domain2.replace('www.', '')
        
        return domain1 == domain2
    
    def find_doctor_pages(self, main_soup, base_url):
        """Find potential doctor/team pages from the main page."""
        doctor_pages = []
        
        for a in main_soup.find_all('a', href=True):
            href = a['href']
            link_text = a.get_text().lower().strip()
            
            # Convert relative URLs to absolute
            if not href.startswith(('http://', 'https://')):
                href = urljoin(base_url, href)
                
            # Only consider links from the same domain
            if not self.is_same_domain(href, base_url):
                continue
                
            # Check if the link text or URL contains doctor-related keywords
            contains_keyword = any(keyword in link_text or keyword in href.lower() for keyword in self.target_pages)
            
            if contains_keyword:
                doctor_pages.append(href)
                
        return doctor_pages
    
    def scrape_clinic(self, idx, row, save_to_file=True):
        """
        Scrape a single clinic website.
        
        Args:
            idx (int): Row index
            row (pandas.Series): Row data
            save_to_file (bool): Whether to save results to file
            
        Returns:
            dict: Scraped data
        """
        practice_name = row.get('Practice', f"Unknown-{idx}")
        website_url = row.get('Website')
        
        if not website_url or not isinstance(website_url, str):
            logger.warning(f"Missing or invalid website URL for {practice_name}")
            return {"error": "Missing or invalid website URL"}
            
        website_url = self.clean_url(website_url)
        if not website_url:
            logger.warning(f"Could not clean URL for {practice_name}")
            return {"error": "Invalid URL format"}
            
        logger.info(f"Scraping website for {practice_name}: {website_url}")
        
        result = {
            "practice_name": practice_name,
            "website_url": website_url,
            "main_page_content": "",
            "email": [],
            "doctor_pages": [],
            "doctor_pages_content": {},
            "other_pages_content": {}
        }
        
        # Fetch main page
        success, response = self.fetch_url(website_url)
        if not success or not response:
            logger.warning(f"Failed to fetch main page for {practice_name}")
            return {"error": f"Failed to fetch {website_url}"}
            
        # Parse main page
        main_soup = BeautifulSoup(response.content, 'html.parser')
        main_page_content = self.extract_text_with_structure(response.content)
        result["main_page_content"] = main_page_content
        
        # Extract emails from main page
        emails = self.find_email(main_page_content)
        if emails:
            result["email"] = emails
            
        # Find doctor/team pages
        doctor_pages = self.find_doctor_pages(main_soup, website_url)
        result["doctor_pages"] = doctor_pages
        
        # Scrape doctor pages
        scraped_pages = set()  # Track already scraped pages
        
        for page_url in doctor_pages:
            if page_url in scraped_pages:
                continue
                
            # Add a slight delay to avoid overwhelming the server
            time.sleep(random.uniform(1, 2))
            
            success, response = self.fetch_url(page_url)
            if not success or not response:
                continue
                
            page_content = self.extract_text_with_structure(response.content)
            
            # Check if this looks like a doctor/team page based on keywords
            is_doctor_page = any(keyword in page_url.lower() for keyword in [
                "about", "team", "staff", "doctors", "practitioners", "psychologists"
            ])
            
            if is_doctor_page:
                result["doctor_pages_content"][page_url] = page_content
            else:
                result["other_pages_content"][page_url] = page_content
                
            scraped_pages.add(page_url)
            
            # Add emails found on this page
            page_emails = self.find_email(page_content)
            if page_emails:
                result["email"].extend(page_emails)
        
        # Remove duplicate emails
        result["email"] = list(set(result["email"]))
        
        # Save results to file
        if save_to_file:
            # Generate a safe filename
            safe_name = re.sub(r'[^\w\s-]', '', practice_name).strip().replace(' ', '_')
            file_path = os.path.join(self.output_dir, f"{safe_name}_{idx}.txt")
            
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(f"Practice: {practice_name}\n")
                f.write(f"Website: {website_url}\n")
                f.write(f"Emails: {', '.join(result['email'])}\n")
                f.write(f"Doctor Pages: {', '.join(result['doctor_pages'])}\n")
                f.write("\n--- MAIN PAGE CONTENT ---\n\n")
                f.write(result["main_page_content"])
                
                for url, content in result["doctor_pages_content"].items():
                    f.write(f"\n\n--- DOCTOR PAGE: {url} ---\n\n")
                    f.write(content)
                    
                for url, content in result["other_pages_content"].items():
                    f.write(f"\n\n--- OTHER PAGE: {url} ---\n\n")
                    f.write(content)
                    
            logger.info(f"Saved scraped data to {file_path}")

            # Also save a mapping file to help connect files to practice names
            mapping_file = os.path.join(self.output_dir, "practice_mapping.txt")
            with open(mapping_file, 'a', encoding='utf-8') as f:
                f.write(f"{os.path.basename(file_path)}\t{practice_name}\n")
        
        return result
    
    def scrape_all_clinics(self, max_workers=4, batch_size=10):
        """
        Scrape all clinics in batches using multiple threads.
        
        Args:
            max_workers (int): Maximum number of worker threads
            batch_size (int): Number of clinics to process in each batch
            
        Returns:
            dict: Scraped data for all clinics
        """
        if self.df is None or self.green_rows is None:
            logger.error("DataFrame or green rows not loaded")
            return {}
            
        all_results = {}
        
        # Process in batches
        for i in range(0, len(self.green_rows), batch_size):
            batch = self.green_rows[i:i+batch_size]
            batch_results = {}
            
            logger.info(f"Processing batch {i//batch_size + 1}: rows {batch[0]} to {batch[-1]}")
            
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                future_to_idx = {
                    executor.submit(self.scrape_clinic, idx, self.df.iloc[idx]): idx 
                    for idx in batch if idx < len(self.df)
                }
                
                for future in as_completed(future_to_idx):
                    idx = future_to_idx[future]
                    try:
                        result = future.result()
                        batch_results[idx] = result
                    except Exception as e:
                        logger.error(f"Error processing row {idx}: {str(e)}")
                        batch_results[idx] = {"error": str(e)}
            
            all_results.update(batch_results)
            
            # Sleep between batches to respect rate limits
            if i + batch_size < len(self.green_rows):
                sleep_time = random.uniform(3, 5)
                logger.info(f"Sleeping for {sleep_time:.2f} seconds before next batch")
                time.sleep(sleep_time)
        
        logger.info(f"Completed scraping {len(all_results)} clinics")
        return all_results
    
    def extract_specific_info(self, scraped_data):
        """
        Extract specific information from scraped data.
        
        Args:
            scraped_data (dict): Scraped data for a clinic
            
        Returns:
            dict: Extracted information
        """
        if "error" in scraped_data:
            return {"success": False, "error": scraped_data["error"]}
            
        # Initialize extracted info
        extracted = {
            "success": True,
            "email": None,
            "doctor_page_url": None,
            "psychologists": [],
            "pricing_info": {}
        }
        
        # Extract email
        if scraped_data["email"]:
            extracted["email"] = scraped_data["email"][0]  # Use the first email found
            
        # Extract doctor page URL
        if scraped_data["doctor_pages"]:
            extracted["doctor_page_url"] = scraped_data["doctor_pages"][0]  # Use the first doctor page
            
        # Try to extract psychologist names and types
        self._extract_psychologists(scraped_data, extracted)
        
        # Try to extract pricing information
        self._extract_pricing(scraped_data, extracted)
        
        return extracted
    
    def _extract_psychologists(self, scraped_data, extracted):
        """Extract psychologist names and types from scraped data."""
        # Combine all text content for analysis
        all_content = scraped_data["main_page_content"]
        
        for content in scraped_data["doctor_pages_content"].values():
            all_content += "\n" + content
            
        # Look for psychologist patterns in the content
        # This is a simplified approach - the LLM-based extraction in Stage 3 will be more sophisticated
        
        # Common title patterns
        title_patterns = [
            r'Dr\.\s+([A-Z][a-z]+\s+[A-Z][a-z]+)',
            r'([A-Z][a-z]+\s+[A-Z][a-z]+),?\s+(?:Clinical|Registered|General)?\s*Psychologist',
            r'<h[1-6]>([^<]+)(?:Clinical|Registered|General)?\s*Psychologist</h[1-6]>'
        ]
        
        # Try to find psychologists using patterns
        for pattern in title_patterns:
            matches = re.findall(pattern, all_content)
            for match in matches:
                name = match.strip()
                # Check if this looks like a valid name (at least two words)
                if ' ' in name and len(name.split()) >= 2:
                    # Try to determine if they're a clinical or general psychologist
                    psych_type = "Unknown"
                    if "Clinical Psychologist" in all_content or "clinical psychologist" in all_content.lower():
                        psych_type = "C"  # Clinical Psychologist
                    elif "General Psychologist" in all_content or "general psychologist" in all_content.lower():
                        psych_type = "G"  # General Psychologist
                    
                    extracted["psychologists"].append({
                        "name": name,
                        "type": psych_type
                    })
        
        # Remove duplicates by name
        seen_names = set()
        unique_psychologists = []
        
        for psych in extracted["psychologists"]:
            if psych["name"] not in seen_names:
                seen_names.add(psych["name"])
                unique_psychologists.append(psych)
                
        extracted["psychologists"] = unique_psychologists
    
    def _extract_pricing(self, scraped_data, extracted):
        """Extract pricing information from scraped data."""
        # Combine all text content for analysis
        all_content = scraped_data["main_page_content"]
        
        for content in scraped_data["doctor_pages_content"].values():
            all_content += "\n" + content
            
        for content in scraped_data["other_pages_content"].values():
            all_content += "\n" + content
        
        # Look for common pricing patterns
        initial_consult_patterns = [
            r'Initial\s+(?:Consultation|Consult|Appointment|Session)(?:[:\s]+)?\$?(\d+)',
            r'First\s+(?:Consultation|Consult|Appointment|Session)(?:[:\s]+)?\$?(\d+)',
            r'New\s+Patient(?:[:\s]+)?\$?(\d+)'
        ]
        
        followup_consult_patterns = [
            r'(?:Followup|Follow-up|Follow\s+up|Subsequent|Regular)\s+(?:Consultation|Consult|Appointment|Session)(?:[:\s]+)?\$?(\d+)',
            r'Return\s+(?:Visit|Appointment|Consultation)(?:[:\s]+)?\$?(\d+)'
        ]
        
        # Try to find pricing information
        for pattern in initial_consult_patterns:
            matches = re.findall(pattern, all_content, re.IGNORECASE)
            if matches:
                extracted["pricing_info"]["initial_consult"] = matches[0]
                break
                
        for pattern in followup_consult_patterns:
            matches = re.findall(pattern, all_content, re.IGNORECASE)
            if matches:
                extracted["pricing_info"]["followup_consult"] = matches[0]
                break
                
        return extracted