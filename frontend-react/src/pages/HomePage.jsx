import { useState, useEffect } from 'react';
import { getDetectionsSummary, getSnapshotsCount, getRecentDetections, getAlertStats, getRecentAlerts } from '../api/client';
import './HomePage.css';

export default function HomePage() {
    const [stats, setStats] = useState({ total: 0, violations: 0, snapshots: 0, classes: 80 });
    const [recentAlerts, setRecentAlerts] = useState([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        Promise.all([
            getDetectionsSummary().catch(() => ({})),
            getSnapshotsCount().catch(() => ({})),
            getRecentAlerts(24).catch(() => ({})),
        ]).then(([sumRes, snapRes, alertRes]) => {
            const s = sumRes?.data || sumRes || {};
            const snap = snapRes?.data || snapRes || {};
            setStats({ total: s.total || 0, violations: s.violations || 0, snapshots: snap.count || 0, classes: 80 });
            setRecentAlerts((alertRes?.data?.alerts || alertRes?.alerts || []).slice(0, 5));
            setLoading(false);
        });
    }, []);

    return (
        <div className="home-page">
            {/* Badge row */}
            <div className="home-badges">
                <span className="badge-live">● Live Monitoring</span>
                <span className="badge-yolo">● YOLOv8</span>
                <span className="badge-secure">● Secure</span>
            </div>

            {/* SYSTEM STATISTICS */}
            <div className="section-header">📊 SYSTEM STATISTICS</div>
            <div className="stats-grid">
                <div className="stat-card">
                    <div className="stat-emoji">🎯</div>
                    <div className="stat-value cyan">{loading ? '...' : stats.total}</div>
                    <div className="stat-label">Total Detections</div>
                </div>
                <div className="stat-card">
                    <div className="stat-emoji">🚨</div>
                    <div className="stat-value red">{loading ? '...' : stats.violations}</div>
                    <div className="stat-label">Violations</div>
                </div>
                <div className="stat-card">
                    <div className="stat-emoji">📸</div>
                    <div className="stat-value green">{loading ? '...' : stats.snapshots}</div>
                    <div className="stat-label">Snapshots</div>
                </div>
                <div className="stat-card">
                    <div className="stat-emoji">👥</div>
                    <div className="stat-value purple">{loading ? '...' : stats.classes}</div>
                    <div className="stat-label">Object Classes</div>
                </div>
            </div>

            {/* KEY FEATURES */}
            <div className="section-header">✨ KEY FEATURES</div>
            <div className="features-grid">
                <div className="feature-card">
                    <div className="feature-header">
                        <span className="feature-icon">🎯</span>
                        <div>
                            <h3>Real-Time Detection</h3>
                            <span className="feature-badge cyan">● Object Recognition</span>
                        </div>
                    </div>
                    <p>Advanced YOLOv8 neural network provides instant object detection with high accuracy. Detect multiple object classes simultaneously in real-time video streams.</p>
                    <ul>
                        <li>Sub-30ms processing time</li>
                        <li>80%+ detection accuracy</li>
                        <li>Multi-class support</li>
                    </ul>
                </div>
                <div className="feature-card">
                    <div className="feature-header">
                        <span className="feature-icon">🔔</span>
                        <div>
                            <h3>Smart Alerting</h3>
                            <span className="feature-badge red">● Instant Notifications</span>
                        </div>
                    </div>
                    <p>Intelligent alerting system triggers immediate notifications when restricted area violations are detected. Audio alerts and visual indicators keep you informed.</p>
                    <ul>
                        <li>🔊 Audio alerts</li>
                        <li>⚠️ Instant visual warnings</li>
                        <li>📧 Configurable thresholds</li>
                    </ul>
                </div>
                <div className="feature-card">
                    <div className="feature-header">
                        <span className="feature-icon">📊</span>
                        <div>
                            <h3>Analytics Dashboard</h3>
                            <span className="feature-badge purple">● Interactive Insights</span>
                        </div>
                    </div>
                    <p>Detailed analytics with charts, trends, and violation patterns. Export data for further analysis and reporting.</p>
                    <ul>
                        <li>📈 Detection trends</li>
                        <li>🔄 Violation patterns</li>
                        <li>📊 CSV export support</li>
                    </ul>
                </div>
                <div className="feature-card">
                    <div className="feature-header">
                        <span className="feature-icon">📷</span>
                        <div>
                            <h3>Snapshots Gallery</h3>
                            <span className="feature-badge green">● Full Access</span>
                        </div>
                    </div>
                    <p>Automatic snapshot capture for every detection event. Build a visual history of all monitored activities with time-stamped evidence.</p>
                    <ul>
                        <li>📸 Auto capture</li>
                        <li>📁 Timestamped images</li>
                        <li>🖼️ Easy gallery view</li>
                    </ul>
                </div>
            </div>

            {/* SYSTEM STATUS */}
            <div className="section-header">⚡ SYSTEM STATUS</div>
            <div className="status-grid">
                <div className="status-section">
                    <h4>Camera & Recording Status</h4>
                    <div className="status-row"><span>Camera Status</span><span className="status-val red-dot">● Inactive</span></div>
                    <div className="status-row"><span>Recording Status</span><span className="status-val red-dot">● Not Recording</span></div>
                    <div className="status-row"><span>Detection Classes</span><span className="status-val blue">80 selected</span></div>
                    <div className="status-row"><span>Confidence Threshold</span><span className="status-val blue">0.15</span></div>
                </div>
                <div className="status-section">
                    <h4>Model Information</h4>
                    <div className="status-row"><span>Model Type</span><span className="status-val blue">YOLOv8n</span></div>
                    <div className="status-row"><span>Total Classes</span><span className="status-val blue">80</span></div>
                    <div className="status-row"><span>Alert Classes</span><span className="status-val blue">80 selected</span></div>
                    <div className="status-row"><span>Last Detection</span><span className="status-val blue">--</span></div>
                </div>
            </div>

            {/* QUICK START GUIDE */}
            <div className="section-header">⭐ QUICK START GUIDE</div>
            <div className="quickstart-grid">
                <div className="quickstart-card">
                    <div className="qs-step green">1</div>
                    <h4>Start Monitoring</h4>
                    <p>Click "Start" in the sidebar to activate the camera feed and begin real-time monitoring.</p>
                </div>
                <div className="quickstart-card">
                    <div className="qs-step purple">2</div>
                    <h4>Configure Settings</h4>
                    <p>Select objects to detect and alert using the sidebar options. Adjust confidence threshold as needed.</p>
                </div>
                <div className="quickstart-card">
                    <div className="qs-step cyan">3</div>
                    <h4>View Analytics</h4>
                    <p>Check the Analytics tab for detailed reports, charts, and violation history.</p>
                </div>
            </div>

            {/* REAL-TIME ALERTS */}
            <div className="section-header">🚨 REAL-TIME ALERTS</div>
            <div className="alerts-grid">
                <div className="alert-stat-card">
                    <div className="alert-emoji">🚨</div>
                    <div className="alert-stat-value red">{stats.violations}</div>
                    <div className="alert-stat-sub">Today / This Week</div>
                    <div className="alert-stat-sub">0 / {stats.violations}</div>
                    <small>Tap to refresh</small>
                </div>
                <div className="alert-stat-card">
                    <div className="alert-emoji">👥</div>
                    <div className="alert-stat-value">0 / {stats.violations}</div>
                    <div className="alert-stat-sub">Today / This Week</div>
                </div>
                <div className="quick-actions">
                    <h4>Quick Actions</h4>
                    <button className="qa-btn">🔊 Test Alert Sound</button>
                    <button className="qa-btn">📧 Test Email Alert</button>
                </div>
            </div>
        </div>
    );
}
