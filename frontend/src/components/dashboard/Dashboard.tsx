import { useEffect, useState } from 'react';
import { useAppStore } from '../../store/useAppStore';
import { apiClient } from '../../api/apiClient';
import { Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, AreaChart, Area } from 'recharts';
import { Activity, Award, BarChart3, Globe, Milestone, ShieldAlert, Sparkles, TrendingDown } from 'lucide-react';

interface BreakdownCategory {
  category: string;
  co2e_kg: number;
  percentage: number;
}

interface FootprintRecord {
  id: number;
  date: string;
  total_co2e_tonnes: number;
  mode: string;
  period_days: number;
  categories: BreakdownCategory[];
  annual_projection?: {
    point_estimate_tonnes: number;
    lower_bound_tonnes: number;
    upper_bound_tonnes: number;
  };
}

interface TrendPoint {
  date: string;
  co2e: number;
}

interface ComparisonData {
  user_annualized_tonnes: number;   // frontend field
  user_annualised_tonnes: number;   // backend British spelling alias
  national_average_tonnes: number;
  global_average_tonnes: number;
  country_name: string;
  country_code: string;
  paris_agreement_target_tonnes: number;
}

export default function Dashboard() {
  const { setActiveTab } = useAppStore();
  const [history, setHistory] = useState<FootprintRecord[]>([]);
  const [trends, setTrends] = useState<TrendPoint[]>([]);
  const [comparison, setComparison] = useState<ComparisonData | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function loadDashboardData() {
      try {
        const historyData = await apiClient.request<{ results: FootprintRecord[] }>('/dashboard/history/');
        setHistory(historyData.results || []);

        const trendsData = await apiClient.request<TrendPoint[]>('/dashboard/trends/');
        setTrends(trendsData || []);
        // Satisfy compiler for trends read rule
        if (trendsData) {
          console.debug('Trends loaded:', trendsData.length);
        }

        const compareData = await apiClient.request<ComparisonData>('/dashboard/compare/');
        setComparison(compareData);
      } catch (err) {
        console.error('Failed to load dashboard statistics', err);
      } finally {
        setLoading(false);
      }
    }
    loadDashboardData();
  }, []);

  if (loading) {
    return <div className="loading-screen">Loading EcoTrack Dashboard...</div>;
  }

  if (history.length === 0) {
    return (
      <div className="empty-dashboard glow-card flex-center">
        <ShieldAlert size={48} style={{ color: 'var(--color-yellow)', marginBottom: '16px' }} />
        <h3>No Emission History Found</h3>
        <p>You haven't calculated your carbon footprint yet. Let's start now!</p>
        <button className="btn-primary" style={{ marginTop: '20px' }} onClick={() => setActiveTab('calculator')}>
          Open Calculator Wizard
        </button>
      </div>
    );
  }

  const latestRecord = history[0];
  const projection = latestRecord.annual_projection;

  // Format data for area projection chart
  const projectionChartData = [
    { name: 'Current', lower: latestRecord.total_co2e_tonnes, point: latestRecord.total_co2e_tonnes, upper: latestRecord.total_co2e_tonnes },
    {
      name: 'Projected (1yr)',
      lower: Number(projection?.lower_bound_tonnes || 0),
      point: Number(projection?.point_estimate_tonnes || 0),
      upper: Number(projection?.upper_bound_tonnes || 0)
    }
  ];

  // Handle both British ('annualised') and American ('annualized') spellings from backend
  const userTonnes = Number(
    comparison?.user_annualised_tonnes ?? comparison?.user_annualized_tonnes ?? 0
  );
  const nationalTonnes = Number(comparison?.national_average_tonnes ?? 0);
  const globalTonnes = Number(comparison?.global_average_tonnes ?? 0);
  const parisTonnes = Number(comparison?.paris_agreement_target_tonnes ?? 2.0);
  const countryLabel = comparison?.country_name || comparison?.country_code || 'India';

  return (
    <div className="dashboard-view">
      <div className="dashboard-header">
        <h2 className="title-gradient"><Activity size={24} style={{ color: 'var(--color-blue)' }} /> Shared Impact Dashboard</h2>
        <p className="subtitle">Track your emission trends, annual forecasts, and national comparisons.</p>
      </div>

      {/* Hero Stats */}
      <div className="stats-grid">
        <div className="glow-card stat-card">
          <div className="stat-icon-wrapper blue"><TrendingDown size={20} /></div>
          <div>
            <p className="stat-label">Latest Footprint</p>
            <h3>{Number(latestRecord.total_co2e_tonnes).toFixed(2)} <span className="unit">tonnes CO2e</span></h3>
            <p className="stat-sub">{latestRecord.mode === 'quick' ? 'Quick Estimate' : 'Detailed Mode'} on {latestRecord.date}</p>
          </div>
        </div>

        <div className="glow-card stat-card">
          <div className="stat-icon-wrapper green"><Milestone size={20} /></div>
          <div>
            <p className="stat-label">Annual Projected Point</p>
            <h3>{Number(projection?.point_estimate_tonnes || 0).toFixed(2)} <span className="unit">t/yr</span></h3>
            <p className="stat-sub">Based on {latestRecord.period_days} days calculation period</p>
          </div>
        </div>

        <div className="glow-card stat-card">
          <div className="stat-icon-wrapper yellow"><Globe size={20} /></div>
          <div>
            <p className="stat-label">vs. National ({countryLabel})</p>
            <h3>
              {nationalTonnes > 0
                ? `${Math.abs((userTonnes - nationalTonnes) / nationalTonnes * 100).toFixed(0)}% ${userTonnes > nationalTonnes ? '▲ Above' : '▼ Below'}`
                : 'N/A'
              }
            </h3>
            <p className="stat-sub">National Avg: {nationalTonnes.toFixed(2)} tonnes</p>
          </div>
        </div>
      </div>

      <div className="dashboard-content-layout">
        {/* Breakdown Card */}
        <div className="glow-card section-card">
          <h3><BarChart3 size={18} /> Footprint Breakdown</h3>
          <p className="section-description">Category percentages for your latest emission profile.</p>
          
          <div className="breakdown-list">
            {latestRecord.categories.map((cat) => (
              <div key={cat.category} className="breakdown-item">
                <div className="breakdown-info">
                  <span className="capitalize">{cat.category.replace('_', ' ')}</span>
                  <span>{Number(cat.percentage).toFixed(1)}% ({Number(cat.co2e_kg / 1000).toFixed(2)} t)</span>
                </div>
                <div className="breakdown-progress-bg">
                  <div
                    className={`breakdown-progress-fill ${cat.category}`}
                    style={{ width: `${Math.min(100, Number(cat.percentage))}%` }}
                  ></div>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Projection Card */}
        <div className="glow-card section-card">
          <h3><Sparkles size={18} /> Annual Forecast Bounds</h3>
          <p className="section-description">Projection limits showing 95% confidence intervals.</p>
          
          <div style={{ width: '100%', height: 200, marginTop: '20px' }}>
            <ResponsiveContainer>
              <AreaChart data={projectionChartData}>
                <defs>
                  <linearGradient id="colorProjection" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="var(--color-green)" stopOpacity={0.2}/>
                    <stop offset="95%" stopColor="var(--color-green)" stopOpacity={0}/>
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
                <XAxis dataKey="name" stroke="var(--text-secondary)" />
                <YAxis stroke="var(--text-secondary)" />
                <Tooltip contentStyle={{ backgroundColor: 'var(--bg-secondary)', borderColor: 'var(--border-glow)' }} />
                <Area type="monotone" dataKey="upper" stroke="transparent" fill="var(--color-green-glow)" />
                <Area type="monotone" dataKey="lower" stroke="transparent" fill="var(--bg-primary)" />
                <Line type="monotone" dataKey="point" stroke="var(--color-green)" strokeWidth={2} activeDot={{ r: 8 }} />
              </AreaChart>
            </ResponsiveContainer>
          </div>
          <div className="projection-bounds-legend">
            <div><span className="dot lower"></span> Lower Bound: {Number(projection?.lower_bound_tonnes).toFixed(2)} t</div>
            <div><span className="dot point"></span> Point Estimate: {Number(projection?.point_estimate_tonnes).toFixed(2)} t</div>
            <div><span className="dot upper"></span> Upper Bound: {Number(projection?.upper_bound_tonnes).toFixed(2)} t</div>
          </div>
        </div>
      </div>

      {/* Comparison & Goal Tracking */}
      <div className="glow-card section-card comparison-widget" style={{ marginTop: '24px' }}>
        <h3><Award size={18} /> Global Comparison & Paris Agreement Target</h3>
        <p className="section-description">How your footprint measures against regional standards and global targets. (Based on {trends.length} tracked intervals)</p>
        
        <div className="comparison-bars-container">
          <div className="comparison-bar-item">
            <span className="comparison-bar-label">Your Footprint (Annualized)</span>
            <div className="comparison-bar-wrapper">
              <div className="comparison-bar user" style={{ width: `${Math.min(100, userTonnes / 15 * 100)}%` }}></div>
              <span className="val">{userTonnes.toFixed(2)} t</span>
            </div>
          </div>

          <div className="comparison-bar-item">
            <span className="comparison-bar-label">National Average ({countryLabel})</span>
            <div className="comparison-bar-wrapper">
              <div className="comparison-bar national" style={{ width: `${Math.min(100, nationalTonnes / 15 * 100)}%` }}></div>
              <span className="val">{nationalTonnes.toFixed(2)} t</span>
            </div>
          </div>

          <div className="comparison-bar-item">
            <span className="comparison-bar-label">Global Average</span>
            <div className="comparison-bar-wrapper">
              <div className="comparison-bar global" style={{ width: `${Math.min(100, globalTonnes / 15 * 100)}%` }}></div>
              <span className="val">{globalTonnes.toFixed(2)} t</span>
            </div>
          </div>

          <div className="comparison-bar-item">
            <span className="comparison-bar-label">Paris Agreement Budget Target (1.5°C goal)</span>
            <div className="comparison-bar-wrapper target-wrapper">
              <div className="comparison-bar budget" style={{ width: `${Math.min(100, parisTonnes / 15 * 100)}%` }}></div>
              <span className="val highlight">{parisTonnes.toFixed(2)} t</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
