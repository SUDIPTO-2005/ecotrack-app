import React, { useState } from 'react';
import { useAppStore } from '../../store/useAppStore';
import { apiClient } from '../../api/apiClient';
import { LogIn, UserPlus, Sprout } from 'lucide-react';

export default function AuthForms() {
  const { fetchUser, showToast, setIsAuthenticated } = useAppStore();
  const [mode, setMode] = useState<'login' | 'register'>('login');
  const [loading, setLoading] = useState(false);

  // Forms states
  const [loginForm, setLoginForm] = useState({
    email: '',
    password: '',
  });

  const [registerForm, setRegisterForm] = useState({
    username: '',
    email: '',
    password: '',
    display_name: '',
    city: '',
    country: '',
  });

  const handleLoginSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    try {
      const tokens: { access: string; refresh: string } = await apiClient.request('/accounts/login/', {
        method: 'POST',
        body: JSON.stringify({
          email: loginForm.email,
          password: loginForm.password
        }),
      });
      apiClient.setTokens(tokens.access, tokens.refresh);
      setIsAuthenticated(true);
      showToast('Logged in successfully!', 'success');
      await fetchUser();
    } catch (err: any) {
      console.error(err);
      showToast(err?.error?.message || err?.detail || 'Invalid email or password.', 'error');
    } finally {
      setLoading(false);
    }
  };

  const handleRegisterSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    try {
      const tokens: { access: string; refresh: string } = await apiClient.request('/accounts/register/', {
        method: 'POST',
        body: JSON.stringify({
          email: registerForm.email,
          password: registerForm.password,
          display_name: registerForm.display_name,
          country: registerForm.country,
        }),
      });
      showToast('Registration successful!', 'success');
      apiClient.setTokens(tokens.access, tokens.refresh);
      setIsAuthenticated(true);
      await fetchUser();
    } catch (err: any) {
      console.error(err);
      let errorMessage = 'Registration failed. Check password length (min 10) and email format.';
      if (err?.error?.details) {
        const details = err.error.details;
        const messages = Object.keys(details).map(key => {
          const fieldErrors = Array.isArray(details[key]) ? details[key].join(', ') : details[key];
          return `${key}: ${fieldErrors}`;
        });
        if (messages.length > 0) {
          errorMessage = messages.join(' | ');
        }
      } else if (err?.error?.message) {
        errorMessage = err.error.message;
      }
      showToast(errorMessage, 'error');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="auth-container">
      <div className="auth-card glow-card">
        <div className="auth-logo-row flex-center-gap">
          <Sprout size={36} className="logo-pulse" style={{ color: 'var(--color-green)' }} />
          <h1 className="title-gradient">EcoTrack</h1>
        </div>
        <p className="auth-subtitle">Calculate, track and reduce emissions collectively.</p>

        <div className="auth-toggle-row">
          <button
            className={mode === 'login' ? 'active' : ''}
            onClick={() => setMode('login')}
          >
            Sign In
          </button>
          <button
            className={mode === 'register' ? 'active' : ''}
            onClick={() => setMode('register')}
          >
            Register
          </button>
        </div>

        {mode === 'login' ? (
          <form onSubmit={handleLoginSubmit} className="auth-form">
            <div className="input-group">
              <label>Email Address</label>
              <input
                type="email"
                required
                value={loginForm.email}
                onChange={(e) => setLoginForm({ ...loginForm, email: e.target.value })}
                placeholder="enter email"
              />
            </div>
            <div className="input-group">
              <label>Password</label>
              <input
                type="password"
                required
                value={loginForm.password}
                onChange={(e) => setLoginForm({ ...loginForm, password: e.target.value })}
                placeholder="••••••••••"
              />
            </div>
            <button type="submit" className="btn-primary flex-center-gap" disabled={loading}>
              {loading ? 'Signing In...' : 'Access Account'} <LogIn size={18} />
            </button>
          </form>
        ) : (
          <form onSubmit={handleRegisterSubmit} className="auth-form scrollable-panel">
            <div className="input-group">
              <label>Username</label>
              <input
                type="text"
                required
                value={registerForm.username}
                onChange={(e) => setRegisterForm({ ...registerForm, username: e.target.value })}
                placeholder="username"
              />
            </div>
            <div className="input-group">
              <label>Email Address</label>
              <input
                type="email"
                required
                value={registerForm.email}
                onChange={(e) => setRegisterForm({ ...registerForm, email: e.target.value })}
                placeholder="you@example.com"
              />
            </div>
            <div className="input-group">
              <label>Password</label>
              <input
                type="password"
                required
                value={registerForm.password}
                onChange={(e) => setRegisterForm({ ...registerForm, password: e.target.value })}
                placeholder="min 10 characters"
              />
            </div>
            <div className="input-group">
              <label>Display Name (Optional)</label>
              <input
                type="text"
                value={registerForm.display_name}
                onChange={(e) => setRegisterForm({ ...registerForm, display_name: e.target.value })}
                placeholder="e.g. EcoExplorer"
              />
            </div>
            <div className="input-row-grid">
              <div className="input-group">
                <label>City</label>
                <input
                  type="text"
                  value={registerForm.city}
                  onChange={(e) => setRegisterForm({ ...registerForm, city: e.target.value })}
                  placeholder="Mumbai"
                />
              </div>
              <div className="input-group">
                <label>Country</label>
                <input
                  type="text"
                  value={registerForm.country}
                  onChange={(e) => setRegisterForm({ ...registerForm, country: e.target.value })}
                  placeholder="India"
                />
              </div>
            </div>
            <button type="submit" className="btn-primary flex-center-gap" disabled={loading}>
              {loading ? 'Creating...' : 'Register & Start'} <UserPlus size={18} />
            </button>
          </form>
        )}
      </div>
    </div>
  );
}
