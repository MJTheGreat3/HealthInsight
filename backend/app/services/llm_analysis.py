"""
LLM Analysis Service for generating lifestyle advice from medical test results.

This service integrates with OpenAI's API to analyze medical test data and generate
comprehensive lifestyle recommendations, nutritional advice, and health insights
without providing medical prescriptions.
"""

import json
import logging
from typing import Any, Dict, List, Optional
from datetime import datetime
import datetime as dt

import openai
from openai import OpenAI

from app.models.report import MetricData, LLMReportModel
from app.models.user import PatientModel
from app.core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class LLMAnalysisService:
    """Service for generating AI-powered health analysis and lifestyle advice."""
    
    def __init__(self):
        """Initialize the LLM Analysis Service with OpenAI client."""
        self.client = OpenAI(api_key=settings.OPENAI_API_KEY)
        self.model = "gpt-3.5-turbo"  # Using GPT-3.5 for cost efficiency
        self.max_tokens = 1500
        self.temperature = 0.3  # Lower temperature for more consistent medical advice
    
    async def analyze_test_results(
        self,
        patient_id: str,
        report_id: str,
        test_data: Dict[str, MetricData],
        patient_profile: Optional[PatientModel] = None
    ) -> LLMReportModel:
        """
        Generate comprehensive health analysis from medical test results.
        
        Args:
            patient_id: Unique patient identifier
            report_id: Unique report identifier
            test_data: Dictionary of medical test results
            patient_profile: Optional patient profile for personalized advice
            
        Returns:
            LLMReportModel containing AI-generated analysis and advice
            
        Raises:
            Exception: If OpenAI API call fails or analysis generation fails
        """
        try:
            # Prepare input data for analysis
            input_data = {
                "attributes": {k: v.model_dump() for k, v in test_data.items()},
                "bio_data": patient_profile.bio_data if patient_profile else {}
            }
            
            # Generate the analysis prompt
            prompt = self._create_analysis_prompt(test_data, patient_profile)
            
            # Call OpenAI API
            response = await self._call_openai_api(prompt)
            
            # Parse and structure the response
            analysis_output = self._parse_analysis_response(response)
            
            # Create LLM report model
            llm_report = LLMReportModel(
                patient_id=patient_id,
                report_id=report_id,
                time=datetime.now(dt.timezone.utc).isoformat(),
                output=analysis_output,
                input=input_data
            )
            
            logger.info(f"Generated LLM analysis for patient {patient_id}, report {report_id}")
            return llm_report
            
        except Exception as e:
            logger.error(f"Failed to generate LLM analysis: {str(e)}")
            raise Exception(f"AI analysis generation failed: {str(e)}")
    
    def _create_analysis_prompt(
        self,
        test_data: Dict[str, MetricData],
        patient_profile: Optional[PatientModel] = None
    ) -> str:
        """Create a structured prompt for medical test analysis."""
        
        # Extract problematic values
        problematic_values = []
        normal_values = []
        
        for key, metric in test_data.items():
            if metric.verdict in ["HIGH", "LOW", "CRITICAL"]:
                problematic_values.append({
                    "name": metric.name or key,
                    "value": metric.value,
                    "range": metric.range,
                    "unit": metric.unit,
                    "verdict": metric.verdict,
                    "remark": metric.remark
                })
            else:
                normal_values.append({
                    "name": metric.name or key,
                    "value": metric.value,
                    "verdict": metric.verdict
                })
        
        # Build patient context
        patient_context = ""
        if patient_profile and patient_profile.bio_data:
            bio_data = patient_profile.bio_data
            
            # Handle allergies safely - could be a list or other type
            allergies = bio_data.get('allergies', [])
            if isinstance(allergies, list):
                allergies_str = ', '.join(allergies) if allergies else 'None reported'
            else:
                allergies_str = str(allergies) if allergies else 'None reported'
            
            patient_context = f"""
Patient Profile:
- Height: {bio_data.get('height', 'Not provided')}
- Weight: {bio_data.get('weight', 'Not provided')}
- Allergies: {allergies_str}
- Age: {bio_data.get('age', 'Not provided')}
- Gender: {bio_data.get('gender', 'Not provided')}
"""
        
        prompt = f"""
You are a health analysis AI assistant. Analyze the following medical test results and provide comprehensive lifestyle advice. 

IMPORTANT GUIDELINES:
- DO NOT provide medical prescriptions or specific medical treatments
- DO NOT diagnose medical conditions
- Focus on lifestyle modifications, nutrition, and general wellness advice
- Suggest consulting healthcare providers for medical concerns
- Be encouraging and supportive in tone

{patient_context}

PROBLEMATIC TEST RESULTS:
{json.dumps(problematic_values, indent=2) if problematic_values else "None identified"}

NORMAL TEST RESULTS:
{json.dumps(normal_values, indent=2) if normal_values else "None"}

Please provide a comprehensive analysis in the following JSON format:
{{
    "lifestyle_recommendations": [
        "Specific lifestyle changes to address concerning values",
        "Exercise recommendations based on test results",
        "Sleep and stress management advice"
    ],
    "nutritional_advice": [
        "Specific foods to include or avoid",
        "Dietary patterns that may help",
        "Hydration and supplement considerations"
    ],
    "symptom_explanations": [
        "What the concerning values might indicate",
        "Possible causes of abnormal results",
        "How these values relate to overall health"
    ],
    "next_steps": [
        "General recommendations for follow-up",
        "When to consult healthcare providers",
        "Monitoring suggestions"
    ],
    "positive_aspects": [
        "Values that are in healthy ranges",
        "Encouraging observations from the results"
    ]
}}

Ensure all advice is general, evidence-based, and emphasizes the importance of professional medical consultation for specific concerns.
"""
        
        return prompt
    
    async def _call_openai_api(self, prompt: str) -> str:
        """Make API call to OpenAI and return the response."""
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a helpful health analysis assistant that provides lifestyle advice based on medical test results. You never provide medical prescriptions or diagnoses."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                max_tokens=self.max_tokens,
                temperature=self.temperature,
                response_format={"type": "json_object"}
            )
            
            return response.choices[0].message.content
            
        except openai.RateLimitError:
            logger.warning("OpenAI rate limit exceeded, implementing backoff")
            raise Exception("AI service temporarily unavailable due to rate limits")
        except openai.APIError as e:
            logger.error(f"OpenAI API error: {str(e)}")
            raise Exception("AI service temporarily unavailable")
        except Exception as e:
            logger.error(f"Unexpected error calling OpenAI API: {str(e)}")
            raise Exception("AI analysis service error")
    
    def _parse_analysis_response(self, response: str) -> Dict[str, Any]:
        """Parse and validate the OpenAI response."""
        try:
            analysis = json.loads(response)
            
            # Validate required fields
            required_fields = [
                "lifestyle_recommendations",
                "nutritional_advice", 
                "symptom_explanations",
                "next_steps"
            ]
            
            for field in required_fields:
                if field not in analysis:
                    analysis[field] = []
                elif not isinstance(analysis[field], list):
                    analysis[field] = [str(analysis[field])]
            
            # Apply safety filtering
            analysis = self._apply_safety_filters(analysis)
            
            # Ensure positive_aspects exists
            if "positive_aspects" not in analysis:
                analysis["positive_aspects"] = []
            
            # Add safety disclaimer
            analysis["disclaimer"] = (
                "This analysis is for informational purposes only and should not "
                "replace professional medical advice. Please consult with your "
                "healthcare provider for medical concerns."
            )
            
            return analysis
            
        except json.JSONDecodeError:
            logger.error("Failed to parse OpenAI response as JSON")
            return self._create_fallback_analysis()
        except Exception as e:
            logger.error(f"Error parsing analysis response: {str(e)}")
            return self._create_fallback_analysis()
    
    def _apply_safety_filters(self, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Apply safety filters to remove medical prescriptions and inappropriate content."""
        
        # Define forbidden patterns for medical prescriptions and dangerous advice
        forbidden_patterns = [
            # Medical prescriptions
            r'\b\d+\s*mg\b',  # Dosages like "20mg", "500 mg"
            r'\btake\s+\w+\s+daily\b',  # "take X daily"
            r'\bprescribe\b',  # "prescribe"
            r'\bprescribed\s+medication\b',  # "prescribed medication"
            r'\bstart\s+\w+\s+therapy\b',  # "start insulin therapy"
            r'\bstop\s+taking\s+all\b',  # "stop taking all"
            r'\btwice\s+daily\b',  # "twice daily"
            r'\bonce\s+daily\b',  # "once daily"
            
            # Specific medications
            r'\blipitor\b', r'\bmetformin\b', r'\binsulin\b', 
            r'\bantibiotic\b', r'\bsteroid\b',
            r'\bstatin\s+therapy\b',  # "statin therapy" but not just "statin"
            
            # Dangerous advice
            r'\bdefinitely\s+have\b',  # "definitely have diabetes"
            r'\bneed\s+insulin\b',  # "need insulin"
            r'\bavoid\s+all\s+\w+\s+completely\b',  # "avoid all carbohydrates completely"
            r'\bstop\s+all\s+medications?\b',  # "stop all medications"
        ]
        
        import re
        
        # Filter each field
        for field in ["lifestyle_recommendations", "nutritional_advice", "symptom_explanations", "next_steps"]:
            if field in analysis and isinstance(analysis[field], list):
                filtered_items = []
                for item in analysis[field]:
                    if isinstance(item, str):
                        # Check if item contains forbidden patterns
                        item_lower = item.lower()
                        contains_forbidden = False
                        
                        for pattern in forbidden_patterns:
                            if re.search(pattern, item_lower, re.IGNORECASE):
                                contains_forbidden = True
                                logger.warning(f"Filtered out content: {item[:50]}...")
                                break
                        
                        if not contains_forbidden:
                            filtered_items.append(item)
                        else:
                            # Replace with safe alternative if it's a critical field
                            if field == "next_steps" and not filtered_items:
                                filtered_items.append("Consult with your healthcare provider for personalized advice")
                
                analysis[field] = filtered_items
        
        return analysis
    
    def _create_fallback_analysis(self) -> Dict[str, Any]:
        """Create a fallback analysis when AI generation fails."""
        return {
            "lifestyle_recommendations": [
                "Maintain a balanced diet with plenty of fruits and vegetables",
                "Engage in regular physical activity as appropriate for your health",
                "Ensure adequate sleep and manage stress levels"
            ],
            "nutritional_advice": [
                "Follow a balanced diet rich in whole foods",
                "Stay adequately hydrated throughout the day",
                "Consider consulting a nutritionist for personalized advice"
            ],
            "symptom_explanations": [
                "Test results should be interpreted by qualified healthcare professionals",
                "Multiple factors can influence test values including diet, exercise, and treatments"
            ],
            "next_steps": [
                "Schedule a follow-up appointment with your healthcare provider",
                "Discuss these results with your doctor for proper interpretation",
                "Continue monitoring your health as recommended by your physician"
            ],
            "positive_aspects": [
                "Taking proactive steps to monitor your health is commendable"
            ],
            "disclaimer": (
                "This is a fallback analysis. Please consult with your healthcare "
                "provider for proper interpretation of your test results."
            ),
            "error_note": "AI analysis temporarily unavailable - showing general health advice"
        }
    
    async def generate_trend_analysis(
        self,
        patient_id: str,
        tracked_metrics: List[str],
        recent_reports: List[Dict[str, Any]],
        patient_profile: Optional[PatientModel] = None
    ) -> Dict[str, Any]:
        """
        Generate trend analysis for tracked metrics across multiple reports.
        
        Args:
            patient_id: Unique patient identifier
            tracked_metrics: List of metric names being tracked
            recent_reports: List of recent report data (max 5)
            patient_profile: Optional patient profile for context
            
        Returns:
            Dictionary containing trend analysis and recommendations
        """
        try:
            # Prepare trend data
            trend_data = self._prepare_trend_data(tracked_metrics, recent_reports)
            
            # Create trend analysis prompt
            prompt = self._create_trend_prompt(trend_data, patient_profile)
            
            # Call OpenAI API
            response = await self._call_openai_api(prompt)
            
            # Parse response
            trend_analysis = json.loads(response)
            
            logger.info(f"Generated trend analysis for patient {patient_id}")
            return trend_analysis
            
        except Exception as e:
            logger.error(f"Failed to generate trend analysis: {str(e)}")
            return self._create_fallback_trend_analysis()
    
    def _prepare_trend_data(
        self,
        tracked_metrics: List[str],
        recent_reports: List[Dict[str, Any]]
    ) -> Dict[str, List[Dict[str, Any]]]:
        """Prepare trend data for analysis."""
        trend_data = {}
        
        for metric_name in tracked_metrics:
            metric_history = []
            
            for report in recent_reports:
                attributes = report.get("attributes", {})
                for key, metric_data in attributes.items():
                    if (metric_data.get("name") == metric_name or 
                        key.replace("_", " ").upper() == metric_name.upper()):
                        metric_history.append({
                            "date": report.get("processed_at"),
                            "value": metric_data.get("value"),
                            "verdict": metric_data.get("verdict"),
                            "range": metric_data.get("range"),
                            "unit": metric_data.get("unit")
                        })
                        break
            
            if metric_history:
                trend_data[metric_name] = sorted(
                    metric_history, 
                    key=lambda x: x["date"]
                )
        
        return trend_data
    
    def _create_trend_prompt(
        self,
        trend_data: Dict[str, List[Dict[str, Any]]],
        patient_profile: Optional[PatientModel] = None
    ) -> str:
        """Create prompt for trend analysis."""
        
        patient_context = ""
        if patient_profile and patient_profile.bio_data:
            bio_data = patient_profile.bio_data
            patient_context = f"""
Patient Profile:
- Height: {bio_data.get('height', 'Not provided')}
- Weight: {bio_data.get('weight', 'Not provided')}
- Age: {bio_data.get('age', 'Not provided')}
"""
        
        prompt = f"""
Analyze the following health metric trends over time and provide actionable insights.

{patient_context}

TRACKED METRICS OVER TIME:
{json.dumps(trend_data, indent=2, default=str)}

Provide analysis in the following JSON format:
{{
    "trend_summary": [
        "Overall trend observations",
        "Key patterns identified"
    ],
    "improving_metrics": [
        "Metrics showing positive trends",
        "Specific improvements noted"
    ],
    "concerning_trends": [
        "Metrics showing negative trends",
        "Areas requiring attention"
    ],
    "actionable_advice": [
        "Specific actions to maintain good trends",
        "Recommendations to address concerning trends"
    ],
    "monitoring_suggestions": [
        "Frequency of monitoring recommendations",
        "Key metrics to watch closely"
    ]
}}

Focus on practical, actionable advice while emphasizing the importance of professional medical consultation.
"""
        
        return prompt
    
    def _create_fallback_trend_analysis(self) -> Dict[str, Any]:
        """Create fallback trend analysis when AI generation fails."""
        return {
            "trend_summary": [
                "Trend analysis temporarily unavailable",
                "Please consult your healthcare provider for trend interpretation"
            ],
            "improving_metrics": [],
            "concerning_trends": [],
            "actionable_advice": [
                "Continue regular health monitoring",
                "Maintain healthy lifestyle habits",
                "Consult healthcare provider for trend analysis"
            ],
            "monitoring_suggestions": [
                "Follow your healthcare provider's monitoring schedule",
                "Keep track of any symptoms or changes"
            ],
            "error_note": "AI trend analysis temporarily unavailable"
        }


# Global service instance
llm_analysis_service = LLMAnalysisService()