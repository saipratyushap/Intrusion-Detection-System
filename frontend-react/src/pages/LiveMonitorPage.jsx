import { useState, useEffect, useRef } from 'react';
import './LiveMonitorPage.css';

export default function LiveMonitorPage() {
    const [cameraActive, setCameraActive] = useState(false);
    const [recording, setRecording] = useState(false);
    const [alertActive, setAlertActive] = useState(false);
    const [currentTime, setCurrentTime] = useState(new Date().toLocaleString());
    const imgRef = useRef(null);
    const audioRef = useRef(new Audio('/sounds/alert.wav'));

    useEffect(() => {
        audioRef.current.loop = true;
    }, []);

    useEffect(() => {
        const timer = setInterval(() => setCurrentTime(new Date().toLocaleString()), 1000);
        return () => clearInterval(timer);
    }, []);

    // Poll backend for camera status
    useEffect(() => {
        const checkCamera = async () => {
            try {
                const r = await fetch('/api/health');
                const data = await r.json();
                if (data.camera_active !== undefined) {
                    setCameraActive(data.camera_active);
                }
                if (data.alert_active !== undefined) {
                    setAlertActive(data.alert_active);
                }
            } catch (err) {
                // ignore
            }
        };

        checkCamera(); // Check immediately
        const timer = setInterval(checkCamera, 1000); // Check every second
        return () => clearInterval(timer);
    }, []);

    useEffect(() => {
        if (alertActive) {
            audioRef.current.play().catch(e => console.error("Audio play failed, user interaction needed", e));
        } else {
            audioRef.current.pause();
            audioRef.current.currentTime = 0;
        }
    }, [alertActive]);

    return (
        <div className="page-content">
            <div className="page-header">Live Camera Feed</div>

            {/* Status badges */}
            <div className="status-row">
                <div className={`status-badge-enhanced ${cameraActive ? 'active' : 'inactive'}`}>
                    {cameraActive ? '● LIVE' : '● OFFLINE'}
                </div>
                <div className={`status-badge-enhanced ${recording ? 'recording' : 'inactive'}`}>
                    {recording ? '● RECORDING' : '● NOT RECORDING'}
                </div>
                <div className="status-time">📅 {currentTime}</div>
            </div>

            {/* Camera feed area */}
            {cameraActive ? (
                <>
                    <div className={`video-wrapper ${alertActive ? 'alerting' : ''}`}>
                        {alertActive && <div className="video-alert-banner">⚠️ INTRUSION DETECTED ⚠️</div>}
                        <img
                            ref={imgRef}
                            src="/api/video_feed"
                            alt="Live Camera Feed"
                            className="camera-feed"
                            onError={(e) => { e.target.style.display = 'none'; }}
                        />
                    </div>

                    {/* Status bar below video */}
                    <div className="glass-card status-bar">
                        <div className="status-bar-items">
                            <div>
                                <span className="status-label">Camera</span>
                                <div className="status-value active">● Active</div>
                            </div>
                            <div>
                                <span className="status-label">Recording</span>
                                <div className="status-value">{recording ? '● True' : '● False'}</div>
                            </div>
                            <div>
                                <span className="status-label">System</span>
                                <div className={alertActive ? "status-value text-red" : "status-value active"}>
                                    {alertActive ? '⚠️ Alerting' : '✓ Ready'}
                                </div>
                            </div>
                        </div>
                    </div>
                </>
            ) : (
                <div className="glass-card" style={{ textAlign: 'center', padding: '3rem' }}>
                    <div style={{ fontSize: '4rem', marginBottom: '1rem' }}>📷</div>
                    <p style={{ color: '#64748B', fontSize: '1.1rem' }}>
                        Click <strong>"Start"</strong> in the sidebar to begin monitoring
                    </p>
                </div>
            )}
        </div>
    );
}
