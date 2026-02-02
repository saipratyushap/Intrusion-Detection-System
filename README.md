# 🚀 Intrusion Detection System

A comprehensive **Intrusion Detection System** built with **FastAPI** and **Streamlit**. This project integrates YOLO object detection with advanced analytics, business intelligence dashboards, and automated reporting capabilities.

---

## 🎯 Key Features

### 🔔 Core Monitoring Features
- ✅ **Real-time Object Detection** with YOLO models
- ✅ **Live Video Streaming** with restricted area overlay
- ✅ **Sound Alerts** when violations are detected
- ✅ **Automatic Detection Logging** to CSV files
- ✅ **WebSocket Communication** for real-time updates

### 🔐 Authentication & Security
- ✅ **User Login/Signup System** with secure password handling
- ✅ **Session Management**
- ✅ **Protected Routes**

### 📊 Analytics & Business Intelligence
- ✅ **Advanced Analytics Dashboard**
  - Predictive forecasting (7-30 days)
  - Anomaly detection (Z-score, Isolation Forest, Statistical methods)
  - Trend analysis
  - KPI calculation
  - Correlation analysis
  - Percentile analysis

- ✅ **Business Intelligence Features**
  - Executive summary reports
  - MTTR (Mean Time to Response) calculation
  - False positive rate analysis
  - Coverage percentage metrics
  - Violation trend analysis

- ✅ **Enhanced Plotly Charts**
  - Interactive visualizations
  - Real-time data updates
  - Multiple chart types (bar, pie, line, scatter)

### 📧 Email Reporting System
- ✅ **Advanced Email Reporting**
  - HTML email templates
  - PDF report attachments
  - CSV data exports
  - Scheduled report delivery

- ✅ **Report Scheduler**
  - Configure automatic report schedules
  - Multiple report types (daily, weekly, monthly)
  - Configurable recipients
  - Manual report triggering

### 📸 Snapshot Management
- ✅ **Snapshot Capture & Storage**
- ✅ **Snapshot Gallery View**
- ✅ **Filter by Date/Time**
- ✅ **Delete Old Snapshots**

### 🎨 Modern UI/UX
- ✅ **Responsive Design**
- ✅ **Dark Mode Interface**
- ✅ **Interactive Charts**
- ✅ **Real-time Data Refresh**
- ✅ **User-friendly Navigation**

---

## 🔐 Default Credentials

For demonstration purposes, the system comes with a default admin account:

| Field | Value |
|-------|-------|
| **Username** | `admin` |
| **Password** | `admin` |

> ⚠️ **Security Note:** Change the default password in production environments!

---

## 🛠️ Installation & Setup

### 1️⃣ Install Dependencies

```bash
pip install -r requirements.txt
```

### 2️⃣ Configure Environment

Create a `.env` file based on `.env.example`:

```env
# Email Configuration
EMAIL_SENDER=your_email@gmail.com
EMAIL_PASSWORD=your_app_password
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587

# Database
DATA_DIR=data
```

### 3️⃣ Start FastAPI Backend

```bash
uvicorn fastapi_run:app --reload
```

- 🔗 **Server URL:** [http://127.0.0.1:8000](http://127.0.0.1:8000)
- 📚 **API Documentation:** [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)

### 4️⃣ Launch Streamlit Dashboard

```bash
streamlit run streamlit_run.py
```

- 📊 **Dashboard:** [http://localhost:8501](http://localhost:8501)

---

## 📁 Project Structure

```
├── fastapi_run.py                    # FastAPI backend server
├── streamlit_run.py                  # Streamlit frontend
├── requirements.txt                  # Python dependencies
├── README.md                         # This file
│
├── advanced_analytics.py             # Forecasting & anomaly detection
├── advanced_email_reporting.py       # Email report generation
├── business_intelligence.py          # BI metrics & dashboards
├── email_service.py                  # Email functionality
├── enhanced_analytics.py             # Enhanced analytics features
├── enhanced_plotly_analytics.py      # Plotly visualizations
├── report_scheduler.py               # Scheduled reporting
│
├── static/                           # Frontend assets
│   ├── styles.css                    # Main styles
│   ├── data.css                      # Data page styles
│   ├── snapshots.css                 # Snapshots page styles
│   ├── login_signup.css              # Login page styles
│   ├── script.js                     # Main JavaScript
│   ├── data.js                       # Data page JS
│   ├── snapshots.js                  # Snapshots page JS
│   └── login_signup.js               # Login page JS
│
├── templates/                        # HTML templates
│   ├── index.html                    # Main dashboard
│   ├── data.html                     # Data analytics page
│   ├── snapshots.html                # Snapshots gallery
│   └── login_signup.html             # Login/Signup page
│
├── model/                            # YOLO Models
│   ├── best.pt                       # Best detection model
│   ├── yolov8n.pt                    # YOLOv8 nano
│   └── ppe8n.pt                      # PPE detection model
│
└── data/                             # Data storage
    ├── cameras.json                  # Camera configuration
    ├── cost_config.json              # Cost settings
    ├── detection_log.csv             # Detection logs
    ├── users.json                    # User database
    ├── user_activity.json            # Activity logs
    ├── report_schedules.json         # Report schedules
    ├── frames/                       # Captured frames
    ├── recordings/                   # Video recordings
    └── reports/                      # Generated reports
```

---

## 🔍 How It Works

### 📁 Data Storage
> **Note:** All detected data is stored and visible in the `detection_log.csv` file. A database has not been implemented as this is a **real-time monitoring system** designed for immediate detection and response. The CSV format provides:
> - Instant write capabilities without database connection overhead
> - Easy data export and analysis
> - Lightweight storage for real-time operations
> - Simple backup and maintenance

### 🚀 FastAPI WebSocket Backend
- **Data Handling**: Reads live data from `detection_log.csv`
- **Real-Time Communication**: Uses WebSockets for instant updates
- **Authentication**: Token-based session security
- **Email Service**: Automated report delivery

#### API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/auth/login` | POST | User login |
| `/api/auth/signup` | POST | User registration |
| `/ws/data` | WebSocket | Real-time data stream |
| `/api/analytics` | GET | Analytics data |
| `/api/reports/schedule` | POST | Schedule report |
| `/api/snapshots` | GET | List snapshots |

### 📊 Streamlit Frontend
- **Real-Time Monitoring**: Live video with detection overlay
- **Restricted Area**: Customizable monitoring zones
- **Sound Alerts**: Audio notifications for violations
- **Analytics Dashboard**: Comprehensive data visualization
- **User Management**: Login and session handling

---

## 📈 Analytics Features

### Predictive Forecasting
- 7-30 day detection predictions
- Trend-based forecasting algorithms
- Confidence intervals

### Anomaly Detection
- **Z-Score Method**: Statistical outlier detection
- **Isolation Forest**: Machine learning-based anomalies
- **Statistical Methods**: Custom threshold detection

### Business Intelligence Metrics
- **MTTR**: Mean Time To Response
- **False Positive Rate**: Accuracy metrics
- **Coverage Percentage**: Monitoring efficiency
- **Executive Summary**: High-level insights

---

## 📧 Email Reports

### Report Types
- **Daily Summary**: 24-hour detection summary
- **Weekly Report**: Weekly trends and statistics
- **Monthly Report**: Comprehensive monthly analysis
- **Violation Alert**: Immediate violation notifications

### Attachment Formats
- **PDF Reports**: Professional formatted documents
- **CSV Data**: Raw data exports
- **HTML Templates**: Customizable email designs

---

## 🎬 Live Demo

1. Start the FastAPI backend server
2. Launch the Streamlit dashboard
3. Open your browser to `http://localhost:8501`
4. Login or signup to access the dashboard
5. Monitor real-time detections and analytics

---

## ⚙️ Configuration

### Camera Setup (`data/cameras.json`)
```json
[
    {
        "id": "camera_1",
        "name": "Main Entrance",
        "url": "rtsp://camera_ip:554/stream",
        "restricted_area": {"x1": 200, "y1": 150, "x2": 400, "y2": 350}
    }
]
```

### Report Scheduling (`data/report_schedules.json`)
```json
[
    {
        "id": "schedule_1",
        "report_type": "daily",
        "recipients": ["admin@example.com"],
        "time": "08:00",
        "enabled": true
    }
]
```

---

## 💡 Contributing

- 💻 **Fork & Customize**: Adapt for your needs
- 🔧 **Contributions Welcome**: Submit pull requests
- 📩 **Feedback**: Always appreciated

---

## 📝 License

This project is open source and available for personal and commercial use.

---

🚀 **Made with ❤️ by Pratyusha**

