from __future__ import annotations

import json
from typing import Any, Dict, List, Optional
import os
import asyncio
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

# Import config for centralized settings
try:
    from src.core.config import settings
    HAS_CONFIG = True
except ImportError:
    HAS_CONFIG = False


class LLMReportAgent:
    
    def __init__(self, model_name: str = "gemini-1.5-flash", temperature: float = 0.0,system_instruction:str | None  = None):
        # Try to get API key from config first, then environment
        if HAS_CONFIG:
            api_key = getattr(settings, 'GEMINI_API_KEY', None)
            if not api_key:
                # Fallback to environment
                api_key = os.getenv("GEMINI_API_KEY")
        else:
            # Fallback to environment only
            api_key = os.getenv("GEMINI_API_KEY")
        
        if not api_key:
            raise ValueError("GEMINI_API_KEY environment variable not set. Please add it to your .env file")

        genai.configure(api_key=api_key)
        self.model_name = model_name
        self.temperature = temperature

        
        self.model = genai.GenerativeModel(
            model_name=model_name,
            generation_config={
                "temperature": temperature,
            },
            system_instruction=system_instruction
        )

    
    def _build_prompt(self, agent_input: Optional[Dict[str, Any]] = None) -> str:
        parts: List[str] = []
        parts.append(
            "You are a clinical nutrition assistant. Produce a structured JSON output following the LLM-report schema exactly.\n"
            "The analysis schema MUST be a single JSON object with these top-level fields:\n"
            "- analysis: object with (these fields are required):\n"
            "    - interpretation: short paragraph summarizing the key findings and interpretation of results\n"
            "    - lifestyle_changes: list of short actionable suggestions (e.g., '30 min walk daily' for high sugar)\n"
            "    - nutritional_changes: list of short actionable nutritional suggestions (e.g., 'increase iron-rich foods')\n"
            "    - symptom_probable_cause: optional short string if symptoms provided, otherwise null\n"
            "    - next_steps: list of prioritized next steps (e.g., 'consult a doctor', 'repeat test in 3 months')\n"
            "    - concern_options: list of nutrients or vitamins that are concerns/options (strings) which is basically the test fields that you think are most abnormal the user can choose from (3-6 items)\n"
        )

        agent_input = agent_input or {}

        biodata = agent_input.get("biodata")
        if biodata:
            parts.append("BioData (from user profile):\n" + json.dumps(biodata, default=str, indent=2))

        favorites = agent_input.get("favorites")
        if favorites:
            parts.append("Favorites / preferences:\n" + json.dumps(favorites, default=str, indent=2))

        if favorites:
            parts.append(
                "Guidelines based on user preferences:\n"
                "   - Prefer recommendations aligned with Favorites\n"
                "   - Avoid repeating items already in Favorites unless clinically critical\n"
            )

        metrics = agent_input.get("input") or []
        parts.append("Parsed metrics (input):\n" + json.dumps(metrics, default=str, indent=2))


        parts.append(
            "Respond ONLY with a single valid JSON object that exactly follows the LLM-report schema above.\n"
            "Return keys exactly as specified and avoid extra narrative. If you cannot provide a value, use null or an empty list/object.\n"
            "Provide `concern_options` as 3-6 short string items. Ensure output is valid JSON and parsable."
        )

        return "\n\n".join(parts)

    async def analyze(self, agent_input : Optional[Dict[str, Any]] = None) -> Dict[str, Any]:

        prompt = self._build_prompt(agent_input)

        full_prompt = (
            "You are a helpful clinical nutrition assistant.\n\n"
            f"{prompt}"
        )

        # Gemini SDK is synchronous → run in thread
        response = await asyncio.to_thread(
            self.model.generate_content,
            full_prompt
        )

        text = response.text if hasattr(response, "text") else str(response)
        parsed: Dict[str, Any]
        try:
            parsed = json.loads(text)
        except Exception:
            import re

            m = re.search(r"\{[\s\S]*\}", text)
            if m:
                try:
                    parsed = json.loads(m.group(0))
                except Exception:
                    parsed = {"error": "failed_to_parse_model_output", "raw": text}
            else:
                parsed = {"error": "no_json_in_response", "raw": text}

        def ensure_list(v: Any) -> List[Any]:
            if v is None:
                return []
            if isinstance(v, list):
                return v
            # if its a comma separated string
            if isinstance(v, str):
                return [s for s in v.split("\n") if s] if "\n" in v else [s for s in v.split(",") if s]
            return [v]

        output_candidate = None
        if isinstance(parsed, dict):
            expected_keys = {"interpretation", "lifestyle_changes", "nutritional_changes", "symptom_probable_cause", "next_steps", "concern_options"}
            if expected_keys.issubset(set(parsed.keys())):
                output_candidate = parsed
            else:
                for key in ("output", "analysis", "result", "llm_report"):
                    if key in parsed and isinstance(parsed[key], dict):
                        output_candidate = parsed[key]
                        break
        
        #if key name changes happened
        if output_candidate is None:
            output_candidate = {}

            if isinstance(parsed, dict):
                output_candidate["interpretation"] = parsed.get("interpretation") or parsed.get("summary") or parsed.get("explain") or parsed.get("analysis")
                output_candidate["lifestyle_changes"] = parsed.get("lifestyle_changes") or (parsed.get("advise") and parsed.get("advise").get("lifestyle_advice") if parsed.get("advise") else None)
                output_candidate["nutritional_changes"] = parsed.get("nutritional_changes") or (parsed.get("advise") and parsed.get("advise").get("nutritional_advice") if parsed.get("advise") else None)
                output_candidate["symptom_probable_cause"] = parsed.get("symptom_probable_cause") or parsed.get("probable_cause")
                output_candidate["next_steps"] = parsed.get("next_steps") or parsed.get("recommendations") or parsed.get("recommend")
                output_candidate["concern_options"] = parsed.get("concern_options") or parsed.get("concerns")


        final_output: Dict[str, Any] = {}
        final_output["interpretation"] = output_candidate.get("interpretation") or (str(parsed.get("summary")) if isinstance(parsed, dict) and parsed.get("summary") else None)
        final_output["lifestyle_changes"] = ensure_list(output_candidate.get("lifestyle_changes"))
        final_output["nutritional_changes"] = ensure_list(output_candidate.get("nutritional_changes"))
        final_output["symptom_probable_cause"] = output_candidate.get("symptom_probable_cause") if output_candidate.get("symptom_probable_cause") else None
        final_output["next_steps"] = ensure_list(output_candidate.get("next_steps"))
        concern_options = ensure_list(output_candidate.get("concern_options"))
       
        favorites_list: List[str] = []
        if isinstance(agent_input, dict):
            favorites_list = ensure_list(agent_input.get("favorites"))

        # if concern options are already in fav remove
        for fav in favorites_list:
            if fav in concern_options:
                concern_options.remove(fav)

        final_output["concern_options"] = concern_options
        return final_output

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

    async def generate_actionable_suggestions(self, meta_input: dict):
        prompt = f"""
            You are a health AI assistant.

            You are given {meta_input.get("report_count")} recent medical reports
            with their AI analyses (some analyses may be missing).

            Rules:
            - If only 1 report exists → base suggestions on it
            - If more than 1 report → detect trends
            - If more than 5 reports were uploaded overall → only latest 5 are included
            - Always prioritize the most recent report
            - Generate 4-6 concise, practical actionable suggestions
            - Avoid repetition

            Data:
            {json.dumps(meta_input, indent=2)}

            Return ONLY valid JSON:
            {{"actionable_suggestions": [string]}}
        """

        response = await asyncio.to_thread(
            self.model.generate_content,
            prompt
        )

        text = response.text if hasattr(response, "text") else str(response)

        try:
            parsed = json.loads(text)
            return parsed
        except Exception:
            import re
            match = re.search(r"\{[\s\S]*\}", text)
            if match:
                try:
                    return json.loads(match.group(0))
                except Exception:
                    pass

        return {"actionable_suggestions": []}



if __name__ == "__main__":
    print("This module provides LLMReportAgent for use by FastAPI routers. Run the API server instead of this file.")
