import os
import uuid
from typing import Optional, Tuple, Dict, Any
from fastapi import UploadFile, HTTPException
import re

class FileHandler:
    def __init__(self, upload_dir: str = "src/uploads"):
        self.upload_dir = upload_dir
        self.allowed_extensions = ['.pdf']
        self.max_file_size = 10 * 1024 * 1024  # 10MB
        
        # Create upload directory if it doesn't exist
        os.makedirs(self.upload_dir, exist_ok=True)

    def validate_file(self, file: UploadFile) -> bool:
        """
        Validate uploaded file
        
        Args:
            file: Uploaded file object
            
        Returns:
            True if valid, raises HTTPException if invalid
        """
        # Check file extension
        if not file.filename:
            raise HTTPException(status_code=400, detail="No filename provided")
        
        file_ext = os.path.splitext(file.filename)[1].lower()
        if file_ext not in self.allowed_extensions:
            raise HTTPException(
                status_code=400, 
                detail=f"File type {file_ext} not allowed. Only PDF files are accepted."
            )
        
        return True

    async def save_upload_file(self, file: UploadFile) -> Tuple[str, str]:
        """
        Save uploaded file to temporary storage
        
        Args:
            file: Uploaded file object
            
        Returns:
            Tuple of (file_id, file_path)
        """
        try:
            # Validate file
            self.validate_file(file)
            
            # Generate unique file ID and path
            file_id = str(uuid.uuid4())
            file_ext = os.path.splitext(file.filename)[1].lower()
            filename = f"{file_id}{file_ext}"
            file_path = os.path.join(self.upload_dir, filename)
            
            # Save file
            with open(file_path, "wb") as buffer:
                content = await file.read()
                
                # Check file size
                if len(content) > self.max_file_size:
                    raise HTTPException(
                        status_code=413, 
                        detail=f"File size exceeds maximum allowed size of {self.max_file_size // (1024*1024)}MB"
                    )
                
                buffer.write(content)
            
            return file_id, file_path
            
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error saving file: {str(e)}")

    def extract_csv(self, input_file_path: str, output_file_path: str) -> Optional[dict]:
        """
        Extract CSV data from PDF file (simplified version for testing)
        """
        try:
            # For now, create a simple mock CSV to test the upload flow
            # In production, this would use camelot or similar PDF parsing
            mock_data = """name,value_and_remark,range,unit
Hemoglobin,14.5 g/dL,12.0-15.5,g/dL
RBC,4.8 M/uL,4.2-5.4,M/uL
WBC,8.2 K/uL,4.5-11.0,K/uL"""
            
            with open(output_file_path, "w") as f:
                f.write(mock_data)
            
            return {"success": True, "input": input_file_path, "output": output_file_path}
        except Exception as e:
            print(f"Error extracting CSV: {e}")
            return None

    def parse_csv(self, input_file_name: str) -> Optional[dict]:
        """
        Read CSV file and extract useful data
        """
        try:
            import pandas as pd
            
            df = pd.read_csv(
                input_file_name,
                header=None,
                engine="python",
                names=["name", "value_and_remark", "range", "unit"],
            )
            
            # Keep only rows that look like actual test results
            df = df[
                df["value_and_remark"].astype(str).str.contains(r"\d", regex=True)
                & ~df["name"].astype(str).str.contains(r"[a-z]", regex=True, na=False)
            ]
            
            # Remove empty rows
            df = df[~df.apply(lambda r: any(str(v).strip() == "" for v in r), axis=1)]
            
            structured_data = []
            for _, row in df.itertuples():
                name = getattr(row, 'name', None)
                value_remark_str = getattr(row, 'value_and_remark', None)
                
                if pd.isna(value_remark_str) or str(value_remark_str).strip() == "":
                    continue
                
                # Extract value and remark
                pattern = r'^(\d+\.?\d*\s*[a-zA-Z/]*)(?:\s+(.+?)$)'
                match = re.match(pattern, str(value_remark_str))
                
                if match:
                    value_part = match.group(1).strip()
                    remark_part = match.group(2).strip() if match.group(2) else None
                    
                    # If remark is in parentheses, extract content
                    if remark_part and remark_part.startswith('(') and remark_part.endswith(')'):
                        remark_part = remark_part[1:-1]
                    
                    return value_part, remark_part if remark_part and remark_part.strip() else None
                else:
                    # Handle pure numbers without units - treat as value
                    return str(value_remark_str), None
            
            for _, row in df.itertuples():
                name = getattr(row, 'name', None)
                value_remark_str = getattr(row, 'value_and_remark', None)
                range_str = getattr(row, 'range', None)
                unit_str = getattr(row, 'unit', None)
                
                if pd.isna(name) or str(name).strip() == "":
                    continue
                
                # Process value and remark
                if pd.isna(value_remark_str) or str(value_remark_str).strip() == "":
                    continue
                
                pattern = r'^(\d+\.?\d*\s*[a-zA-Z/]*)(?:\s+(.+?)$)'
                match = re.match(pattern, str(value_remark_str))
                
                if match:
                    value_part = match.group(1).strip()
                    remark_part = match.group(2).strip() if match.group(2) else None
                else:
                    value_part = str(value_remark_str)
                    remark_part = None
                
                structured_data.append({
                    "name": name,
                    "value": value_part,
                    "remark": remark_part,
                    "range": range_str,
                    "unit": unit_str
                })
            
            # Save processed data
            processed_file = input_file_name.replace('.csv', '_processed.csv')
            processed_df = pd.DataFrame(structured_data)
            processed_df.to_csv(processed_file, index=False)
            
            return {
                "success": True, 
                "data": structured_data, 
                "processed_file": processed_file
            }
        except Exception as e:
            print(f"Error parsing CSV: {e}")
            return None

    def delete_file(self, file_path: str) -> bool:
        """
        Delete a file
        """
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
                return True
            return False
        except Exception as e:
            print(f"Error deleting file {file_path}: {e}")
            return False

    def cleanup_old_files(self, max_age_hours: int = 24) -> int:
        """
        Clean up old files from upload directory
        """
        try:
            import time
            current_time = time.time()
            max_age_seconds = max_age_hours * 3600
            cleaned_count = 0
            
            for filename in os.listdir(self.upload_dir):
                file_path = os.path.join(self.upload_dir, filename)
                if os.path.isfile(file_path):
                    file_age = current_time - os.path.getmtime(file_path)
                    if file_age > max_age_seconds:
                        os.remove(file_path)
                        cleaned_count += 1
            
            return cleaned_count
        except Exception as e:
            print(f"Error during cleanup: {e}")
            return 0
