import { useState, useEffect } from 'react';
import './EmailReportingPage.css';

export default function EmailReportingPage() {
    const [subTab, setSubTab] = useState('send');
    const [reportType, setReportType] = useState('daily');
    const [templateType, setTemplateType] = useState('summary');
    const [includeCSV, setIncludeCSV] = useState(true);
    const [includePDF, setIncludePDF] = useState(false);
    const [recipients, setRecipients] = useState('');
    const [sending, setSending] = useState(false);
    const [message, setMessage] = useState('');
    const [schedules, setSchedules] = useState([]);

    // Load schedules
    useEffect(() => {
        fetch('/api/email/schedules')
            .then(r => r.json())
            .then(data => setSchedules(data.schedules || []))
            .catch(() => { });
    }, []);

    const sendReport = async () => {
        if (!recipients.trim()) { setMessage('❌ Please enter at least one recipient email'); return; }
        setSending(true);
        setMessage('');
        try {
            const recipientList = recipients.split(',').map(e => e.trim()).filter(Boolean);
            const res = await fetch('/api/email/send-report', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    report_type: reportType,
                    template_type: templateType,
                    recipient_email: recipientList[0],
                    include_pdf: includePDF,
                    include_csv: includeCSV
                })
            });
            const data = await res.json();
            if (data.error) { setMessage(`❌ ${data.error}`); }
            else { setMessage(`✅ Report sent successfully to ${recipientList.join(', ')}`); }
        } catch (err) {
            setMessage(`❌ Error: ${err.message}`);
        }
        setSending(false);
    };

    return (
        <div className="page-content">
            <div className="tab-section-header">📧 Email Reporting</div>

            {/* Sub tabs */}
            <div className="email-tabs">
                <button className={`email-tab ${subTab === 'send' ? 'active' : ''}`} onClick={() => setSubTab('send')}>Send Report</button>
                <button className={`email-tab ${subTab === 'schedule' ? 'active' : ''}`} onClick={() => setSubTab('schedule')}>Scheduled Reports</button>
                <button className={`email-tab ${subTab === 'templates' ? 'active' : ''}`} onClick={() => setSubTab('templates')}>Report Templates</button>
            </div>

            {/* Send Report */}
            {subTab === 'send' && (
                <div className="email-section">
                    <h3>📤 Send Report Immediately</h3>
                    <p style={{ color: '#64748B' }}>Generate and send a report right now.</p>

                    <div className="email-form-grid">
                        <div className="form-group">
                            <label>Report Type</label>
                            <select value={reportType} onChange={e => setReportType(e.target.value)}>
                                <option value="daily">daily</option>
                                <option value="weekly">weekly</option>
                                <option value="monthly">monthly</option>
                            </select>
                        </div>
                        <div className="form-group">
                            <label>Report Template</label>
                            <select value={templateType} onChange={e => setTemplateType(e.target.value)}>
                                <option value="summary">summary</option>
                                <option value="detailed">detailed</option>
                                <option value="compliance">compliance</option>
                                <option value="operational">operational</option>
                            </select>
                        </div>
                    </div>

                    <div className="checkbox-row">
                        <label><input type="checkbox" checked={includeCSV} onChange={e => setIncludeCSV(e.target.checked)} /> Include CSV</label>
                        <label><input type="checkbox" checked={includePDF} onChange={e => setIncludePDF(e.target.checked)} /> Include PDF</label>
                    </div>

                    <div className="form-group">
                        <label>Recipients (comma-separated)</label>
                        <textarea rows={3} value={recipients} onChange={e => setRecipients(e.target.value)}
                            placeholder="Enter email addresses separated by commas" />
                    </div>

                    {message && (
                        <div className={`email-message ${message.startsWith('✅') ? 'success' : 'error'}`}>{message}</div>
                    )}

                    <button className="send-btn" onClick={sendReport} disabled={sending}>
                        {sending ? '⏳ Sending...' : '📨 Send Report Now'}
                    </button>
                </div>
            )}

            {/* Scheduled Reports */}
            {subTab === 'schedule' && (
                <div className="email-section">
                    <h3>📅 Manage Scheduled Reports</h3>
                    <p style={{ color: '#64748B' }}>Create and manage automatic report delivery schedules.</p>

                    {schedules.length > 0 ? (
                        <div className="schedule-list">
                            {schedules.map((s, i) => (
                                <div key={i} className="glass-card schedule-card">
                                    <div className="schedule-header">
                                        📋 {s.name || 'Unnamed'} ({s.report_type || 'unknown'})
                                    </div>
                                    <div className="schedule-meta">
                                        <span><strong>Type:</strong> {s.report_type || 'N/A'}</span>
                                        <span><strong>Template:</strong> {s.template_type || 'N/A'}</span>
                                        <span><strong>Status:</strong> {s.active !== false ? '🟢 Active' : '🔴 Inactive'}</span>
                                    </div>
                                    <div className="schedule-meta">
                                        <span><strong>Recipients:</strong> {(s.recipients || []).join(', ')}</span>
                                    </div>
                                </div>
                            ))}
                        </div>
                    ) : (
                        <div className="glass-card" style={{ textAlign: 'center', padding: '2rem' }}>
                            <p style={{ color: '#94A3B8' }}>No scheduled reports configured yet. Create one to get started!</p>
                        </div>
                    )}
                </div>
            )}

            {/* Templates */}
            {subTab === 'templates' && (
                <div className="email-section">
                    <h3>📋 Report Templates</h3>
                    <p style={{ color: '#64748B' }}>Choose and configure report templates for your needs.</p>

                    <div className="template-list">
                        {[
                            { id: 'summary', name: 'Summary Report', desc: 'Quick overview of detections and violations', sections: ['Overview', 'Key Metrics', 'Top Classes'] },
                            { id: 'detailed', name: 'Detailed Report', desc: 'Comprehensive analysis with charts and data', sections: ['Overview', 'Metrics', 'Charts', 'Data Table', 'Insights'] },
                            { id: 'compliance', name: 'Compliance Report', desc: 'Security compliance and audit trail', sections: ['Violations', 'Audit Log', 'Risk Assessment'] },
                            { id: 'operational', name: 'Operational Report', desc: 'System performance and uptime stats', sections: ['System Status', 'Performance', 'Camera Health'] },
                        ].map(t => (
                            <div key={t.id} className="glass-card template-card">
                                <h4>📄 {t.name}</h4>
                                <p style={{ color: '#64748B', fontSize: '0.9rem' }}>{t.desc}</p>
                                <div><strong>Sections:</strong></div>
                                <ul className="template-sections">
                                    {t.sections.map(s => <li key={s}>• {s}</li>)}
                                </ul>
                                <div className="template-id">Template ID: <code>{t.id}</code></div>
                            </div>
                        ))}
                    </div>
                </div>
            )}
        </div>
    );
}
