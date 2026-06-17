import { useState, useEffect } from 'react';
import { useAppStore } from '../../store/useAppStore';
import { apiClient } from '../../api/apiClient';
import { MessageSquare, Sparkles, ShieldCheck, ShieldAlert, Heart, Sprout, ShoppingCart, RefreshCw, Leaf } from 'lucide-react';

interface CoachingTip {
  category: string;
  recommendation: string;
  impact_level: string;
}

interface CoachingResponse {
  tips: CoachingTip[];
  next_update_available: string;
  was_fallback: boolean;
}

interface OffsetProject {
  id: number;
  name: string;
  registry: string;
  project_id: string;
  price_per_tonne: string;
  certification: string;
  project_url: string;
}

const CATEGORY_ICONS: Record<string, string> = {
  transport: '🚗',
  energy: '⚡',
  diet: '🥗',
  consumption: '🛍️',
  waste: '♻️',
};

export default function AiCoach() {
  const { showToast, setActiveTab } = useAppStore();
  const [coachResponse, setCoachResponse] = useState<CoachingResponse | null>(null);
  const [offsets, setOffsets] = useState<OffsetProject[]>([]);
  const [loadingTips, setLoadingTips] = useState(false);
  const [loadingOffsets, setLoadingOffsets] = useState(false);
  const [noData, setNoData] = useState(false);
  const [errorMsg, setErrorMsg] = useState('');

  const loadCoachingTips = async () => {
    setLoadingTips(true);
    setNoData(false);
    setErrorMsg('');
    try {
      const response = await apiClient.request<CoachingResponse>('/ai-coach/tips/', {
        method: 'POST',
        body: JSON.stringify({}),
      });
      setCoachResponse(response);
    } catch (err: any) {
      // apiClient throws the raw JSON body — check nested error.code
      const code = err?.error?.code || '';
      const msg = err?.error?.message || '';
      if (code === 'no_data' || msg.includes('footprint') || msg.includes('no_data')) {
        setNoData(true);
      } else {
        setErrorMsg('Unable to generate coaching tips. Please try again.');
        showToast('Failed to retrieve coaching suggestions.', 'error');
      }
    } finally {
      setLoadingTips(false);
    }
  };

  const loadOffsets = async () => {
    setLoadingOffsets(true);
    try {
      const response = await apiClient.request<any>('/offsets/');
      // Backend may return paginated { results: [] } or a plain array
      const list = Array.isArray(response)
        ? response
        : Array.isArray(response?.results)
        ? response.results
        : [];
      setOffsets(list);
    } catch {
      // silently ignore — offset marketplace is optional
      setOffsets([]);
    } finally {
      setLoadingOffsets(false);
    }
  };

  // Load offsets once on first render
  useEffect(() => {
    loadOffsets();
  }, []);

  return (
    <div className="coach-view">
      <div className="coach-header">
        <h2 className="title-gradient"><Sparkles size={24} style={{ color: 'var(--color-green)' }} /> AI Coach &amp; Offsets</h2>
        <p className="subtitle">Get evidence-based personalized carbon suggestions and offset marketplace links.</p>
      </div>

      <div className="coach-content-grid">
        {/* AI Coaching Panel */}
        <div className="glow-card coach-panel">
          <div className="panel-header">
            <h3><MessageSquare size={18} /> EcoCoach Weekly Advice</h3>
            {coachResponse?.was_fallback && (
              <span className="fallback-badge flex-center-gap"><ShieldAlert size={14} /> Rule-Based Engine</span>
            )}
          </div>
          <p className="section-description">Personalized tips generated from your latest footprint calculation.</p>

          {/* States */}
          {loadingTips ? (
            <div className="panel-loader">
              <div className="coach-loading-animation">
                <Leaf size={32} style={{ color: 'var(--color-green)', animation: 'spin 2s linear infinite' }} />
                <p>Consulting EcoCoach AI...</p>
              </div>
            </div>
          ) : coachResponse ? (
            <div className="tips-list">
              {coachResponse.tips.map((tip, index) => (
                <div key={index} className="tip-item">
                  <div className="tip-icon-col">
                    <span className="tip-emoji">{CATEGORY_ICONS[tip.category] || '🌿'}</span>
                    <span className={`impact-dot ${tip.impact_level}`}></span>
                  </div>
                  <div className="tip-body">
                    <div className="tip-meta">
                      <span className={`category-tag ${tip.category}`}>{tip.category}</span>
                      <span className={`impact-tag ${tip.impact_level}`}>{tip.impact_level} Impact</span>
                    </div>
                    <p className="tip-text">{tip.recommendation}</p>
                  </div>
                </div>
              ))}

              <div className="next-update-notice">
                <Heart size={16} /> Next coaching assessment available after: <strong>{new Date(coachResponse.next_update_available).toLocaleString()}</strong>
              </div>

              <button className="btn-secondary refresh-btn" onClick={loadCoachingTips} disabled={loadingTips}>
                <RefreshCw size={14} /> Regenerate Tips
              </button>
            </div>
          ) : noData ? (
            <div className="empty-panel coach-no-data">
              <span style={{ fontSize: '3rem' }}>🌱</span>
              <h4>No Footprint Data Yet</h4>
              <p>You need to calculate your carbon footprint first before EcoCoach can generate personalized advice.</p>
              <button className="btn-primary" onClick={() => setActiveTab('calculator')}>
                Open Calculator
              </button>
            </div>
          ) : errorMsg ? (
            <div className="empty-panel">
              <ShieldAlert size={32} style={{ color: 'var(--color-orange)' }} />
              <p>{errorMsg}</p>
              <button className="btn-primary" onClick={loadCoachingTips}>Try Again</button>
            </div>
          ) : (
            <div className="coach-cta">
              <div className="coach-cta-icon">🤖</div>
              <h4>Ready to get your personalized tips?</h4>
              <p>EcoCoach AI will analyze your footprint data and generate up to 5 custom recommendations, ranked by impact.</p>
              <button
                className="btn-primary coach-generate-btn"
                onClick={loadCoachingTips}
                disabled={loadingTips}
              >
                <Sparkles size={16} />
                Generate My Personalized Tips
              </button>
            </div>
          )}
        </div>

        {/* Offsets Marketplace */}
        <div className="glow-card marketplace-panel">
          <div className="panel-header">
            <h3><Sprout size={18} /> Informational Offset Marketplace</h3>
          </div>
          <p className="section-description">
            Offset your hard-to-avoid footprint emissions. We list certified projects for transparency.
          </p>

          <div className="disclaimer-alert-card">
            <ShieldCheck size={20} className="alert-icon" />
            <div>
              <strong>No-Transaction Compliance Policy</strong>
              <p>
                EcoTrack shows estimated offset costs for informational purposes only. We do not sell offsets, process payments, or guarantee any carbon retirement. To purchase verified offsets, follow the link to the registry's official listing.
              </p>
            </div>
          </div>

          {loadingOffsets ? (
            <div className="panel-loader">Loading projects...</div>
          ) : offsets.length === 0 ? (
            <p className="empty-projects-msg">No active projects available in registry sandbox mode currently.</p>
          ) : (
            <div className="offsets-list">
              {offsets.map((proj) => (
                <div key={proj.id} className="offset-card glow-card">
                  <div className="offset-meta-row">
                    <span className="registry-tag">{proj.registry}</span>
                    <span className="cert-tag">{proj.certification}</span>
                  </div>
                  <h4>{proj.name}</h4>
                  <div className="offset-price-row">
                    <span className="price">${Number(proj.price_per_tonne).toFixed(2)} <span className="unit">/ tonne</span></span>
                    <a
                      href={proj.project_url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="btn-secondary flex-center-gap select-offset-btn"
                    >
                      View Registry <ShoppingCart size={14} />
                    </a>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
