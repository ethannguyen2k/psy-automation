# Psychology Researcher Automation

This project automates the process of researching psychology clinics in Australia and possibly other countries around the world using basic web scraper and Gemini API. It extracts information from clinic websites, including:

- Email addresses
- Doctor page URLs
- Lists of psychologists with their types (Clinical or General)
- Pricing information for consultations

## Pipeline Stages

The automation is divided into 5 stages:

1. **Excel Parsing and Initial Validation** - Processes the input Excel file, identifies green rows, and validates address and contact information
2. **Website Scraping and Content Extraction** - Scrapes clinic websites to extract text content while preserving structure
3. **LLM-based Information Extraction** - Uses Google's Gemini API to extract specific information from the scraped text
4. **Validation and Structural Formatting** - Validates and formats the extracted data
5. **Excel Output Generation** - Generates the final Excel output and invoice

## Setup

### Prerequisites

- Python 3.9 or higher
- Google Gemini API key

### Installation

1. Clone the repository:
   ```
   git clone https://github.com/ethannguyen2k/psy-automation.git
   cd psy-automation
   ```

2. Install the required dependencies:
   ```
   pip install -r requirements.txt
   ```

3. Set your Gemini API key:
   ```
   export GEMINI_API_KEY="your-api-key"
   set GEMINI_API_KEY=your-api-key
   $env:GEMINI_API_KEY="your-api-key"
   ```

## Usage

### Running the Full Pipeline

To run the complete pipeline:

```
python main_pipeline.py path/to/your/input.xlsx
```

Additional options:
```
python main_pipeline.py path/to/your/input.xlsx --output-dir output --scraped-data-dir scraped_data --batch-size 10 --max-workers 4
```

### Running Individual Stages for Testing

Each stage can be tested individually:

```
python test_stage1.py
python test_stage2.py
python test_stage3.py
python test_stage4.py
python test_stage5.py
```

## Output

The pipeline generates the following outputs:

1. **Processed Excel file** - Contains all the extracted information for each clinic
2. **Invoice file** - Contains the invoice details for submission
3. **Scraped data** - Text files containing the scraped content from clinic websites
4. **Extraction results** - JSON file with the structured information extracted by Gemini

## Configuration

You can adjust the following parameters:

- `batch_size` - Number of websites to process in each batch (default: 10)
- `max_workers` - Maximum number of concurrent workers for web scraping (default: 4)
- `output_dir` - Directory to save output files (default: "output")
- `scraped_data_dir` - Directory to save scraped website data (default: "scraped_data")

## Rate Limiting

The pipeline implements rate limiting to respect website servers and API limits:

- For website scraping: 3-5 second delay between batches
- For Gemini API: 4 second minimum interval between requests

## Troubleshooting

### Common Issues

1. **Missing API Key**: Ensure the `GEMINI_API_KEY` environment variable is set or pass it using the `--api-key` option
2. **Website Access Issues**: Some websites may block scraping. Check the logs for details.
3. **Gemini API Errors**: Check your API key and quota limits

### Logs

The pipeline generates detailed logs in the file `pipeline_YYYYMMDD_HHMMSS.log`. Check this file for troubleshooting.

## License

[MIT License](LICENSE)