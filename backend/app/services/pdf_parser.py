"""
PDF Parser Service for extracting medical test data from PDF reports.

This service uses PyMuPDF (fitz) to extract text from PDF files and parse
structured medical test results including test names, values, ranges, and units.
"""

import re
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime
import logging
from io import BytesIO

# Try to import PyMuPDF, handle gracefully if not available
try:
    import fitz  # PyMuPDF
    PYMUPDF_AVAILABLE = True
except ImportError:
    PYMUPDF_AVAILABLE = False
    fitz = None

from ..models.report import MetricData

logger = logging.getLogger(__name__)


class PDFParsingError(Exception):
    """Custom exception for PDF parsing errors."""
    pass


class PDFParserService:
    """Service for parsing medical test reports from PDF files."""
    
    def __init__(self):
        # Common patterns for medical test data extraction
        self.test_patterns = [
            # Pattern for "TEST NAME    VALUE    RANGE    UNIT"
            r'([A-Z][A-Z\s,\-\.]+?)\s+([0-9]+\.?[0-9]*)\s+([0-9\.\-\s]+)\s+([a-zA-Z\/\%]+)',
            # Pattern for "TEST NAME: VALUE UNIT (RANGE)"
            r'([A-Z][A-Z\s,\-\.]+?):\s*([0-9]+\.?[0-9]*)\s*([a-zA-Z\/\%]*)\s*\(([0-9\.\-\s]+)\)',
            # Pattern for tabular data with multiple columns
            r'([A-Z][A-Z\s,\-\.]+?)\s+([0-9]+\.?[0-9]*)\s+([a-zA-Z\/\%]*)\s+([0-9\.\-\s]+)\s*(NORMAL|HIGH|LOW|CRITICAL)?',
        ]
        
        # Common medical test name variations
        self.test_name_mappings = {
            'BILIRUBIN TOTAL': 'BILIRUBIN, TOTAL',
            'BILIRUBIN DIRECT': 'BILIRUBIN, DIRECT',
            'CHOLESTEROL TOTAL': 'CHOLESTEROL, TOTAL',
            'GLUCOSE FASTING': 'GLUCOSE, FASTING',
            'HEMOGLOBIN': 'HEMOGLOBIN',
            'WBC COUNT': 'WHITE BLOOD CELL COUNT',
            'RBC COUNT': 'RED BLOOD CELL COUNT',
            'PLATELET COUNT': 'PLATELET COUNT',
        }
        
        # Verdict determination based on ranges
        self.verdict_keywords = {
            'HIGH': ['HIGH', 'ELEVATED', 'ABOVE', 'INCREASED'],
            'LOW': ['LOW', 'BELOW', 'DECREASED', 'REDUCED'],
            'CRITICAL': ['CRITICAL', 'URGENT', 'SEVERE'],
            'NORMAL': ['NORMAL', 'WITHIN', 'OK', 'GOOD']
        }

    async def extract_text_from_pdf(self, pdf_content: bytes) -> str:
        """
        Extract raw text from PDF content.
        
        Args:
            pdf_content: PDF file content as bytes
            
        Returns:
            Extracted text as string
            
        Raises:
            PDFParsingError: If PDF cannot be opened or read
        """
        if not PYMUPDF_AVAILABLE:
            raise PDFParsingError("PyMuPDF is not available. Please install PyMuPDF to use PDF parsing functionality.")
        
        try:
            # Open PDF from bytes
            pdf_stream = BytesIO(pdf_content)
            doc = fitz.open(stream=pdf_stream, filetype="pdf")
            
            if doc.page_count == 0:
                raise PDFParsingError("PDF contains no pages")
            
            # Extract text from all pages
            full_text = ""
            for page_num in range(doc.page_count):
                page = doc[page_num]
                text = page.get_text()
                full_text += text + "\n"
            
            doc.close()
            
            if not full_text.strip():
                raise PDFParsingError("No text could be extracted from PDF")
                
            return full_text
            
        except fitz.FileDataError as e:
            raise PDFParsingError(f"Invalid PDF file: {str(e)}")
        except Exception as e:
            raise PDFParsingError(f"Error extracting text from PDF: {str(e)}")

    def _normalize_test_name(self, raw_name: str) -> str:
        """
        Normalize test name to standard format.
        
        Args:
            raw_name: Raw test name from PDF
            
        Returns:
            Normalized test name
        """
        # Clean up the name
        name = raw_name.strip().upper()
        name = re.sub(r'\s+', ' ', name)  # Replace multiple spaces with single space
        name = name.rstrip(',.:')  # Remove trailing punctuation
        
        # Apply mappings if available
        return self.test_name_mappings.get(name, name)

    def _determine_verdict(self, value: str, range_str: str, remark: str = "") -> str:
        """
        Determine verdict (NORMAL/HIGH/LOW/CRITICAL) based on value, range, and remarks.
        
        Args:
            value: Test value
            range_str: Reference range
            remark: Additional remarks
            
        Returns:
            Verdict string
        """
        # Check remarks for explicit verdict keywords
        remark_upper = remark.upper()
        for verdict, keywords in self.verdict_keywords.items():
            if any(keyword in remark_upper for keyword in keywords):
                return verdict
        
        # Try to parse numeric comparison
        try:
            numeric_value = float(value)
            
            # Parse range like "0.2-1.0" or "< 5.0" or "> 10"
            if '-' in range_str:
                range_parts = range_str.split('-')
                if len(range_parts) == 2:
                    try:
                        min_val = float(range_parts[0].strip())
                        max_val = float(range_parts[1].strip())
                        
                        if numeric_value < min_val:
                            return "LOW"
                        elif numeric_value > max_val:
                            return "HIGH"
                        else:
                            return "NORMAL"
                    except ValueError:
                        pass
            
            # Handle single-bound ranges
            if range_str.startswith('<'):
                try:
                    max_val = float(range_str[1:].strip())
                    return "HIGH" if numeric_value >= max_val else "NORMAL"
                except ValueError:
                    pass
            
            if range_str.startswith('>'):
                try:
                    min_val = float(range_str[1:].strip())
                    return "LOW" if numeric_value <= min_val else "NORMAL"
                except ValueError:
                    pass
                    
        except ValueError:
            pass
        
        # Default to NORMAL if we can't determine
        return "NORMAL"

    def _extract_test_data_from_text(self, text: str) -> Dict[str, MetricData]:
        """
        Extract structured test data from raw text using regex patterns.
        
        Args:
            text: Raw text extracted from PDF
            
        Returns:
            Dictionary mapping test names to MetricData objects
        """
        extracted_data = {}
        
        # Try each pattern
        for pattern in self.test_patterns:
            matches = re.finditer(pattern, text, re.MULTILINE | re.IGNORECASE)
            
            for match in matches:
                groups = match.groups()
                
                if len(groups) >= 4:
                    raw_name = groups[0].strip()
                    value = groups[1].strip()
                    
                    # Handle different group arrangements based on pattern
                    if len(groups) == 4:
                        # Pattern: name, value, range, unit
                        range_str = groups[2].strip()
                        unit = groups[3].strip()
                        remark = ""
                    elif len(groups) == 5:
                        # Pattern: name, value, unit, range, verdict
                        unit = groups[2].strip()
                        range_str = groups[3].strip()
                        remark = groups[4].strip() if groups[4] else ""
                    else:
                        continue
                    
                    # Normalize test name
                    test_name = self._normalize_test_name(raw_name)
                    
                    # Skip if test name is too short or generic
                    if len(test_name) < 3 or test_name in ['TEST', 'NAME', 'VALUE']:
                        continue
                    
                    # Determine verdict
                    verdict = self._determine_verdict(value, range_str, remark)
                    
                    # Create MetricData object
                    metric_data = MetricData(
                        name=test_name,
                        value=value,
                        remark=remark,
                        range=range_str,
                        unit=unit,
                        verdict=verdict
                    )
                    
                    # Use a key that's safe for MongoDB
                    key = re.sub(r'[^\w]', '_', test_name)
                    extracted_data[key] = metric_data
        
        return extracted_data

    async def parse_medical_report(self, pdf_content: bytes) -> Dict[str, MetricData]:
        """
        Parse a medical test report PDF and extract structured test data.
        
        Args:
            pdf_content: PDF file content as bytes
            
        Returns:
            Dictionary mapping test names to MetricData objects
            
        Raises:
            PDFParsingError: If parsing fails
        """
        try:
            # Extract text from PDF
            text = await self.extract_text_from_pdf(pdf_content)
            
            # Extract structured test data
            test_data = self._extract_test_data_from_text(text)
            
            if not test_data:
                raise PDFParsingError("No medical test data could be extracted from PDF")
            
            logger.info(f"Successfully extracted {len(test_data)} test results from PDF")
            return test_data
            
        except PDFParsingError:
            raise
        except Exception as e:
            raise PDFParsingError(f"Unexpected error during PDF parsing: {str(e)}")

    def validate_pdf_content(self, pdf_content: bytes) -> bool:
        """
        Validate that the content is a valid PDF file.
        
        Args:
            pdf_content: PDF file content as bytes
            
        Returns:
            True if valid PDF, False otherwise
        """
        if not PYMUPDF_AVAILABLE:
            # Basic validation without PyMuPDF - check for PDF header
            return pdf_content.startswith(b'%PDF-')
        
        try:
            pdf_stream = BytesIO(pdf_content)
            doc = fitz.open(stream=pdf_stream, filetype="pdf")
            is_valid = doc.page_count > 0
            doc.close()
            return is_valid
        except:
            return False


# Global instance
pdf_parser_service = PDFParserService()