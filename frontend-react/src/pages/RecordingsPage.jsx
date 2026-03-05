import { useState, useEffect } from 'react';
import './RecordingsPage.css';

export default function RecordingsPage() {
    const [recordings, setRecordings] = useState([]);
    const [loading, setLoading] = useState(true);
    const [search, setSearch] = useState('');

    useEffect(() => { loadRecordings(); }, []);

    const loadRecordings = async () => {
        setLoading(true);
        try {
            const res = await fetch('/api/activity/detections?limit=100');
            const data = await res.json();
            // Backend may return recordings differently, handle both cases
            setRecordings(data.recordings || data.detections || []);
        } catch (err) {
            console.error('Failed to load recordings:', err);
        }
        setLoading(false);
    };

    const filtered = recordings.filter(r =>
        !search || (r.name || '').toLowerCase().includes(search.toLowerCase())
    );

    const totalSize = recordings.reduce((sum, r) => sum + (r.size_mb || 0), 0);

    return (
        <div className="page-content">
            <div className="tab-section-header">🎬 Video Recordings</div>

            {/* Stats */}
            <div className="rec-stats">
                <div className="metric-card">
                    <div className="metric-value" style={{ color: '#709138' }}>{recordings.length}</div>
                    <div className="metric-label">Total Recordings</div>
                </div>
                <div className="metric-card">
                    <div className="metric-value" style={{ color: '#22c55e' }}>{totalSize.toFixed(2)} MB</div>
                    <div className="metric-label">Total Storage</div>
                </div>
                <div className="metric-card">
                    <div className="metric-value" style={{ color: '#f59e0b' }}>{recordings.length > 0 ? (recordings[0].created || 'N/A') : 'N/A'}</div>
                    <div className="metric-label">Latest Recording</div>
                </div>
            </div>

            <div className="section-header">📁 Recordings Library</div>

            {/* Search */}
            <input type="text" className="rec-search" placeholder="🔍 Search recordings..."
                value={search} onChange={e => setSearch(e.target.value)} />

            {loading ? (
                <p style={{ color: '#94A3B8', textAlign: 'center', padding: '2rem' }}>Loading recordings...</p>
            ) : filtered.length > 0 ? (
                <>
                    <p style={{ color: '#64748B', marginBottom: '1rem' }}>Showing {filtered.length} recording(s)</p>
                    <div className="rec-grid">
                        {filtered.map((rec, i) => (
                            <div key={i} className="glass-card rec-card">
                                <div className="rec-card-header">🎬 {rec.name || `Recording ${i + 1}`}</div>
                                <div className="rec-meta">
                                    <div className="rec-meta-row"><span>Created:</span><span>{rec.created || 'N/A'}</span></div>
                                    <div className="rec-meta-row"><span>Size:</span><span style={{ color: '#22c55e' }}>{(rec.size_mb || 0).toFixed(2)} MB</span></div>
                                    <div className="rec-meta-row"><span>Duration:</span><span style={{ color: '#00d4ff' }}>{rec.duration || 'N/A'}</span></div>
                                </div>
                                <div className="rec-actions">
                                    {rec.path && (
                                        <a href={`/api/recordings/download/${rec.name}`} download className="rec-dl-btn">📥 Download</a>
                                    )}
                                </div>
                            </div>
                        ))}
                    </div>
                </>
            ) : (
                <>
                    <div className="glass-card" style={{ textAlign: 'center', padding: '3rem' }}>
                        <div style={{ fontSize: '4rem', marginBottom: '1rem' }}>🎬</div>
                        <p style={{ color: '#64748B' }}>No recordings found. Start video recording from the Live Monitor tab!</p>
                    </div>
                    <div className="glass-card" style={{ padding: '2rem', marginTop: '1rem' }}>
                        <h4 style={{ color: '#709138', marginBottom: '1rem' }}>📝 How to Record</h4>
                        <ol style={{ color: '#4A4A4A', lineHeight: 2 }}>
                            <li>Go to the <strong>Live Monitor</strong> tab</li>
                            <li>Start the camera if not already running</li>
                            <li>In the sidebar, select your <strong>Recording Quality</strong> (Low/Medium/High)</li>
                            <li>Adjust <strong>Recording FPS</strong> as needed</li>
                            <li>Click <strong>⏺ Start Recording</strong> to begin</li>
                            <li>Click <strong>⏹ Stop Recording</strong> when finished</li>
                            <li>View and manage recordings in this tab</li>
                        </ol>
                    </div>
                </>
            )}
        </div>
    );
}
