import { useState, useEffect } from 'react';
import './SnapshotsPage.css';

export default function SnapshotsPage() {
    const [snapshots, setSnapshots] = useState([]);
    const [loading, setLoading] = useState(true);
    const [confirmDeleteAll, setConfirmDeleteAll] = useState(false);

    useEffect(() => { loadSnapshots(); }, []);

    const loadSnapshots = async () => {
        setLoading(true);
        try {
            const res = await fetch('/api/snapshots');
            const data = await res.json();
            setSnapshots(data.snapshots || data || []);
        } catch (err) {
            console.error('Failed to load snapshots:', err);
        }
        setLoading(false);
    };

    const deleteSnapshot = async (id) => {
        try {
            await fetch('/api/snapshots/delete', {
                method: 'POST', headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ id })
            });
            setSnapshots(prev => prev.filter(s => (s.id || s.name) !== id));
        } catch (err) { console.error('Delete failed:', err); }
    };

    const deleteAll = async () => {
        if (!confirmDeleteAll) { setConfirmDeleteAll(true); return; }
        for (const s of snapshots) {
            try { await deleteSnapshot(s.id || s.name); } catch { }
        }
        setSnapshots([]);
        setConfirmDeleteAll(false);
    };

    return (
        <div className="page-content">
            <div className="tab-section-header">📸 Captured Snapshots</div>

            {loading ? (
                <p style={{ color: '#94A3B8', textAlign: 'center' }}>Loading snapshots...</p>
            ) : snapshots.length > 0 ? (
                <>
                    {/* Header bar */}
                    <div className="snap-header">
                        <div className="glass-card" style={{ padding: '1rem', flex: 3 }}>
                            <h4>📸 Captured Snapshots ({snapshots.length})</h4>
                        </div>
                        <div style={{ flex: 1, display: 'flex', gap: '0.5rem' }}>
                            <button className="delete-all-btn" onClick={deleteAll}>
                                {confirmDeleteAll ? '⚠️ Confirm Delete All' : '🗑️ Delete All'}
                            </button>
                            {confirmDeleteAll && (
                                <button className="cancel-btn" onClick={() => setConfirmDeleteAll(false)}>❌ Cancel</button>
                            )}
                        </div>
                    </div>

                    {/* Grid */}
                    <div className="snap-grid">
                        {snapshots.map((snap, i) => (
                            <div key={i} className="snap-card">
                                <img
                                    src={snap.url || `/api/snapshots/${snap.id || snap.name}`}
                                    alt={snap.name || `Snapshot ${i}`}
                                    className="snap-img"
                                    onError={e => { e.target.src = 'data:image/svg+xml,<svg xmlns="http://www.w3.org/2000/svg" width="200" height="150"><rect fill="%23f1f5f9" width="200" height="150"/><text x="50%" y="50%" fill="%2394a3b8" font-size="14" text-anchor="middle" dy="5">No Preview</text></svg>'; }}
                                />
                                <div className="snap-info">
                                    <span className="snap-name">{(snap.name || `Snapshot ${i}`).substring(0, 25)}</span>
                                    {snap.size_kb && <span className="snap-size">📁 {snap.size_kb.toFixed(1)} KB</span>}
                                </div>
                                <button className="snap-delete-btn" onClick={() => deleteSnapshot(snap.id || snap.name)}>🗑️ Delete</button>
                            </div>
                        ))}
                    </div>
                </>
            ) : (
                <>
                    <div className="glass-card" style={{ textAlign: 'center', padding: '3rem' }}>
                        <div style={{ fontSize: '4rem', marginBottom: '1rem' }}>📸</div>
                        <p style={{ color: '#64748B' }}>No snapshots captured yet. Start monitoring to capture violation images.</p>
                    </div>
                    <div className="glass-card" style={{ padding: '2rem', marginTop: '1rem' }}>
                        <h4 style={{ color: '#709138', marginBottom: '1rem' }}>📝 How Snapshots Work</h4>
                        <ol style={{ color: '#4A4A4A', lineHeight: 2 }}>
                            <li>Go to the <strong>Live Monitor</strong> tab</li>
                            <li>Start the camera</li>
                            <li>When a violation is detected, a snapshot is automatically captured</li>
                            <li>View and manage snapshots in this tab</li>
                            <li>Use the delete buttons to remove unwanted snapshots</li>
                        </ol>
                    </div>
                </>
            )}
        </div>
    );
}
