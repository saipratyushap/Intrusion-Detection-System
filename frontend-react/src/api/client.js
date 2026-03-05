import axios from 'axios';

const api = axios.create({
  baseURL: '',
  timeout: 60000,
  headers: { 'Content-Type': 'application/json' }
});

api.interceptors.response.use(
  (response) => response.data,
  (error) => {
    const message = error.response?.data?.message || error.message || 'API Error';
    console.error('API Error:', message);
    return Promise.reject({ message });
  }
);

// Health
export const getHealth = () => api.get('/api/health');
export const getHealthDetailed = () => api.get('/api/health/detailed');
export const getHealthUptime = () => api.get('/api/health/uptime');
export const getHealthCameras = () => api.get('/api/health/cameras');

// Detections
export const getDetectionsSummary = () => api.get('/api/detections/summary');
export const getRecentDetections = (limit = 100) => api.get(`/api/detections/recent?limit=${limit}`);
export const getTodayDetections = () => api.get('/api/detections/today');

// Alerts
export const getAlerts = (limit = 50) => api.get(`/api/alerts?limit=${limit}`);
export const getRecentAlerts = (hours = 24) => api.get(`/api/alerts/recent?hours=${hours}`);
export const getAlertStats = () => api.get('/api/alerts/stats');
export const sendViolationAlert = (data) => api.post('/api/violations/alert', data);

// Snapshots
export const getSnapshotsCount = () => api.get('/api/snapshots-count');
export const getSnapshots = () => api.get('/api/snapshots');
export const deleteSnapshot = (id) => api.post('/api/snapshots/delete', { id });

// Analytics
export const getAnalyticsStats = () => api.get('/api/analytics/stats');
export const getAnalyticsDashboard = () => api.get('/api/analytics/dashboard');
export const getExecutiveSummary = () => api.get('/api/analytics/executive-summary');
export const getTrendAnalysis = (days = 30) => api.get(`/api/analytics/trend-analysis?days=${days}`);
export const getMTTR = () => api.get('/api/analytics/kpis/mttr');
export const getFalsePositiveRate = () => api.get('/api/analytics/kpis/false-positive-rate');
export const getCoverage = () => api.get('/api/analytics/kpis/coverage');
export const getAdvancedKPIs = () => api.get('/api/analytics/kpis/advanced');
export const getCorrelation = () => api.get('/api/analytics/correlation');
export const getPercentiles = () => api.get('/api/analytics/percentiles');

// Charts
export const getClassDistribution = () => api.get('/api/analytics/charts/class-distribution');
export const getViolationTrend = (days = 7) => api.get(`/api/analytics/charts/violation-trend?days=${days}`);
export const getConfidenceByClass = () => api.get('/api/analytics/charts/confidence-by-class');
export const getHourlyActivity = () => api.get('/api/analytics/charts/hourly-activity');
export const getViolationStatus = () => api.get('/api/analytics/charts/violation-status');

// Predictive
export const getForecast = (days = 7) => api.get(`/api/analytics/predictive/forecast?days_ahead=${days}`);
export const getPredictiveTrend = (days = 30) => api.get(`/api/analytics/predictive/trend?days=${days}`);
export const detectAnomalies = (method = 'zscore') => api.post('/api/analytics/anomalies/detect', { method });
export const detectBehavioral = () => api.post('/api/analytics/anomalies/behavioral', {});

// Reports
export const getDailyReport = (date) => api.get(`/api/reports/daily${date ? `?date=${date}` : ''}`);
export const getWeeklyReport = (endDate) => api.get(`/api/reports/weekly${endDate ? `?end_date=${endDate}` : ''}`);
export const getMonthlyReport = (year, month) => api.get(`/api/reports/monthly?year=${year}&month=${month}`);
export const getComplianceReport = (type = 'gdpr') => api.get(`/api/reports/compliance/${type}`);
export const sendReportEmail = (data) => api.post('/api/reports/send-email', data);

// Cost
export const getCostConfig = () => api.get('/api/cost/config');
export const updateCostConfig = (data) => api.put('/api/cost/config', data);
export const getOperationalCost = () => api.get('/api/cost/operational');
export const getROI = () => api.get('/api/cost/roi');
export const getResourceUtilization = () => api.get('/api/cost/resource-utilization');
export const getCompleteAnalysis = () => api.get('/api/cost/complete-analysis');

// Email
export const testEmail = () => api.get('/api/email/test');
export const getEmailConfig = () => api.get('/api/email/config');
export const sendEmailAlert = (data) => api.post('/api/email/alert', data);
export const sendEmailReport = (data) => api.post('/api/email/send-report', data);
export const scheduleReport = (data) => api.post('/api/email/schedule-report', data);
export const getEmailSchedules = () => api.get('/api/email/schedules');
export const deleteEmailSchedule = (id) => api.delete(`/api/email/schedules/${id}`);
export const getEmailTemplates = () => api.get('/api/email/templates');

// Cameras
export const getCameras = () => api.get('/api/cameras');
export const addCamera = (data) => api.post('/api/cameras', data);
export const getCamera = (id) => api.get(`/api/cameras/${id}`);
export const updateCamera = (id, data) => api.put(`/api/cameras/${id}`, data);
export const deleteCamera = (id) => api.delete(`/api/cameras/${id}`);

// Activity
export const getActivityFeed = (limit = 50) => api.get(`/api/activity/feed?limit=${limit}`);
export const syncActivity = () => api.post('/api/activity/sync');
export const getActivityDetections = (limit = 100) => api.get(`/api/activity/detections?limit=${limit}`);

// Users
export const getUserActivity = (limit = 100) => api.get(`/api/users/activity?limit=${limit}`);
export const logUserActivity = (data) => api.post('/api/users/activity', data);
export const getUserStats = () => api.get('/api/users/stats');

// Info
export const getInfo = () => api.get('/api/info');

export default api;
