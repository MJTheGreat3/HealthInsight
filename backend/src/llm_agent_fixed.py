    def extract_csv_from_text(self, text: str) -> Optional[list]:
        """
        Extract structured CSV data from OCR text using LLM
        """
        try:
            import csv
            import io
            
            prompt = f"""
Extract medical test results from the following OCR text and return as CSV data.

The text contains medical test results with columns for test name, value, unit, and reference range.

Requirements:
- Extract ONLY actual test results with numerical values
- Ignore headers, footers, and non-test data
- Return CSV format with exactly these columns: test_name,value,unit,range
- Values should include numbers (e.g., "110", "12.5", "82")
- Units should be standardized (e.g., "mg/dL", "g/dL", "fL", "mmol/L")
- Reference ranges should preserve the format shown in text
- Return ONLY the CSV data, no explanations or additional text

OCR Text:
{text}

CSV Output:
"""
            
            # Use synchronous call since this is a utility method
            response = self.model.generate_content(prompt)
            csv_text = response.text if hasattr(response, 'text') else str(response)
            
            # Parse CSV response
            if not csv_text.strip():
                return None
            
            # Strip code block formatting if present
            clean_text = csv_text.strip()
            if clean_text.startswith('```'):
                clean_text = clean_text[3:]
            if clean_text.endswith('```'):
                clean_text = clean_text[:-3]
            clean_text = clean_text.strip()
            if clean_text.startswith('csv'):
                clean_text = clean_text[3:].strip()
                
            # Use StringIO to parse CSV
            csv_file = io.StringIO(clean_text.strip())
            csv_reader = csv.reader(csv_file)
            
            # Skip header if present
            first_row = next(csv_reader, None)
            if first_row and len(first_row) >= 4:
                if first_row[0].lower() in ['test_name', 'test', 'name']:
                    # Header detected, skip it
                    data_rows = list(csv_reader)
                else:
                    # This is data, include it
                    data_rows = [first_row] + list(csv_reader)
            else:
                data_rows = []
            
            # Filter and validate data
            structured_data = []
            for row in data_rows:
                if len(row) >= 4:
                    test_name = str(row[0]).strip()
                    value = str(row[1]).strip()
                    unit = str(row[2]).strip()
                    range_val = str(row[3]).strip()
                    
                    # Validate that we have a test name and value
                    if test_name and value and any(char.isdigit() for char in value):
                        structured_data.append([test_name, value, unit, range_val])
            
            return structured_data if structured_data else None
            
        except Exception as e:
            print(f"Error extracting CSV from text: {e}")
            return None