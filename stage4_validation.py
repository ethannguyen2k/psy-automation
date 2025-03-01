import pandas as pd
import re
import logging
import datetime
from typing import Dict, List, Any, Tuple

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("log/validation.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class DataValidator:
    def __init__(self):
        """Initialize the data validator."""
        # Validation patterns
        self.address_pattern1 = r"^\d+\s+[\w\s]+,\s+[\w\s]+\s+[A-Z]{2,3}\s+\d{4,5}$"
        self.address_pattern2 = r"^Cnr\s+[\w\s]+\s+&\s+[\w\s]+,\s+[\w\s]+\s+[A-Z]{2,3}\s+\d{4,5}$"
        self.email_pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
        self.url_pattern = r"^(http|https)://[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}(/.*)?$"
        self.phone_pattern = r"^(?:(?:0[2-478])|(?:04\d{2}))\d{6,8}$"
        
        # Australian state abbreviations
        self.au_states = ['NSW', 'VIC', 'QLD', 'SA', 'WA', 'TAS', 'NT', 'ACT']
        
    def validate_address(self, address: str) -> Tuple[bool, str]:
        """
        Validate and clean an address.
        
        Args:
            address (str): Address to validate
            
        Returns:
            tuple: (is_valid, cleaned_address)
        """
        if not address or not isinstance(address, str):
            return False, ""
            
        address = address.strip()

        # More comprehensive unit pattern that can handle full addresses
        # This pattern looks for unit/building patterns at the beginning of the address
        unit_pattern = r'^((?:Unit\s+)?[\dA-Za-z]+[\/\\])(\d+(?:[A-Za-z])?)\s+(.+)$'
        unit_match = re.match(unit_pattern, address)
        
        if unit_match:
            # Extract the main address without the unit number
            building_number = unit_match.group(2)  # Building number
            rest_of_address = unit_match.group(3)  # Street name and everything else
            
            # Rebuild the address without the unit number
            address = f"{building_number} {rest_of_address}"
            logger.info(f"Reformatted unit address to: {address}")
        
        # Check if it matches any of the valid patterns
        if (re.match(self.address_pattern1, address) or 
            re.match(self.address_pattern2, address)):
            return True, address
            
        # Try to clean/fix the address
        # Extract potential postcode (4 digits)
        postcode_match = re.search(r'\b\d{4}\b', address)
        
        # Extract potential state code
        state_match = None
        for state in self.au_states:
            if f" {state} " in f" {address} ":
                state_match = state
                break
                
        if not postcode_match or not state_match:
            return False, address
            
        # If we have both state and postcode, try to restructure the address
        try:
            # Split the address at the state
            parts = re.split(f"\\s+{state_match}\\s+", address)
            if len(parts) != 2:
                return False, address
                
            street_part = parts[0].strip()
            
            # Clean up the street part if needed
            if ',' not in street_part:
                # Try to extract the suburb before the state
                street_suburb_parts = street_part.rsplit(' ', 1)
                if len(street_suburb_parts) == 2:
                    street = street_suburb_parts[0].strip()
                    suburb = street_suburb_parts[1].strip()
                    street_part = f"{street}, {suburb}"
            
            # Construct a properly formatted address
            formatted_address = f"{street_part}, {state_match} {postcode_match.group(0)}"
            
            # Verify it matches a pattern now
            if (re.match(self.address_pattern1, formatted_address) or 
                re.match(self.address_pattern2, formatted_address)):
                return True, formatted_address
                
        except Exception as e:
            logger.warning(f"Error cleaning address '{address}': {str(e)}")
            
        return False, address
    
    def validate_email(self, email: str) -> Tuple[bool, str]:
        """
        Validate and clean an email address.
        
        Args:
            email (str): Email to validate
            
        Returns:
            tuple: (is_valid, cleaned_email)
        """
        if not email or not isinstance(email, str):
            return False, ""
            
        email = email.strip().lower()
        
        if re.match(self.email_pattern, email):
            return True, email
            
        return False, email
    
    def validate_url(self, url: str) -> Tuple[bool, str]:
        """
        Validate and clean a URL.
        
        Args:
            url (str): URL to validate
            
        Returns:
            tuple: (is_valid, cleaned_url)
        """
        if not url or not isinstance(url, str):
            return False, ""
            
        url = url.strip()
        
        # Add http:// prefix if missing
        if not url.startswith(('http://', 'https://')):
            url = 'http://' + url
            
        if re.match(self.url_pattern, url):
            return True, url
            
        return False, url
    
    def validate_phone(self, phone: str) -> Tuple[bool, str]:
        """
        Validate, clean a phone number, and format it correctly.
        
        Args:
            phone (str): Phone number to validate
            
        Returns:
            tuple: (is_valid, cleaned_phone)
        """
        if not phone or not isinstance(phone, str):
            return False, ""
            
        # Extract only digits
        digits_only = ''.join(filter(str.isdigit, str(phone)))
        # Ensure we keep the leading zero if present
        if len(digits_only) == 9 and digits_only[0] == '4':
            digits_only = '0' + digits_only
        
        # Australian numbers should be 8-10 digits (or 12 with country code)
        # Check if we have enough digits for a valid phone number
        if len(digits_only) >= 8 and len(digits_only) <= 12:
            # Format mobile number (10 digits starting with 04)
            if len(digits_only) == 10 and digits_only.startswith('04'):
                formatted = f"0{digits_only[1:4]} {digits_only[4:7]} {digits_only[7:10]}"
                return True, formatted
                
            # Format landline (with area code)
            elif len(digits_only) == 10 and (digits_only.startswith('02') or 
                                        digits_only.startswith('03') or 
                                        digits_only.startswith('07') or 
                                        digits_only.startswith('08')):
                formatted = f"({digits_only[0:2]}) {digits_only[2:6]} {digits_only[6:10]}"
                return True, formatted
            
            elif len(digits_only) == 10 and digits_only.startswith('1300') or digits_only.startswith('1800'):
                formatted = f"{digits_only[0:4]} {digits_only[4:7]} {digits_only[7:10]}"
                return True, formatted
                
            # Other numbers just group in blocks of 3-4 digits
            else:
                # Group in blocks of 3 or 4 digits
                if len(digits_only) == 8:
                    formatted = f"{digits_only[0:4]} {digits_only[4:8]}"
                elif len(digits_only) == 9:
                    formatted = f"{digits_only[0:3]} {digits_only[3:6]} {digits_only[6:9]}"
                else:
                    # Keep as is for other lengths
                    formatted = digits_only
                    
                return True, formatted
            
        return False, phone
    
    def validate_psychologist_type(self, psych_type: str) -> Tuple[bool, str]:
        """
        Validate and clean a psychologist type.
        
        Args:
            psych_type (str): Psychologist type to validate
            
        Returns:
            tuple: (is_valid, cleaned_type)
        """
        if not psych_type or not isinstance(psych_type, str):
            return False, ""
            
        psych_type = psych_type.strip().upper()
        
        # Should be 'C' or 'G'
        if psych_type in ['C', 'G']:
            return True, psych_type
            
        # Try to determine from longer strings
        if psych_type.startswith('C') or 'CLINICAL' in psych_type:
            return True, 'C'
            
        if psych_type.startswith('G') or 'GENERAL' in psych_type:
            return True, 'G'
            
        return False, ""
    
    def validate_price(self, price: str) -> Tuple[bool, str]:
        """
        Validate and clean a price.
        
        Args:
            price (str): Price to validate
            
        Returns:
            tuple: (is_valid, cleaned_price)
        """
        if not price or not isinstance(price, str):
            return False, ""
            
        # Extract digits and possibly decimal point
        price_match = re.search(r'\$?(\d+(?:\.\d{2})?)', price)
        if price_match:
            return True, price_match.group(1)
            
        return False, price

class DataFormatter:
    def __init__(self, validator=None):
        """
        Initialize the data formatter.
        
        Args:
            validator: DataValidator instance
        """
        self.validator = validator or DataValidator()
        
    def flag_discrepancies(self, existing_data, new_data, field):
        """
        Flag discrepancies between existing and new data.
        
        Args:
            existing_data: Existing data
            new_data: New data
            field: Field name
            
        Returns:
            tuple: (has_discrepancy, message)
        """
        if field not in existing_data or field not in new_data:
            return False, ""
            
        existing_value = existing_data[field]
        new_value = new_data[field]
        
        if not existing_value or not new_value:
            return False, ""
            
        if str(existing_value).strip() != str(new_value).strip():
            return True, f"Discrepancy in {field}: '{existing_value}' vs '{new_value}'"
            
        return False, ""
    
    def format_data_for_excel(self, df, extracted_data):
        """
        Format extracted data for Excel output.
        
        Args:
            df (pandas.DataFrame): Original DataFrame
            extracted_data (dict): Extracted data
            
        Returns:
            tuple: (updated_df, new_rows, discrepancies)
        """
        logger.info(f"DataFrame practices: {list(df['Practice'])}")
        logger.info(f"Extracted data keys: {list(extracted_data.keys())}")
        updated_df = df.copy()
        new_rows = []
        discrepancies = []
        
        # Ensure required columns exist
        required_columns = ['Name', 'Email', 'Doctors', 'Type', 'Initial Consult', 'Follow-up Consult', 'Date', 'Notes']
        for col in required_columns:
            if col not in updated_df.columns:
                updated_df[col] = ""
        
        # Format all phone numbers in the DataFrame first
        if 'Phone' in updated_df.columns:
            for idx, phone in enumerate(updated_df['Phone']):
                if pd.notna(phone) and phone:
                    valid, clean_phone = self.validator.validate_phone(str(phone))
                    if valid:
                        updated_df.at[idx, 'Phone'] = clean_phone
        
        # Process each practice
        for idx, row in updated_df.iterrows():
            practice_name = row.get('Practice')
            if not practice_name or practice_name not in extracted_data:
                continue
                
            practice_data = extracted_data[practice_name]

            # Type check
            if isinstance(practice_data, list):
                # Handle case where practice_data is a list
                if len(practice_data) > 0:
                    practice_data = practice_data[0]  # Use first item in list
                else:
                    practice_data = {"error": "Empty list for practice data"}
            
            # Check for extraction errors
            if "error" in practice_data:
                updated_df.at[idx, 'Notes'] = f"Extraction error: {practice_data['error']}"
                continue
                
            # Email
            if practice_data.get('email'):
                valid, clean_email = self.validator.validate_email(practice_data['email'])
                if valid:
                    # Check for discrepancy with existing data
                    has_discrepancy, message = self.flag_discrepancies(
                        row, {'Email': clean_email}, 'Email')
                    if has_discrepancy:
                        discrepancies.append((idx, message))
                        
                    updated_df.at[idx, 'Email'] = clean_email
                    
            # Doctor page URL
            if practice_data.get('doctor_page_url'):
                valid, clean_url = self.validator.validate_url(practice_data['doctor_page_url'])
                if valid:
                    # Check for discrepancy with existing data
                    has_discrepancy, message = self.flag_discrepancies(
                        row, {'Doctors': clean_url}, 'Doctors')
                    if has_discrepancy:
                        discrepancies.append((idx, message))
                        
                    updated_df.at[idx, 'Doctors'] = clean_url
                    
            # Pricing information
            pricing_info = practice_data.get('pricing_info', {})
            
            if pricing_info.get('initial_consult'):
                valid, clean_price = self.validator.validate_price(pricing_info['initial_consult'])
                if valid:
                    # Check for discrepancy with existing data
                    has_discrepancy, message = self.flag_discrepancies(
                        row, {'Initial Consult': clean_price}, 'Initial Consult')
                    if has_discrepancy:
                        discrepancies.append((idx, message))
                        
                    updated_df.at[idx, 'Initial Consult'] = clean_price
                    
            if pricing_info.get('followup_consult'):
                valid, clean_price = self.validator.validate_price(pricing_info['followup_consult'])
                if valid:
                    # Check for discrepancy with existing data
                    has_discrepancy, message = self.flag_discrepancies(
                        row, {'Follow-up Consult': clean_price}, 'Follow-up Consult')
                    if has_discrepancy:
                        discrepancies.append((idx, message))
                        
                    updated_df.at[idx, 'Follow-up Consult'] = clean_price
            
            # Set today's date
            today = datetime.datetime.now().strftime('%Y-%m-%d')
            updated_df.at[idx, 'Date'] = today
            
            # Process psychologists
            psychologists = practice_data.get('psychologists', [])
            
            if not psychologists:
                updated_df.at[idx, 'Notes'] = "No psychologists found"
                continue
                
            # Update the first psychologist in the current row
            if psychologists:
                first_psych = psychologists[0]
                
                # Name
                name = first_psych.get('name', '')
                if name:
                    # Check for discrepancy with existing data
                    has_discrepancy, message = self.flag_discrepancies(
                        row, {'Name': name}, 'Name')
                    if has_discrepancy:
                        discrepancies.append((idx, message))
                        
                    updated_df.at[idx, 'Name'] = name
                    
                # Type
                psych_type = first_psych.get('type', '')
                if psych_type:
                    valid, clean_type = self.validator.validate_psychologist_type(psych_type)
                    if valid:
                        # Check for discrepancy with existing data
                        has_discrepancy, message = self.flag_discrepancies(
                            row, {'Type': clean_type}, 'Type')
                        if has_discrepancy:
                            discrepancies.append((idx, message))
                            
                        updated_df.at[idx, 'Type'] = clean_type
                
                # Create new rows for additional psychologists
                for psych in psychologists[1:]:
                    new_row = row.copy()
                    
                    name = psych.get('name', '')
                    if name:
                        new_row['Name'] = name
                        
                    psych_type = psych.get('type', '')
                    if psych_type:
                        valid, clean_type = self.validator.validate_psychologist_type(psych_type)
                        if valid:
                            new_row['Type'] = clean_type
                    
                    # Ensure doctor page URL is copied to all rows
                    if practice_data.get('doctor_page_url'):
                        valid, clean_url = self.validator.validate_url(practice_data['doctor_page_url'])
                        if valid:
                            new_row['Doctors'] = clean_url
                    
                    # Ensure email is copied to all rows
                    if practice_data.get('email'):
                        valid, clean_email = self.validator.validate_email(practice_data['email'])
                        if valid:
                            new_row['Email'] = clean_email
                            
                    new_row['Date'] = today
                    new_rows.append(new_row)
        
        return updated_df, new_rows, discrepancies

# Example usage
if __name__ == "__main__":
    validator = DataValidator()
    formatter = DataFormatter(validator)
    
    # Example validations
    print("Example validations:")
    
    # Address
    address = "123 Main St, Sydney NSW 2000"
    valid, clean = validator.validate_address(address)
    print(f"Address '{address}' is {'valid' if valid else 'invalid'}: {clean}")
    
    # Email
    email = "info@example.com.au"
    valid, clean = validator.validate_email(email)
    print(f"Email '{email}' is {'valid' if valid else 'invalid'}: {clean}")
    
    # URL
    url = "www.example.com.au"
    valid, clean = validator.validate_url(url)
    print(f"URL '{url}' is {'valid' if valid else 'invalid'}: {clean}")
    
    # Phone
    phone = "(02) 9876 5432"
    valid, clean = validator.validate_phone(phone)
    print(f"Phone '{phone}' is {'valid' if valid else 'invalid'}: {clean}")
    
    # Psychologist type
    psych_type = "Clinical Psychologist"
    valid, clean = validator.validate_psychologist_type(psych_type)
    print(f"Type '{psych_type}' is {'valid' if valid else 'invalid'}: {clean}")
    
    # Price
    price = "$240.00"
    valid, clean = validator.validate_price(price)
    print(f"Price '{price}' is {'valid' if valid else 'invalid'}: {clean}")