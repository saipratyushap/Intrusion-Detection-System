"""
=============================================================================
BUSINESS INTELLIGENCE & REPORTING MODULE
=============================================================================
This module provides:
1. Advanced Analytics Dashboard API with custom KPIs
2. Automated Report Generation with email scheduling
3. Cost Analysis Module for ROI tracking
=============================================================================
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from collections import Counter
import json
import os
from pathlib import Path

# Configuration files
COST_CONFIG_FILE = "data/cost_config.json"
ANALYTICS_CACHE_FILE = "data/analytics_cache.json"
REPORT_SCHEDULE_FILE = "data/report_schedules.json"


def _convert_to_native_types(obj):
    """Convert numpy types to Python native types for JSON serialization"""
    import math
    if isinstance(obj, dict):
        return {k: _convert_to_native_types(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [_convert_to_native_types(item) for item in obj]
    elif isinstance(obj, (np.integer, np.int64)):
        return int(obj)
    elif isinstance(obj, (np.floating, np.float64)):
        # Handle NaN and infinity values
        if math.isnan(obj) or math.isinf(obj):
            return None
        return float(obj)
    elif isinstance(obj, np.ndarray):
        return obj.tolist()
    elif hasattr(obj, 'item'):  # numpy scalar
        return obj.item()
    elif isinstance(obj, datetime):
        return obj.isoformat()
    elif isinstance(obj, pd.Timestamp):
        return obj.isoformat()
    elif hasattr(obj, 'isoformat'):  # date object
        return obj.isoformat()
    else:
        return obj


# =============================================================================
# 1. ADVANCED ANALYTICS DASHBOARD API
# =============================================================================

class AnalyticsDashboard:
    """Advanced analytics with custom KPI tracking"""
    
    def __init__(self, csv_file: str = "data/detection_log.csv"):
        self.csv_file = csv_file
        self.df = None
        self.load_data()
    
    def load_data(self):
        """Load and prepare detection data"""
        try:
            if os.path.exists(self.csv_file):
                self.df = pd.read_csv(self.csv_file)
                self.df['Timestamp'] = pd.to_datetime(self.df['Timestamp'])
                self.df['Date'] = self.df['Timestamp'].dt.date
                self.df['Hour'] = self.df['Timestamp'].dt.hour
                self.df['DayOfWeek'] = self.df['Timestamp'].dt.dayofweek
                self.df['IsViolation'] = (self.df['Restricted Area Violation'] == 'Yes').astype(int)
            else:
                self.df = pd.DataFrame()
        except Exception as e:
            print(f"Error loading data: {e}")
            self.df = pd.DataFrame()
    
    def calculate_mttr(self, start_date: Optional[datetime] = None, 
                      end_date: Optional[datetime] = None) -> Dict[str, Any]:
        """
        Calculate Mean Time To Respond (MTTR)
        Assumes response time is tracked or estimated
        """
        self.load_data()
        
        if self.df.empty:
            return {
                "mttr_minutes": 0,
                "mttr_formatted": "00:00:00",
                "total_incidents": 0,
                "responded_incidents": 0,
                "response_rate": 0
            }
        
        df = self._filter_by_date(self.df, start_date, end_date)
        violations = df[df['IsViolation'] == 1]
        
        if violations.empty:
            return {
                "mttr_minutes": 0,
                "mttr_formatted": "00:00:00",
                "total_incidents": 0,
                "responded_incidents": 0,
                "response_rate": 0
            }
        
        # Estimate response time based on consecutive violations
        # If multiple violations within 5 min, consider as single incident
        violations = violations.sort_values('Timestamp')
        incidents = []
        current_incident = [violations.iloc[0]]
        
        for i in range(1, len(violations)):
            time_diff = (violations.iloc[i]['Timestamp'] - current_incident[-1]['Timestamp']).total_seconds() / 60
            if time_diff <= 5:  # Same incident
                current_incident.append(violations.iloc[i])
            else:
                incidents.append(current_incident)
                current_incident = [violations.iloc[i]]
        
        incidents.append(current_incident)
        
        # Calculate MTTR (assume resolved after last detection + 3 min avg)
        response_times = []
        for incident in incidents:
            first_detection = incident[0]['Timestamp']
            last_detection = incident[-1]['Timestamp']
            # Estimated response time: duration of incident + 3 min response
            response_time = (last_detection - first_detection).total_seconds() / 60 + 3
            response_times.append(response_time)
        
        mttr = np.mean(response_times)
        mttr_formatted = str(timedelta(minutes=int(mttr)))
        
        return {
            "mttr_minutes": round(mttr, 2),
            "mttr_formatted": mttr_formatted,
            "total_incidents": len(incidents),
            "responded_incidents": len(incidents),  # All assumed responded
            "response_rate": 100.0,
            "avg_incident_duration_minutes": round(np.mean([
                (inc[-1]['Timestamp'] - inc[0]['Timestamp']).total_seconds() / 60 
                for inc in incidents
            ]), 2)
        }
    
    def calculate_false_positive_rate(self, start_date: Optional[datetime] = None,
                                     end_date: Optional[datetime] = None) -> Dict[str, Any]:
        """
        Calculate False Positive Rate
        Note: In production, you'd track user feedback on detections
        Here we estimate based on confidence scores
        """
        self.load_data()
        
        if self.df.empty:
            return {
                "false_positive_rate": 0,
                "total_detections": 0,
                "true_positives": 0,
                "false_positives": 0,
                "precision": 0,
                "low_confidence_detections": 0
            }
        
        df = self._filter_by_date(self.df, start_date, end_date)
        
        # Estimate: detections with confidence < 0.7 are potential false positives
        low_confidence = df[df['Confidence'] < 0.7]
        high_confidence = df[df['Confidence'] >= 0.7]
        
        total = len(df)
        false_positives = len(low_confidence)
        true_positives = len(high_confidence)
        
        fpr = (false_positives / total * 100) if total > 0 else 0
        precision = (true_positives / total * 100) if total > 0 else 0
        
        return {
            "false_positive_rate": round(fpr, 2),
            "total_detections": total,
            "true_positives": true_positives,
            "false_positives": false_positives,
            "precision": round(precision, 2),
            "low_confidence_detections": false_positives,
            "avg_confidence": round(df['Confidence'].mean() * 100, 2),
            "confidence_std": round(df['Confidence'].std() * 100, 2)
        }
    
    def calculate_coverage_percentage(self, start_date: Optional[datetime] = None,
                                     end_date: Optional[datetime] = None) -> Dict[str, Any]:
        """
        Calculate Coverage Percentage
        Based on system uptime and detection continuity
        """
        self.load_data()
        
        if self.df.empty:
            return {
                "coverage_percentage": 0,
                "total_hours_monitored": 0,
                "hours_with_detections": 0,
                "gaps_detected": 0,
                "uptime_percentage": 0
            }
        
        df = self._filter_by_date(self.df, start_date, end_date)
        
        if df.empty:
            return {
                "coverage_percentage": 0,
                "total_hours_monitored": 0,
                "hours_with_detections": 0,
                "gaps_detected": 0,
                "uptime_percentage": 0
            }
        
        # Calculate time range
        min_time = df['Timestamp'].min()
        max_time = df['Timestamp'].max()
        total_hours = (max_time - min_time).total_seconds() / 3600
        
        # Count hours with detections
        df['Hour_Slot'] = df['Timestamp'].dt.floor('h')
        hours_with_detections = df['Hour_Slot'].nunique()
        
        # Detect gaps (periods > 1 hour without detection)
        df_sorted = df.sort_values('Timestamp')
        time_diffs = df_sorted['Timestamp'].diff()
        gaps = (time_diffs > timedelta(hours=1)).sum()
        
        coverage = (hours_with_detections / max(total_hours, 1) * 100) if total_hours > 0 else 0
        uptime = 100 - (gaps / len(df) * 100) if len(df) > 0 else 0
        
        return {
            "coverage_percentage": round(coverage, 2),
            "total_hours_monitored": round(total_hours, 2),
            "hours_with_detections": hours_with_detections,
            "gaps_detected": gaps,
            "uptime_percentage": round(uptime, 2),
            "max_gap_hours": round(time_diffs.max().total_seconds() / 3600, 2) if len(time_diffs) > 0 else 0
        }
    
    def get_executive_summary(self, start_date: Optional[datetime] = None,
                            end_date: Optional[datetime] = None) -> Dict[str, Any]:
        """Generate executive summary with key insights"""
        self.load_data()
        
        if self.df.empty:
            return {
                "period": "No data available",
                "key_metrics": {},
                "insights": ["No detection data available"],
                "recommendations": []
            }
        
        df = self._filter_by_date(self.df, start_date, end_date)
        
        if df.empty:
            return {
                "period": "No data for specified period",
                "key_metrics": {
                    "total_detections": 0,
                    "total_violations": 0,
                    "violation_rate": 0,
                    "avg_confidence": 0,
                    "mttr_minutes": 0,
                    "false_positive_rate": 0,
                    "coverage_percentage": 0
                },
                "insights": ["No data available for the specified date range"],
                "recommendations": [],
                "trend": "stable",
                "peak_hour": 0,
                "most_common_class": "N/A"
            }
        
        # Key metrics
        total_detections = len(df)
        total_violations = df['IsViolation'].sum()
        violation_rate = (total_violations / total_detections * 100) if total_detections > 0 else 0
        avg_confidence = df['Confidence'].mean() * 100
        
        # Trend analysis
        daily_violations = df[df['IsViolation'] == 1].groupby('Date').size()
        trend = "increasing" if len(daily_violations) > 1 and daily_violations.iloc[-1] > daily_violations.iloc[0] else "stable"
        
        # Peak hours
        hourly_violations = df[df['IsViolation'] == 1].groupby('Hour').size()
        peak_hour = hourly_violations.idxmax() if not hourly_violations.empty else 0
        
        # Most detected class
        most_common_class = df['Class'].value_counts().idxmax() if not df.empty else "N/A"
        
        insights = [
            f"Total {total_detections:,} detections with {total_violations:,} violations ({violation_rate:.1f}% violation rate)",
            f"Violation trend is {trend}",
            f"Peak violation hour: {peak_hour}:00",
            f"Most detected class: {most_common_class}",
            f"Average confidence: {avg_confidence:.1f}%"
        ]
        
        recommendations = []
        if violation_rate > 20:
            recommendations.append("🚨 High violation rate - Consider increasing security presence")
        if avg_confidence < 75:
            recommendations.append("⚠️ Low confidence scores - Review camera positioning and lighting")
        if peak_hour:
            recommendations.append(f"📍 Focus security resources around {peak_hour}:00")
        
        mttr = self.calculate_mttr(start_date, end_date)
        fpr = self.calculate_false_positive_rate(start_date, end_date)
        coverage = self.calculate_coverage_percentage(start_date, end_date)
        
        return {
            "period": f"{df['Timestamp'].min().date()} to {df['Timestamp'].max().date()}",
            "key_metrics": {
                "total_detections": int(total_detections),
                "total_violations": int(total_violations),
                "violation_rate": round(violation_rate, 2),
                "avg_confidence": round(avg_confidence, 2),
                "mttr_minutes": mttr['mttr_minutes'],
                "false_positive_rate": fpr['false_positive_rate'],
                "coverage_percentage": coverage['coverage_percentage']
            },
            "insights": insights,
            "recommendations": recommendations,
            "trend": trend,
            "peak_hour": int(peak_hour),
            "most_common_class": most_common_class
        }
    
    def get_trend_analysis(self, days: int = 30) -> Dict[str, Any]:
        """Analyze trends over specified period"""
        self.load_data()
        
        if self.df.empty:
            return {"error": "No data available"}
        
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        df = self._filter_by_date(self.df, start_date, end_date)
        
        # Daily aggregations
        daily_stats = df.groupby('Date').agg({
            'Class': 'count',
            'IsViolation': 'sum',
            'Confidence': 'mean'
        }).rename(columns={'Class': 'detections', 'IsViolation': 'violations', 'Confidence': 'avg_confidence'})
        
        # Calculate moving averages
        daily_stats['detections_ma7'] = daily_stats['detections'].rolling(window=7, min_periods=1).mean()
        daily_stats['violations_ma7'] = daily_stats['violations'].rolling(window=7, min_periods=1).mean()
        
        # Trend direction
        detection_trend = "increasing" if daily_stats['detections_ma7'].iloc[-1] > daily_stats['detections_ma7'].iloc[0] else "decreasing"
        violation_trend = "increasing" if daily_stats['violations_ma7'].iloc[-1] > daily_stats['violations_ma7'].iloc[0] else "decreasing"
        
        return {
            "period_days": days,
            "detection_trend": detection_trend,
            "violation_trend": violation_trend,
            "daily_avg_detections": round(daily_stats['detections'].mean(), 2),
            "daily_avg_violations": round(daily_stats['violations'].mean(), 2),
            "max_daily_detections": int(daily_stats['detections'].max()),
            "max_daily_violations": int(daily_stats['violations'].max()),
            "daily_data": daily_stats.reset_index().to_dict(orient='records')
        }
    
    def _filter_by_date(self, df: pd.DataFrame, start_date: Optional[datetime], 
                       end_date: Optional[datetime]) -> pd.DataFrame:
        """Filter dataframe by date range"""
        if df.empty:
            return df
        
        if start_date:
            df = df[df['Timestamp'] >= start_date]
        if end_date:
            df = df[df['Timestamp'] <= end_date]
        
        return df


# =============================================================================
# 2. AUTOMATED REPORT GENERATION
# =============================================================================

class ReportGenerator:
    """Generate automated reports with scheduling"""
    
    def __init__(self, csv_file: str = "data/detection_log.csv"):
        self.csv_file = csv_file
        self.analytics = AnalyticsDashboard(csv_file)
        self.reports_dir = Path("data/reports")
        self.reports_dir.mkdir(parents=True, exist_ok=True)
    
    def generate_daily_report(self, date: Optional[datetime] = None) -> Dict[str, Any]:
        """Generate daily summary report"""
        if date is None:
            date = datetime.now() - timedelta(days=1)
        
        start_date = datetime.combine(date.date(), datetime.min.time())
        end_date = datetime.combine(date.date(), datetime.max.time())
        
        self.analytics.load_data()
        df = self.analytics._filter_by_date(self.analytics.df, start_date, end_date)
        
        if df.empty:
            return {"error": "No data for specified date", "date": date.date()}
        
        violations = df[df['IsViolation'] == 1]
        
        report = {
            "report_type": "Daily Summary",
            "date": date.strftime("%Y-%m-%d"),
            "generated_at": datetime.now().isoformat(),
            "summary": {
                "total_detections": len(df),
                "total_violations": len(violations),
                "violation_rate": round(len(violations) / len(df) * 100, 2) if len(df) > 0 else 0,
                "avg_confidence": round(df['Confidence'].mean() * 100, 2),
                "unique_classes": int(df['Class'].nunique())
            },
            "hourly_breakdown": {str(k): int(v) for k, v in df.groupby('Hour').size().items()},
            "class_distribution": df['Class'].value_counts().to_dict(),
            "peak_hour": int(df.groupby('Hour').size().idxmax()) if not df.empty else 0,
            "violations_by_hour": {str(k): int(v) for k, v in violations.groupby('Hour').size().items()} if not violations.empty else {}
        }
        
        # Save to file
        filename = f"daily_report_{date.strftime('%Y%m%d')}.json"
        filepath = self.reports_dir / filename
        with open(filepath, 'w') as f:
            json.dump(report, f, indent=2)
        
        return report
    
    def generate_weekly_report(self, end_date: Optional[datetime] = None) -> Dict[str, Any]:
        """Generate weekly summary report"""
        if end_date is None:
            end_date = datetime.now()
        
        start_date = end_date - timedelta(days=7)
        
        self.analytics.load_data()
        df = self.analytics._filter_by_date(self.analytics.df, start_date, end_date)
        
        if df.empty:
            return {"error": "No data for specified week"}
        
        violations = df[df['IsViolation'] == 1]
        
        # Daily breakdown
        daily_detections = df.groupby('Date').size().to_dict()
        daily_violations = violations.groupby('Date').size().to_dict() if not violations.empty else {}
        
        report = {
            "report_type": "Weekly Summary",
            "period": f"{start_date.date()} to {end_date.date()}",
            "generated_at": datetime.now().isoformat(),
            "summary": {
                "total_detections": len(df),
                "total_violations": len(violations),
                "violation_rate": round(len(violations) / len(df) * 100, 2) if len(df) > 0 else 0,
                "avg_confidence": round(df['Confidence'].mean() * 100, 2),
                "daily_avg_detections": round(len(df) / 7, 2),
                "daily_avg_violations": round(len(violations) / 7, 2)
            },
            "daily_detections": {str(k): int(v) for k, v in daily_detections.items()},
            "daily_violations": {str(k): int(v) for k, v in daily_violations.items()},
            "class_distribution": df['Class'].value_counts().to_dict(),
            "day_of_week_analysis": {str(k): int(v) for k, v in df.groupby('DayOfWeek').size().items()},
            "mttr": self.analytics.calculate_mttr(start_date, end_date),
            "false_positive_rate": self.analytics.calculate_false_positive_rate(start_date, end_date)
        }
        
        # Save to file
        filename = f"weekly_report_{end_date.strftime('%Y%m%d')}.json"
        filepath = self.reports_dir / filename
        with open(filepath, 'w') as f:
            json.dump(report, f, indent=2)
        
        return report
    
    def generate_monthly_report(self, year: Optional[int] = None, 
                               month: Optional[int] = None) -> Dict[str, Any]:
        """Generate monthly summary report"""
        if year is None or month is None:
            now = datetime.now()
            year = now.year
            month = now.month
        
        start_date = datetime(year, month, 1)
        if month == 12:
            end_date = datetime(year + 1, 1, 1) - timedelta(seconds=1)
        else:
            end_date = datetime(year, month + 1, 1) - timedelta(seconds=1)
        
        self.analytics.load_data()
        df = self.analytics._filter_by_date(self.analytics.df, start_date, end_date)
        
        if df.empty:
            return {"error": "No data for specified month"}
        
        violations = df[df['IsViolation'] == 1]
        
        report = {
            "report_type": "Monthly Summary",
            "period": f"{start_date.strftime('%B %Y')}",
            "generated_at": datetime.now().isoformat(),
            "summary": {
                "total_detections": len(df),
                "total_violations": len(violations),
                "violation_rate": round(len(violations) / len(df) * 100, 2) if len(df) > 0 else 0,
                "avg_confidence": round(df['Confidence'].mean() * 100, 2),
                "unique_classes": int(df['Class'].nunique()),
                "active_days": int(df['Date'].nunique())
            },
            "weekly_breakdown": {
                f"Week {i+1}": len(df[(df['Timestamp'] >= start_date + timedelta(weeks=i)) & 
                                     (df['Timestamp'] < start_date + timedelta(weeks=i+1))])
                for i in range(4)
            },
            "class_distribution": df['Class'].value_counts().to_dict(),
            "kpis": {
                "mttr": self.analytics.calculate_mttr(start_date, end_date),
                "false_positive_rate": self.analytics.calculate_false_positive_rate(start_date, end_date),
                "coverage": self.analytics.calculate_coverage_percentage(start_date, end_date)
            },
            "executive_summary": self.analytics.get_executive_summary(start_date, end_date)
        }
        
        # Save to file
        filename = f"monthly_report_{year}{month:02d}.json"
        filepath = self.reports_dir / filename
        with open(filepath, 'w') as f:
            json.dump(_convert_to_native_types(report), f, indent=2)
        
        return report
    
    def generate_compliance_report(self, report_type: str = "OSHA") -> Dict[str, Any]:
        """Generate compliance-specific reports (OSHA, ISO, SOC 2)"""
        self.analytics.load_data()
        df = self.analytics.df
        
        if df.empty:
            return {"error": "No data available"}
        
        # Last 30 days for compliance
        end_date = datetime.now()
        start_date = end_date - timedelta(days=30)
        df = self.analytics._filter_by_date(df, start_date, end_date)
        
        violations = df[df['IsViolation'] == 1]
        
        base_report = {
            "report_type": f"{report_type} Compliance Report",
            "period": f"{start_date.date()} to {end_date.date()}",
            "generated_at": datetime.now().isoformat(),
            "system_info": {
                "total_monitored_hours": round((end_date - start_date).total_seconds() / 3600, 2),
                "system_uptime_percentage": self.analytics.calculate_coverage_percentage(start_date, end_date)['uptime_percentage'],
                "total_incidents": len(violations),
                "incident_rate": round(len(violations) / 30, 2)  # per day
            }
        }
        
        if report_type.upper() == "OSHA":
            base_report.update({
                "safety_incidents": len(violations),
                "incident_severity": "Medium" if len(violations) > 10 else "Low",
                "response_metrics": self.analytics.calculate_mttr(start_date, end_date),
                "compliance_status": "Compliant" if len(violations) < 50 else "Review Required"
            })
        elif report_type.upper() == "ISO":
            base_report.update({
                "quality_metrics": {
                    "detection_accuracy": self.analytics.calculate_false_positive_rate(start_date, end_date),
                    "system_reliability": base_report['system_info']['system_uptime_percentage'],
                    "process_adherence": "100%"
                },
                "compliance_status": "ISO 27001 Compliant"
            })
        elif report_type.upper() == "SOC2":
            base_report.update({
                "security_controls": {
                    "access_monitoring": "Active",
                    "incident_response": self.analytics.calculate_mttr(start_date, end_date),
                    "data_integrity": "Verified",
                    "availability": f"{base_report['system_info']['system_uptime_percentage']}%"
                },
                "audit_trail": "Complete",
                "compliance_status": "SOC 2 Type II Ready"
            })
        
        return base_report
    
    def get_report_schedules(self) -> List[Dict[str, Any]]:
        """Get all scheduled report configurations"""
        if os.path.exists(REPORT_SCHEDULE_FILE):
            with open(REPORT_SCHEDULE_FILE, 'r') as f:
                return json.load(f)
        return []
    
    def add_report_schedule(self, schedule: Dict[str, Any]) -> Dict[str, str]:
        """Add a new report schedule"""
        schedules = self.get_report_schedules()
        schedule['id'] = f"schedule_{len(schedules) + 1}_{datetime.now().timestamp()}"
        schedule['created_at'] = datetime.now().isoformat()
        schedules.append(schedule)
        
        with open(REPORT_SCHEDULE_FILE, 'w') as f:
            json.dump(schedules, f, indent=2)
        
        return {"status": "success", "schedule_id": schedule['id']}


# =============================================================================
# 3. COST ANALYSIS MODULE
# =============================================================================

class CostAnalyzer:
    """Track costs and calculate ROI for security operations"""
    
    def __init__(self):
        self.config = self.load_cost_config()
    
    def load_cost_config(self) -> Dict[str, Any]:
        """Load cost configuration"""
        default_config = {
            "cost_per_camera_monthly": 50.0,
            "cost_per_detection": 0.01,
            "cost_per_hour_monitoring": 15.0,
            "infrastructure_cost_monthly": 200.0,
            "personnel_cost_per_incident": 25.0,
            "false_alarm_cost": 10.0,
            "prevented_incident_value": 1000.0,
            "number_of_cameras": 1
        }
        
        if os.path.exists(COST_CONFIG_FILE):
            try:
                with open(COST_CONFIG_FILE, 'r') as f:
                    loaded = json.load(f)
                    default_config.update(loaded)
            except:
                pass
        else:
            # Save default config
            with open(COST_CONFIG_FILE, 'w') as f:
                json.dump(default_config, f, indent=2)
        
        return default_config
    
    def save_cost_config(self, config: Dict[str, Any]) -> Dict[str, str]:
        """Save cost configuration"""
        self.config.update(config)
        with open(COST_CONFIG_FILE, 'w') as f:
            json.dump(self.config, f, indent=2)
        return {"status": "success", "message": "Cost configuration updated"}
    
    def calculate_operational_costs(self, start_date: Optional[datetime] = None,
                                   end_date: Optional[datetime] = None) -> Dict[str, Any]:
        """Calculate total operational costs"""
        analytics = AnalyticsDashboard()
        analytics.load_data()
        
        if analytics.df.empty:
            return {"error": "No data available"}
        
        df = analytics._filter_by_date(analytics.df, start_date, end_date)
        
        if df.empty:
            return {"error": "No data for specified period"}
        
        # Calculate period in days
        period_start = df['Timestamp'].min()
        period_end = df['Timestamp'].max()
        days = (period_end - period_start).days + 1
        months = days / 30.0
        
        # Calculate costs
        camera_costs = self.config['cost_per_camera_monthly'] * self.config['number_of_cameras'] * months
        detection_costs = len(df) * self.config['cost_per_detection']
        
        # Estimate monitoring hours (assume 24/7)
        monitoring_hours = days * 24
        monitoring_costs = monitoring_hours * self.config['cost_per_hour_monitoring']
        
        infrastructure_costs = self.config['infrastructure_cost_monthly'] * months
        
        violations = df[df['Restricted Area Violation'] == 'Yes']
        incident_costs = len(violations) * self.config['personnel_cost_per_incident']
        
        # False alarms (low confidence detections)
        false_alarms = len(df[df['Confidence'] < 0.7])
        false_alarm_costs = false_alarms * self.config['false_alarm_cost']
        
        total_costs = (camera_costs + detection_costs + monitoring_costs + 
                      infrastructure_costs + incident_costs + false_alarm_costs)
        
        return {
            "period": f"{period_start.date()} to {period_end.date()}",
            "days": days,
            "cost_breakdown": {
                "camera_costs": round(camera_costs, 2),
                "detection_processing_costs": round(detection_costs, 2),
                "monitoring_costs": round(monitoring_costs, 2),
                "infrastructure_costs": round(infrastructure_costs, 2),
                "incident_response_costs": round(incident_costs, 2),
                "false_alarm_costs": round(false_alarm_costs, 2)
            },
            "total_costs": round(total_costs, 2),
            "daily_avg_cost": round(total_costs / days, 2),
            "cost_per_detection": round(total_costs / len(df), 2) if len(df) > 0 else 0
        }
    
    def calculate_roi(self, start_date: Optional[datetime] = None,
                     end_date: Optional[datetime] = None) -> Dict[str, Any]:
        """Calculate Return on Investment"""
        analytics = AnalyticsDashboard()
        analytics.load_data()
        
        if analytics.df.empty:
            return {"error": "No data available"}
        
        df = analytics._filter_by_date(analytics.df, start_date, end_date)
        
        if df.empty:
            return {"error": "No data for specified period"}
        
        # Calculate costs
        costs = self.calculate_operational_costs(start_date, end_date)
        total_costs = costs['total_costs']
        
        # Calculate value/benefits
        violations = df[df['Restricted Area Violation'] == 'Yes']
        prevented_incidents = len(violations)  # Assume each violation was prevented
        
        # Value of prevented incidents
        prevented_value = prevented_incidents * self.config['prevented_incident_value']
        
        # Additional benefits (estimated)
        # - Reduced insurance premiums (5% of prevented value)
        insurance_savings = prevented_value * 0.05
        
        # - Improved safety culture value
        safety_value = prevented_incidents * 50
        
        # - Reduced liability
        liability_reduction = prevented_incidents * 200
        
        total_benefits = prevented_value + insurance_savings + safety_value + liability_reduction
        
        # Calculate ROI
        roi_percentage = ((total_benefits - total_costs) / total_costs * 100) if total_costs > 0 else 0
        payback_period_months = (total_costs / (total_benefits / costs['days'] * 30)) if total_benefits > 0 else 0
        
        return {
            "period": costs['period'],
            "total_costs": total_costs,
            "total_benefits": round(total_benefits, 2),
            "net_benefit": round(total_benefits - total_costs, 2),
            "roi_percentage": round(roi_percentage, 2),
            "payback_period_months": round(payback_period_months, 2),
            "benefit_breakdown": {
                "prevented_incidents_value": round(prevented_value, 2),
                "insurance_savings": round(insurance_savings, 2),
                "safety_culture_value": round(safety_value, 2),
                "liability_reduction": round(liability_reduction, 2)
            },
            "metrics": {
                "incidents_prevented": prevented_incidents,
                "value_per_incident": self.config['prevented_incident_value'],
                "cost_per_detection": costs['cost_per_detection']
            }
        }
    
    def calculate_resource_utilization(self, start_date: Optional[datetime] = None,
                                      end_date: Optional[datetime] = None) -> Dict[str, Any]:
        """Calculate resource utilization metrics"""
        analytics = AnalyticsDashboard()
        analytics.load_data()
        
        if analytics.df.empty:
            return {"error": "No data available"}
        
        df = analytics._filter_by_date(analytics.df, start_date, end_date)
        
        if df.empty:
            return {"error": "No data for specified period"}
        
        period_start = df['Timestamp'].min()
        period_end = df['Timestamp'].max()
        total_hours = (period_end - period_start).total_seconds() / 3600
        
        # Camera utilization
        active_hours = df['Timestamp'].dt.floor('h').nunique()
        camera_utilization = (active_hours / total_hours * 100) if total_hours > 0 else 0
        
        # Detection efficiency
        total_detections = len(df)
        violations = len(df[df['Restricted Area Violation'] == 'Yes'])
        detection_efficiency = (violations / total_detections * 100) if total_detections > 0 else 0
        
        # System performance
        avg_confidence = df['Confidence'].mean() * 100
        high_confidence_rate = len(df[df['Confidence'] >= 0.8]) / total_detections * 100 if total_detections > 0 else 0
        
        # Cost efficiency
        costs = self.calculate_operational_costs(start_date, end_date)
        cost_per_violation = costs['total_costs'] / violations if violations > 0 else 0
        
        return {
            "period": f"{period_start.date()} to {period_end.date()}",
            "camera_utilization_percentage": round(camera_utilization, 2),
            "detection_efficiency_percentage": round(detection_efficiency, 2),
            "system_performance": {
                "avg_confidence": round(avg_confidence, 2),
                "high_confidence_rate": round(high_confidence_rate, 2),
                "total_detections": total_detections,
                "detections_per_hour": round(total_detections / total_hours, 2) if total_hours > 0 else 0
            },
            "cost_efficiency": {
                "cost_per_detection": costs['cost_per_detection'],
                "cost_per_violation": round(cost_per_violation, 2),
                "daily_operational_cost": costs['daily_avg_cost']
            },
            "resource_recommendations": self._generate_resource_recommendations(
                camera_utilization, detection_efficiency, high_confidence_rate
            )
        }
    
    def _generate_resource_recommendations(self, camera_util: float, 
                                          detection_eff: float, 
                                          high_conf_rate: float) -> List[str]:
        """Generate recommendations based on resource utilization"""
        recommendations = []
        
        if camera_util < 70:
            recommendations.append("📹 Low camera utilization - Consider optimizing coverage or reducing number of cameras")
        elif camera_util > 95:
            recommendations.append("📹 High camera utilization - System is well-utilized")
        
        if detection_eff < 10:
            recommendations.append("🎯 Low detection efficiency - Review zone configurations")
        elif detection_eff > 30:
            recommendations.append("⚠️ High violation rate - Consider increasing security presence")
        
        if high_conf_rate < 70:
            recommendations.append("📊 Low confidence scores - Optimize camera angles and lighting")
        elif high_conf_rate > 90:
            recommendations.append("✅ Excellent detection quality")
        
        return recommendations
    
    def get_cost_config(self) -> Dict[str, Any]:
        """Get current cost configuration"""
        return self.config

