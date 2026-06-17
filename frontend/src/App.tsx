import { useEffect } from 'react';
import { useAppStore } from './store/useAppStore';
import AuthForms from './components/auth/AuthForms';
import Dashboard from './components/dashboard/Dashboard';
import Calculator from './components/calculator/Calculator';
import Challenges from './components/challenges/Challenges';
import AiCoach from './components/coach/AiCoach';
import Profile from './components/profile/Profile';
import EcoBot from './components/chatbot/EcoBot';
import { LayoutDashboard, Leaf, Trophy, Sparkles, User, LogOut, Sprout } from 'lucide-react';
import './index.css';

function App() {
  const {
    user,
    isAuthenticated,
    isLoadingUser,
    activeTab,
    toast,
    setActiveTab,
    fetchUser,
    logout,
    clearToast
  } = useAppStore();

  useEffect(() => {
    if (isAuthenticated) {
      fetchUser();
    }
  }, [isAuthenticated]);

  // Handle global auth-expired event from apiClient
  useEffect(() => {
    const handleAuthExpired = () => {
      useAppStore.setState({ isAuthenticated: false, user: null });
    };
    window.addEventListener('auth-expired', handleAuthExpired);
    return () => window.removeEventListener('auth-expired', handleAuthExpired);
  }, []);

  if (!isAuthenticated) {
    return (
      <>
        <AuthForms />
        {toast && (
          <div className="toast-container" role="alert" aria-live="assertive">
            <div 
              className={`toast ${toast.type}`} 
              onClick={clearToast}
              role="button"
              tabIndex={0}
              onKeyDown={(e) => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); clearToast(); } }}
              aria-label={`Notification: ${toast.message}. Click to dismiss.`}
            >
              {toast.message}
            </div>
          </div>
        )}
      </>
    );
  }

  if (isLoadingUser && !user) {
    return <div className="loading-screen">Loading EcoTrack...</div>;
  }

  // Force onboarding calculator redirect
  const isOnboarding = user && !user.onboarding_complete;
  const currentTab = isOnboarding ? 'calculator' : activeTab;

  const renderActiveComponent = () => {
    switch (currentTab) {
      case 'dashboard':
        return <Dashboard />;
      case 'calculator':
        return <Calculator />;
      case 'challenges':
        return <Challenges />;
      case 'coach':
        return <AiCoach />;
      case 'profile':
        return <Profile />;
      default:
        return <Dashboard />;
    }
  };

  return (
    <div className="app-container">
      {/* Sidebar Navigation */}
      <aside className="sidebar">
        <div>
          <div className="sidebar-logo">
            <Sprout size={28} className="logo-pulse" style={{ color: 'var(--color-green)' }} />
            <h1 className="title-gradient">EcoTrack</h1>
          </div>

          <nav className="nav-links">
            <button
              disabled={!!isOnboarding}
              className={`nav-link ${currentTab === 'dashboard' ? 'active' : ''}`}
              onClick={() => setActiveTab('dashboard')}
            >
              <LayoutDashboard size={18} /> Dashboard
            </button>
            <button
              className={`nav-link ${currentTab === 'calculator' ? 'active' : ''}`}
              onClick={() => setActiveTab('calculator')}
            >
              <Leaf size={18} /> Calculator {isOnboarding && <span className="fallback-badge" style={{ fontSize: '0.65rem', marginLeft: 'auto' }}>Required</span>}
            </button>
            <button
              disabled={!!isOnboarding}
              className={`nav-link ${currentTab === 'challenges' ? 'active' : ''}`}
              onClick={() => setActiveTab('challenges')}
            >
              <Trophy size={18} /> Challenges
            </button>
            <button
              disabled={!!isOnboarding}
              className={`nav-link ${currentTab === 'coach' ? 'active' : ''}`}
              onClick={() => setActiveTab('coach')}
            >
              <Sparkles size={18} /> AI Coach
            </button>
            <button
              disabled={!!isOnboarding}
              className={`nav-link ${currentTab === 'profile' ? 'active' : ''}`}
              onClick={() => setActiveTab('profile')}
            >
              <User size={18} /> Profile
            </button>
          </nav>
        </div>

        <div className="sidebar-footer">
          <div className="user-info-brief">
            <span className="name">{user?.display_name || user?.username || 'Eco User'}</span>
            <span className="role capitalize">{user?.privacy_level || 'anonymous'} privacy</span>
          </div>
          <button className="nav-link" onClick={() => logout()} style={{ color: 'var(--color-red)' }}>
            <LogOut size={18} /> Sign Out
          </button>
        </div>
      </aside>

      {/* Main Panel Viewport */}
      <main className="main-content">
        {renderActiveComponent()}
      </main>

      {/* Floating EcoBot Chatbot — always visible when logged in */}
      <EcoBot />

      {/* Notification Toast Messages */}
      {toast && (
        <div className="toast-container" role="alert" aria-live="assertive">
          <div 
            className={`toast ${toast.type}`} 
            onClick={clearToast}
            role="button"
            tabIndex={0}
            onKeyDown={(e) => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); clearToast(); } }}
            aria-label={`Notification: ${toast.message}. Click to dismiss.`}
          >
            {toast.message}
          </div>
        </div>
      )}
    </div>
  );
}

export default App;
