import { useState } from 'react';
import Sidebar from './Sidebar';
import './Layout.css';

export default function Layout({ activeTab, onTabChange, children }) {
    const [sidebarOpen, setSidebarOpen] = useState(true);

    const tabs = ['Home', 'Live Monitor', 'Analytics', 'Snapshots', 'Recordings', 'Email Reporting'];

    return (
        <div className="app-layout">
            <Sidebar sidebarOpen={sidebarOpen} onToggle={() => setSidebarOpen(!sidebarOpen)} />

            <main className={`main-area ${sidebarOpen ? 'sidebar-open' : 'sidebar-closed'}`}>
                {/* Header */}
                <div className="main-header">
                    <h1>Real-Time Intrusion Detection</h1>
                    <p>AI-Powered Restricted Area Monitoring System</p>
                </div>

                {/* Horizontal Tabs */}
                <div className="tabs-bar">
                    {tabs.map(tab => (
                        <button
                            key={tab}
                            className={`tab-btn ${activeTab === tab ? 'active' : ''}`}
                            onClick={() => onTabChange(tab)}
                        >
                            {tab}
                        </button>
                    ))}
                </div>

                {/* Tab Content */}
                <div className="tab-content">
                    {children}
                </div>
            </main>
        </div>
    );
}
