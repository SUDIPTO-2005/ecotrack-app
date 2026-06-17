import React, { useEffect, useState } from 'react';
import { useAppStore } from '../../store/useAppStore';
import { apiClient } from '../../api/apiClient';
import { User, Bell, Shield, Check } from 'lucide-react';

interface ProfileData {
  display_name: string;
  city: string;
  country: string;
  privacy_level: 'public' | 'friends' | 'anonymous';
}

interface NotificationPreference {
  email_enabled: boolean;
  in_app_enabled: boolean;
  frequency_cap: number;
}

export default function Profile() {
  const { user, fetchUser, showToast } = useAppStore();
  const [profileForm, setProfileForm] = useState<ProfileData>({
    display_name: '',
    city: '',
    country: '',
    privacy_level: 'anonymous',
  });

  const [notifForm, setNotifForm] = useState<NotificationPreference>({
    email_enabled: true,
    in_app_enabled: true,
    frequency_cap: 7,
  });

  const [savingProfile, setSavingProfile] = useState(false);
  const [savingNotif, setSavingNotif] = useState(false);

  useEffect(() => {
    if (user) {
      setProfileForm({
        display_name: user.display_name || '',
        city: user.city || '',
        country: user.country || '',
        privacy_level: user.privacy_level || 'anonymous',
      });
    }

    async function loadNotificationPrefs() {
      try {
        const response = await apiClient.request<NotificationPreference>('/accounts/notifications/preferences/');
        setNotifForm(response);
      } catch (err) {
        console.error('Failed to load notification settings', err);
      }
    }
    loadNotificationPrefs();
  }, [user]);

  const handleProfileSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSavingProfile(true);
    try {
      await apiClient.request('/accounts/profile/', {
        method: 'PUT',
        body: JSON.stringify(profileForm),
      });
      showToast('Profile configuration updated!', 'success');
      await fetchUser();
    } catch (err) {
      const error = err as { error?: { message?: string } };
      showToast(error.error?.message || 'Failed to update profile.', 'error');
    } finally {
      setSavingProfile(false);
    }
  };

  const handleNotifSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSavingNotif(true);
    try {
      await apiClient.request('/accounts/notifications/preferences/', {
        method: 'PUT',
        body: JSON.stringify(notifForm),
      });
      showToast('Notification frequency settings updated.', 'success');
    } catch (err) {
      const error = err as { error?: { message?: string } };
      showToast(error.error?.message || 'Failed to update notification rules.', 'error');
    } finally {
      setSavingNotif(false);
    }
  };

  return (
    <div className="profile-view">
      <div className="profile-header">
        <h2 className="title-gradient"><User size={24} style={{ color: 'var(--color-yellow)' }} /> Account Settings</h2>
        <p className="subtitle">Manage your profile visibility, location info, and frequency notifications.</p>
      </div>

      <div className="profile-content-grid">
        {/* Profile Settings */}
        <form onSubmit={handleProfileSubmit} className="glow-card settings-card">
          <div className="card-header">
            <h3><Shield size={18} /> Public Profile Visibility</h3>
          </div>
          <p className="card-desc">Decide how your metrics appear on regional and global standers leaderboards.</p>

          <div className="input-group">
            <label htmlFor="display_name">Display Name</label>
            <input
              id="display_name"
              type="text"
              value={profileForm.display_name}
              onChange={(e) => setProfileForm({ ...profileForm, display_name: e.target.value })}
              placeholder="e.g. EcoExplorer"
            />
          </div>

          <div className="input-row-grid">
            <div className="input-group">
              <label htmlFor="city">City</label>
              <input
                id="city"
                type="text"
                value={profileForm.city}
                onChange={(e) => setProfileForm({ ...profileForm, city: e.target.value })}
                placeholder="Mumbai"
              />
            </div>
            <div className="input-group">
              <label htmlFor="country">Country</label>
              <input
                id="country"
                type="text"
                value={profileForm.country}
                onChange={(e) => setProfileForm({ ...profileForm, country: e.target.value })}
                placeholder="India"
              />
            </div>
          </div>

          <div className="input-group">
            <label htmlFor="privacy_level">Privacy Level</label>
            <select
              id="privacy_level"
              value={profileForm.privacy_level}
              onChange={(e) => setProfileForm({ ...profileForm, privacy_level: e.target.value as ProfileData['privacy_level'] })}
            >
              <option value="anonymous">Anonymous (Hidden from lists, shows as Anonymous User)</option>
              <option value="friends">Friends Only (Visible to friends network)</option>
              <option value="public">Public (Visible on global & city leaderboards)</option>
            </select>
          </div>

          <button type="submit" className="btn-primary flex-center-gap" disabled={savingProfile}>
            {savingProfile ? 'Saving...' : 'Update Settings'} <Check size={16} />
          </button>
        </form>

        {/* Notification Preferences */}
        <form onSubmit={handleNotifSubmit} className="glow-card settings-card">
          <div className="card-header">
            <h3><Bell size={18} /> Notification Frequency</h3>
          </div>
          <p className="card-desc">Control email notifications and opt-out limits at the data level.</p>

          <div className="checkbox-group">
            <label className="checkbox-container">
              <input
                type="checkbox"
                checked={notifForm.email_enabled}
                onChange={(e) => setNotifForm({ ...notifForm, email_enabled: e.target.checked })}
              />
              <span className="checkmark"></span>
              Receive Email Notifications (weekly reports, challenge digests)
            </label>
          </div>

          <div className="checkbox-group" style={{ marginTop: '16px' }}>
            <label className="checkbox-container">
              <input
                type="checkbox"
                checked={notifForm.in_app_enabled}
                onChange={(e) => setNotifForm({ ...notifForm, in_app_enabled: e.target.checked })}
              />
              <span className="checkmark"></span>
              Enable In-App Notification Alerts
            </label>
          </div>

          <div className="input-group" style={{ marginTop: '24px' }}>
            <label htmlFor="frequency_cap">Frequency Cap Limit (minimum days between notifications)</label>
            <input
              id="frequency_cap"
              type="number"
              min="1"
              max="30"
              value={notifForm.frequency_cap}
              onChange={(e) => setNotifForm({ ...notifForm, frequency_cap: Number(e.target.value) })}
            />
            <span className="field-hint">Helps prevent inbox spam (e.g. 7 means max once a week).</span>
          </div>

          <button type="submit" className="btn-primary flex-center-gap" disabled={savingNotif}>
            {savingNotif ? 'Saving...' : 'Save Preferences'} <Check size={16} />
          </button>
        </form>
      </div>
    </div>
  );
}
