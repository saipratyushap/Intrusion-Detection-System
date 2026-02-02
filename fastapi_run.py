import os
import json
from fastapi import FastAPI, WebSocket, HTTPException, Body
from fastapi.responses import HTMLResponse, FileResponse, Response, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.requests import Request
from fastapi.middleware.cors import CORSMiddleware
import pandas as pd
import asyncio
from collections import Counter
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from pydantic import BaseModel

# Import Business Intelligence modules
from business_intelligence import AnalyticsDashboard, ReportGenerator, CostAnalyzer, _convert_to_native_types
from email_service import EmailService
from report_scheduler import get_scheduler

# Import Advanced Analytics & Email Reporting modules
try:
    from advanced_analytics import (
        PredictiveAnalytics, AnomalyDetection, StatisticalAnalyzer,
        get_predictive_forecast, get_trend_analysis, detect_anomalies,
        detect_behavioral_anomalies, calculate_kpis, get_correlation_analysis,
        get_percentile_analysis
    )
    HAS_ADVANCED_ANALYTICS = True
except ImportError:
    HAS_ADVANCED_ANALYTICS = False
    print("Warning: advanced_analytics.py not found")

try:
    from advanced_email_reporting import (
        AdvancedEmailReporter, ReportScheduleManager, EmailReportTemplate
    )
    HAS_EMAIL_REPORTING = True
except ImportError:
    HAS_EMAIL_REPORTING = False
    print("Warning: advanced_email_reporting.py not found")

app = FastAPI(
    title="Real-Time Restricted Area Monitoring System API",
    description="Advanced Business Intelligence & Reporting API",
    version="2.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

csv_file = "data/detection_log.csv"
frames_dir = "data/frames"

# Initialize services
analytics_service = AnalyticsDashboard(csv_file)
report_service = ReportGenerator(csv_file)
cost_service = CostAnalyzer()
email_service = EmailService()

# Initialize advanced modules if available
advanced_analytics = None
advanced_email_reporter = None
schedule_manager = None

if HAS_ADVANCED_ANALYTICS:
    advanced_analytics = PredictiveAnalytics(csv_file)

if HAS_EMAIL_REPORTING:
    advanced_email_reporter = AdvancedEmailReporter()
    schedule_manager = ReportScheduleManager()

# Start scheduler
scheduler = get_scheduler()

# Static files with cache-busting
app.mount("/static", StaticFiles(directory="static"), name="static")

# Templates directory
templates = Jinja2Templates(directory="templates")

@app.get("/", response_class=HTMLResponse)
async def get_home(request: Request):
    """Home page with navigation to dashboard"""
    from fastapi.responses import HTMLResponse as HTMLResp
    html_content = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Real-Time Restricted Area Monitoring System</title>
        <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
        <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap" rel="stylesheet">
        <style>
            * {
                margin: 0;
                padding: 0;
                box-sizing: border-box;
            }
            
            body {
                font-family: 'Inter', 'Segoe UI', sans-serif;
                background: linear-gradient(135deg, #0f172a 0%, #1a1a2e 50%, #16213e 100%);
                min-height: 100vh;
                display: flex;
                align-items: center;
                justify-content: center;
                color: #f1f5f9;
                margin: 0;
                padding: 20px;
                overflow-x: hidden;
            }
            
            .hero-container {
                text-align: center;
                max-width: 900px;
                animation: fadeInUp 0.8s ease-out;
            }
            
            @keyframes fadeInUp {
                from {
                    opacity: 0;
                    transform: translateY(30px);
                }
                to {
                    opacity: 1;
                    transform: translateY(0);
                }
            }
            
            @keyframes slideDown {
                from {
                    opacity: 0;
                    transform: translateY(-20px);
                }
                to {
                    opacity: 1;
                    transform: translateY(0);
                }
            }
            
            @keyframes pulse {
                0%, 100% {
                    opacity: 1;
                }
                50% {
                    opacity: 0.8;
                }
            }
            
            @keyframes iconPulse {
                0%, 100% {
                    box-shadow: 0 10px 40px rgba(0, 212, 255, 0.4), 
                               0 0 30px rgba(0, 212, 255, 0.2);
                }
                50% {
                    box-shadow: 0 15px 50px rgba(0, 212, 255, 0.6),
                               0 0 40px rgba(124, 58, 237, 0.3);
                }
            }
            
            @keyframes shimmer {
                0% {
                    background-position: -1000px 0;
                }
                100% {
                    background-position: 1000px 0;
                }
            }
            
            @keyframes glow {
                0%, 100% {
                    box-shadow: 0 12px 40px rgba(0, 212, 255, 0.2),
                               0 0 20px rgba(0, 212, 255, 0.1);
                }
                50% {
                    box-shadow: 0 12px 50px rgba(124, 58, 237, 0.3),
                               0 0 30px rgba(124, 58, 237, 0.15);
                }
            }
            
            .logo {
                width: 140px;
                height: 140px;
                background: linear-gradient(145deg, #00d4ff, #7c3aed, #ec4899);
                border-radius: 40px;
                display: flex;
                align-items: center;
                justify-content: center;
                margin: 0 auto 40px;
                font-size: 70px;
                box-shadow: 0 15px 50px rgba(0, 212, 255, 0.4),
                           0 0 30px rgba(124, 58, 237, 0.3),
                           inset 0 2px 10px rgba(255, 255, 255, 0.1);
                animation: iconPulse 3s ease-in-out infinite, slideDown 0.8s ease-out;
                position: relative;
                overflow: hidden;
            }
            
            .logo::before {
                content: '';
                position: absolute;
                top: -50%;
                left: -50%;
                width: 200%;
                height: 200%;
                background: radial-gradient(circle, rgba(255, 255, 255, 0.1) 0%, transparent 70%);
                animation: pulse 2s ease-in-out infinite;
            }
            
            h1 {
                font-size: 3.8rem;
                font-weight: 800;
                margin: 0 0 15px 0;
                background: linear-gradient(135deg, #00d4ff 0%, #7c3aed 50%, #ec4899 100%);
                -webkit-background-clip: text;
                -webkit-text-fill-color: transparent;
                background-clip: text;
                letter-spacing: -1px;
                animation: slideDown 0.8s ease-out 0.1s both;
            }
            
            .subtitle {
                font-size: 1.2rem;
                color: #cbd5e1;
                margin: 0 0 60px 0;
                line-height: 1.8;
                font-weight: 400;
                animation: slideDown 0.8s ease-out 0.2s both;
            }
            
            .button-group {
                display: flex;
                gap: 20px;
                justify-content: center;
                flex-wrap: wrap;
                margin-bottom: 70px;
                animation: slideDown 0.8s ease-out 0.3s both;
            }
            
            .btn {
                padding: 16px 40px;
                border-radius: 16px;
                font-size: 1.05rem;
                font-weight: 700;
                border: none;
                cursor: pointer;
                transition: all 0.3s cubic-bezier(0.23, 1, 0.320, 1);
                display: inline-flex;
                align-items: center;
                gap: 12px;
                text-decoration: none;
                color: white;
                position: relative;
                overflow: hidden;
                text-transform: uppercase;
                letter-spacing: 0.5px;
            }
            
            .btn::before {
                content: '';
                position: absolute;
                top: 0;
                left: -100%;
                width: 100%;
                height: 100%;
                background: rgba(255, 255, 255, 0.1);
                transition: left 0.3s ease;
                z-index: 0;
            }
            
            .btn:hover::before {
                left: 100%;
            }
            
            .btn > * {
                position: relative;
                z-index: 1;
            }
            
            .btn-primary {
                background: linear-gradient(135deg, #00d4ff, #7c3aed);
                box-shadow: 0 10px 30px rgba(0, 212, 255, 0.3),
                           0 0 20px rgba(0, 212, 255, 0.1);
                border: 1px solid rgba(0, 212, 255, 0.3);
            }
            
            .btn-primary:hover {
                transform: translateY(-4px);
                box-shadow: 0 15px 40px rgba(0, 212, 255, 0.5),
                           0 0 30px rgba(0, 212, 255, 0.2);
            }
            
            .btn-secondary {
                background: linear-gradient(135deg, #7c3aed, #ec4899);
                box-shadow: 0 10px 30px rgba(124, 58, 237, 0.3),
                           0 0 20px rgba(236, 72, 153, 0.1);
                border: 1px solid rgba(124, 58, 237, 0.3);
            }
            
            .btn-secondary:hover {
                transform: translateY(-4px);
                box-shadow: 0 15px 40px rgba(124, 58, 237, 0.5),
                           0 0 30px rgba(236, 72, 153, 0.2);
            }
            
            .info-cards {
                display: grid;
                grid-template-columns: repeat(3, 1fr);
                gap: 25px;
                margin-top: 40px;
            }
            
            .card {
                background: rgba(255, 255, 255, 0.04);
                backdrop-filter: blur(16px);
                border: 1px solid rgba(255, 255, 255, 0.08);
                border-radius: 20px;
                padding: 40px 30px;
                text-align: center;
                transition: all 0.3s cubic-bezier(0.23, 1, 0.320, 1);
                position: relative;
                overflow: hidden;
                animation: fadeInUp 0.8s ease-out;
            }
            
            .card:nth-child(1) { animation-delay: 0.4s; }
            .card:nth-child(2) { animation-delay: 0.5s; }
            .card:nth-child(3) { animation-delay: 0.6s; }
            
            .card::before {
                content: '';
                position: absolute;
                top: -50%;
                right: -50%;
                width: 300px;
                height: 300px;
                background: radial-gradient(circle, rgba(0, 212, 255, 0.1) 0%, transparent 70%);
                pointer-events: none;
            }
            
            .card:hover {
                background: rgba(255, 255, 255, 0.08);
                transform: translateY(-8px);
                border-color: rgba(0, 212, 255, 0.3);
                box-shadow: 0 12px 40px rgba(0, 212, 255, 0.15),
                           0 0 20px rgba(124, 58, 237, 0.1);
            }
            
            .card-icon {
                font-size: 3rem;
                margin-bottom: 20px;
                color: #00d4ff;
                display: inline-block;
                animation: pulse 2s ease-in-out infinite;
                position: relative;
                z-index: 1;
            }
            
            .card h3 {
                font-size: 1.4rem;
                margin: 0 0 15px 0;
                color: #f1f5f9;
                font-weight: 700;
                position: relative;
                z-index: 1;
            }
            
            .card p {
                color: #94a3b8;
                margin: 0;
                font-size: 0.95rem;
                line-height: 1.6;
                position: relative;
                z-index: 1;
            }
            
            /* Responsive Design */
            @media (max-width: 768px) {
                .hero-container {
                    max-width: 100%;
                }
                
                h1 {
                    font-size: 2.5rem;
                }
                
                .subtitle {
                    font-size: 1rem;
                    margin-bottom: 40px;
                }
                
                .button-group {
                    gap: 15px;
                    margin-bottom: 50px;
                }
                
                .btn {
                    padding: 14px 32px;
                    font-size: 0.95rem;
                }
                
                .logo {
                    width: 110px;
                    height: 110px;
                    font-size: 55px;
                    margin-bottom: 30px;
                }
                
                .info-cards {
                    gap: 20px;
                }
                
                .card {
                    padding: 30px 20px;
                }
                
                .card-icon {
                    font-size: 2.5rem;
                }
                
                .card h3 {
                    font-size: 1.2rem;
                }
            }
            
            @media (max-width: 480px) {
                h1 {
                    font-size: 2rem;
                }
                
                .subtitle {
                    font-size: 0.9rem;
                }
                
                .button-group {
                    flex-direction: column;
                    gap: 12px;
                }
                
                .btn {
                    width: 100%;
                    justify-content: center;
                }
                
                .info-cards {
                    grid-template-columns: 1fr;
                }
            }
        </style>
    </head>
    <body>
        <div class="hero-container">
            <div class="logo">
                <i class="fas fa-shield-alt"></i>
            </div>
            
            <h1>Real-Time Monitoring System</h1>
            <p class="subtitle">Advanced AI-Powered Restricted Area Detection with Business Intelligence</p>
            
            <div class="button-group">
                <a href="/data" class="btn btn-primary">
                    <i class="fas fa-chart-line"></i> View Dashboard
                </a>
                <a href="/docs" class="btn btn-secondary">
                    <i class="fas fa-code"></i> API Documentation
                </a>
            </div>
            
            <div class="info-cards">
                <div class="card">
                    <div class="card-icon"><i class="fas fa-chart-line"></i></div>
                    <h3>Live Dashboard</h3>
                    <p>Real-time detection metrics and analytics</p>
                </div>
                <div class="card">
                    <div class="card-icon"><i class="fas fa-brain"></i></div>
                    <h3>AI Analytics</h3>
                    <p>Advanced predictive analytics and anomaly detection</p>
                </div>
                <div class="card">
                    <div class="card-icon"><i class="fas fa-envelope"></i></div>
                    <h3>Email Reports</h3>
                    <p>Automated scheduled reporting system</p>
                </div>
            </div>
        </div>
    </body>
    </html>
    """
    response = HTMLResp(content=html_content)
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate, max-age=0"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    return response

@app.get("/data", response_class=HTMLResponse)
async def get_data_dashboard(request: Request):
    """Serve the live monitoring dashboard"""
    return templates.get_template("data.html").render(request=request)

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    last_line_count = 0

    while True:
        df = pd.read_csv(csv_file)

        # Only send new data
        if len(df) > last_line_count:
            new_data = df.iloc[last_line_count:]  # Get all new rows since last read
            last_line_count = len(df)  # Update last read count

            # Summary Stats
            total_detections = len(df)
            total_violations = df[df["Restricted Area Violation"] == "Yes"].shape[0]
            most_frequent_class = Counter(df["Class"]).most_common(1)[0][0]
            top_5_violations = df[df["Restricted Area Violation"] == "Yes"].tail(5).to_dict(orient="records")

            # Prepare data
            data = {
                "timestamp": new_data["Timestamp"].tolist(),  # Convert to list
                "class": new_data["Class"].tolist(),  # Convert to list
                "confidence": new_data["Confidence"].apply(lambda x: round(float(x) * 100, 2)).tolist(),  # Convert to list
                "restricted_area_violation": new_data["Restricted Area Violation"].tolist(),
                "summary": {
                    "total_detections": total_detections,
                    "total_violations": total_violations,
                    "most_frequent_class": most_frequent_class,
                    "top_5_violations": top_5_violations
                }
            }

            await websocket.send_json(data)

        await asyncio.sleep(1)  # Check every second




@app.websocket("/ws/data")
async def websocket_data_endpoint(websocket: WebSocket):
    await websocket.accept()
    
    try:
        while True:
            try:
                if os.path.exists(csv_file):
                    df = pd.read_csv(csv_file)

                    if not df.empty:
                        # Ensure the Timestamp column is in datetime format
                        df['Timestamp'] = pd.to_datetime(df['Timestamp'])

                        # Sort the DataFrame by Timestamp in descending order (most recent first)
                        df = df.sort_values(by='Timestamp', ascending=False)

                        # Convert the 'Timestamp' column to string to make it JSON serializable
                        df['Timestamp'] = df['Timestamp'].dt.strftime('%Y-%m-%d %H:%M:%S')

                        # Convert the DataFrame to a list of dictionaries
                        data_list = df.to_dict(orient="records")

                        # Send the full data
                        await websocket.send_json({"data": data_list})
                    else:
                        # Send empty list if file is empty
                        await websocket.send_json({"data": []})
                else:
                    print(f"CSV file not found: {csv_file}")
                    await websocket.send_json({"data": []})
            except Exception as e:
                print(f"Error reading data: {e}")
                # Do not break the loop, just wait and try again
                await asyncio.sleep(1)
                continue
                
            await asyncio.sleep(1)  # Send data every second
    except Exception as e:
        print(f"WebSocket error: {e}")
    finally:
        try:
            await websocket.close()
        except:
            pass

@app.get("/video")
async def get_video():
    """Serve the recorded video file."""
    video_path = "data/recorded_video.mp4"
    return FileResponse(video_path, media_type="video/mp4")

@app.get("/api/snapshots-count")
async def get_snapshots_count():
    """Get the count of snapshot files."""
    count = 0
    if os.path.exists(frames_dir):
        count = len([f for f in os.listdir(frames_dir) if f.endswith('.jpg')])
    return {"count": count}


# =============================================================================
# REAL-TIME ALERTS API ENDPOINTS
# =============================================================================

@app.get("/api/alerts")
async def get_alerts(limit: int = 50):
    """Get all alerts (violations) from the detection log."""
    try:
        df = pd.read_csv(csv_file)
        
        if df.empty:
            return JSONResponse(content={
                "total_alerts": 0,
                "alerts": [],
                "timestamp": datetime.now().isoformat()
            })
        
        # Filter violations
        violations = df[df["Restricted Area Violation"] == "Yes"].copy()
        
        # Sort by timestamp descending (most recent first)
        violations['Timestamp'] = pd.to_datetime(violations['Timestamp'])
        violations = violations.sort_values('Timestamp', ascending=False)
        
        # Take top N
        recent_violations = violations.head(limit)
        
        # Format for response
        alerts = []
        for _, row in recent_violations.iterrows():
            alerts.append({
                "timestamp": row['Timestamp'].strftime('%Y-%m-%d %H:%M:%S'),
                "class": row['Class'],
                "confidence": round(float(row['Confidence']) * 100, 2),
                "is_violation": True
            })
        
        return JSONResponse(content={
            "total_alerts": len(violations),
            "recent_alerts": len(alerts),
            "alerts": alerts,
            "timestamp": datetime.now().isoformat()
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/alerts/recent")
async def get_recent_alerts(hours: int = 24):
    """Get alerts from the last N hours."""
    try:
        df = pd.read_csv(csv_file)
        
        if df.empty:
            return JSONResponse(content={
                "total_alerts": 0,
                "time_range_hours": hours,
                "alerts": [],
                "timestamp": datetime.now().isoformat()
            })
        
        df['Timestamp'] = pd.to_datetime(df['Timestamp'])
        
        # Filter by time range
        cutoff = datetime.now() - timedelta(hours=hours)
        recent_df = df[df['Timestamp'] >= cutoff]
        
        # Filter violations
        violations = recent_df[recent_df["Restricted Area Violation"] == "Yes"].copy()
        
        # Sort by timestamp descending
        violations = violations.sort_values('Timestamp', ascending=False)
        
        # Format for response
        alerts = []
        for _, row in violations.iterrows():
            alerts.append({
                "timestamp": row['Timestamp'].strftime('%Y-%m-%d %H:%M:%S'),
                "class": row['Class'],
                "confidence": round(float(row['Confidence']) * 100, 2)
            })
        
        return JSONResponse(content={
            "total_alerts": len(violations),
            "time_range_hours": hours,
            "alerts": alerts,
            "timestamp": datetime.now().isoformat()
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/alerts/stats")
async def get_alerts_stats():
    """Get alert statistics."""
    try:
        df = pd.read_csv(csv_file)
        
        if df.empty:
            return JSONResponse(content={
                "total_alerts": 0,
                "today_alerts": 0,
                "week_alerts": 0,
                "unique_classes": 0,
                "top_class": None,
                "avg_confidence": 0,
                "timestamp": datetime.now().isoformat()
            })
        
        # Convert Timestamp to datetime for date comparisons
        df['Timestamp'] = pd.to_datetime(df['Timestamp'])
        
        # Get all violations
        violations = df[df["Restricted Area Violation"] == "Yes"].copy()
        
        # Today's violations
        today = datetime.now().date()
        today_violations = violations[violations['Timestamp'].dt.date == today]
        
        # This week's violations
        week_ago = datetime.now() - timedelta(days=7)
        week_violations = violations[violations['Timestamp'] >= week_ago]
        
        # Top violation class
        top_class = violations['Class'].mode().iloc[0] if not violations.empty and not violations['Class'].mode().empty else None
        
        # Average confidence
        avg_conf = violations['Confidence'].mean() * 100 if not violations.empty and 'Confidence' in violations.columns and violations['Confidence'].notna().any() else 0
        
        return JSONResponse(content={
            "total_alerts": len(violations),
            "today_alerts": len(today_violations),
            "week_alerts": len(week_violations),
            "unique_classes": violations['Class'].nunique() if not violations.empty else 0,
            "top_class": top_class,
            "avg_confidence": round(avg_conf, 2),
            "timestamp": datetime.now().isoformat()
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# DETECTION DATA API ENDPOINTS (for dashboard fallback)
# =============================================================================

@app.get("/api/detections/summary")
async def get_detections_summary():
    """Get detection summary statistics from CSV file."""
    try:
        df = pd.read_csv(csv_file)
        
        total_detections = len(df)
        total_violations = len(df[df["Restricted Area Violation"] == "Yes"])
        
        # Calculate unique classes with violations
        violations_df = df[df["Restricted Area Violation"] == "Yes"]
        alert_classes = violations_df["Class"].nunique() if not violations_df.empty else 0
        
        # Calculate average confidence
        avg_confidence = df["Confidence"].mean() * 100 if not df.empty else 0
        
        # Get unique classes for dropdown
        unique_classes = df["Class"].unique().tolist()
        
        # Most frequent class
        most_frequent = df["Class"].mode().iloc[0] if not df.empty else "N/A"
        
        return JSONResponse(content={
            "total_detections": total_detections,
            "total_violations": total_violations,
            "alert_classes": alert_classes,
            "avg_confidence": round(avg_confidence, 2),
            "most_frequent_class": most_frequent,
            "unique_classes": unique_classes,
            "timestamp": datetime.now().isoformat()
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/detections/recent")
async def get_recent_detections(limit: int = 100):
    """Get recent detection records from CSV file."""
    try:
        df = pd.read_csv(csv_file)
        
        # Sort by timestamp descending (most recent first)
        df['Timestamp'] = pd.to_datetime(df['Timestamp'])
        df = df.sort_values(by='Timestamp', ascending=False)
        
        # Convert to list of dicts
        df['Timestamp'] = df['Timestamp'].dt.strftime('%Y-%m-%d %H:%M:%S')
        recent_data = df.head(limit).to_dict(orient="records")
        
        return JSONResponse(content={
            "data": recent_data,
            "total_count": len(df),
            "displayed_count": len(recent_data)
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/detections/today")
async def get_today_detections():
    """Get today's detection statistics."""
    try:
        df = pd.read_csv(csv_file)
        df['Timestamp'] = pd.to_datetime(df['Timestamp'])
        
        today = datetime.now().date()
        today_start = datetime.combine(today, datetime.min.time())
        today_end = datetime.combine(today, datetime.max.time())
        
        today_df = df[(df['Timestamp'] >= today_start) & (df['Timestamp'] <= today_end)]
        
        week_ago = today_start - timedelta(days=7)
        week_df = df[df['Timestamp'] >= week_ago]
        
        today_count = len(today_df)
        week_count = len(week_df)
        
        today_violations = len(today_df[today_df["Restricted Area Violation"] == "Yes"]) if not today_df.empty else 0
        total_violations = len(df[df["Restricted Area Violation"] == "Yes"]) if not df.empty else 0
        violation_rate = round((total_violations / len(df) * 100), 2) if not df.empty else 0
        
        avg_confidence = today_df["Confidence"].mean() * 100 if not today_df.empty else 0
        
        return JSONResponse(content={
            "today_count": today_count,
            "week_count": week_count,
            "violation_rate": violation_rate,
            "avg_confidence": round(avg_confidence, 2),
            "total_detections": len(df),
            "total_violations": total_violations
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# BUSINESS INTELLIGENCE API ENDPOINTS
# =============================================================================

# Pydantic models for request/response
class DateRangeQuery(BaseModel):
    start_date: Optional[str] = None
    end_date: Optional[str] = None

class CostConfigUpdate(BaseModel):
    cost_per_camera_monthly: Optional[float] = None
    cost_per_detection: Optional[float] = None
    cost_per_hour_monitoring: Optional[float] = None
    infrastructure_cost_monthly: Optional[float] = None
    personnel_cost_per_incident: Optional[float] = None
    false_alarm_cost: Optional[float] = None
    prevented_incident_value: Optional[float] = None
    number_of_cameras: Optional[int] = None

class ReportScheduleConfig(BaseModel):
    name: str
    report_type: str  # daily, weekly, monthly, compliance
    frequency: str    # daily, weekly, monthly
    time: str         # HH:MM format
    day_of_week: Optional[int] = None  # 0-6 for Monday-Sunday
    day_of_month: Optional[int] = None # 1-31
    email_recipients: List[str] = []
    compliance_type: Optional[str] = None  # OSHA, ISO, SOC2
    active: bool = True


# =============================================================================
# 1. ADVANCED ANALYTICS DASHBOARD API
# =============================================================================

@app.get("/api/analytics/kpis/mttr")
async def get_mttr(start_date: Optional[str] = None, end_date: Optional[str] = None):
    """Get Mean Time To Respond (MTTR) metrics"""
    try:
        start = datetime.fromisoformat(start_date) if start_date else None
        end = datetime.fromisoformat(end_date) if end_date else None
        
        analytics_service.load_data()
        result = analytics_service.calculate_mttr(start, end)
        return JSONResponse(content=result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/analytics/kpis/false-positive-rate")
async def get_false_positive_rate(start_date: Optional[str] = None, end_date: Optional[str] = None):
    """Get False Positive Rate metrics"""
    try:
        start = datetime.fromisoformat(start_date) if start_date else None
        end = datetime.fromisoformat(end_date) if end_date else None
        
        analytics_service.load_data()
        result = analytics_service.calculate_false_positive_rate(start, end)
        return JSONResponse(content=result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/analytics/kpis/coverage")
async def get_coverage(start_date: Optional[str] = None, end_date: Optional[str] = None):
    """Get system coverage percentage metrics"""
    try:
        start = datetime.fromisoformat(start_date) if start_date else None
        end = datetime.fromisoformat(end_date) if end_date else None
        
        analytics_service.load_data()
        result = analytics_service.calculate_coverage_percentage(start, end)
        return JSONResponse(content=_convert_to_native_types(result))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/analytics/executive-summary")
async def get_executive_summary(start_date: Optional[str] = None, end_date: Optional[str] = None):
    """Get executive summary with key insights and recommendations"""
    try:
        start = datetime.fromisoformat(start_date) if start_date else None
        end = datetime.fromisoformat(end_date) if end_date else None
        
        analytics_service.load_data()
        result = analytics_service.get_executive_summary(start, end)
        return JSONResponse(content=result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/analytics/trend-analysis")
async def get_trend_analysis(days: int = 30):
    """Get trend analysis over specified period"""
    try:
        analytics_service.load_data()
        result = analytics_service.get_trend_analysis(days)
        return JSONResponse(content=_convert_to_native_types(result))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/analytics/dashboard")
async def get_full_dashboard(start_date: Optional[str] = None, end_date: Optional[str] = None):
    """Get complete analytics dashboard with all KPIs"""
    try:
        start = datetime.fromisoformat(start_date) if start_date else None
        end = datetime.fromisoformat(end_date) if end_date else None
        
        analytics_service.load_data()
        
        dashboard = {
            "generated_at": datetime.now().isoformat(),
            "period": f"{start_date or 'Beginning'} to {end_date or 'Now'}",
            "kpis": {
                "mttr": analytics_service.calculate_mttr(start, end),
                "false_positive_rate": analytics_service.calculate_false_positive_rate(start, end),
                "coverage": analytics_service.calculate_coverage_percentage(start, end)
            },
            "executive_summary": analytics_service.get_executive_summary(start, end),
            "trend_analysis": analytics_service.get_trend_analysis(30)
        }
        
        return JSONResponse(content=_convert_to_native_types(dashboard))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# 2. AUTOMATED REPORT GENERATION API
# =============================================================================

@app.get("/api/reports/daily")
async def generate_daily_report(date: Optional[str] = None):
    """Generate daily summary report"""
    try:
        report_date = datetime.fromisoformat(date) if date else datetime.now() - timedelta(days=1)
        result = report_service.generate_daily_report(report_date)
        return JSONResponse(content=_convert_to_native_types(result))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/reports/weekly")
async def generate_weekly_report(end_date: Optional[str] = None):
    """Generate weekly summary report"""
    try:
        end = datetime.fromisoformat(end_date) if end_date else datetime.now()
        result = report_service.generate_weekly_report(end)
        return JSONResponse(content=_convert_to_native_types(result))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/reports/monthly")
async def generate_monthly_report(year: Optional[int] = None, month: Optional[int] = None):
    """Generate monthly summary report"""
    try:
        result = report_service.generate_monthly_report(year, month)
        return JSONResponse(content=_convert_to_native_types(result))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/reports/compliance/{report_type}")
async def generate_compliance_report(report_type: str):
    """Generate compliance report (OSHA, ISO, SOC2)"""
    try:
        if report_type.upper() not in ['OSHA', 'ISO', 'SOC2']:
            raise HTTPException(status_code=400, detail="Invalid report type. Use OSHA, ISO, or SOC2")
        
        result = report_service.generate_compliance_report(report_type.upper())
        return JSONResponse(content=result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/reports/send-email")
async def send_report_email(
    report_type: str = Body(...),
    date: Optional[str] = Body(None),
    recipients: List[str] = Body(...)
):
    """Generate report and send via email"""
    try:
        # Generate report based on type
        if report_type == "daily":
            report_date = datetime.fromisoformat(date) if date else datetime.now() - timedelta(days=1)
            report = report_service.generate_daily_report(report_date)
        elif report_type == "weekly":
            end = datetime.fromisoformat(date) if date else datetime.now()
            report = report_service.generate_weekly_report(end)
        elif report_type == "monthly":
            report = report_service.generate_monthly_report()
        else:
            raise HTTPException(status_code=400, detail="Invalid report type")
        
        # Send email
        result = email_service.send_report_email(report, recipients)
        return JSONResponse(content=result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# 3. REPORT SCHEDULING API
# =============================================================================

@app.get("/api/schedules")
async def get_all_schedules():
    """Get all report schedules"""
    try:
        schedules = scheduler.get_all_schedules()
        return JSONResponse(content={"schedules": schedules})
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/schedules")
async def create_schedule(schedule: ReportScheduleConfig):
    """Create a new report schedule"""
    try:
        result = scheduler.add_schedule(schedule.dict())
        return JSONResponse(content=result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/schedules/{schedule_id}")
async def delete_schedule(schedule_id: str):
    """Delete a report schedule"""
    try:
        result = scheduler.remove_schedule(schedule_id)
        return JSONResponse(content=result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.patch("/api/schedules/{schedule_id}/toggle")
async def toggle_schedule(schedule_id: str, active: bool = Body(...)):
    """Enable or disable a schedule"""
    try:
        result = scheduler.toggle_schedule(schedule_id, active)
        return JSONResponse(content=result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/schedules/{schedule_id}/execute")
async def execute_schedule_now(schedule_id: str):
    """Manually trigger a schedule immediately"""
    try:
        result = scheduler.execute_schedule_now(schedule_id)
        return JSONResponse(content=result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# 4. COST ANALYSIS API
# =============================================================================

@app.get("/api/cost/config")
async def get_cost_config():
    """Get current cost configuration"""
    try:
        config = cost_service.get_cost_config()
        return JSONResponse(content=config)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/api/cost/config")
async def update_cost_config(config: CostConfigUpdate):
    """Update cost configuration"""
    try:
        result = cost_service.save_cost_config(config.dict(exclude_none=True))
        return JSONResponse(content=result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/cost/operational")
async def get_operational_costs(start_date: Optional[str] = None, end_date: Optional[str] = None):
    """Calculate operational costs for specified period"""
    try:
        start = datetime.fromisoformat(start_date) if start_date else None
        end = datetime.fromisoformat(end_date) if end_date else None
        
        result = cost_service.calculate_operational_costs(start, end)
        return JSONResponse(content=result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/cost/roi")
async def get_roi_analysis(start_date: Optional[str] = None, end_date: Optional[str] = None):
    """Calculate Return on Investment"""
    try:
        start = datetime.fromisoformat(start_date) if start_date else None
        end = datetime.fromisoformat(end_date) if end_date else None
        
        result = cost_service.calculate_roi(start, end)
        return JSONResponse(content=result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/cost/resource-utilization")
async def get_resource_utilization(start_date: Optional[str] = None, end_date: Optional[str] = None):
    """Get resource utilization metrics"""
    try:
        start = datetime.fromisoformat(start_date) if start_date else None
        end = datetime.fromisoformat(end_date) if end_date else None
        
        result = cost_service.calculate_resource_utilization(start, end)
        return JSONResponse(content=result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/cost/complete-analysis")
async def get_complete_cost_analysis(start_date: Optional[str] = None, end_date: Optional[str] = None):
    """Get complete cost analysis with all metrics"""
    try:
        start = datetime.fromisoformat(start_date) if start_date else None
        end = datetime.fromisoformat(end_date) if end_date else None
        
        analysis = {
            "generated_at": datetime.now().isoformat(),
            "period": f"{start_date or 'Beginning'} to {end_date or 'Now'}",
            "config": cost_service.get_cost_config(),
            "operational_costs": cost_service.calculate_operational_costs(start, end),
            "roi_analysis": cost_service.calculate_roi(start, end),
            "resource_utilization": cost_service.calculate_resource_utilization(start, end)
        }
        
        return JSONResponse(content=analysis)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# 5. EMAIL SERVICE API
# =============================================================================

@app.get("/api/email/test")
async def test_email_connection():
    """Test email service configuration"""
    try:
        result = email_service.test_email_connection()
        return JSONResponse(content=result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/email/config")
async def get_email_config():
    """Get email service configuration (without credentials)"""
    try:
        config = email_service.config.copy()
        config.pop('sender_password', None)  # Don't expose password
        return JSONResponse(content=config)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# =============================================================================
# VIOLATION ALERT API ENDPOINT
# =============================================================================

class ViolationAlertRequest(BaseModel):
    class_name: str
    confidence: float
    timestamp: Optional[str] = None
    location: str = "Main Camera"
    camera_id: str = "CAM-001"
    snapshot_path: Optional[str] = None
    video_path: Optional[str] = None

@app.post("/api/alerts/send-email")
async def send_violation_alert(request: ViolationAlertRequest):
    """Send immediate violation alert email to configured recipients"""
    try:
        violation_data = {
            "class_name": request.class_name,
            "confidence": request.confidence,
            "timestamp": request.timestamp or datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            "location": request.location,
            "camera_id": request.camera_id,
            "snapshot_path": request.snapshot_path,
            "video_path": request.video_path
        }
        
        result = email_service.send_violation_alert(
            violation_data,
            snapshot_path=request.snapshot_path,
            video_path=request.video_path
        )
        return JSONResponse(content=result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==================================================================================
# ADVANCED ANALYTICS API ENDPOINTS
# ==================================================================================

class ForecastRequest(BaseModel):
    days: int = 30
    confidence_level: float = 0.95

class AnomalyRequest(BaseModel):
    method: str = "zscore"  # zscore, isolation_forest, iqr
    threshold: float = 2.0

@app.get("/api/analytics/predictive/forecast")
async def get_forecast(days: int = 30):
    """Get predictive forecast for future detections"""
    if not HAS_ADVANCED_ANALYTICS:
        raise HTTPException(status_code=503, detail="Advanced Analytics module not available")
    
    try:
        forecast = get_predictive_forecast(csv_file, days=days)
        return JSONResponse(content=forecast)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/analytics/predictive/trend")
async def get_trend_analysis(days: int = 30):
    """Get trend analysis from predictive analytics"""
    if not HAS_ADVANCED_ANALYTICS:
        raise HTTPException(status_code=503, detail="Advanced Analytics module not available")
    
    try:
        trend = get_trend_analysis(csv_file, days=days)
        return JSONResponse(content=trend)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/analytics/anomalies/detect")
async def detect_dataset_anomalies(request: AnomalyRequest):
    """Detect anomalies in detection data"""
    if not HAS_ADVANCED_ANALYTICS:
        raise HTTPException(status_code=503, detail="Advanced Analytics module not available")
    
    try:
        anomalies = detect_anomalies(csv_file, method=request.method, threshold=request.threshold)
        return JSONResponse(content=anomalies)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/analytics/anomalies/behavioral")
async def detect_behavior_anomalies(threshold: float = 2.0):
    """Detect behavioral anomalies"""
    if not HAS_ADVANCED_ANALYTICS:
        raise HTTPException(status_code=503, detail="Advanced Analytics module not available")
    
    try:
        anomalies = detect_behavioral_anomalies(csv_file, threshold=threshold)
        return JSONResponse(content=anomalies)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/analytics/kpis/advanced")
async def get_advanced_kpis():
    """Get advanced KPI calculations"""
    if not HAS_ADVANCED_ANALYTICS:
        raise HTTPException(status_code=503, detail="Advanced Analytics module not available")
    
    try:
        kpis = calculate_kpis(csv_file)
        return JSONResponse(content=kpis)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/analytics/correlation")
async def get_correlations():
    """Get correlation analysis"""
    if not HAS_ADVANCED_ANALYTICS:
        raise HTTPException(status_code=503, detail="Advanced Analytics module not available")
    
    try:
        correlations = get_correlation_analysis(csv_file)
        return JSONResponse(content=correlations)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/analytics/percentiles")
async def get_percentiles():
    """Get percentile analysis"""
    if not HAS_ADVANCED_ANALYTICS:
        raise HTTPException(status_code=503, detail="Advanced Analytics module not available")
    
    try:
        percentiles = get_percentile_analysis(csv_file)
        return JSONResponse(content=percentiles)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==================================================================================
# ADVANCED EMAIL REPORTING API ENDPOINTS
# ==================================================================================

class SendReportRequest(BaseModel):
    report_type: str = "daily"  # daily, weekly, monthly
    template_type: str = "summary"  # summary, detailed, compliance, operational
    recipient_email: str
    subject: Optional[str] = None
    include_pdf: bool = False  # Include PDF attachment

class ScheduleReportRequest(BaseModel):
    report_type: str
    template_type: str
    recipient_email: str
    schedule_type: str  # daily, weekly, monthly
    day_of_week: Optional[int] = None
    day_of_month: Optional[int] = None
    time: str = "09:00"

# ==================================================================================
# CHART DATA API ENDPOINTS (for Analytics Dashboard)
# ==================================================================================

@app.get("/api/analytics/charts/class-distribution")
async def get_class_distribution_chart():
    """Get data for class distribution pie chart"""
    try:
        df = pd.read_csv(csv_file)
        if df.empty:
            return JSONResponse(content={"labels": [], "data": [], "colors": []})
        
        # Count by class
        class_counts = df['Class'].value_counts()
        labels = class_counts.index.tolist()
        data = class_counts.values.tolist()
        
        # Generate colors
        colors = []
        base_colors = ['#00d4ff', '#7c3aed', '#ec4899', '#22c55e', '#f59e0b', '#ef4444', '#06b6d4', '#8b5cf6']
        for i in range(len(labels)):
            colors.append(base_colors[i % len(base_colors)])
        
        return JSONResponse(content={
            "labels": labels,
            "data": data,
            "colors": colors
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/analytics/charts/violation-trend")
async def get_violation_trend_chart(days: int = 7):
    """Get data for violation trend line chart"""
    try:
        df = pd.read_csv(csv_file)
        if df.empty:
            return JSONResponse(content={"labels": [], "violations": [], "detections": []})
        
        df['Timestamp'] = pd.to_datetime(df['Timestamp'])
        
        # Filter by last N days
        start_date = datetime.now() - timedelta(days=days)
        df = df[df['Timestamp'] >= start_date]
        
        if df.empty:
            return JSONResponse(content={"labels": [], "violations": [], "detections": []})
        
        # Group by date
        df['Date'] = df['Timestamp'].dt.date
        daily = df.groupby('Date').size()
        daily_violations = df[df['Restricted Area Violation'] == 'Yes'].groupby('Date').size()
        
        # Create complete date range
        date_range = pd.date_range(start=df['Date'].min(), end=df['Date'].max(), freq='D')
        labels = [d.strftime('%Y-%m-%d') for d in date_range]
        
        violations_data = []
        detections_data = []
        
        for date in date_range:
            date_str = date.date()
            detections_data.append(int(daily.get(date_str, 0)))
            violations_data.append(int(daily_violations.get(date_str, 0)))
        
        return JSONResponse(content={
            "labels": labels,
            "violations": violations_data,
            "detections": detections_data
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/analytics/charts/confidence-by-class")
async def get_confidence_by_class_chart():
    """Get data for confidence by class bar chart"""
    try:
        df = pd.read_csv(csv_file)
        if df.empty:
            return JSONResponse(content={"labels": [], "data": []})
        
        # Calculate average confidence by class
        avg_confidence = df.groupby('Class')['Confidence'].mean() * 100
        avg_confidence = avg_confidence.sort_values(ascending=True)
        
        labels = avg_confidence.index.tolist()
        data = [round(v, 2) for v in avg_confidence.values.tolist()]
        
        return JSONResponse(content={
            "labels": labels,
            "data": data
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/analytics/charts/hourly-activity")
async def get_hourly_activity_chart():
    """Get data for hourly activity bar chart"""
    try:
        df = pd.read_csv(csv_file)
        if df.empty:
            return JSONResponse(content={"labels": [], "detections": [], "violations": []})
        
        df['Timestamp'] = pd.to_datetime(df['Timestamp'])
        df['Hour'] = df['Timestamp'].dt.hour
        
        # Count by hour
        hourly_detections = df.groupby('Hour').size()
        hourly_violations = df[df['Restricted Area Violation'] == 'Yes'].groupby('Hour').size()
        
        labels = [f"{h:02d}:00" for h in range(24)]
        detections = [int(hourly_detections.get(h, 0)) for h in range(24)]
        violations = [int(hourly_violations.get(h, 0)) for h in range(24)]
        
        return JSONResponse(content={
            "labels": labels,
            "detections": detections,
            "violations": violations
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/analytics/charts/violation-status")
async def get_violation_status_chart():
    """Get data for violation status doughnut chart"""
    try:
        df = pd.read_csv(csv_file)
        if df.empty:
            return JSONResponse(content={"labels": [], "data": [], "colors": []})
        
        # Count violations vs safe
        violations = len(df[df['Restricted Area Violation'] == 'Yes'])
        safe = len(df[df['Restricted Area Violation'] == 'No'])
        
        labels = ['Violations', 'Safe']
        data = [violations, safe]
        colors = ['#ef4444', '#22c55e']
        
        return JSONResponse(content={
            "labels": labels,
            "data": data,
            "colors": colors
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/analytics/stats")
async def get_analytics_stats():
    """Get summary statistics for analytics dashboard"""
    try:
        df = pd.read_csv(csv_file)
        
        if df.empty:
            return JSONResponse(content={
                "total_detections": 0,
                "total_violations": 0,
                "total_safe": 0,
                "violation_rate": 0,
                "avg_confidence": 0,
                "top_class": "-"
            })
        
        total = len(df)
        violations = len(df[df['Restricted Area Violation'] == 'Yes'])
        safe = total - violations
        violation_rate = round(violations / total * 100, 2) if total > 0 else 0
        avg_confidence = round(df['Confidence'].mean() * 100, 2)
        top_class = df['Class'].mode().iloc[0] if not df.empty else "-"
        
        return JSONResponse(content={
            "total_detections": total,
            "total_violations": violations,
            "total_safe": safe,
            "violation_rate": violation_rate,
            "avg_confidence": avg_confidence,
            "top_class": top_class
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/email/send-report")
async def send_report(request: SendReportRequest):
    """Send a report immediately"""
    if not HAS_EMAIL_REPORTING:
        raise HTTPException(status_code=503, detail="Email Reporting module not available")
    
    try:
        result = advanced_email_reporter.send_scheduled_report(
            report_type=request.report_type,
            template_type=request.template_type,
            recipients=[request.recipient_email],  # Pass as a list
            include_csv=True,
            include_pdf=request.include_pdf
        )
        return JSONResponse(content=result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/email/schedule-report")
async def schedule_report(request: ScheduleReportRequest):
    """Schedule a recurring report"""
    if not HAS_EMAIL_REPORTING:
        raise HTTPException(status_code=503, detail="Email Reporting module not available")
    
    try:
        schedule = schedule_manager.add_schedule(
            report_type=request.report_type,
            template_type=request.template_type,
            recipient=request.recipient_email,
            schedule_type=request.schedule_type,
            day_of_week=request.day_of_week,
            day_of_month=request.day_of_month,
            time=request.time
        )
        return JSONResponse(content=schedule)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/email/schedules")
async def get_email_schedules():
    """Get all scheduled reports"""
    if not HAS_EMAIL_REPORTING:
        raise HTTPException(status_code=503, detail="Email Reporting module not available")
    
    try:
        schedules = schedule_manager.get_schedules()
        return JSONResponse(content=schedules)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/email/schedules/{schedule_id}")
async def delete_email_schedule(schedule_id: str):
    """Delete a scheduled report"""
    if not HAS_EMAIL_REPORTING:
        raise HTTPException(status_code=503, detail="Email Reporting module not available")
    
    try:
        result = schedule_manager.delete_schedule(schedule_id)
        return JSONResponse(content=result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/email/templates")
async def get_email_templates():
    """Get available report templates"""
    if not HAS_EMAIL_REPORTING:
        raise HTTPException(status_code=503, detail="Email Reporting module not available")
    
    try:
        templates_list = [
            {
                "name": "summary",
                "description": "Executive summary with key metrics and recommendations"
            },
            {
                "name": "detailed",
                "description": "Detailed report with charts and comprehensive analysis"
            },
            {
                "name": "compliance",
                "description": "Compliance-focused report for regulatory requirements"
            },
            {
                "name": "operational",
                "description": "Operational metrics for security teams"
            }
        ]
        return JSONResponse(content={"templates": templates_list})
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))




# =============================================================================
# API DOCUMENTATION & HEALTH CHECK
# =============================================================================

@app.get("/api/health")
async def health_check():
    """API health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "services": {
            "analytics": "operational",
            "reports": "operational",
            "cost_analysis": "operational",
            "email": "operational" if email_service.config['enabled'] else "disabled",
            "scheduler": "operational" if scheduler.scheduler.running else "stopped"
        }
    }

@app.get("/api/info")
async def api_info():
    """Get API information and available endpoints"""
    return {
        "name": "Real-Time Restricted Area Monitoring System API",
        "version": "2.0.0",
        "description": "Advanced Business Intelligence & Reporting API",
        "features": {
            "analytics": {
                "description": "Advanced analytics with custom KPI tracking",
                "endpoints": [
                    "GET /api/analytics/kpis/mttr",
                    "GET /api/analytics/kpis/false-positive-rate",
                    "GET /api/analytics/kpis/coverage",
                    "GET /api/analytics/executive-summary",
                    "GET /api/analytics/trend-analysis",
                    "GET /api/analytics/dashboard"
                ]
            },
            "reports": {
                "description": "Automated report generation",
                "endpoints": [
                    "GET /api/reports/daily",
                    "GET /api/reports/weekly",
                    "GET /api/reports/monthly",
                    "GET /api/reports/compliance/{type}",
                    "POST /api/reports/send-email"
                ]
            },
            "scheduling": {
                "description": "Report scheduling and automation",
                "endpoints": [
                    "GET /api/schedules",
                    "POST /api/schedules",
                    "DELETE /api/schedules/{id}",
                    "PATCH /api/schedules/{id}/toggle",
                    "POST /api/schedules/{id}/execute"
                ]
            },
            "cost_analysis": {
                "description": "Cost tracking and ROI calculation",
                "endpoints": [
                    "GET /api/cost/config",
                    "PUT /api/cost/config",
                    "GET /api/cost/operational",
                    "GET /api/cost/roi",
                    "GET /api/cost/resource-utilization",
                    "GET /api/cost/complete-analysis"
                ]
            },
            "email": {
                "description": "Email service management",
                "endpoints": [
                    "GET /api/email/test",
                    "GET /api/email/config"
                ]
            },
            "advanced_analytics": {
                "description": "Advanced predictive analytics and anomaly detection",
                "endpoints": [
                    "GET /api/analytics/predictive/forecast",
                    "GET /api/analytics/predictive/trend",
                    "POST /api/analytics/anomalies/detect",
                    "POST /api/analytics/anomalies/behavioral",
                    "GET /api/analytics/kpis/advanced",
                    "GET /api/analytics/correlation",
                    "GET /api/analytics/percentiles"
                ]
            },
            "advanced_email_reporting": {
                "description": "Advanced email report generation and scheduling",
                "endpoints": [
                    "POST /api/email/send-report",
                    "POST /api/email/schedule-report",
                    "GET /api/email/schedules",
                    "DELETE /api/email/schedules/{schedule_id}",
                    "GET /api/email/templates"
                ]
            },
            "activity_feed": {
                "description": "Real-time activity stream and detection events",
                "endpoints": [
                    "GET /api/activity/feed",
                    "GET /api/activity/detections",
                    "WS /ws/activity"
                ]
            },
            "system_health": {
                "description": "System health monitoring and camera status",
                "endpoints": [
                    "GET /api/health/detailed",
                    "GET /api/health/cameras",
                    "GET /api/health/uptime"
                ]
            },
            "camera_management": {
                "description": "Camera configuration and management",
                "endpoints": [
                    "GET /api/cameras",
                    "POST /api/cameras",
                    "GET /api/cameras/{id}",
                    "PUT /api/cameras/{id}",
                    "DELETE /api/cameras/{id}"
                ]
            },
            "user_activity": {
                "description": "User activity logging and statistics",
                "endpoints": [
                    "GET /api/users/activity",
                    "POST /api/users/activity",
                    "GET /api/users/stats"
                ]
            }
        },
        "documentation": "/docs"
    }


# =============================================================================
# ACTIVITY FEED API ENDPOINTS
# =============================================================================

# In-memory activity feed for real-time updates
activity_feed = []
ACTIVITY_FEED_MAX_SIZE = 1000

def sync_activity_from_csv():
    """Sync activity feed from detection CSV file - called on startup"""
    global activity_feed
    synced_count = 0
    try:
        # Use absolute path for CSV file
        csv_path = os.path.abspath(csv_file)
        print(f"Attempting to sync from CSV: {csv_path}")
        
        if os.path.exists(csv_path):
            df = pd.read_csv(csv_path)
            if not df.empty:
                # Handle timestamp parsing - try multiple formats
                def parse_timestamp(ts):
                    if pd.isna(ts):
                        return datetime.now()
                    try:
                        return pd.to_datetime(ts)
                    except:
                        return datetime.now()
                
                df['Timestamp'] = df['Timestamp'].apply(parse_timestamp)
                df = df.sort_values('Timestamp', ascending=False)
                
                # Clear existing activity feed before syncing
                activity_feed.clear()
                
                # Convert CSV detections to activity feed events
                for idx, row in df.head(500).iterrows():  # Limit to 500 entries
                    try:
                        is_violation = str(row.get('Restricted Area Violation', 'No')).lower() == 'yes'
                        confidence = float(row.get('Confidence', 0))
                        class_name = str(row.get('Class', 'Unknown'))
                        
                        event = {
                            "id": str(len(activity_feed) + 1),
                            "timestamp": row['Timestamp'].strftime('%Y-%m-%dT%H:%M:%S') if hasattr(row['Timestamp'], 'strftime') else str(row['Timestamp']),
                            "type": "detection",
                            "title": f"Detection: {class_name}",
                            "description": f"Confidence: {confidence*100:.1f}%",
                            "is_violation": is_violation,
                            "class": class_name,
                            "confidence": round(confidence * 100, 2)
                        }
                        activity_feed.append(event)
                        synced_count += 1
                    except Exception as e:
                        print(f"Error processing row: {e}")
                        continue
                
                print(f"✓ Successfully synced {synced_count} activity events from CSV (path: {csv_path})")
            else:
                print("CSV file is empty - no activity to sync")
        else:
            print(f"CSV file not found at: {csv_path}")
    except Exception as e:
        print(f"Error syncing activity from CSV: {e}")
        import traceback
        traceback.print_exc()
    
    return synced_count

def sync_activity_from_user_activity():
    """Sync activity feed from user_activity.json file"""
    global activity_feed
    synced_count = 0
    try:
        user_activity_path = os.path.abspath("data/user_activity.json")
        print(f"Attempting to sync from user activity: {user_activity_path}")
        
        if os.path.exists(user_activity_path):
            with open(user_activity_path, 'r') as f:
                data = json.load(f)
            activities = data.get("activities", [])
            
            for activity in activities[:200]:  # Limit to 200 entries
                try:
                    event = {
                        "id": str(len(activity_feed) + 1),
                        "timestamp": activity.get("timestamp", datetime.now().isoformat()),
                        "type": "user_activity",
                        "title": f"{activity.get('user', 'Unknown')}: {activity.get('action', 'Unknown')}",
                        "description": activity.get("details", ""),
                        "status": activity.get("status", "success"),
                        "user": activity.get("user", "Unknown"),
                        "action": activity.get("action", "Unknown")
                    }
                    activity_feed.append(event)
                    synced_count += 1
                except Exception as e:
                    print(f"Error processing activity: {e}")
                    continue
            
            print(f"✓ Successfully synced {synced_count} user activity events")
        else:
            print(f"User activity file not found at: {user_activity_path}")
    except Exception as e:
        print(f"Error syncing user activity: {e}")
        import traceback
        traceback.print_exc()
    
    return synced_count

def refresh_activity_feed():
    """Refresh the entire activity feed from all sources"""
    global activity_feed
    activity_feed.clear()
    csv_count = sync_activity_from_csv()
    user_count = sync_activity_from_user_activity()
    print(f"Activity feed refresh complete: {len(activity_feed)} total events")
    return len(activity_feed)

# Initialize activity feed on module load
print("Initializing activity feed from CSV and user activity...")
refresh_activity_feed()

def add_activity_event(event_type: str, data: dict):
    """Add an event to the activity feed"""
    event = {
        "id": str(len(activity_feed) + 1),
        "timestamp": datetime.now().isoformat(),
        "type": event_type,
        "data": data
    }
    activity_feed.insert(0, event)
    # Keep feed at max size
    if len(activity_feed) > ACTIVITY_FEED_MAX_SIZE:
        activity_feed.pop()
    return event

@app.get("/api/activity/feed")
async def get_activity_feed(limit: int = 50, event_type: str = None):
    """Get recent activity feed events"""
    try:
        events = activity_feed[:limit]
        
        if event_type:
            events = [e for e in events if e.get("type") == event_type]
        
        return JSONResponse(content={
            "events": events,
            "total_count": len(activity_feed),
            "displayed_count": len(events)
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/activity/sync")
async def sync_activity():
    """Manually sync activity feed from CSV and user activity"""
    try:
        count = refresh_activity_feed()
        return JSONResponse(content={
            "success": True,
            "total_events": count,
            "message": f"Activity feed synced successfully with {count} events"
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/activity/detections")
async def get_detection_activity(limit: int = 100):
    """Get detection activity stream"""
    try:
        # Read from CSV for detection data
        df = pd.read_csv(csv_file)
        
        if df.empty:
            return JSONResponse(content={"events": [], "total_count": 0})
        
        # Sort by timestamp descending
        df['Timestamp'] = pd.to_datetime(df['Timestamp'])
        df = df.sort_values('Timestamp', ascending=False)
        
        # Take recent detections
        recent = df.head(limit)
        
        events = []
        for _, row in recent.iterrows():
            events.append({
                "id": str(len(events) + 1),
                "timestamp": row['Timestamp'].strftime('%Y-%m-%d %H:%M:%S'),
                "type": "detection",
                "class": row['Class'],
                "confidence": round(float(row['Confidence']) * 100, 2),
                "is_violation": row['Restricted Area Violation'] == "Yes"
            })
        
        return JSONResponse(content={
            "events": events,
            "total_count": len(df),
            "displayed_count": len(events)
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.websocket("/ws/activity")
async def websocket_activity_feed(websocket: WebSocket):
    """WebSocket for real-time activity feed"""
    await websocket.accept()
    
    try:
        while True:
            # Send recent activity
            if activity_feed:
                await websocket.send_json({"events": activity_feed[:20]})
            else:
                # Fallback to detection data
                df = pd.read_csv(csv_file)
                if not df.empty:
                    df['Timestamp'] = pd.to_datetime(df['Timestamp'])
                    df = df.sort_values('Timestamp', ascending=False)
                    recent = df.head(20)
                    events = []
                    for _, row in recent.iterrows():
                        events.append({
                            "timestamp": row['Timestamp'].strftime('%Y-%m-%d %H:%M:%S'),
                            "type": "detection",
                            "class": row['Class'],
                            "confidence": round(float(row['Confidence']) * 100, 2),
                            "is_violation": row['Restricted Area Violation'] == "Yes"
                        })
                    await websocket.send_json({"events": events})
            
            await asyncio.sleep(2)  # Send updates every 2 seconds
    except Exception as e:
        print(f"WebSocket activity error: {e}")
    finally:
        try:
            await websocket.close()
        except:
            pass


# =============================================================================
# SYSTEM HEALTH API ENDPOINTS
# =============================================================================

import psutil
import platform

system_start_time = datetime.now()

@app.get("/api/health/detailed")
async def get_detailed_health():
    """Get detailed system health information"""
    try:
        # CPU usage
        cpu_percent = psutil.cpu_percent(interval=1)
        cpu_count = psutil.cpu_count()
        
        # Memory usage
        memory = psutil.virtual_memory()
        memory_percent = memory.percent
        memory_used_gb = round(memory.used / (1024**3), 2)
        memory_total_gb = round(memory.total / (1024**3), 2)
        
        # Disk usage
        disk = psutil.disk_usage('/')
        disk_percent = disk.percent
        disk_used_gb = round(disk.used / (1024**3), 2)
        disk_total_gb = round(disk.total / (1024**3), 2)
        
        # Network info
        network = psutil.net_io_counters()
        bytes_sent = round(network.bytes_sent / (1024**2), 2)
        bytes_recv = round(network.bytes_recv / (1024**2), 2)
        network_connected = True  # If we can get network stats, we're connected
        
        # Process info
        process = psutil.Process()
        process_memory_mb = round(process.memory_info().rss / (1024**2), 2)
        process_cpu_percent = process.cpu_percent(interval=0.5)
        
        # Get process thread count and open files
        try:
            active_threads = process.num_threads()
        except:
            active_threads = 0
        
        try:
            open_files = len(process.open_files())
        except:
            open_files = 0
        
        # Python version
        import sys
        python_version = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
        
        # Camera status (from cameras.json)
        try:
            with open("data/cameras.json", 'r') as f:
                cameras_data = json.load(f)
            cameras = cameras_data.get("cameras", [])
            camera_count = len(cameras)
            online_cameras = sum(1 for c in cameras if c.get("status") == "online")
        except:
            camera_count = 0
            online_cameras = 0
        
        # Uptime
        uptime_seconds = (datetime.now() - system_start_time).total_seconds()
        uptime_formatted = str(timedelta(seconds=int(uptime_seconds)))
        
        # Return flat structure for frontend compatibility
        return JSONResponse(content={
            "status": "healthy" if cpu_percent < 90 and memory_percent < 90 else "warning",
            "timestamp": datetime.now().isoformat(),
            "cpu_percent": cpu_percent,
            "memory_percent": memory_percent,
            "disk_percent": disk_percent,
            "network_connected": network_connected,
            "uptime_formatted": uptime_formatted,
            "active_threads": active_threads,
            "open_files": open_files,
            "python_version": python_version,
            "cpu_count": cpu_count,
            "memory_used_gb": memory_used_gb,
            "memory_total_gb": memory_total_gb,
            "disk_used_gb": disk_used_gb,
            "disk_total_gb": disk_total_gb,
            "bytes_sent_mb": bytes_sent,
            "bytes_recv_mb": bytes_recv,
            "process_memory_mb": process_memory_mb,
            "process_cpu_percent": process_cpu_percent,
            "camera_count": camera_count,
            "online_cameras": online_cameras,
            "offline_cameras": camera_count - online_cameras
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/health/cameras")
async def get_camera_health():
    """Get camera status from cameras.json"""
    try:
        with open("data/cameras.json", 'r') as f:
            cameras_data = json.load(f)
        cameras = cameras_data.get("cameras", [])
        
        camera_status = []
        for camera in cameras:
            camera_status.append({
                "id": camera.get("id"),
                "name": camera.get("name"),
                "location": camera.get("location"),
                "status": camera.get("status", "unknown"),
                "enabled": camera.get("enabled", True),
                "last_active": camera.get("last_active"),
                "url": camera.get("url")
            })
        
        return JSONResponse(content={
            "cameras": camera_status,
            "total_count": len(cameras),
            "online_count": sum(1 for c in cameras if c.get("status") == "online"),
            "offline_count": sum(1 for c in cameras if c.get("status") != "online")
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/health/uptime")
async def get_system_uptime():
    """Get system uptime information"""
    try:
        uptime_seconds = (datetime.now() - system_start_time).total_seconds()
        
        # Format uptime
        days = int(uptime_seconds // 86400)
        hours = int((uptime_seconds % 86400) // 3600)
        minutes = int((uptime_seconds % 3600) // 60)
        
        return JSONResponse(content={
            "start_time": system_start_time.isoformat(),
            "uptime_seconds": int(uptime_seconds),
            "uptime_formatted": str(timedelta(seconds=int(uptime_seconds))),
            "uptime_days": days,
            "uptime_hours": hours,
            "uptime_minutes": minutes
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# CAMERA MANAGEMENT API ENDPOINTS
# =============================================================================

CAMERAS_FILE = "data/cameras.json"

def load_cameras():
    """Load cameras from JSON file"""
    try:
        with open(CAMERAS_FILE, 'r') as f:
            data = json.load(f)
        return data.get("cameras", [])
    except:
        return []

def save_cameras(cameras):
    """Save cameras to JSON file"""
    with open(CAMERAS_FILE, 'w') as f:
        json.dump({"cameras": cameras}, f, indent=2)

def generate_camera_id():
    """Generate unique camera ID"""
    import uuid
    return f"cam_{uuid.uuid4().hex[:8]}"

class CameraConfig(BaseModel):
    name: str
    url: str
    location: str = ""
    resolution: str = "640x480"
    fps: int = 20
    detection_classes: List[str] = []
    alert_classes: List[str] = []
    enabled: bool = True

@app.get("/api/cameras")
async def get_all_cameras():
    """Get all cameras"""
    try:
        cameras = load_cameras()
        return JSONResponse(content={
            "cameras": cameras,
            "total_count": len(cameras)
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/cameras")
async def add_camera(config: CameraConfig):
    """Add a new camera"""
    try:
        cameras = load_cameras()
        
        # Check for duplicate name
        if any(c.get("name") == config.name for c in cameras):
            raise HTTPException(status_code=400, detail="Camera with this name already exists")
        
        new_camera = {
            "id": generate_camera_id(),
            "name": config.name,
            "url": config.url,
            "enabled": config.enabled,
            "resolution": config.resolution,
            "fps": config.fps,
            "location": config.location,
            "detection_classes": config.detection_classes,
            "alert_classes": config.alert_classes,
            "created_at": datetime.now().isoformat(),
            "last_active": None,
            "status": "offline"
        }
        
        cameras.append(new_camera)
        save_cameras(cameras)
        
        # Log activity
        add_activity_event("camera_added", {
            "camera_id": new_camera["id"],
            "camera_name": new_camera["name"]
        })
        
        return JSONResponse(content={
            "success": True,
            "camera": new_camera,
            "message": f"Camera '{config.name}' added successfully"
        })
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/cameras/{camera_id}")
async def get_camera(camera_id: str):
    """Get camera details"""
    try:
        cameras = load_cameras()
        camera = next((c for c in cameras if c.get("id") == camera_id), None)
        
        if not camera:
            raise HTTPException(status_code=404, detail="Camera not found")
        
        return JSONResponse(content={"camera": camera})
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/api/cameras/{camera_id}")
async def update_camera(camera_id: str, config: CameraConfig):
    """Update camera configuration"""
    try:
        cameras = load_cameras()
        index = next((i for i, c in enumerate(cameras) if c.get("id") == camera_id), None)
        
        if index is None:
            raise HTTPException(status_code=404, detail="Camera not found")
        
        # Check for duplicate name (excluding current camera)
        if any(c.get("name") == config.name and c.get("id") != camera_id for c in cameras):
            raise HTTPException(status_code=400, detail="Camera with this name already exists")
        
        cameras[index].update({
            "name": config.name,
            "url": config.url,
            "enabled": config.enabled,
            "resolution": config.resolution,
            "fps": config.fps,
            "location": config.location,
            "detection_classes": config.detection_classes,
            "alert_classes": config.alert_classes
        })
        
        save_cameras(cameras)
        
        # Log activity
        add_activity_event("camera_updated", {
            "camera_id": camera_id,
            "camera_name": config.name
        })
        
        return JSONResponse(content={
            "success": True,
            "camera": cameras[index],
            "message": f"Camera '{config.name}' updated successfully"
        })
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/cameras/{camera_id}")
async def delete_camera(camera_id: str):
    """Delete a camera"""
    try:
        cameras = load_cameras()
        index = next((i for i, c in enumerate(cameras) if c.get("id") == camera_id), None)
        
        if index is None:
            raise HTTPException(status_code=404, detail="Camera not found")
        
        deleted_camera = cameras.pop(index)
        save_cameras(cameras)
        
        # Log activity
        add_activity_event("camera_deleted", {
            "camera_id": camera_id,
            "camera_name": deleted_camera.get("name")
        })
        
        return JSONResponse(content={
            "success": True,
            "message": f"Camera '{deleted_camera.get('name')}' deleted successfully"
        })
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# USER ACTIVITY LOGGING API ENDPOINTS
# =============================================================================

import hashlib
import secrets

USER_ACTIVITY_FILE = "data/user_activity.json"
USERS_FILE = "data/users.json"

def load_user_activity():
    """Load user activity from JSON file"""
    try:
        with open(USER_ACTIVITY_FILE, 'r') as f:
            data = json.load(f)
        return data.get("activities", [])
    except:
        return []

def save_user_activity(activities):
    """Save user activity to JSON file"""
    with open(USER_ACTIVITY_FILE, 'w') as f:
        json.dump({"activities": activities[-1000:]}, f, indent=2)  # Keep last 1000 entries

def load_users():
    """Load users from JSON file"""
    try:
        with open(USERS_FILE, 'r') as f:
            data = json.load(f)
        return data
    except:
        return {}

def save_users(users):
    """Save users to JSON file"""
    with open(USERS_FILE, 'w') as f:
        json.dump(users, f, indent=2)

def hash_password(password: str) -> str:
    """Hash password using SHA-256"""
    return hashlib.sha256(password.encode()).hexdigest()

def verify_password(password: str, password_hash: str) -> bool:
    """Verify password against hash"""
    return hash_password(password) == password_hash

def log_activity(user: str, action: str, details: str = "", ip_address: str = "", status: str = "success"):
    """Log a user activity event"""
    activity = {
        "id": str(len(load_user_activity()) + 1),
        "timestamp": datetime.now().isoformat(),
        "user": user,
        "action": action,
        "details": details,
        "ip_address": ip_address,
        "status": status
    }
    
    activities = load_user_activity()
    activities.insert(0, activity)
    # Keep last 1000 entries
    if len(activities) > 1000:
        activities = activities[:1000]
    save_user_activity(activities)
    
    # Also add to real-time activity feed
    add_activity_event("user_activity", {
        "user": user,
        "action": action,
        "status": status
    })
    
    return activity

def generate_token():
    """Generate a simple auth token"""
    return secrets.token_hex(32)

class ActivityLogRequest(BaseModel):
    user: str
    action: str
    details: str = ""
    ip_address: str = ""
    status: str = "success"

class LoginRequest(BaseModel):
    username: str
    password: str

class SignupRequest(BaseModel):
    username: str
    password: str
    email: str = ""

# Active sessions storage
active_sessions = {}

@app.get("/api/users/activity")
async def get_user_activity(limit: int = 100, user: str = None, action: str = None):
    """Get user activity log"""
    try:
        activities = load_user_activity()
        
        if user:
            activities = [a for a in activities if a.get("user") == user]
        if action:
            activities = [a for a in activities if a.get("action") == action]
        
        activities = activities[:limit]
        
        return JSONResponse(content={
            "activities": activities,
            "total_count": len(load_user_activity()),
            "displayed_count": len(activities)
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/users/activity")
async def log_user_activity(request: ActivityLogRequest):
    """Log a new user activity event"""
    try:
        activity = log_activity(
            user=request.user,
            action=request.action,
            details=request.details,
            ip_address=request.ip_address,
            status=request.status
        )
        
        return JSONResponse(content={
            "success": True,
            "activity": activity,
            "message": "Activity logged successfully"
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# =============================================================================
# AUTHENTICATION API ENDPOINTS
# =============================================================================

@app.post("/api/auth/login")
async def login(request: LoginRequest, client_host: str = "127.0.0.1"):
    """Authenticate user and log login activity"""
    try:
        # Normalize username to lowercase for case-insensitive comparison
        username = request.username.strip().lower()
        password = request.password
        
        users = load_users()
        
        # Check if user exists (case-insensitive search)
        user_found = None
        for user_key in users.keys():
            if user_key.lower() == username:
                user_found = user_key
                break
        
        if user_found is None:
            log_activity(
                user=username,
                action="login_failed",
                details="User not found",
                ip_address=client_host,
                status="failed"
            )
            raise HTTPException(status_code=401, detail="Invalid username or password")
        
        # Verify password using the original stored username
        stored_hash = users[user_found]
        if not verify_password(password, stored_hash):
            log_activity(
                user=user_found,
                action="login_failed",
                details="Invalid password",
                ip_address=client_host,
                status="failed"
            )
            raise HTTPException(status_code=401, detail="Invalid username or password")
        
        # Generate token and create session
        token = generate_token()
        active_sessions[token] = {
            "username": user_found,  # Use the original stored username
            "created_at": datetime.now().isoformat(),
            "ip_address": client_host
        }
        
        # Log successful login using the original stored username
        log_activity(
            user=user_found,
            action="login_success",
            details="User logged in successfully",
            ip_address=client_host,
            status="success"
        )
        
        return JSONResponse(content={
            "success": True,
            "token": token,
            "username": user_found,  # Return the original stored username
            "message": "Login successful"
        })
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/auth/logout")
async def logout(token: str = None, client_host: str = "127.0.0.1"):
    """Log out user and invalidate session"""
    try:
        # If token provided, get username from session
        username = None
        if token and token in active_sessions:
            username = active_sessions[token].get("username")
            del active_sessions[token]
        
        # Log logout activity
        if username:
            log_activity(
                user=username,
                action="logout",
                details="User logged out",
                ip_address=client_host,
                status="success"
            )
        
        return JSONResponse(content={
            "success": True,
            "message": "Logout successful"
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/auth/signup")
async def signup(request: SignupRequest, client_host: str = "127.0.0.1"):
    """Create new user account"""
    try:
        username = request.username.strip()
        password = request.password
        email = request.email.strip()
        
        users = load_users()
        
        # Check if user already exists
        if username in users:
            raise HTTPException(status_code=400, detail="Username already exists")
        
        # Create new user
        users[username] = hash_password(password)
        save_users(users)
        
        # Log signup activity
        log_activity(
            user=username,
            action="signup_success",
            details=f"New user registered${f' with email: {email}' if email else ''}",
            ip_address=client_host,
            status="success"
        )
        
        # Generate token for auto-login
        token = generate_token()
        active_sessions[token] = {
            "username": username,
            "created_at": datetime.now().isoformat(),
            "ip_address": client_host
        }
        
        return JSONResponse(content={
            "success": True,
            "token": token,
            "username": username,
            "message": "Account created successfully"
        })
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/users/stats")
async def get_user_stats():
    """Get user access statistics with proper counts"""
    try:
        activities = load_user_activity()
        
        if not activities:
            return JSONResponse(content={
                "total_users": 0,
                "total_actions": 0,
                "active_today": 0,
                "unique_ips": 0
            })
        
        # Get unique users from activity log
        unique_users = set(a.get("user") for a in activities if a.get("user"))
        
        # Get unique IPs
        unique_ips = set(a.get("ip_address") for a in activities if a.get("ip_address"))
        
        # Get users active today (last 24 hours)
        cutoff = (datetime.now() - timedelta(hours=24)).isoformat()
        active_today_users = set(a.get("user") for a in activities 
                                  if a.get("timestamp") >= cutoff and a.get("user"))
        
        # Total actions (excluding system events)
        user_actions = [a for a in activities if a.get("user") and a.get("user") != "system"]
        
        return JSONResponse(content={
            "total_users": len(unique_users),
            "total_actions": len(user_actions),
            "active_today": len(active_today_users),
            "unique_ips": len(unique_ips),
            "timestamp": datetime.now().isoformat()
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/users/sessions")
async def get_active_sessions():
    """Get list of active sessions"""
    return JSONResponse(content={
        "active_sessions": len(active_sessions),
        "sessions": [
            {
                "username": session["username"],
                "ip_address": session["ip_address"],
                "created_at": session["created_at"]
            }
            for token, session in active_sessions.items()
        ]
    })
    import uvicorn
    print("\n" + "="*60)
    print("🚀 Starting FastAPI Backend Server")
    print("="*60)
    print("📍 Server: http://localhost:8000")
    print("📚 API Docs: http://localhost:8000/docs")
    print("🔍 ReDoc: http://localhost:8000/redoc")
    print("="*60 + "\n")
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="info"
    )


if __name__ == "__main__":
    import uvicorn
    print("\n" + "="*60)
    print("🚀 Starting FastAPI Backend Server")
    print("="*60)
    print("📍 Server: http://localhost:8000")
    print("📚 API Docs: http://localhost:8000/docs")
    print("🔍 ReDoc: http://localhost:8000/redoc")
    print("="*60 + "\n")
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="info"
    )
