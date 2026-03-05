import { useState } from 'react';
import { AuthProvider, useAuth } from './context/AuthContext';
import Layout from './components/Layout';
import LoginPage from './pages/LoginPage';
import HomePage from './pages/HomePage';
import LiveMonitorPage from './pages/LiveMonitorPage';
import AnalyticsPage from './pages/AnalyticsPage';
import SnapshotsPage from './pages/SnapshotsPage';
import RecordingsPage from './pages/RecordingsPage';
import EmailReportingPage from './pages/EmailReportingPage';

function MainApp() {
  const { isAuthenticated } = useAuth();
  const [activeTab, setActiveTab] = useState('Home');

  if (!isAuthenticated) {
    return <LoginPage />;
  }

  const renderTab = () => {
    switch (activeTab) {
      case 'Home': return <HomePage />;
      case 'Live Monitor': return <LiveMonitorPage />;
      case 'Analytics': return <AnalyticsPage />;
      case 'Snapshots': return <SnapshotsPage />;
      case 'Recordings': return <RecordingsPage />;
      case 'Email Reporting': return <EmailReportingPage />;
      default: return <HomePage />;
    }
  };

  return (
    <Layout activeTab={activeTab} onTabChange={setActiveTab}>
      {renderTab()}
    </Layout>
  );
}

export default function App() {
  return (
    <AuthProvider>
      <MainApp />
    </AuthProvider>
  );
}
