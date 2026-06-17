import { useEffect, useState } from 'react';
import { useAppStore } from '../../store/useAppStore';
import { apiClient } from '../../api/apiClient';
import { Trophy, ShieldCheck, Plus, Minus, Users, Star, Landmark } from 'lucide-react';

interface Challenge {
  id: number;
  title: string;
  description: string;
  category: string;
  start_date: string;
  end_date: string;
  target_reduction_pct: string;
  joined: boolean;
  participants_count: number;
}

interface Badge {
  id: number;
  badge: {
    name: string;
    description: string;
    criteria: string;
  };
  awarded_at: string;
}

interface LeaderboardUser {
  rank: number;
  public_name: string;
  city: string;
  country: string;
  score: number;
}

export default function Challenges() {
  const { showToast } = useAppStore();
  const [challenges, setChallenges] = useState<Challenge[]>([]);
  const [badges, setBadges] = useState<Badge[]>([]);
  const [leaderboard, setLeaderboard] = useState<LeaderboardUser[]>([]);
  const [leaderboardScope, setLeaderboardScope] = useState<'global' | 'city'>('global');
  const [loading, setLoading] = useState(true);

  const loadChallengesData = async () => {
    try {
      const challengeList = await apiClient.request<Challenge[]>('/challenges/');
      setChallenges(challengeList || []);

      const badgeList = await apiClient.request<Badge[]>('/challenges/badges/');
      setBadges(badgeList || []);

      const rankingList = await apiClient.request<LeaderboardUser[]>(`/challenges/leaderboard/?scope=${leaderboardScope}`);
      setLeaderboard(rankingList || []);
    } catch (err) {
      console.error('Failed to load challenges and badges data', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadChallengesData();
  }, [leaderboardScope]);

  const handleJoin = async (id: number) => {
    try {
      await apiClient.request(`/challenges/${id}/join/`, { method: 'POST' });
      showToast('Joined community challenge successfully!', 'success');
      loadChallengesData();
    } catch (err: any) {
      showToast(err?.error?.message || 'Failed to join challenge', 'error');
    }
  };

  const handleLeave = async (id: number) => {
    try {
      await apiClient.request(`/challenges/${id}/leave/`, { method: 'POST' });
      showToast('Left community challenge.', 'info');
      loadChallengesData();
    } catch (err: any) {
      showToast(err?.error?.message || 'Failed to leave challenge', 'error');
    }
  };

  if (loading) {
    return <div className="loading-screen">Loading Challenges & Standings...</div>;
  }

  return (
    <div className="challenges-view">
      <div className="challenges-header">
        <h2 className="title-gradient"><Trophy size={24} style={{ color: 'var(--color-yellow)' }} /> Community Challenges</h2>
        <p className="subtitle">Join active initiatives, earn unique badges, and level up the leaderboard.</p>
      </div>

      <div className="challenges-content-layout">
        {/* Challenge Cards list */}
        <div className="challenges-main">
          <h3>Active Challenges</h3>
          <div className="challenges-grid">
            {challenges.map((challenge) => (
              <div key={challenge.id} className={`glow-card challenge-card ${challenge.joined ? 'joined' : ''}`}>
                <div className="challenge-card-header">
                  <span className="challenge-category">{challenge.category}</span>
                  <span className="challenge-reduction">Target: {Number(challenge.target_reduction_pct).toFixed(0)}% Reduction</span>
                </div>
                <h4>{challenge.title}</h4>
                <p className="desc">{challenge.description}</p>
                <div className="challenge-info-row">
                  <span className="flex-center-gap"><Users size={16} /> {challenge.participants_count} joined</span>
                  <span className="dates">Ends {challenge.end_date}</span>
                </div>
                <div className="challenge-actions">
                  {challenge.joined ? (
                    <button className="btn-secondary flex-center-gap" onClick={() => handleLeave(challenge.id)}>
                      <Minus size={16} /> Leave Challenge
                    </button>
                  ) : (
                    <button className="btn-primary flex-center-gap" onClick={() => handleJoin(challenge.id)}>
                      <Plus size={16} /> Join Challenge
                    </button>
                  )}
                </div>
              </div>
            ))}
          </div>

          <h3 style={{ marginTop: '32px' }}>Your Badges</h3>
          {badges.length === 0 ? (
            <div className="glow-card empty-badges">
              <Star size={24} style={{ color: 'var(--text-secondary)' }} />
              <p>No badges earned yet. Complete footprint calculations or challenges to unlock!</p>
            </div>
          ) : (
            <div className="badges-grid">
              {badges.map((item) => (
                <div key={item.id} className="glow-card badge-card">
                  <div className="badge-icon-wrapper"><ShieldCheck size={28} /></div>
                  <h4>{item.badge.name}</h4>
                  <p>{item.badge.description}</p>
                  <span className="badge-criteria">Criteria: {item.badge.criteria.replace('_', ' ')}</span>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Leaderboard Standing sidebar */}
        <div className="leaderboard-sidebar glow-card">
          <div className="leaderboard-header-row">
            <h3>Standings</h3>
            <div className="scope-selectors">
              <button
                className={leaderboardScope === 'global' ? 'active' : ''}
                onClick={() => setLeaderboardScope('global')}
              >
                Global
              </button>
              <button
                className={leaderboardScope === 'city' ? 'active' : ''}
                onClick={() => setLeaderboardScope('city')}
              >
                City
              </button>
            </div>
          </div>
          <p className="leaderboard-desc">Ranked by carbon footprint improvement. Default values represent standard metrics.</p>

          <div className="leaderboard-list">
            {leaderboard.map((item) => (
              <div key={item.rank} className="leaderboard-item">
                <div className="user-rank-info">
                  <span className="rank-num">#{item.rank}</span>
                  <div>
                    <span className="username">{item.public_name}</span>
                    <span className="location"><Landmark size={12} /> {item.city || 'Anywhere'}, {item.country || 'Global'}</span>
                  </div>
                </div>
                <div className="improvement-score">
                  {item.score !== undefined ? `${Number(item.score).toFixed(1)}%` : '0%'}
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
