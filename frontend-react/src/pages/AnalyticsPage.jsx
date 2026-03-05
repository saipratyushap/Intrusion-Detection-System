import { useState, useEffect } from 'react';
import './AnalyticsPage.css';

export default function AnalyticsPage() {
    const [stats, setStats] = useState(null);
    const [timeFilter, setTimeFilter] = useState('All Time');
    const [loading, setLoading] = useState(true);
    const [chartData, setChartData] = useState(null);

    useEffect(() => {
        loadData();
    }, []);

    const loadData = async () => {
        setLoading(true);
        try {
            const [summaryRes, classRes, trendRes, hourlyRes] = await Promise.all([
                fetch('/api/detections/summary').then(r => r.json()).catch(() => null),
                fetch('/api/analytics/charts/class-distribution').then(r => r.json()).catch(() => null),
                fetch('/api/analytics/charts/violation-trend?days=7').then(r => r.json()).catch(() => null),
                fetch('/api/analytics/charts/hourly-activity').then(r => r.json()).catch(() => null),
            ]);
            setStats(summaryRes);
            setChartData({ classes: classRes, trends: trendRes, hourly: hourlyRes });
        } catch (err) {
            console.error('Failed to load analytics:', err);
        }
        setLoading(false);
    };

    const totalDetections = stats?.total_detections || 0;
    const totalViolations = stats?.total_violations || 0;
    const avgConfidence = stats?.average_confidence ? (stats.average_confidence * 100).toFixed(1) : '0.0';
    const topClass = stats?.top_class || 'N/A';

    return (
        <div className="page-content">
            <div className="tab-section-header">📊 Analytics & Insights</div>

            {/* Key Metrics */}
            <div className="section-header">📈 Key Metrics</div>
            <div className="metrics-grid">
                <div className="metric-card">
                    <div className="metric-value" style={{ color: '#00d4ff' }}>{totalDetections}</div>
                    <div className="metric-label">Total Detections</div>
                </div>
                <div className="metric-card">
                    <div className="metric-value" style={{ color: '#ef4444' }}>{totalViolations}</div>
                    <div className="metric-label">Total Violations</div>
                </div>
                <div className="metric-card">
                    <div className="metric-value" style={{ color: '#22c55e' }}>{avgConfidence}%</div>
                    <div className="metric-label">Avg Confidence</div>
                </div>
                <div className="metric-card">
                    <div className="metric-value" style={{ color: '#7c3aed' }}>{topClass}</div>
                    <div className="metric-label">Top Class</div>
                </div>
            </div>

            {/* Time Filter */}
            <div className="section-header">⏱️ Time Filter</div>
            <select className="time-filter" value={timeFilter} onChange={e => setTimeFilter(e.target.value)}>
                <option>All Time</option>
                <option>Last 24 Hours</option>
                <option>Last 7 Days</option>
                <option>Last 30 Days</option>
            </select>

            {/* Charts Section */}
            <div className="section-header">📈 Detection Trends</div>
            <div className="glass-card chart-area">
                {loading ? (
                    <p style={{ textAlign: 'center', color: '#94A3B8', padding: '2rem' }}>Loading chart data...</p>
                ) : chartData?.trends?.data ? (
                    <div className="simple-chart">
                        {chartData.trends.data.map((item, i) => (
                            <div key={i} className="bar-item">
                                <div className="bar" style={{ height: `${Math.max(item.count || item.value || 0, 5)}px`, background: '#709138' }}></div>
                                <span className="bar-label">{item.date || item.label || i}</span>
                            </div>
                        ))}
                    </div>
                ) : (
                    <p style={{ textAlign: 'center', color: '#94A3B8', padding: '2rem' }}>
                        {totalDetections === 0 ? 'No data yet. Start monitoring to see analytics.' : 'Chart data not available from API.'}
                    </p>
                )}
            </div>

            {/* Class Distribution */}
            <div className="section-header">🎯 Class Distribution</div>
            <div className="glass-card chart-area">
                {chartData?.classes?.data ? (
                    <div className="class-bars">
                        {(Array.isArray(chartData.classes.data) ? chartData.classes.data : Object.entries(chartData.classes.data).map(([k, v]) => ({ class: k, count: v }))).slice(0, 10).map((item, i) => {
                            const maxCount = Math.max(...(Array.isArray(chartData.classes.data) ? chartData.classes.data : Object.entries(chartData.classes.data).map(([, v]) => v)).map(x => x.count || x));
                            const pct = maxCount > 0 ? ((item.count || 0) / maxCount * 100) : 0;
                            return (
                                <div key={i} className="hbar-item">
                                    <span className="hbar-label">{item.class || item.name || 'Unknown'}</span>
                                    <div className="hbar-track">
                                        <div className="hbar-fill" style={{ width: `${pct}%` }}></div>
                                    </div>
                                    <span className="hbar-count">{item.count || 0}</span>
                                </div>
                            );
                        })}
                    </div>
                ) : (
                    <p style={{ textAlign: 'center', color: '#94A3B8', padding: '2rem' }}>No class data available</p>
                )}
            </div>

            {/* Additional Insights */}
            <div className="section-header">💡 Additional Insights</div>
            <div className="insights-grid">
                <div className="glass-card" style={{ padding: '1.5rem' }}>
                    <h4 style={{ color: '#2D3E50', marginBottom: '1rem' }}>🎯 Detection Statistics</h4>
                    <ul className="insight-list">
                        <li><strong>Total Detections:</strong> {totalDetections}</li>
                        <li><strong>Avg Confidence:</strong> {avgConfidence}%</li>
                        <li><strong>Top Class:</strong> {topClass}</li>
                    </ul>
                </div>
                <div className="glass-card" style={{ padding: '1.5rem' }}>
                    <h4 style={{ color: '#2D3E50', marginBottom: '1rem' }}>🚨 Violation Statistics</h4>
                    <ul className="insight-list">
                        <li><strong>Total Violations:</strong> {totalViolations}</li>
                        <li><strong>Violation Rate:</strong> {totalDetections > 0 ? ((totalViolations / totalDetections) * 100).toFixed(1) : 0}%</li>
                    </ul>
                </div>
            </div>

            {/* Raw Data */}
            <div className="section-header">📋 Export Data</div>
            <div className="glass-card" style={{ padding: '1.5rem' }}>
                <button className="export-btn" onClick={() => window.open('/api/detections/recent?limit=10000', '_blank')}>
                    📥 Download Detection Data as CSV
                </button>
            </div>
        </div>
    );
}
