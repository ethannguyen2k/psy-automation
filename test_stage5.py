import pandas as pd
import os
from openpyxl import Workbook
from openpyxl.styles import PatternFill
from stage5_excel_output import ExcelOutputGenerator

def create_sample_data():
    """Create a sample DataFrame with Wisemind Psychology data."""
    data = {
        "Practice": [
            "Wisemind Psychology",
            "Wisemind Psychology",
            "Wisemind Psychology"
        ],
        "Address": [
            "40 Minchinton St, Caloundra QLD 4551",
            "40 Minchinton St, Caloundra QLD 4551",
            "40 Minchinton St, Caloundra QLD 4551"
        ],
        "Website": [
            "http://www.wisemind.com.au",
            "http://www.wisemind.com.au",
            "http://www.wisemind.com.au"
        ],
        "Phone": [
            "0490193347",
            "0490193347",
            "0490193347"
        ],
        "Name": [
            "Melissa Madden",
            "Danielle Comerford",
            "Rachel Hannam"
        ],
        "Email": [
            "admin@wisemind.com.au",
            "admin@wisemind.com.au",
            "admin@wisemind.com.au"
        ],
        "Doctors": [
            "http://www.wisemind.com.au/our-team/",
            "http://www.wisemind.com.au/our-team/",
            "http://www.wisemind.com.au/our-team/"
        ],
        "Type": [
            "C",
            "G",
            "G"
        ],
        "Initial Consult": [
            "220",
            "220",
            "220"
        ],
        "Follow-up Consult": [
            "180",
            "180",
            "180"
        ],
        "Date": [
            "2025-02-27",
            "2025-02-27",
            "2025-02-27"
        ],
        "Notes": [
            "",
            "",
            ""
        ]
    }
    
    return pd.DataFrame(data)

def test_excel_generator():
    """Test the Excel Output Generator."""
    print("\n" + "="*50)
    print("TESTING EXCEL OUTPUT GENERATION")
    print("="*50)
    
    # Create output directory
    output_dir = "test_output"
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    # Create sample data
    df = create_sample_data()
    print(f"\nCreated sample DataFrame with {len(df)} rows")
    
    # Create a standardized output file path
    output_file = os.path.join(output_dir, "wisemind_psychology_formatted.xlsx")
    
    # Initialize the Excel generator
    generator = ExcelOutputGenerator(output_file)
    
    # Generate the Excel file with green_rows information
    print(f"\nGenerating Excel file: {output_file}")
    green_rows = [0]  # In this case, only the first row was originally green
    generator.generate_excel(df, green_rows=green_rows)
    
    print(f"\nExcel output test completed. Check {output_dir} for the generated files.")

def test_with_wisemind_full_dataset():
    """Test the Excel Output Generator with a more complete dataset."""
    print("\n" + "="*50)
    print("TESTING EXCEL OUTPUT WITH COMPLETE DATASET")
    print("="*50)
    
    # Create a more comprehensive dataset including different cases
    data = {
        "Practice": [
            "Wisemind Psychology",
            "Wisemind Psychology", 
            "Wisemind Psychology",
            "Coastal Psychology", 
            "Brisbane Mind Centre"
        ],
        "Address": [
            "40 Minchinton St, Caloundra QLD 4551",
            "40 Minchinton St, Caloundra QLD 4551",
            "40 Minchinton St, Caloundra QLD 4551",
            "123 Beach Rd, Maroochydore QLD 4558",
            "456 Main St, Brisbane QLD 4000"
        ],
        "Website": [
            "http://www.wisemind.com.au",
            "http://www.wisemind.com.au",
            "http://www.wisemind.com.au",
            "http://www.coastalpsych.com.au",
            "http://www.brisbanemind.com.au"
        ],
        "Phone": [
            "0490193347",
            "0490193347",
            "0490193347",
            "0754443333",
            "0730002000"
        ],
        "Name": [
            "Melissa Madden",
            "Danielle Comerford",
            "Rachel Hannam",
            "John Smith",
            "Sarah Johnson"
        ],
        "Email": [
            "admin@wisemind.com.au",
            "admin@wisemind.com.au",
            "admin@wisemind.com.au",
            "info@coastalpsych.com.au",
            "contact@brisbanemind.com.au"
        ],
        "Doctors": [
            "http://www.wisemind.com.au/our-team/",
            "http://www.wisemind.com.au/our-team/",
            "http://www.wisemind.com.au/our-team/",
            "http://www.coastalpsych.com.au/team",
            "http://www.brisbanemind.com.au/psychologists"
        ],
        "Type": [
            "C",
            "G",
            "G",
            "C",
            "C"
        ],
        "Initial Consult": [
            "220",
            "220",
            "220",
            "250",
            "280"
        ],
        "Follow-up Consult": [
            "180",
            "180",
            "180",
            "200",
            "240"
        ],
        "Date": [
            "2025-02-27",
            "2025-02-27",
            "2025-02-27",
            "2025-02-27",
            "2025-02-27"
        ],
        "Notes": [
            "",
            "",
            "",
            "Discrepancy found in address format",
            ""
        ]
    }
    
    df = pd.DataFrame(data)
    print(f"\nCreated comprehensive dataset with {len(df)} rows")
    
    # Create output directory
    output_dir = "test_output"
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    # Create a standardized output file path
    output_file = os.path.join(output_dir, "comprehensive_formatted.xlsx")
    
    # Initialize the Excel generator
    generator = ExcelOutputGenerator(output_file)
    
    # Generate the Excel file
    print(f"\nGenerating comprehensive Excel file: {output_file}")
    generator.generate_excel(df)
    
    print(f"\nComprehensive test completed. Check {output_dir} for the generated files.")

if __name__ == "__main__":
    test_excel_generator()
    print("\n" + "="*70 + "\n")
    test_with_wisemind_full_dataset()