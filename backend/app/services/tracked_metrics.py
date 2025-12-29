"""
Tracked Metrics Service for managing patient metric tracking and trend analysis
"""

from typing import Any, Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from statistics import mean, stdev
import logging

from app.services.database import db_service
from app.models.report import MetricData

logger = logging.getLogger(__name__)


class TrackedMetricsService:
    """Service for managing tracked metrics and trend analysis"""
    
    def __init__(self):
        self.db_service = db_service
    
    async def add_metric_to_tracking(self, patient_id: str, metric_name: str) -> bool:
        """Add a metric to patient's tracked metrics (favorites)"""
        try:
            # Get current patient data
            patient = await self.db_service.get_user_by_uid(patient_id)
            if not patient:
                logger.error(f"Patient {patient_id} not found")
                return False
            
            # Get current favorites and add new metric if not already present
            current_favorites = patient.get("favorites", [])
            if metric_name not in current_favorites:
                current_favorites.append(metric_name)
                
                # Update patient's favorites
                success = await self.db_service.update_user_favorites(patient_id, current_favorites)
                if success:
                    logger.info(f"Added metric '{metric_name}' to tracking for patient {patient_id}")
                return success
            
            return True  # Already tracked
            
        except Exception as e:
            logger.error(f"Failed to add metric to tracking: {e}")
            raise
    
    async def remove_metric_from_tracking(self, patient_id: str, metric_name: str) -> bool:
        """Remove a metric from patient's tracked metrics"""
        try:
            # Get current patient data
            patient = await self.db_service.get_user_by_uid(patient_id)
            if not patient:
                logger.error(f"Patient {patient_id} not found")
                return False
            
            # Remove metric from favorites if present
            current_favorites = patient.get("favorites", [])
            if metric_name in current_favorites:
                current_favorites.remove(metric_name)
                
                # Update patient's favorites
                success = await self.db_service.update_user_favorites(patient_id, current_favorites)
                if success:
                    logger.info(f"Removed metric '{metric_name}' from tracking for patient {patient_id}")
                return success
            
            return True  # Already not tracked
            
        except Exception as e:
            logger.error(f"Failed to remove metric from tracking: {e}")
            raise
    
    async def get_tracked_metrics(self, patient_id: str) -> List[str]:
        """Get list of tracked metrics for a patient"""
        try:
            patient = await self.db_service.get_user_by_uid(patient_id)
            if not patient:
                return []
            
            return patient.get("favorites", [])
            
        except Exception as e:
            logger.error(f"Failed to get tracked metrics for patient {patient_id}: {e}")
            raise
    
    async def get_metric_time_series_data(self, patient_id: str, metric_name: str, 
                                        days_back: int = 365) -> List[Dict[str, Any]]:
        """Get time-series data for a specific metric"""
        try:
            # Get reports for the patient within the time range
            cutoff_date = datetime.utcnow() - timedelta(days=days_back)
            
            # Get all reports for the patient
            reports = await self.db_service.get_reports_by_patient_id(patient_id, limit=1000)
            
            # Filter reports by date and extract metric data
            time_series_data = []
            for report in reports:
                if report.get("processed_at") and report["processed_at"] >= cutoff_date:
                    attributes = report.get("attributes", {})
                    if metric_name in attributes:
                        metric_data = attributes[metric_name]
                        
                        # Try to convert value to float for numerical analysis
                        value = metric_data.get("value")
                        numeric_value = None
                        if value:
                            try:
                                numeric_value = float(value)
                            except (ValueError, TypeError):
                                pass
                        
                        time_series_data.append({
                            "date": report["processed_at"],
                            "report_id": report["report_id"],
                            "value": value,
                            "numeric_value": numeric_value,
                            "unit": metric_data.get("unit"),
                            "range": metric_data.get("range"),
                            "verdict": metric_data.get("verdict"),
                            "remark": metric_data.get("remark")
                        })
            
            # Sort by date (oldest first)
            time_series_data.sort(key=lambda x: x["date"])
            
            return time_series_data
            
        except Exception as e:
            logger.error(f"Failed to get time series data for metric {metric_name}: {e}")
            raise
    
    async def analyze_metric_trend(self, patient_id: str, metric_name: str, 
                                 days_back: int = 365) -> Dict[str, Any]:
        """Analyze trend for a specific metric"""
        try:
            # Get time series data
            time_series = await self.get_metric_time_series_data(patient_id, metric_name, days_back)
            
            if not time_series:
                return {
                    "metric_name": metric_name,
                    "trend": "no_data",
                    "data_points": 0,
                    "message": "No data available for this metric"
                }
            
            # Extract numeric values for trend analysis
            numeric_values = [point["numeric_value"] for point in time_series 
                            if point["numeric_value"] is not None]
            
            if len(numeric_values) < 2:
                return {
                    "metric_name": metric_name,
                    "trend": "insufficient_data",
                    "data_points": len(time_series),
                    "latest_value": time_series[-1]["value"] if time_series else None,
                    "latest_date": time_series[-1]["date"] if time_series else None,
                    "message": "Insufficient numeric data for trend analysis"
                }
            
            # Calculate trend statistics
            latest_value = numeric_values[-1]
            earliest_value = numeric_values[0]
            mean_value = mean(numeric_values)
            
            # Calculate trend direction
            trend_direction = "stable"
            change_percentage = 0
            
            if earliest_value != 0:
                change_percentage = ((latest_value - earliest_value) / earliest_value) * 100
                
                if change_percentage > 5:
                    trend_direction = "increasing"
                elif change_percentage < -5:
                    trend_direction = "decreasing"
            
            # Calculate variability
            variability = "low"
            if len(numeric_values) > 2:
                std_dev = stdev(numeric_values)
                coefficient_of_variation = (std_dev / mean_value) * 100 if mean_value != 0 else 0
                
                if coefficient_of_variation > 20:
                    variability = "high"
                elif coefficient_of_variation > 10:
                    variability = "moderate"
            
            # Analyze recent trend (last 3 data points)
            recent_trend = "stable"
            if len(numeric_values) >= 3:
                recent_values = numeric_values[-3:]
                if all(recent_values[i] < recent_values[i+1] for i in range(len(recent_values)-1)):
                    recent_trend = "improving"
                elif all(recent_values[i] > recent_values[i+1] for i in range(len(recent_values)-1)):
                    recent_trend = "worsening"
            
            return {
                "metric_name": metric_name,
                "trend": trend_direction,
                "recent_trend": recent_trend,
                "data_points": len(time_series),
                "numeric_data_points": len(numeric_values),
                "latest_value": latest_value,
                "earliest_value": earliest_value,
                "mean_value": round(mean_value, 2),
                "change_percentage": round(change_percentage, 2),
                "variability": variability,
                "latest_date": time_series[-1]["date"],
                "earliest_date": time_series[0]["date"],
                "unit": time_series[-1]["unit"],
                "latest_verdict": time_series[-1]["verdict"]
            }
            
        except Exception as e:
            logger.error(f"Failed to analyze trend for metric {metric_name}: {e}")
            raise
    
    async def get_dashboard_data(self, patient_id: str, days_back: int = 365) -> Dict[str, Any]:
        """Get comprehensive dashboard data for tracked metrics"""
        try:
            # Get tracked metrics for the patient
            tracked_metrics = await self.get_tracked_metrics(patient_id)
            
            if not tracked_metrics:
                return {
                    "patient_id": patient_id,
                    "tracked_metrics": [],
                    "trends": {},
                    "time_series": {},
                    "summary": {
                        "total_tracked": 0,
                        "improving": 0,
                        "worsening": 0,
                        "stable": 0
                    }
                }
            
            # Get trend analysis for each tracked metric
            trends = {}
            time_series = {}
            summary_counts = {"improving": 0, "worsening": 0, "stable": 0}
            
            for metric_name in tracked_metrics:
                # Get trend analysis
                trend_analysis = await self.analyze_metric_trend(patient_id, metric_name, days_back)
                trends[metric_name] = trend_analysis
                
                # Get time series data
                metric_time_series = await self.get_metric_time_series_data(patient_id, metric_name, days_back)
                time_series[metric_name] = metric_time_series
                
                # Update summary counts
                recent_trend = trend_analysis.get("recent_trend", "stable")
                if recent_trend in summary_counts:
                    summary_counts[recent_trend] += 1
            
            return {
                "patient_id": patient_id,
                "tracked_metrics": tracked_metrics,
                "trends": trends,
                "time_series": time_series,
                "summary": {
                    "total_tracked": len(tracked_metrics),
                    **summary_counts
                },
                "generated_at": datetime.utcnow()
            }
            
        except Exception as e:
            logger.error(f"Failed to get dashboard data for patient {patient_id}: {e}")
            raise
    
    async def generate_actionable_advice(self, patient_id: str, limit_reports: int = 5) -> List[str]:
        """Generate actionable advice based on tracked metrics trends"""
        try:
            # Get recent reports for context
            recent_reports = await self.db_service.get_reports_by_patient_id(patient_id, limit=limit_reports)
            
            if not recent_reports:
                return ["No recent reports available for analysis."]
            
            # Get tracked metrics
            tracked_metrics = await self.get_tracked_metrics(patient_id)
            
            if not tracked_metrics:
                return ["No metrics are currently being tracked. Consider adding concerning values to your tracked metrics."]
            
            advice = []
            
            # Analyze each tracked metric for advice
            for metric_name in tracked_metrics:
                trend_analysis = await self.analyze_metric_trend(patient_id, metric_name, days_back=90)
                
                if trend_analysis["trend"] == "no_data":
                    continue
                
                latest_verdict = trend_analysis.get("latest_verdict", "").upper()
                recent_trend = trend_analysis.get("recent_trend", "stable")
                change_percentage = trend_analysis.get("change_percentage", 0)
                
                # Generate specific advice based on trend and verdict
                if latest_verdict in ["HIGH", "CRITICAL"] and recent_trend == "worsening":
                    advice.append(f"{metric_name}: Values are elevated and worsening ({change_percentage:+.1f}% change). Consider consulting your healthcare provider for management strategies.")
                
                elif latest_verdict in ["LOW", "CRITICAL"] and recent_trend == "worsening":
                    advice.append(f"{metric_name}: Values are low and declining ({change_percentage:+.1f}% change). Discuss supplementation or dietary changes with your doctor.")
                
                elif recent_trend == "improving" and abs(change_percentage) > 10:
                    advice.append(f"{metric_name}: Showing positive improvement ({change_percentage:+.1f}% change). Continue current lifestyle modifications.")
                
                elif trend_analysis["variability"] == "high":
                    advice.append(f"{metric_name}: Values show high variability. Focus on consistency in diet, exercise, and medication adherence.")
                
                elif latest_verdict == "NORMAL" and recent_trend == "stable":
                    advice.append(f"{metric_name}: Maintaining healthy levels. Continue current health practices.")
            
            # Add general advice if no specific advice generated
            if not advice:
                advice.append("Your tracked metrics show stable patterns. Continue regular monitoring and maintain healthy lifestyle habits.")
            
            # Limit to most important advice
            return advice[:5]
            
        except Exception as e:
            logger.error(f"Failed to generate actionable advice for patient {patient_id}: {e}")
            raise


# Global tracked metrics service instance
tracked_metrics_service = TrackedMetricsService()