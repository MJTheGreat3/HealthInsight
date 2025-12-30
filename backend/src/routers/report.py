from fastapi import APIRouter, UploadFile, File, HTTPException, Depends, Form
from fastapi.responses import JSONResponse
from typing import List, Optional
import os
import re
import json
from datetime import datetime
from bson import ObjectId
from bson.json_util import dumps

from src.db.mongoWrapper import getMongo
from src.schemas import ReportModel, ProcessedAtUpdate, AttributeUpdateByName, AttributeCreate, AttributeDeleteByName
from src.utils.file_handler import FileHandler
from src.llm_agent import LLMReportAgent
from src.auth.dependencies import get_current_user

router = APIRouter(prefix="/api")

# Initialize services
file_handler = FileHandler()


@router.get("/ping")
def ping():
    return {"message": "pong"}


@router.get("/db-test")
async def test_db(current_user: dict = Depends(get_current_user)):
    try:
        mongo = await getMongo()
        if mongo is None:
            return {"status": "error", "message": "Database not connected"}
        
        # Test basic operation
        count = await mongo.count("Reports", {})
        return {"status": "ok", "report_count": count}
    except Exception as e:
        return {"status": "error", "message": str(e)}


# Internal helper functions for orchestration
async def _upload_and_parse_report(
    file: UploadFile, 
    patient_id: Optional[str], 
    report_id: Optional[str],
    current_user: Optional[dict] = None
) -> dict:
    """Internal function to handle file upload and parsing"""
    file_path = None
    csv_file_path = None
    processed_csv_path = None
    file_id = None
    
    try:
        # Save uploaded file
        file_id, file_path = await file_handler.save_upload_file(file)
        
        # Generate patient ID if not provided or empty
        if not patient_id or patient_id.strip() == "":
            if current_user and 'uid' in current_user:
                patient_id = current_user['uid']
            else:
                patient_id = f"patient_{file_id[:8]}"
        
        # Generate report ID if not provided or empty
        if not report_id or report_id.strip() == "":
            report_id = f"report_{file_id[:8]}"
        
        # Extract CSV from PDF
        csv_file_path = os.path.join(file_handler.upload_dir, f"{file_id}_extracted.csv")
        csv_extraction_result = file_handler.extract_csv(file_path, csv_file_path)
        
        # Parse extracted CSV data
        if not csv_extraction_result or not csv_extraction_result.get("success"):
            raise HTTPException(status_code=400, detail="CSV extraction failed")
            
        csv_parsing_result = file_handler.parse_csv(csv_file_path)
        if not csv_parsing_result or not csv_parsing_result.get("success"):
            raise HTTPException(status_code=400, detail="CSV parsing failed")
        
        # Get CSV structured data
        csv_data = csv_parsing_result.get("data", [])
        processed_csv_path = csv_parsing_result.get("processed_file")
        
        # Create attributes dictionary with CSV data (all 4 columns)
        parsed_attributes = {}
        for i, test in enumerate(csv_data, 1):
            key = f"test_{i}"
            parsed_attributes[key] = test
        
        # Get current timestamp for processing time
        from datetime import datetime, UTC
        current_time = datetime.now(UTC).isoformat()
        
        report_data = {
            "Report_id": report_id,
            "Patient_id": patient_id,
            "Attributes": parsed_attributes,
            "Processed_at": current_time
        }
        
        # Save to database
        mongo = await getMongo()
        if mongo is None:
            raise HTTPException(status_code=500, detail="Database not connected")
        
        result_id = await mongo.insert_one("Reports", report_data)
        
        return {
            "report_id": report_id,
            "patient_id": patient_id,
            "tests_stored": len(parsed_attributes),
            "id": result_id,
            "attributes": parsed_attributes,
            "file_id": file_id,
            "file_path": file_path,
            "csv_path": csv_file_path
        }
        
    finally:
        # Clean up temporary files
        if file_path:
            file_handler.delete_file(file_path)
        if csv_file_path and os.path.exists(csv_file_path):
            os.remove(csv_file_path)
        if processed_csv_path and os.path.exists(processed_csv_path):
            os.remove(processed_csv_path)
        
        # Additional cleanup: remove any processed CSV files that might be left behind
        # Use pattern matching to clean up any _processed.csv files related to this file_id
        if file_id:
            import glob
            processed_pattern = os.path.join(os.path.dirname(csv_file_path or ""), f"{file_id}_*_processed.csv")
            for processed_file in glob.glob(processed_pattern):
                try:
                    os.remove(processed_file)
                    print(f"Cleaned up extra processed file: {processed_file}")
                except Exception as e:
                    print(f"Failed to clean up {processed_file}: {e}")

async def _analyze_report_data(
    patient_id: str, 
    report_id: str, 
    attributes: dict
) -> dict:
    """Internal function to handle LLM analysis"""
    try:
        agent = LLMReportAgent()
        agent_input = {
            "report_id": report_id,
            "patient_id": patient_id,
            "input": attributes,
            "favorites": [],
            "biodata": {},
        }
        analysis = await agent.analyze(agent_input)
        
        # Store LLM result
        mongo = await getMongo()
        if mongo is None:
            raise HTTPException(status_code=500, detail="Database not connected")
        
        from datetime import datetime
        llm_doc = {
            "patient_id": patient_id,
            "report_id": report_id,
            "time": datetime.utcnow().isoformat(),
            "output": analysis,
            "input": attributes,
        }
        
        llm_report_id = await mongo.insert_one("LLMReports", llm_doc)
        
        # Update original report with LLM reference
        if report_id:
            await mongo.update_one("Reports", {"Report_id": report_id}, {"llm_report_id": llm_report_id})
        
        return {
            "llm_report_id": llm_report_id,
            "analysis": analysis
        }
        
    except Exception as e:
        return {
            "error": "llm_analysis_failed",
            "message": str(e),
            "llm_report_id": None,
            "analysis": None
        }

async def _update_report_with_llm(report_id: str, llm_report_id: str):
    """Internal function to update report with LLM reference"""
    try:
        mongo = await getMongo()
        if mongo:
            await mongo.update_one("Reports", {"Report_id": report_id}, {"llm_report_id": llm_report_id})
    except Exception as e:
        print(f"Failed to update report with LLM reference: {e}")

@router.post("/reports/upload")
async def upload_report(
    file: UploadFile = File(...), 
    patient_id: Optional[str] = Form(None), 
    report_id: Optional[str] = Form(None),
    current_user: dict = Depends(get_current_user)
):
    """
    Upload and process a medical report PDF
    """
    
    file_path = None
    csv_file_path = None
    processed_csv_path = None
    
    try:
        # Save uploaded file
        file_id, file_path = await file_handler.save_upload_file(file)
        
        # Extract CSV from PDF
        csv_file_path = os.path.join(file_handler.upload_dir, f"{file_id}_extracted.csv")
        csv_extraction_result = file_handler.extract_csv(file_path, csv_file_path)
        
        # Parse extracted CSV data
        if not csv_extraction_result or not csv_extraction_result.get("success"):
            raise HTTPException(status_code=400, detail="CSV extraction failed")
            
        csv_parsing_result = file_handler.parse_csv(csv_file_path)
        if not csv_parsing_result or not csv_parsing_result.get("success"):
            raise HTTPException(status_code=400, detail="CSV parsing failed")
        
        # Get CSV structured data
        processed_csv_path = csv_parsing_result.get("processed_file")
        csv_data = csv_parsing_result.get("data", [])
        
        # Create attributes dictionary with CSV data (all 4 columns)
        parsed_attributes = {}
        for i, test in enumerate(csv_data, 1):
            key = f"test_{i}"
            parsed_attributes[key] = test
        
        # Generate patient ID if not provided or empty
        if not patient_id or patient_id.strip() == "":
            # Note: This function doesn't have access to current_user, so use fallback
            patient_id = f"patient_{file_id[:8]}"
        
        # Generate report ID if not provided or empty
        if not report_id or report_id.strip() == "":
            report_id = f"report_{file_id[:8]}"
        
        report_data = {
            "Report_id": report_id,
            "Patient_id": patient_id,
            "Attributes": parsed_attributes,
            "Processed_at": datetime.utcnow().isoformat()
        }
        
        # Save to database
        mongo = await getMongo()
        if mongo is None:
            raise HTTPException(status_code=500, detail="Database not connected")
        
        result_id = await mongo.insert_one("Reports", report_data)
        
        # Clean up temporary files
        file_handler.delete_file(file_path)
        if csv_file_path and os.path.exists(csv_file_path):
            os.remove(csv_file_path)
        if processed_csv_path and os.path.exists(processed_csv_path):
            os.remove(processed_csv_path)
        
        return {
            "message": "Report uploaded and processed successfully",
            "report_id": report_id,
            "patient_id": patient_id,
            "tests_stored": len(parsed_attributes),
            "id": result_id
        }
        
    except HTTPException:
        # Clean up file on HTTP errors
        if 'file_path' in locals() and file_path is not None:
            file_handler.delete_file(file_path)
        if 'csv_file_path' in locals() and csv_file_path and os.path.exists(csv_file_path):
            os.remove(csv_file_path)
        if 'processed_csv_path' in locals() and processed_csv_path and os.path.exists(processed_csv_path):
            os.remove(processed_csv_path)
        raise
    except Exception as e:
        # Clean up file on general errors
        if 'file_path' in locals() and file_path is not None:
            file_handler.delete_file(file_path)
        if 'csv_file_path' in locals() and csv_file_path and os.path.exists(csv_file_path):
            os.remove(csv_file_path)
        if 'processed_csv_path' in locals() and processed_csv_path and os.path.exists(processed_csv_path):
            os.remove(processed_csv_path)
        raise HTTPException(status_code=500, detail=f"Error processing report: {str(e)}")


@router.post("/reports/upload-and-analyze")
async def upload_and_analyze(
    file: UploadFile = File(...),
    patient_id: Optional[str] = Form(None),
    report_id: Optional[str] = Form(None),
    auto_analyze: bool = Form(True),  # Allow disable for testing
    current_user: dict = Depends(get_current_user)
):
    """
    Upload, process, and automatically analyze a medical report PDF in one atomic operation
    """
    try:
        # Step 1: Upload and parse the report
        upload_result = await _upload_and_parse_report(file, patient_id, report_id, current_user)
        
        if not auto_analyze:
            return {
                "message": "Report uploaded successfully (auto-analysis disabled)",
                "report_id": upload_result["report_id"],
                "patient_id": upload_result["patient_id"],
                "tests_stored": upload_result["tests_stored"],
                "llm_analysis_complete": False,
                "id": upload_result["id"]
            }
        
        # Step 2: Perform LLM analysis
        llm_result = await _analyze_report_data(
            upload_result["patient_id"],
            upload_result["report_id"], 
            upload_result["attributes"]
        )
        
        if llm_result.get("error"):
            # LLM failed but upload succeeded
            return {
                "message": "Report uploaded successfully, but LLM analysis failed",
                "report_id": upload_result["report_id"],
                "patient_id": upload_result["patient_id"],
                "tests_stored": upload_result["tests_stored"],
                "llm_analysis_complete": False,
                "llm_error": llm_result.get("message"),
                "id": upload_result["id"]
            }
        
        # Step 3: Update original report with LLM reference
        await _update_report_with_llm(upload_result["report_id"], llm_result["llm_report_id"])
        
        # Step 4: Return unified response
        return {
            "message": "Report uploaded and analyzed successfully",
            "report_id": upload_result["report_id"],
            "patient_id": upload_result["patient_id"],
            "tests_stored": upload_result["tests_stored"],
            "llm_analysis_complete": True,
            "llm_report_id": llm_result["llm_report_id"],
            "llm_analysis": llm_result["analysis"],
            "id": upload_result["id"]
        }
        
    except HTTPException:
        # Cleanup is handled in the helper function
        raise
    except Exception as e:
        # Cleanup is handled in the helper function
        raise HTTPException(status_code=500, detail=f"Error processing report: {str(e)}")


@router.get("/reports/{report_id}")
async def get_report(report_id: str, current_user: dict = Depends(get_current_user)):
    """
    Retrieve a specific report by ID
    """
    try:
        mongo = await getMongo()
        if mongo is None:
            raise HTTPException(status_code=500, detail="Database not connected")
        
        report = await mongo.find_one("Reports", {"Report_id": report_id})
        if not report:
            raise HTTPException(status_code=404, detail="Report not found")
        
        # Convert ObjectId to string for JSON serialization
        if "_id" in report:
            report["_id"] = str(report["_id"])
        
        return report
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving report: {str(e)}")


@router.get("/reports/patient/{patient_id}")
async def get_patient_reports(patient_id: str, current_user: dict = Depends(get_current_user)):
    """
    Retrieve all reports for a specific patient
    """
    try:
        mongo = await getMongo()
        if mongo is None:
            raise HTTPException(status_code=500, detail="Database not connected")
        
        reports = await mongo.find_many("Reports", {"Patient_id": patient_id}, limit=50)
        
        # Convert ObjectIds to strings for JSON serialization
        for report in reports:
            if "_id" in report:
                report["_id"] = str(report["_id"])
        
        return {
            "patient_id": patient_id,
            "report_count": len(reports),
            "reports": reports
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving patient reports: {str(e)}")

@router.patch("/reports/{report_id}/processed-at")
async def update_processed_at(
    report_id: str,
    payload: ProcessedAtUpdate,
    current_user: dict = Depends(get_current_user)
):
    mongo = await getMongo()
    if mongo is None:
        raise HTTPException(status_code=500, detail="Database not connected")

    updated = await mongo.update_one(
        "Reports",
        {"Report_id": report_id},
        {"Processed_at": payload.processed_at.isoformat()}
    )

    if updated == 0:
        raise HTTPException(status_code=404, detail="Report not found")

    return {
        "message": "Processed_at updated successfully",
        "report_id": report_id,
        "processed_at": payload.processed_at
    }

@router.patch("/reports/{report_id}/attribute-by-name")
async def update_attribute_by_name(
    report_id: str,
    payload: AttributeUpdateByName,
    current_user: dict = Depends(get_current_user)
):
    mongo = await getMongo()
    if mongo is None:
        raise HTTPException(status_code=500, detail="Database not connected")

    # 1. Fetch report
    report = await mongo.find_one("Reports", {"Report_id": report_id})
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")

    attributes = report.get("Attributes", {})

    # 2. Find matching test key
    test_key = None
    for key, test in attributes.items():
        if test.get("name") == payload.name:
            test_key = key
            break

    if not test_key:
        raise HTTPException(
            status_code=404,
            detail=f"Test with name '{payload.name}' not found"
        )

    # 3. Build update dict (only provided fields)
    update_fields = {}
    for field in ["value", "remark", "range", "unit"]:
        field_value = getattr(payload, field)
        if field_value is not None:
            update_fields[f"Attributes.{test_key}.{field}"] = field_value

    if not update_fields:
        raise HTTPException(
            status_code=400,
            detail="No fields provided for update"
        )

    # 4. Apply update
    await mongo.update_one(
        "Reports",
        {"Report_id": report_id},
        update_fields
    )

    return {
        "message": "Test attribute updated successfully",
        "report_id": report_id,
        "test_key": test_key,
        "test_name": payload.name,
        "updated_fields": update_fields
    }

@router.post("/reports/{report_id}/attribute")
async def add_attribute(
    report_id: str,
    payload: AttributeCreate
):
    mongo = await getMongo()
    if mongo is None:
        raise HTTPException(status_code=500, detail="Database not connected")

    # 1. Fetch report
    report = await mongo.find_one("Reports", {"Report_id": report_id})
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")

    attributes = report.get("Attributes", {})

    # 2. Prevent duplicate test names
    for test in attributes.values():
        if test.get("name") == payload.name:
            raise HTTPException(
                status_code=409,
                detail=f"Test with name '{payload.name}' already exists"
            )

    # 3. Compute next test key
    max_index = 0
    pattern = re.compile(r"test_(\d+)")

    for key in attributes.keys():
        match = pattern.match(key)
        if match:
            max_index = max(max_index, int(match.group(1)))

    new_test_key = f"test_{max_index + 1}"

    # 4. Create new attribute
    new_attribute = {
        "name": payload.name,
        "value": payload.value,
        "remark": payload.remark,
        "range": payload.range,
        "unit": payload.unit
    }

    await mongo.update_one(
        "Reports",
        {"Report_id": report_id},
        {f"Attributes.{new_test_key}": new_attribute}
    )

    return {
        "message": "Attribute added successfully",
        "report_id": report_id,
        "test_key": new_test_key,
        "attribute": new_attribute
    }


@router.delete("/reports/{report_id}/attribute-by-name")
async def delete_attribute_by_name(report_id: str, payload: AttributeDeleteByName, current_user: dict = Depends(get_current_user)):
    mongo = await getMongo()
    if mongo is None:
        raise HTTPException(status_code=500, detail="Database not connected")

    report = await mongo.find_one("Reports", {"Report_id": report_id})
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")

    attributes = report.get("Attributes", {})

    test_key = None
    for key, test in attributes.items():
        if test.get("name") == payload.name:
            test_key = key
            break

    if not test_key:
        raise HTTPException(
            status_code=404,
            detail=f"Test '{payload.name}' not found"
        )

    # 🔥 REAL deletion
    await mongo.update_one(
        "Reports",
        {"Report_id": report_id},
        {"$unset": {f"Attributes.{test_key}": ""}},
        raw=True
    )

    return {
        "message": "Attribute deleted successfully",
        "deleted_test_key": test_key,
        "deleted_test_name": payload.name
    }

def _fuzzy_match(search_term: str, test_name: str) -> bool:
    """Conservative fuzzy matching function for biomarker names."""
    import re
    
    # Handle exact match first (case insensitive)
    if search_term.lower().strip() == test_name.lower().strip():
        return True
    
    # Remove common units and normalize
    search_clean = re.sub(r'(/dL|/uL|/L|mg/dl|mmol/l|mm/hg|%|mmol/l)', '', search_term, flags=re.IGNORECASE).strip()
    test_clean = re.sub(r'(/dL|/uL|/L|mg/dl|mmol/l|mm/hg|%|mmol/l)', '', test_name, flags=re.IGNORECASE).strip()
    
    # Remove content in parentheses
    search_clean = re.sub(r'\([^)]*\)', '', search_clean).strip()
    test_clean = re.sub(r'\([^)]*\)', '', test_clean).strip()
    
    # Common abbreviations mapping
    abbreviations = {
        'rbc': 'red blood cell',
        'wbc': 'white blood cell', 
        'hgb': 'hemoglobin',
        'hct': 'hematocrit',
        'mcv': 'mean corpuscular volume',
        'mch': 'mean corpuscular hemoglobin',
        'mchc': 'mean corpuscular hemoglobin concentration',
        'plt': 'platelet',
        'rdw': 'red cell distribution width',
        'mpv': 'mean platelet volume',
        'neut': 'neutrophil',
        'lymp': 'lymphocyte',
        'mono': 'monocyte',
        'eo': 'eosinophil',
        'baso': 'basophil'
    }
    
    # Expand abbreviations in both terms
    for abbr, full in abbreviations.items():
        search_clean = search_clean.replace(abbr, full)
        test_clean = test_clean.replace(abbr, full)
    
    # Split into words and filter out common filler words
    filler_words = {'count', 'cell', 'cells', 'blood', 'corpuscular', 'mean', 'distribution', 'width'}
    search_words = [w.lower() for w in search_clean.split() if len(w) > 1 and w.lower() not in filler_words]
    test_words = [w.lower() for w in test_clean.split() if len(w) > 1 and w.lower() not in filler_words]
    
    # If we have meaningful words to compare
    if search_words and test_words:
        # Check for partial matches - one term contained in the other
        search_joined = ' '.join(search_words)
        test_joined = ' '.join(test_words)
        
        if search_joined in test_joined or test_joined in search_joined:
            return True
        
        # Count common meaningful words
        common_words = set(search_words) & set(test_words)
        
        # More conservative matching:
        # - For single word searches, need exact match on that word
        if len(search_words) == 1:
            return len(common_words) == 1
        # - For 2-3 word searches, need at least 50% match
        elif len(search_words) <= 3:
            return len(common_words) >= 1 and (len(common_words) / len(search_words)) >= 0.5
        # - For longer searches, need at least 60% match or 2+ words
        else:
            return (len(common_words) / len(search_words)) >= 0.6 or len(common_words) >= 2
    
    return False


@router.get("/draw_graph/{patient_id}/{attribute}")
async def draw_graph_data(patient_id: str, attribute: str, current_user: dict = Depends(get_current_user)):
    """
    Extract specific attribute values from all patient reports for graphing
    """
    try:
        # Input validation
        if not patient_id or not patient_id.strip():
            raise HTTPException(status_code=400, detail="Patient ID cannot be empty")
        
        if not attribute or not attribute.strip():
            raise HTTPException(status_code=400, detail="Attribute cannot be empty")
        
        mongo = await getMongo()
        if mongo is None:
            raise HTTPException(status_code=500, detail="Database not connected")

        # Fetch reports with error handling
        try:
            patient_reports = await mongo.find_many(
                "Reports",
                {"Patient_id": patient_id},
                limit=100
            )
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error fetching patient reports: {str(e)}")

        if not patient_reports:
            return {
                "patient_id": patient_id,
                "attribute": attribute,
                "data_points": 0,
                "values": [],
                "message": "No reports found for this patient"
            }

        values = []

        for report in patient_reports:
            try:
                attributes = report.get("Attributes", {})
                timestamp = report.get("Processed_at")

                # Skip if no attributes or timestamp
                if not attributes or not timestamp:
                    continue

                # Smart matching for attribute - case insensitive and partial match
                found_match = False
                matched_name = None
                test_dict = None
                
                for test_key, test_data in attributes.items():
                    if not isinstance(test_data, dict):
                        continue
                        
                    test_name = test_data.get("name", "")
                    if not test_name:
                        continue
                    
                    # Normalize both names for comparison
                    normalized_search = attribute.lower().strip()
                    normalized_test = test_name.lower().strip()
                    
                    # Exact match
                    if normalized_search == normalized_test:
                        found_match = True
                        matched_name = test_name
                        test_dict = test_data
                        break
                    # Partial match - if search term is contained in test name
                    elif normalized_search in normalized_test or normalized_test in normalized_search:
                        found_match = True
                        matched_name = test_name
                        test_dict = test_data
                        break
                    # Fuzzy match - check if major words match
                    elif _fuzzy_match(normalized_search, normalized_test):
                        found_match = True
                        matched_name = test_name
                        test_dict = test_data
                        break
                
                if found_match and test_dict:
                    raw_value = test_dict.get("value")
                    remark = test_dict.get("remark")

                    # Try to extract number (optional)
                    value = raw_value
                    try:
                        if raw_value is not None and str(raw_value).strip():
                            value = float(str(raw_value).split()[0])
                    except (ValueError, TypeError, AttributeError):
                        # Keep original value if conversion fails
                        value = raw_value

                    values.append({
                        "value": value,
                        "timestamp": timestamp,
                        "remark": remark,
                        "matched_name": matched_name  # Return the actual matched name
                    })

            except Exception as e:
                # Log error for this report but continue processing others
                print(f"Error processing report {report.get('Report_id', 'unknown')}: {e}")
                continue

        return {
            "patient_id": patient_id,
            "attribute": attribute,
            "data_points": len(values),
            "values": values,
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error extracting graph data: {str(e)}"
        )



@router.delete("/reports/{report_id}")
async def delete_report(report_id: str, current_user: dict = Depends(get_current_user)):
    """
    Delete a report
    """
    try:
        mongo = await getMongo()
        if mongo is None:
            raise HTTPException(status_code=500, detail="Database not connected")
        
        deleted_count = await mongo.delete_one("Reports", {"Report_id": report_id})
        
        if deleted_count == 0:
            raise HTTPException(status_code=404, detail="Report not found")
        
        return {"message": "Report deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting report: {str(e)}")


@router.get("/reports")
async def list_reports(current_user: dict = Depends(get_current_user)):
    """
    List all reports (with pagination)
    """
    try:
        mongo = await getMongo()
        if mongo is None:
            raise HTTPException(status_code=500, detail="Database not connected")
        
        reports = await mongo.find_many("Reports", {}, limit=50)
        
        # Convert ObjectIds to strings for JSON serialization
        for report in reports:
            if "_id" in report:
                report["_id"] = str(report["_id"])
        
        return {
            "report_count": len(reports),
            "reports": reports
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error listing reports: {str(e)}")

