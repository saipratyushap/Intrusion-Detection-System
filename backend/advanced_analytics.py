"""
=============================================================================
ADVANCED ANALYTICS MODULE
=============================================================================
Predictive analytics, anomaly detection, and statistical analysis
=============================================================================
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, Any, List, Tuple
import json
from pathlib import Path
from collections import Counter

# Try to import advanced libraries
try:
    from scipy import stats
    HAS_SCIPY = True
except ImportError:
    HAS_SCIPY = False

try:
    from sklearn.ensemble import IsolationForest
    from sklearn.preprocessing import StandardScaler
    HAS_SKLEARN = True
except ImportError:
    HAS_SKLEARN = False

try:
    from statsmodels.tsa.seasonal import seasonal_decompose
    from statsmodels.tsa.holtwinters import ExponentialSmoothing
    HAS_STATSMODELS = True
except ImportError:
    HAS_STATSMODELS = False

import warnings
warnings.filterwarnings('ignore')


class PredictiveAnalytics:
    """Predictive analytics for trend forecasting and forecasting"""
    
    def __init__(self, data_file: str = "data/detection_log.csv"):
        self.data_file = data_file
        self.df = None
        self.load_data()
    
    def load_data(self):
        """Load detection log data"""
        try:
            self.df = pd.read_csv(self.data_file)
            # Standardize column names
            self.df.columns = [col.strip() for col in self.df.columns]
            return True
        except Exception as e:
            print(f"Error loading data: {e}")
            return False
    
    def forecast_detections(self, days_ahead: int = 7) -> Dict[str, Any]:
        """
        Forecast detection trends using exponential smoothing
        
        Args:
            days_ahead: Number of days to forecast
            
        Returns:
            Dictionary with forecast data and statistics
        """
        try:
            if self.df is None or self.df.empty:
                return {
                    "status": "error",
                    "message": "No data available for forecasting"
                }
            
            # Parse timestamps and extract date for grouping
            df_copy = self.df.copy()
            date_col = 'Date' if 'Date' in self.df.columns else 'Timestamp'
            
            # Convert to datetime and extract date
            df_copy['_parsed_date'] = pd.to_datetime(df_copy[date_col]).dt.date
            
            # Get daily detection counts
            daily_counts = df_copy.groupby('_parsed_date').size().reset_index(name='count')
            daily_counts = daily_counts.sort_values('_parsed_date').reset_index(drop=True)
            
            if len(daily_counts) < 3:
                return {
                    "status": "insufficient_data",
                    "message": "Need at least 3 days of data for forecasting",
                    "current_data_points": len(daily_counts)
                }
            
            # Use exponential smoothing if available
            if HAS_STATSMODELS:
                try:
                    # Fit exponential smoothing model
                    model = ExponentialSmoothing(
                        daily_counts['count'],
                        seasonal_periods=min(7, len(daily_counts) // 2),
                        trend='add',
                        seasonal='add'
                    )
                    fitted_model = model.fit(optimized=True)
                    
                    # Forecast
                    forecast = fitted_model.forecast(steps=days_ahead)
                    
                    # Calculate confidence intervals (simple approach)
                    residuals = fitted_model.resid
                    std_error = np.std(residuals)
                    
                    forecast_data = []
                    base_date = daily_counts['_parsed_date'].iloc[-1]
                    
                    for i, pred_value in enumerate(forecast, 1):
                        future_date = base_date + timedelta(days=i)
                        forecast_data.append({
                            "date": str(future_date),
                            "predicted_detections": max(0, round(pred_value)),
                            "upper_bound": max(0, round(pred_value + 1.96 * std_error)),
                            "lower_bound": max(0, round(pred_value - 1.96 * std_error))
                        })
                    
                    return {
                        "status": "success",
                        "method": "exponential_smoothing",
                        "forecast": forecast_data,
                        "historical_avg": float(daily_counts['count'].mean()),
                        "trend": "increasing" if forecast[-1] > daily_counts['count'].iloc[-1] else "decreasing",
                        "model_fit": float(fitted_model.sse) if hasattr(fitted_model, 'sse') else None
                    }
                except Exception as e:
                    # Fallback to simple moving average
                    return self._simple_forecast(daily_counts, days_ahead)
            else:
                return self._simple_forecast(daily_counts, days_ahead)
                
        except Exception as e:
            return {
                "status": "error",
                "message": str(e)
            }
    
    def _simple_forecast(self, daily_counts: pd.DataFrame, days_ahead: int) -> Dict[str, Any]:
        """Simple moving average forecast (fallback)"""
        # Use 7-day moving average
        window = min(7, len(daily_counts) // 2)
        ma = daily_counts['count'].rolling(window=window).mean().iloc[-1]
        
        forecast_data = []
        base_date = daily_counts['_parsed_date'].iloc[-1]
        std_dev = daily_counts['count'].std()
        
        for i in range(1, days_ahead + 1):
            future_date = base_date + timedelta(days=i)
            forecast_data.append({
                "date": str(future_date),
                "predicted_detections": max(0, round(ma)),
                "upper_bound": max(0, round(ma + 1.96 * std_dev)),
                "lower_bound": max(0, round(ma - 1.96 * std_dev))
            })
        
        return {
            "status": "success",
            "method": "moving_average",
            "forecast": forecast_data,
            "historical_avg": float(daily_counts['count'].mean()),
            "trend": "stable"
        }
    
    def get_trend_analysis(self, days: int = 30) -> Dict[str, Any]:
        """
        Analyze detection trends over specified period
        
        Args:
            days: Number of days to analyze
            
        Returns:
            Trend analysis statistics
        """
        try:
            if self.df is None or self.df.empty:
                return {"status": "error", "message": "No data available"}
            
            date_col = 'Date' if 'Date' in self.df.columns else 'Timestamp'
            df_filtered = self.df.copy()
            df_filtered[date_col] = pd.to_datetime(df_filtered[date_col])
            
            cutoff_date = datetime.now() - timedelta(days=days)
            df_filtered = df_filtered[df_filtered[date_col] >= cutoff_date]
            
            if df_filtered.empty:
                return {"status": "error", "message": f"No data in last {days} days"}
            
            # Extract date for daily aggregation
            df_filtered['_date'] = df_filtered[date_col].dt.date
            
            # Daily counts
            daily_counts = df_filtered.groupby('_date').size()
            
            # Calculate statistics
            trend_stats = {
                "period_days": days,
                "total_detections": int(df_filtered.shape[0]),
                "daily_avg": float(daily_counts.mean()),
                "daily_max": int(daily_counts.max()),
                "daily_min": int(daily_counts.min()),
                "std_deviation": float(daily_counts.std()),
                "peak_day": str(daily_counts.idxmax()),
                "slowest_day": str(daily_counts.idxmin())
            }
            
            # Calculate trend direction
            if len(daily_counts) >= 2:
                first_half_avg = daily_counts[:len(daily_counts)//2].mean()
                second_half_avg = daily_counts[len(daily_counts)//2:].mean()
                
                if second_half_avg > first_half_avg * 1.1:
                    trend_direction = "increasing"
                    trend_strength = float((second_half_avg - first_half_avg) / first_half_avg * 100)
                elif second_half_avg < first_half_avg * 0.9:
                    trend_direction = "decreasing"
                    trend_strength = float((first_half_avg - second_half_avg) / first_half_avg * 100)
                else:
                    trend_direction = "stable"
                    trend_strength = 0.0
                
                trend_stats["trend_direction"] = trend_direction
                trend_stats["trend_strength_percent"] = trend_strength
            
            # Hourly analysis
            hourly_counts = df_filtered.groupby(df_filtered[date_col].dt.hour).size()
            if not hourly_counts.empty:
                trend_stats["peak_hour"] = int(hourly_counts.idxmax())
                trend_stats["peak_hour_detections"] = int(hourly_counts.max())
            
            # Violation rate
            violation_col = 'Restricted Area Violation' if 'Restricted Area Violation' in df_filtered.columns else None
            if violation_col:
                violation_rate = (df_filtered[violation_col] == 'Yes').sum() / len(df_filtered) * 100
                trend_stats["violation_rate_percent"] = float(violation_rate)
            
            return {
                "status": "success",
                "trend_analysis": trend_stats
            }
        
        except Exception as e:
            return {
                "status": "error",
                "message": str(e)
            }


class AnomalyDetection:
    """Anomaly detection using statistical and ML methods"""
    
    def __init__(self, data_file: str = "data/detection_log.csv"):
        self.data_file = data_file
        self.df = None
        self.load_data()
    
    def load_data(self):
        """Load detection log data"""
        try:
            self.df = pd.read_csv(self.data_file)
            self.df.columns = [col.strip() for col in self.df.columns]
            return True
        except Exception as e:
            print(f"Error loading data: {e}")
            return False
    
    def detect_anomalies(self, method: str = "zscore") -> Dict[str, Any]:
        """
        Detect anomalies in detection patterns
        
        Args:
            method: 'zscore', 'isolation_forest', or 'statistical'
            
        Returns:
            Anomaly detection results
        """
        try:
            if self.df is None or self.df.empty:
                return {"status": "error", "message": "No data available"}
            
            # Extract hour from Timestamp column
            df_copy = self.df.copy()
            timestamp_col = 'Timestamp' if 'Timestamp' in self.df.columns else 'Date'
            df_copy['_hour'] = pd.to_datetime(df_copy[timestamp_col]).dt.hour
            
            hourly_counts = df_copy.groupby('_hour').size().values.reshape(-1, 1)
            
            if len(hourly_counts) < 3:
                return {"status": "error", "message": "Insufficient data for anomaly detection"}
            
            if method == "isolation_forest" and HAS_SKLEARN:
                return self._isolation_forest_anomalies(hourly_counts)
            elif method == "statistical":
                return self._statistical_anomalies(hourly_counts)
            else:  # zscore (default)
                return self._zscore_anomalies(hourly_counts)
        
        except Exception as e:
            return {"status": "error", "message": str(e)}
    
    def _zscore_anomalies(self, data: np.ndarray) -> Dict[str, Any]:
        """Z-score based anomaly detection"""
        if not HAS_SCIPY:
            # Manual Z-score calculation
            mean = np.mean(data)
            std = np.std(data)
            z_scores = np.abs((data - mean) / (std + 1e-10))
        else:
            z_scores = np.abs(stats.zscore(data, nan_policy='propagate'))
        
        threshold = 2.5
        anomalies = z_scores.flatten() > threshold
        
        anomaly_indices = np.where(anomalies)[0]
        anomaly_details = []
        
        for idx in anomaly_indices:
            anomaly_details.append({
                "hour": int(idx),
                "detection_count": int(data[idx][0]),
                "z_score": float(z_scores[idx][0]),
                "severity": "high" if z_scores[idx][0] > 3 else "medium"
            })
        
        return {
            "status": "success",
            "method": "zscore",
            "anomalies_detected": len(anomaly_indices),
            "anomaly_hours": anomaly_details,
            "threshold": threshold,
            "normal_range": {
                "mean": float(np.mean(data)),
                "std_dev": float(np.std(data))
            }
        }
    
    def _isolation_forest_anomalies(self, data: np.ndarray) -> Dict[str, Any]:
        """Isolation Forest based anomaly detection"""
        scaler = StandardScaler()
        data_scaled = scaler.fit_transform(data)
        
        iso_forest = IsolationForest(contamination=0.15, random_state=42)
        predictions = iso_forest.fit_predict(data_scaled)
        
        anomalies = predictions == -1
        anomaly_indices = np.where(anomalies)[0]
        
        anomaly_details = []
        for idx in anomaly_indices:
            anomaly_details.append({
                "hour": int(idx),
                "detection_count": int(data[idx][0]),
                "anomaly_score": float(iso_forest.score_samples(data_scaled[idx:idx+1])[0]),
                "severity": "high" if data[idx][0] > np.percentile(data, 90) else "medium"
            })
        
        return {
            "status": "success",
            "method": "isolation_forest",
            "anomalies_detected": int(anomalies.sum()),
            "anomaly_hours": anomaly_details,
            "contamination_estimate": 0.15
        }
    
    def _statistical_anomalies(self, data: np.ndarray) -> Dict[str, Any]:
        """Statistical anomaly detection using IQR"""
        Q1 = np.percentile(data, 25)
        Q3 = np.percentile(data, 75)
        IQR = Q3 - Q1
        
        lower_bound = Q1 - 1.5 * IQR
        upper_bound = Q3 + 1.5 * IQR
        
        anomalies = (data < lower_bound) | (data > upper_bound)
        anomaly_indices = np.where(anomalies)[0]
        
        anomaly_details = []
        for idx in anomaly_indices:
            if data[idx][0] > upper_bound:
                severity = "high"
            else:
                severity = "medium"
            
            anomaly_details.append({
                "hour": int(idx),
                "detection_count": int(data[idx][0]),
                "deviation": float(abs(data[idx][0] - np.mean(data))),
                "severity": severity
            })
        
        return {
            "status": "success",
            "method": "iqr",
            "anomalies_detected": int(anomalies.sum()),
            "anomaly_hours": anomaly_details,
            "bounds": {
                "lower": float(lower_bound),
                "upper": float(upper_bound),
                "q1": float(Q1),
                "q3": float(Q3)
            }
        }
    
    def detect_behavioral_anomalies(self) -> Dict[str, Any]:
        """Detect unusual patterns in object class detections"""
        try:
            if self.df is None or self.df.empty:
                return {"status": "error", "message": "No data available"}
            
            class_col = 'Class' if 'Class' in self.df.columns else 'class'
            
            # Get class distribution
            class_counts = self.df[class_col].value_counts()
            total = class_counts.sum()
            class_probs = class_counts / total
            
            # Calculate expected vs actual
            expected_prob = 1.0 / len(class_counts)
            
            anomalies = []
            for class_name, prob in class_probs.items():
                deviation = abs(prob - expected_prob) / expected_prob
                if deviation > 0.5:  # 50% deviation threshold
                    anomalies.append({
                        "class": str(class_name),
                        "count": int(class_counts[class_name]),
                        "probability": float(prob),
                        "expected_probability": float(expected_prob),
                        "deviation_percent": float(deviation * 100),
                        "anomaly_type": "overrepresented" if prob > expected_prob else "underrepresented"
                    })
            
            return {
                "status": "success",
                "total_classes": len(class_counts),
                "anomalous_classes": len(anomalies),
                "anomalies": anomalies,
                "class_distribution": class_counts.to_dict()
            }
        
        except Exception as e:
            return {"status": "error", "message": str(e)}


class StatisticalAnalyzer:
    """Statistical analysis and KPI computation"""
    
    def __init__(self, data_file: str = "data/detection_log.csv"):
        self.data_file = data_file
        self.df = None
        self.load_data()
    
    def load_data(self):
        """Load detection log data"""
        try:
            self.df = pd.read_csv(self.data_file)
            self.df.columns = [col.strip() for col in self.df.columns]
            return True
        except Exception as e:
            print(f"Error loading data: {e}")
            return False
    
    def calculate_kpis(self) -> Dict[str, Any]:
        """Calculate comprehensive KPIs"""
        try:
            if self.df is None or self.df.empty:
                return {"status": "error", "message": "No data available"}
            
            kpis = {}
            
            # Detection KPIs
            kpis["total_detections"] = int(len(self.df))
            
            confidence_col = 'Confidence' if 'Confidence' in self.df.columns else 'confidence'
            if confidence_col in self.df.columns:
                kpis["avg_confidence"] = float(self.df[confidence_col].mean())
                kpis["max_confidence"] = float(self.df[confidence_col].max())
                kpis["min_confidence"] = float(self.df[confidence_col].min())
                kpis["std_confidence"] = float(self.df[confidence_col].std())
                kpis["confidence_median"] = float(self.df[confidence_col].median())
            
            # Violation KPIs
            violation_col = 'Restricted Area Violation' if 'Restricted Area Violation' in self.df.columns else None
            if violation_col and violation_col in self.df.columns:
                violations = (self.df[violation_col] == 'Yes').sum()
                kpis["total_violations"] = int(violations)
                kpis["violation_rate"] = float(violations / len(self.df) * 100)
                kpis["compliance_rate"] = float((len(self.df) - violations) / len(self.df) * 100)
            
            # Temporal KPIs
            date_col = 'Date' if 'Date' in self.df.columns else 'Timestamp'
            if date_col in self.df.columns:
                df_time = self.df.copy()
                df_time[date_col] = pd.to_datetime(df_time[date_col])
                daily_detections = df_time.groupby(df_time[date_col].dt.date).size()
                kpis["days_with_detections"] = int(len(daily_detections))
                kpis["avg_detections_per_day"] = float(daily_detections.mean())
                kpis["max_detections_per_day"] = int(daily_detections.max())
            
            # Class diversity KPI
            class_col = 'Class' if 'Class' in self.df.columns else 'class'
            if class_col in self.df.columns:
                unique_classes = self.df[class_col].nunique()
                kpis["unique_classes_detected"] = int(unique_classes)
                kpis["class_diversity_index"] = float(unique_classes / len(self.df) if len(self.df) > 0 else 0)
            
            return {
                "status": "success",
                "kpis": kpis
            }
        
        except Exception as e:
            return {"status": "error", "message": str(e)}
    
    def get_correlation_analysis(self) -> Dict[str, Any]:
        """Analyze correlations between numerical features"""
        try:
            if self.df is None or self.df.empty:
                return {"status": "error", "message": "No data available"}
            
            # Select numerical columns
            numerical_df = self.df.select_dtypes(include=[np.number]).copy()
            
            if numerical_df.empty:
                return {"status": "warning", "message": "No numerical columns found"}
            
            if HAS_SCIPY:
                correlations = {}
                for col1 in numerical_df.columns:
                    for col2 in numerical_df.columns:
                        if col1 < col2:  # Avoid duplicates
                            corr, pvalue = stats.pearsonr(
                                numerical_df[col1].fillna(0),
                                numerical_df[col2].fillna(0)
                            )
                            if abs(corr) > 0.3:  # Only strong correlations
                                correlations[f"{col1}_vs_{col2}"] = {
                                    "correlation": float(corr),
                                    "p_value": float(pvalue),
                                    "significant": pvalue < 0.05
                                }
                
                return {
                    "status": "success",
                    "correlations": correlations,
                    "strong_correlations_count": len(correlations)
                }
            else:
                # Simple correlation matrix
                corr_matrix = numerical_df.corr().to_dict()
                return {
                    "status": "success",
                    "correlations": corr_matrix
                }
        
        except Exception as e:
            return {"status": "error", "message": str(e)}
    
    def get_percentile_analysis(self) -> Dict[str, Any]:
        """Get percentile analysis for key metrics"""
        try:
            if self.df is None or self.df.empty:
                return {"status": "error", "message": "No data available"}
            
            confidence_col = 'Confidence' if 'Confidence' in self.df.columns else 'confidence'
            
            if confidence_col not in self.df.columns:
                return {"status": "error", "message": "Confidence column not found"}
            
            percentiles = {}
            for p in [10, 25, 50, 75, 90, 95, 99]:
                percentiles[f"p{p}"] = float(np.percentile(self.df[confidence_col], p))
            
            return {
                "status": "success",
                "percentiles": percentiles,
                "outliers_low": int((self.df[confidence_col] < percentiles["p10"]).sum()),
                "outliers_high": int((self.df[confidence_col] > percentiles["p90"]).sum())
            }
        
        except Exception as e:
            return {"status": "error", "message": str(e)}


# Convenience functions for Streamlit integration
def get_predictive_forecast(days_ahead: int = 7) -> Dict[str, Any]:
    """Get predictive forecast for detections"""
    pa = PredictiveAnalytics()
    return pa.forecast_detections(days_ahead)

def get_trend_analysis(days: int = 30) -> Dict[str, Any]:
    """Get trend analysis"""
    pa = PredictiveAnalytics()
    return pa.get_trend_analysis(days)

def detect_anomalies(method: str = "zscore") -> Dict[str, Any]:
    """Detect anomalies in patterns"""
    ad = AnomalyDetection()
    return ad.detect_anomalies(method)

def detect_behavioral_anomalies() -> Dict[str, Any]:
    """Detect behavioral anomalies"""
    ad = AnomalyDetection()
    return ad.detect_behavioral_anomalies()

def calculate_kpis() -> Dict[str, Any]:
    """Calculate comprehensive KPIs"""
    sa = StatisticalAnalyzer()
    return sa.calculate_kpis()

def get_correlation_analysis() -> Dict[str, Any]:
    """Get correlation analysis"""
    sa = StatisticalAnalyzer()
    return sa.get_correlation_analysis()

def get_percentile_analysis() -> Dict[str, Any]:
    """Get percentile analysis"""
    sa = StatisticalAnalyzer()
    return sa.get_percentile_analysis()
