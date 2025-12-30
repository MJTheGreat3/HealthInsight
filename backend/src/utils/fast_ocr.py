#!/usr/bin/env python3
"""
Fast OCR module integrating PyMuPDF for direct text extraction with optimized OCR fallback.
Based on testing/test_fast.py logic integrated for production use.
"""
import os
import subprocess
import time
from typing import Optional, Dict, Any
import fitz  # PyMuPDF

# Crop coordinates optimized for medical reports (from test_fast.py)
CROP_Y1 = 190
CROP_Y2 = 630


class FastOCR:
    """Fast OCR processor with PyMuPDF extraction and optimized OCR fallback."""
    
    def __init__(self):
        self.ocr_timeout = 120  # Increased from 30 to handle complex medical reports
        self.ocr_jobs = 4       # Reduced from 6 to reduce memory pressure
        self.image_dpi = 150    # Reduced from 200 to balance speed and accuracy
    
    def fast_extract(self, pdf_path: str) -> Optional[str]:
        """
        Extract text quickly using PyMuPDF (no subprocesses).
        
        Args:
            pdf_path: Path to PDF file
            
        Returns:
            Extracted text or None if no text found
        """
        try:
            text_chunks = []
            doc = fitz.open(pdf_path)
            
            for page in doc:
                # Crop to the medical report table area
                rect = fitz.Rect(0, CROP_Y1, page.rect.width, CROP_Y2)
                page_text = page.get_text("text", clip=rect)
                if page_text.strip():
                    text_chunks.append(page_text)
            
            doc.close()
            
            extracted_text = "\n".join(text_chunks).strip()
            return extracted_text if extracted_text else None
            
        except Exception as e:
            print(f"Fast extraction failed: {e}")
            return None
    
    def run_optimized_ocr(self, pdf_path: str, max_retries: int = 2) -> Optional[str]:
        """
        OCR only the cropped region, optimized for speed with retry logic.
        Uses enhanced parameters from test_fast.py for optimal performance.
        
        Args:
            pdf_path: Path to PDF file
            max_retries: Maximum number of retry attempts
            
        Returns:
            OCR'd text or None if OCR failed
        """
        ocr_path = pdf_path.replace(".pdf", "_ocr.pdf")
        
        for attempt in range(max_retries + 1):
            try:
                print(f"OCR attempt {attempt + 1}/{max_retries + 1}")
                
                # Progressive timeout increase for retries
                timeout_buffer = 30 + (attempt * 15)
                
                # Build optimized OCR command with enhanced timeout handling
                cmd = [
                    "ocrmypdf",
                    "--force-ocr",
                    "--output-type", "pdf",
                    "--jobs", str(self.ocr_jobs),
                    "--image-dpi", str(self.image_dpi),
                    "--tesseract-timeout", str(self.ocr_timeout),
                    "--tesseract-non-ocr-timeout", "60",  # Timeout for preprocessing operations
                    "--tesseract-downsample-large-images",  # Handle very large pages
                    pdf_path,
                    ocr_path,
                ]
                
                # Progressive timeout increase for retries
                timeout_buffer = 30 + (attempt * 15)
                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    timeout=self.ocr_timeout + timeout_buffer
                )
                
                if result.returncode != 0:
                    print(f"❌ OCR failed: {result.stderr}")
                    if attempt < max_retries:
                        print(f"Retrying in 2 seconds...")
                        time.sleep(2)
                        continue
                    return None
                
                if not os.path.exists(ocr_path):
                    print("❌ OCR finished but output not found")
                    if attempt < max_retries:
                        print(f"Retrying in 2 seconds...")
                        time.sleep(2)
                        continue
                    return None
                
                # Extract text from OCR'd PDF
                extracted_text = self.fast_extract(ocr_path)
                
                # Cleanup OCR file
                try:
                    os.remove(ocr_path)
                except Exception as e:
                    print(f"Failed to cleanup OCR file: {e}")
                
                if extracted_text:
                    print(f"✅ OCR successful on attempt {attempt + 1}")
                    return extracted_text
                elif attempt < max_retries:
                    print(f"No text extracted, retrying...")
                    time.sleep(2)
                    continue
                else:
                    return None
                    
            except subprocess.TimeoutExpired:
                print(f"❌ OCR timed out after {self.ocr_timeout + timeout_buffer} seconds")
                # Cleanup on timeout
                if os.path.exists(ocr_path):
                    try:
                        os.remove(ocr_path)
                    except Exception:
                        pass
                
                if attempt < max_retries:
                    print(f"Timeout occurred, retrying with longer timeout...")
                    continue
                else:
                    return None
                    
            except Exception as e:
                print(f"❌ OCR processing failed: {e}")
                # Cleanup on error
                if os.path.exists(ocr_path):
                    try:
                        os.remove(ocr_path)
                    except Exception:
                        pass
                
                if attempt < max_retries:
                    print(f"Error occurred, retrying...")
                    time.sleep(2)
                    continue
                else:
                    return None
        
        return None
    
    def extract_text_with_fallback(self, pdf_path: str) -> Dict[str, Any]:
        """
        Extract text using fast PyMuPDF method first, then OCR fallback.
        
        Args:
            pdf_path: Path to PDF file
            
        Returns:
            Dictionary with extraction results and metadata
        """
        start_time = time.time()
        
        # Step 1: Fast text extraction
        text = self.fast_extract(pdf_path)
        
        if text:
            extraction_time = time.time() - start_time
            return {
                "success": True,
                "text": text,
                "method": "fast_extraction",
                "processing_time": extraction_time,
                "text_length": len(text)
            }
        
        # Step 2: OCR fallback
        print("ℹ️ No extractable text — falling back to OCR…")
        ocr_text = self.run_optimized_ocr(pdf_path)
        
        if ocr_text:
            total_time = time.time() - start_time
            return {
                "success": True,
                "text": ocr_text,
                "method": "ocr_fallback",
                "processing_time": total_time,
                "text_length": len(ocr_text)
            }
        
        # Step 3: Failure
        total_time = time.time() - start_time
        return {
            "success": False,
            "text": None,
            "method": "failed",
            "processing_time": total_time,
            "error": "Both fast extraction and OCR failed"
        }


def extract_text_from_pdf(pdf_path: str) -> Dict[str, Any]:
    """
    Convenience function to extract text from PDF using fast OCR logic.
    
    Args:
        pdf_path: Path to PDF file
        
    Returns:
        Dictionary with extraction results
    """
    ocr_processor = FastOCR()
    return ocr_processor.extract_text_with_fallback(pdf_path)
