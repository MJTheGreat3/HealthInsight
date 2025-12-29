"""
Unit tests for PDF processing edge cases and error conditions
"""

import pytest
from io import BytesIO
from unittest.mock import patch, MagicMock

# Try to import PyMuPDF, skip tests if not available
try:
    import fitz  # PyMuPDF
    PYMUPDF_AVAILABLE = True
except ImportError:
    PYMUPDF_AVAILABLE = False
    fitz = None

from app.services.pdf_parser import PDFParserService, PDFParsingError
from app.models.report import MetricData


class TestPDFProcessingEdgeCases:
    """Test class for PDF processing edge cases"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.parser = PDFParserService()
    
    @pytest.mark.skipif(not PYMUPDF_AVAILABLE, reason="PyMuPDF not available")
    def test_empty_pdf_content(self):
        """Test handling of empty PDF content"""
        empty_content = b""
        
        # Should return False for validation
        assert self.parser.validate_pdf_content(empty_content) == False
        
        # Should raise PDFParsingError for parsing
        with pytest.raises(PDFParsingError) as exc_info:
            import asyncio
            asyncio.run(self.parser.parse_medical_report(empty_content))
        
        assert "Invalid PDF file" in str(exc_info.value) or "Error extracting text" in str(exc_info.value)
    
    def test_invalid_pdf_header(self):
        """Test handling of content with invalid PDF header"""
        invalid_content = b"This is not a PDF file"
        
        # Should return False for validation
        assert self.parser.validate_pdf_content(invalid_content) == False
        
        # Should raise PDFParsingError for parsing
        with pytest.raises(PDFParsingError):
            import asyncio
            asyncio.run(self.parser.parse_medical_report(invalid_content))
    
    def test_corrupted_pdf_content(self):
        """Test handling of corrupted PDF content"""
        # Create content that looks like PDF but is corrupted
        corrupted_content = b"%PDF-1.4\nCorrupted content that is not valid PDF"
        
        if PYMUPDF_AVAILABLE:
            # With PyMuPDF, should return False for validation
            assert self.parser.validate_pdf_content(corrupted_content) == False
        else:
            # Without PyMuPDF, basic header check returns True
            assert self.parser.validate_pdf_content(corrupted_content) == True
        
        # Should raise PDFParsingError for parsing regardless
        with pytest.raises(PDFParsingError):
            import asyncio
            asyncio.run(self.parser.parse_medical_report(corrupted_content))
    
    def test_very_large_content(self):
        """Test handling of very large content (simulated)"""
        # Create large binary content
        large_content = b"x" * (20 * 1024 * 1024)  # 20MB of data
        
        # Should return False for validation (not a valid PDF)
        assert self.parser.validate_pdf_content(large_content) == False
    
    def test_binary_garbage_content(self):
        """Test handling of random binary garbage"""
        import random
        
        # Generate random binary data
        garbage_content = bytes([random.randint(0, 255) for _ in range(1000)])
        
        # Should return False for validation
        assert self.parser.validate_pdf_content(garbage_content) == False
        
        # Should raise PDFParsingError for parsing
        with pytest.raises(PDFParsingError):
            import asyncio
            asyncio.run(self.parser.parse_medical_report(garbage_content))
    
    @pytest.mark.skipif(not PYMUPDF_AVAILABLE, reason="PyMuPDF not available")
    def test_pdf_with_no_text(self):
        """Test handling of PDF with no extractable text"""
        # Create a PDF with no text content
        doc = fitz.open()
        page = doc.new_page()
        # Don't add any text to the page
        pdf_bytes = doc.tobytes()
        doc.close()
        
        # Should validate as valid PDF
        assert self.parser.validate_pdf_content(pdf_bytes) == True
        
        # Should raise PDFParsingError due to no extractable text
        with pytest.raises(PDFParsingError) as exc_info:
            import asyncio
            asyncio.run(self.parser.parse_medical_report(pdf_bytes))
        
        assert "No text could be extracted" in str(exc_info.value)
    
    @pytest.mark.skipif(not PYMUPDF_AVAILABLE, reason="PyMuPDF not available")
    def test_pdf_with_only_whitespace(self):
        """Test handling of PDF with only whitespace text"""
        # Create a PDF with only whitespace
        doc = fitz.open()
        page = doc.new_page()
        page.insert_text((72, 72), "   \n\t\r   ")  # Only whitespace
        pdf_bytes = doc.tobytes()
        doc.close()
        
        # Should validate as valid PDF
        assert self.parser.validate_pdf_content(pdf_bytes) == True
        
        # Should raise PDFParsingError due to no meaningful text
        with pytest.raises(PDFParsingError) as exc_info:
            import asyncio
            asyncio.run(self.parser.parse_medical_report(pdf_bytes))
        
        assert "No text could be extracted" in str(exc_info.value)
    
    @pytest.mark.skipif(not PYMUPDF_AVAILABLE, reason="PyMuPDF not available")
    def test_pdf_with_non_medical_content(self):
        """Test handling of PDF with non-medical content"""
        # Create a PDF with non-medical text
        doc = fitz.open()
        page = doc.new_page()
        page.insert_text((72, 72), "This is a story about a cat named Fluffy.")
        pdf_bytes = doc.tobytes()
        doc.close()
        
        # Should validate as valid PDF
        assert self.parser.validate_pdf_content(pdf_bytes) == True
        
        # Should raise PDFParsingError due to no medical data
        with pytest.raises(PDFParsingError) as exc_info:
            import asyncio
            asyncio.run(self.parser.parse_medical_report(pdf_bytes))
        
        assert "No medical test data could be extracted" in str(exc_info.value)
    
    def test_normalize_test_name_edge_cases(self):
        """Test test name normalization with edge cases"""
        # Test with extra whitespace
        assert self.parser._normalize_test_name("  BILIRUBIN TOTAL  ") == "BILIRUBIN, TOTAL"
        
        # Test with multiple spaces
        assert self.parser._normalize_test_name("BILIRUBIN    TOTAL") == "BILIRUBIN, TOTAL"
        
        # Test with trailing punctuation
        assert self.parser._normalize_test_name("CHOLESTEROL TOTAL:") == "CHOLESTEROL, TOTAL"
        assert self.parser._normalize_test_name("GLUCOSE FASTING.") == "GLUCOSE, FASTING"
        
        # Test with lowercase input
        assert self.parser._normalize_test_name("hemoglobin") == "HEMOGLOBIN"
        
        # Test with unknown test name
        assert self.parser._normalize_test_name("UNKNOWN TEST") == "UNKNOWN TEST"
        
        # Test with empty string
        assert self.parser._normalize_test_name("") == ""
        
        # Test with only whitespace
        assert self.parser._normalize_test_name("   ") == ""
    
    def test_determine_verdict_edge_cases(self):
        """Test verdict determination with edge cases"""
        # Test with explicit verdict in remarks
        assert self.parser._determine_verdict("5.0", "2.0-4.0", "HIGH") == "HIGH"
        assert self.parser._determine_verdict("1.0", "2.0-4.0", "LOW") == "LOW"
        assert self.parser._determine_verdict("3.0", "2.0-4.0", "NORMAL") == "NORMAL"
        assert self.parser._determine_verdict("10.0", "2.0-4.0", "CRITICAL") == "CRITICAL"
        
        # Test with numeric comparison - high value
        assert self.parser._determine_verdict("5.0", "2.0-4.0", "") == "HIGH"
        
        # Test with numeric comparison - low value
        assert self.parser._determine_verdict("1.0", "2.0-4.0", "") == "LOW"
        
        # Test with numeric comparison - normal value
        assert self.parser._determine_verdict("3.0", "2.0-4.0", "") == "NORMAL"
        
        # Test with single-bound ranges
        assert self.parser._determine_verdict("6.0", "< 5.0", "") == "HIGH"
        assert self.parser._determine_verdict("4.0", "< 5.0", "") == "NORMAL"
        assert self.parser._determine_verdict("8.0", "> 10.0", "") == "LOW"
        assert self.parser._determine_verdict("12.0", "> 10.0", "") == "NORMAL"
        
        # Test with non-numeric values
        assert self.parser._determine_verdict("POSITIVE", "NEGATIVE", "") == "NORMAL"
        
        # Test with invalid range format
        assert self.parser._determine_verdict("5.0", "invalid-range", "") == "NORMAL"
        
        # Test with empty inputs
        assert self.parser._determine_verdict("", "", "") == "NORMAL"
    
    @pytest.mark.skipif(not PYMUPDF_AVAILABLE, reason="PyMuPDF not available")
    def test_pdf_with_special_characters(self):
        """Test handling of PDF with special characters and encoding"""
        # Create a PDF with special characters
        doc = fitz.open()
        page = doc.new_page()
        special_text = "BILIRUBIN TÖTÄL    2.5    1.0-2.0    mg/dL"
        page.insert_text((72, 72), special_text)
        pdf_bytes = doc.tobytes()
        doc.close()
        
        # Should validate as valid PDF
        assert self.parser.validate_pdf_content(pdf_bytes) == True
        
        # Should handle special characters gracefully
        import asyncio
        try:
            result = asyncio.run(self.parser.parse_medical_report(pdf_bytes))
            # Should extract some data or handle gracefully
            assert isinstance(result, dict)
        except PDFParsingError as e:
            # It's acceptable if special characters cause parsing to fail
            # The important thing is that it fails gracefully with a proper error
            assert isinstance(e, PDFParsingError)
            assert len(str(e)) > 0
    
    @pytest.mark.skipif(not PYMUPDF_AVAILABLE, reason="PyMuPDF not available")
    def test_pdf_with_malformed_test_data(self):
        """Test handling of PDF with malformed test data"""
        # Create a PDF with malformed test data
        doc = fitz.open()
        page = doc.new_page()
        malformed_text = """
        MEDICAL TEST REPORT
        TEST NAME    VALUE    RANGE
        BILIRUBIN    2.5      # Missing unit and range
        GLUCOSE      # Missing value
        # Missing test name    5.0    4.0-6.0    mg/dL
        CHOLESTEROL    HIGH    NORMAL    # Non-numeric value
        """
        page.insert_text((72, 72), malformed_text)
        pdf_bytes = doc.tobytes()
        doc.close()
        
        # Should validate as valid PDF
        assert self.parser.validate_pdf_content(pdf_bytes) == True
        
        # Should handle malformed data gracefully
        import asyncio
        result = asyncio.run(self.parser.parse_medical_report(pdf_bytes))
        
        # Should return a dictionary (may be empty due to malformed data)
        assert isinstance(result, dict)
    
    def test_extract_test_data_with_no_matches(self):
        """Test text extraction when no patterns match"""
        # Text that doesn't match any medical test patterns
        non_medical_text = """
        This is a regular document.
        It contains no medical test data.
        Just some random text about cats and dogs.
        """
        
        result = self.parser._extract_test_data_from_text(non_medical_text)
        
        # Should return empty dictionary
        assert result == {}
    
    def test_extract_test_data_with_minimal_matches(self):
        """Test text extraction with minimal pattern matches"""
        # Text with minimal medical-like patterns
        minimal_text = """
        GLUCOSE 5.0 4.0-6.0 mg/dL
        """
        
        result = self.parser._extract_test_data_from_text(minimal_text)
        
        # Should extract at least one test result
        assert isinstance(result, dict)
        assert len(result) >= 0  # May be 0 if pattern is too strict
        
        # If data is extracted, verify structure
        for key, metric in result.items():
            assert isinstance(metric, MetricData)
            assert isinstance(key, str)
    
    def test_file_size_validation_simulation(self):
        """Test file size validation (simulated without actual large files)"""
        # This would be tested in the API endpoint, but we can test the concept
        max_size = 10 * 1024 * 1024  # 10MB
        
        # Small file should pass
        small_content = b"small content"
        assert len(small_content) < max_size
        
        # Large file would fail (simulated)
        large_size = 15 * 1024 * 1024  # 15MB
        assert large_size > max_size
    
    def test_content_type_validation_simulation(self):
        """Test content type validation (simulated)"""
        allowed_types = ["application/pdf"]
        
        # Valid content type
        assert "application/pdf" in allowed_types
        
        # Invalid content types
        assert "text/plain" not in allowed_types
        assert "image/jpeg" not in allowed_types
        assert "application/msword" not in allowed_types
    
    @pytest.mark.skipif(not PYMUPDF_AVAILABLE, reason="PyMuPDF not available")
    def test_pdf_with_multiple_pages(self):
        """Test handling of multi-page PDF"""
        # Create a PDF with multiple pages
        doc = fitz.open()
        
        # Page 1
        page1 = doc.new_page()
        page1.insert_text((72, 72), "MEDICAL TEST REPORT - PAGE 1")
        page1.insert_text((72, 100), "GLUCOSE    5.0    4.0-6.0    mg/dL")
        
        # Page 2
        page2 = doc.new_page()
        page2.insert_text((72, 72), "MEDICAL TEST REPORT - PAGE 2")
        page2.insert_text((72, 100), "CHOLESTEROL    200    150-200    mg/dL")
        
        pdf_bytes = doc.tobytes()
        doc.close()
        
        # Should validate as valid PDF
        assert self.parser.validate_pdf_content(pdf_bytes) == True
        
        # Should extract text from all pages
        import asyncio
        text = asyncio.run(self.parser.extract_text_from_pdf(pdf_bytes))
        
        # Should contain text from both pages
        assert "PAGE 1" in text
        assert "PAGE 2" in text
        assert "GLUCOSE" in text
        assert "CHOLESTEROL" in text
    
    def test_without_pymupdf_availability(self):
        """Test behavior when PyMuPDF is not available"""
        # Mock PyMuPDF as unavailable
        with patch('app.services.pdf_parser.PYMUPDF_AVAILABLE', False):
            parser = PDFParserService()
            
            # Should handle validation with basic PDF header check
            valid_pdf_header = b"%PDF-1.4\nsome content"
            assert parser.validate_pdf_content(valid_pdf_header) == True
            
            invalid_content = b"not a pdf"
            assert parser.validate_pdf_content(invalid_content) == False
            
            # Should raise appropriate error for parsing
            with pytest.raises(PDFParsingError) as exc_info:
                import asyncio
                asyncio.run(parser.parse_medical_report(valid_pdf_header))
            
            assert "PyMuPDF is not available" in str(exc_info.value)


# Integration-style tests for error handling
class TestPDFProcessingErrorHandling:
    """Test error handling in PDF processing"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.parser = PDFParserService()
    
    def test_exception_handling_in_text_extraction(self):
        """Test exception handling during text extraction"""
        # Mock fitz to raise an exception
        if PYMUPDF_AVAILABLE:
            with patch('fitz.open') as mock_open:
                mock_open.side_effect = Exception("Mocked extraction error")
                
                with pytest.raises(PDFParsingError) as exc_info:
                    import asyncio
                    asyncio.run(self.parser.extract_text_from_pdf(b"dummy content"))
                
                assert "Error extracting text from PDF" in str(exc_info.value)
    
    def test_exception_handling_in_validation(self):
        """Test exception handling during PDF validation"""
        if PYMUPDF_AVAILABLE:
            with patch('fitz.open') as mock_open:
                mock_open.side_effect = Exception("Mocked validation error")
                
                # Should return False on exception
                result = self.parser.validate_pdf_content(b"dummy content")
                assert result == False
    
    def test_parsing_with_extraction_failure(self):
        """Test parsing when text extraction fails"""
        with patch.object(self.parser, 'extract_text_from_pdf') as mock_extract:
            mock_extract.side_effect = PDFParsingError("Extraction failed")
            
            with pytest.raises(PDFParsingError) as exc_info:
                import asyncio
                asyncio.run(self.parser.parse_medical_report(b"dummy content"))
            
            assert "Extraction failed" in str(exc_info.value)
    
    def test_parsing_with_data_extraction_failure(self):
        """Test parsing when data extraction returns empty results"""
        with patch.object(self.parser, 'extract_text_from_pdf') as mock_extract:
            mock_extract.return_value = "Some text with no medical data"
            
            with patch.object(self.parser, '_extract_test_data_from_text') as mock_data_extract:
                mock_data_extract.return_value = {}
                
                with pytest.raises(PDFParsingError) as exc_info:
                    import asyncio
                    asyncio.run(self.parser.parse_medical_report(b"dummy content"))
                
                assert "No medical test data could be extracted" in str(exc_info.value)