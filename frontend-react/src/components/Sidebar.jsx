import { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import MultiSelect from './MultiSelect';
import './Sidebar.css';

const AVAILABLE_CLASSES = [
    'person', 'bicycle', 'car', 'motorcycle', 'airplane', 'bus',
    'train', 'truck', 'boat', 'traffic light', 'fire hydrant',
    'stop sign', 'parking meter', 'bench', 'bird', 'cat', 'dog',
    'horse', 'sheep', 'cow', 'elephant', 'bear', 'zebra', 'giraffe',
    'backpack', 'umbrella', 'handbag', 'tie', 'suitcase', 'frisbee',
    'skis', 'snowboard', 'sports ball', 'kite', 'baseball bat',
    'baseball glove', 'skateboard', 'surfboard', 'tennis racket',
    'bottle', 'wine glass', 'cup', 'fork', 'knife', 'spoon', 'bowl',
    'banana', 'apple', 'sandwich', 'orange', 'broccoli', 'carrot',
    'hot dog', 'pizza', 'donut', 'cake', 'chair', 'couch',
    'potted plant', 'bed', 'dining table', 'toilet', 'tv', 'laptop',
    'mouse', 'remote', 'keyboard', 'cell phone', 'microwave', 'oven',
    'toaster', 'sink', 'refrigerator', 'book', 'clock', 'vase',
    'scissors', 'teddy bear', 'hair drier', 'toothbrush'
];

export default function Sidebar({ sidebarOpen, onToggle }) {
    const { user, logout } = useAuth();
    const [detectClasses, setDetectClasses] = useState([...AVAILABLE_CLASSES]);
    const [alertClasses, setAlertClasses] = useState([...AVAILABLE_CLASSES]);
    const [confidence, setConfidence] = useState(0.15);
    const [cameraActive, setCameraActive] = useState(false);
    const [recordingQuality, setRecordingQuality] = useState('Medium (720p)');
    const [recordingFps, setRecordingFps] = useState(20);
    const [isRecording, setIsRecording] = useState(false);

    const handleCameraStart = async () => {
        try {
            const res = await fetch('/api/cameras/start', { method: 'POST' });
            if (res.ok) setCameraActive(true);
        } catch (err) {
            console.error('Camera start failed:', err);
            setCameraActive(true); // Still toggle UI for demo
        }
    };

    const handleCameraStop = async () => {
        try {
            await fetch('/api/cameras/stop', { method: 'POST' });
            if (isRecording) {
                await fetch('/api/recording/stop', { method: 'POST' });
            }
        } catch (err) {
            console.error('Camera stop failed:', err);
        }
        setCameraActive(false);
        setIsRecording(false);
    };

    const handleStartRecording = async () => {
        try {
            const res = await fetch('/api/recording/start', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    quality: recordingQuality,
                    fps: recordingFps
                })
            });
            if (res.ok) setIsRecording(true);
        } catch (err) {
            console.error('Recording start failed:', err);
        }
    };

    const handleStopRecording = async () => {
        try {
            const res = await fetch('/api/recording/stop', { method: 'POST' });
            if (res.ok) setIsRecording(false);
        } catch (err) {
            console.error('Recording stop failed:', err);
        }
    };

    // Auto-sync settings to backend
    useEffect(() => {
        const syncSettings = async () => {
            try {
                await fetch('/api/camera_settings', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        conf_threshold: confidence,
                        detect_classes: detectClasses,
                        alert_classes: alertClasses
                    })
                });
            } catch (err) {
                console.error("Failed to sync camera settings", err);
            }
        };
        syncSettings();
    }, [confidence, detectClasses, alertClasses]);

    return (
        <>
            <aside className={`sidebar ${sidebarOpen ? 'open' : 'closed'}`}>
                {/* Collapse button */}
                <button className="sidebar-collapse-btn" onClick={onToggle} title="Collapse sidebar">«</button>

                {/* Logo */}
                <div className="sidebar-logo">
                    <img src="/logo.png" alt="ThirdEye" />
                </div>

                {/* User */}
                <div className="sidebar-user">User: {user?.username || 'guest'}</div>
                <button className="logout-btn" onClick={logout}>Logout</button>

                <hr className="sidebar-divider" />

                {/* System Settings */}
                <h3 className="sidebar-heading">System Settings</h3>

                {/* Objects to Detect */}
                <div className="btn-pair">
                    <button className="ctrl-btn" onClick={() => setDetectClasses([...AVAILABLE_CLASSES])}>All</button>
                    <button className="ctrl-btn" onClick={() => setDetectClasses([])}>None</button>
                </div>
                <label className="sidebar-label">Objects to Detect</label>
                <MultiSelect
                    options={AVAILABLE_CLASSES}
                    selected={detectClasses}
                    onChange={setDetectClasses}
                />

                {/* Objects for Alert */}
                <div className="btn-pair">
                    <button className="ctrl-btn" onClick={() => setAlertClasses([...AVAILABLE_CLASSES])}>All</button>
                    <button className="ctrl-btn" onClick={() => setAlertClasses([])}>None</button>
                </div>
                <label className="sidebar-label">Objects for Alert</label>
                <MultiSelect
                    options={AVAILABLE_CLASSES}
                    selected={alertClasses}
                    onChange={setAlertClasses}
                />

                {/* Confidence Threshold */}
                <label className="sidebar-label">Confidence Threshold</label>
                <div className="slider-val">{confidence.toFixed(2)}</div>
                <input type="range" min="0" max="1" step="0.05" value={confidence}
                    onChange={e => setConfidence(parseFloat(e.target.value))} className="slider" />

                <hr className="sidebar-divider" />

                {/* Camera Controls */}
                <h3 className="sidebar-heading">Camera Controls</h3>
                <div className="btn-pair">
                    <button className="ctrl-btn" onClick={handleCameraStart}>Start</button>
                    <button className="ctrl-btn" onClick={handleCameraStop}>Stop</button>
                </div>
                <div className={`camera-status ${cameraActive ? 'live' : 'offline'}`}>
                    {cameraActive ? '● Live' : 'Offline'}
                </div>

                {/* Video Recording - visible when camera active */}
                {cameraActive && (
                    <>
                        <hr className="sidebar-divider" />
                        <h3 className="sidebar-heading">Video Recording</h3>

                        <label className="sidebar-label">Recording Quality</label>
                        <select className="sidebar-select" value={recordingQuality}
                            onChange={e => setRecordingQuality(e.target.value)}>
                            <option>Low (480p)</option>
                            <option>Medium (720p)</option>
                            <option>High (1080p)</option>
                        </select>

                        <label className="sidebar-label">Recording FPS</label>
                        <div className="slider-val">{recordingFps}</div>
                        <input type="range" min="5" max="30" value={recordingFps}
                            onChange={e => setRecordingFps(parseInt(e.target.value))} className="slider" />

                        <div className="btn-pair">
                            <button className="ctrl-btn" disabled={isRecording}
                                onClick={handleStartRecording}>⏺ Start</button>
                            <button className="ctrl-btn" disabled={!isRecording}
                                onClick={handleStopRecording}>⏹ Stop</button>
                        </div>
                        {isRecording && (
                            <div className="recording-status">🔴 Recording...</div>
                        )}
                    </>
                )}
            </aside>

            {/* Expand button when sidebar closed */}
            {!sidebarOpen && (
                <button className="sidebar-expand-btn" onClick={onToggle} title="Expand sidebar">»</button>
            )}
        </>
    );
}
