#!/usr/bin/env python3
"""
Test script to verify the complete upload integration with fast OCR and LLM fallback
"""
import asyncio
import aiohttp
import json
import os
import time

async def test_upload_integration():
    """Test the upload and analyze endpoint with integration"""
    
    # Create a simple test PDF if it doesn't exist
    test_pdf_path = "test_upload.pdf"
    if not os.path.exists(test_pdf_path):
        print("Creating test PDF...")
        import fitz
        doc = fitz.open()
        page = doc.new_page()
        page.insert_text((50, 200), 'Complete Blood Count Report')
        page.insert_text((50, 230), 'HEMOGLOBIN 14.5 g/dL 12.0-15.5')
        page.insert_text((50, 250), 'RBC 4.8 M/uL 4.2-5.4')
        page.insert_text((50, 270), 'WBC 8.2 K/uL 4.5-11.0')
        page.insert_text((50, 290), 'PLATELETS 250 K/uL 150-450')
        doc.save(test_pdf_path)
        doc.close()
        print(f"Test PDF created: {test_pdf_path}")
    
    print("Testing upload and analyze endpoint...")
    
    async with aiohttp.ClientSession() as session:
        # Test upload with auto-analysis
        data = aiohttp.FormData()
        data.add_field('file', open(test_pdf_path, 'rb'), 
                      filename='test_upload.pdf', 
                      content_type='application/pdf')
        data.add_field('auto_analyze', 'true')
        
        start_time = time.time()
        
        try:
            async with session.post(
                'http://127.0.0.1:8000/api/reports/upload-and-analyze',
                data=data,
                timeout=aiohttp.ClientTimeout(total=120)  # 2 minute timeout
            ) as response:
                
                elapsed = time.time() - start_time
                print(f"Response received in {elapsed:.2f} seconds")
                
                if response.status == 200:
                    result = await response.json()
                    print("✅ Upload and analyze successful!")
                    print(f"Report ID: {result.get('report_id')}")
                    print(f"Patient ID: {result.get('patient_id')}")
                    print(f"Tests stored: {result.get('tests_stored')}")
                    print(f"LLM analysis complete: {result.get('llm_analysis_complete')}")
                    
                    if result.get('llm_analysis_complete'):
                        print("✅ Full pipeline working!")
                        return True
                    else:
                        print("⚠️ Upload successful but LLM analysis failed")
                        return False
                else:
                    error_text = await response.text()
                    print(f"❌ Upload failed with status {response.status}")
                    print(f"Error: {error_text}")
                    return False
                    
        except asyncio.TimeoutError:
            print("❌ Upload timed out after 120 seconds")
            return False
        except Exception as e:
            print(f"❌ Upload failed with error: {e}")
            return False
        finally:
            # Cleanup
            if os.path.exists(test_pdf_path):
                os.remove(test_pdf_path)

if __name__ == "__main__":
    asyncio.run(test_upload_integration())