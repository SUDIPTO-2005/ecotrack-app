import React, { useState } from 'react';
import { useAppStore } from '../../store/useAppStore';
import { apiClient } from '../../api/apiClient';
import { Leaf, Car, Lightbulb, Plane, ShieldAlert, Sparkles, Trash2, ShoppingBag } from 'lucide-react';

export default function Calculator() {
  const { fetchUser, showToast } = useAppStore();
  const [mode, setMode] = useState<'quick' | 'detailed'>('quick');
  const [step, setStep] = useState(1);
  const [isSubmitting, setIsSubmitting] = useState(false);

  // Quick form state
  const [quickForm, setQuickForm] = useState({
    car_km_per_week: 100,
    car_fuel_type: 'petrol',
    electricity_kwh_per_month: 250,
    diet_type: 'meat_medium',
    flights_short_haul_per_year: 2,
    flights_long_haul_per_year: 1,
  });

  // Detailed form state
  const [detailedForm, setDetailedForm] = useState({
    car_km_per_week: 100,
    car_fuel_type: 'petrol',
    bus_km_per_week: 20,
    rail_km_per_week: 10,
    motorbike_km_per_week: 0,
    flights_short_haul_per_year: 2,
    flights_long_haul_per_year: 1,
    electricity_kwh_per_month: 250,
    natural_gas_kwh_per_month: 50,
    heating_oil_litres_per_year: 0,
    diet_type: 'meat_medium',
    new_clothing_items_per_year: 12,
    new_electronics_laptops_per_year: 1,
    new_electronics_smartphones_per_year: 1,
    waste_kg_per_week: 10,
    recycling_fraction: 0.3,
    food_waste_kg_per_week: 4,
  });

  const handleQuickSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsSubmitting(true);
    try {
      await apiClient.request('/calculator/estimate/', {
        method: 'POST',
        body: JSON.stringify(quickForm),
      });
      showToast('Carbon footprint estimated successfully!', 'success');
      await fetchUser(); // Updates onboarding_complete status
    } catch (err: any) {
      console.error(err);
      showToast(err?.error?.message || 'Calculation failed. Please verify inputs.', 'error');
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleDetailedSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsSubmitting(true);
    try {
      await apiClient.request('/calculator/detailed/', {
        method: 'POST',
        body: JSON.stringify(detailedForm),
      });
      showToast('Detailed carbon footprint calculated successfully!', 'success');
      await fetchUser(); // Updates onboarding_complete status
    } catch (err: any) {
      console.error(err);
      showToast(err?.error?.message || 'Detailed calculation failed. Please check inputs.', 'error');
    } finally {
      setIsSubmitting(false);
    }
  };

  const renderQuickWizard = () => {
    const totalSteps = 4;
    return (
      <form onSubmit={handleQuickSubmit} className="calculator-form">
        <div className="progress-bar-container">
          <div className="progress-bar" style={{ width: `${(step / totalSteps) * 100}%` }}></div>
        </div>
        <p className="step-label">Question {step} of {totalSteps}</p>

        {step === 1 && (
          <div className="wizard-step">
            <h3 className="wizard-step-title"><Car size={20} className="step-icon" /> Daily Transport</h3>
            <label htmlFor="quick_car_travel">Weekly Car Travel ({quickForm.car_km_per_week} km)</label>
            <input
              id="quick_car_travel"
              type="range"
              min="0"
              max="1000"
              step="10"
              value={quickForm.car_km_per_week}
              onChange={(e) => setQuickForm({ ...quickForm, car_km_per_week: Number(e.target.value) })}
            />
            <div className="input-range-labels">
              <span>0 km</span>
              <span>500 km</span>
              <span>1000+ km</span>
            </div>

            <label htmlFor="quick_car_fuel" style={{ marginTop: '20px', display: 'block' }}>Car Fuel Type</label>
            <select
              id="quick_car_fuel"
              value={quickForm.car_fuel_type}
              onChange={(e) => setQuickForm({ ...quickForm, car_fuel_type: e.target.value })}
            >
              <option value="petrol">Petrol</option>
              <option value="diesel">Diesel</option>
              <option value="hybrid">Hybrid</option>
              <option value="electric">Electric (EV)</option>
            </select>
          </div>
        )}

        {step === 2 && (
          <div className="wizard-step">
            <h3 className="wizard-step-title"><Lightbulb size={20} className="step-icon" /> Energy Consumption</h3>
            <label htmlFor="quick_electricity">Monthly Household Electricity Usage ({quickForm.electricity_kwh_per_month} kWh)</label>
            <input
              id="quick_electricity"
              type="range"
              min="0"
              max="2000"
              step="20"
              value={quickForm.electricity_kwh_per_month}
              onChange={(e) => setQuickForm({ ...quickForm, electricity_kwh_per_month: Number(e.target.value) })}
            />
            <div className="input-range-labels">
              <span>0 kWh</span>
              <span>1000 kWh</span>
              <span>2000+ kWh</span>
            </div>
            <p className="field-hint">Tip: Find this on your utility bill, or estimate (an average home is 250-500 kWh).</p>
          </div>
        )}

        {step === 3 && (
          <div className="wizard-step">
            <h3 className="wizard-step-title"><Leaf size={20} className="step-icon" /> Diet & Food Style</h3>
            <label htmlFor="quick_diet">Describe your general eating habits:</label>
            <select
              id="quick_diet"
              value={quickForm.diet_type}
              onChange={(e) => setQuickForm({ ...quickForm, diet_type: e.target.value })}
            >
              <option value="meat_heavy">Meat Heavy (Daily meat, beef, pork)</option>
              <option value="meat_medium">Meat Medium (Average meat consumer)</option>
              <option value="meat_low">Meat Low (Rarely eat red meat, mostly poultry/fish)</option>
              <option value="fish">Pescatarian (Fish & veggies only)</option>
              <option value="vegetarian">Vegetarian (No meat/fish, dairy included)</option>
              <option value="vegan">Vegan (Plant-based only)</option>
            </select>
          </div>
        )}

        {step === 4 && (
          <div className="wizard-step">
            <h3 className="wizard-step-title"><Plane size={20} className="step-icon" /> Air Travel</h3>
            <div className="number-fields-grid">
              <div>
                <label htmlFor="quick_flights_short">Short-haul Flights (per year)</label>
                <input
                  id="quick_flights_short"
                  type="number"
                  min="0"
                  max="100"
                  value={quickForm.flights_short_haul_per_year}
                  onChange={(e) => setQuickForm({ ...quickForm, flights_short_haul_per_year: Number(e.target.value) })}
                />
                <span className="field-hint">Under 3 hours duration</span>
              </div>
              <div>
                <label htmlFor="quick_flights_long">Long-haul Flights (per year)</label>
                <input
                  id="quick_flights_long"
                  type="number"
                  min="0"
                  max="100"
                  value={quickForm.flights_long_haul_per_year}
                  onChange={(e) => setQuickForm({ ...quickForm, flights_long_haul_per_year: Number(e.target.value) })}
                />
                <span className="field-hint">Over 3 hours duration</span>
              </div>
            </div>
          </div>
        )}

        <div className="wizard-buttons">
          {step > 1 && (
            <button type="button" className="btn-secondary" onClick={() => setStep(step - 1)}>
              Back
            </button>
          )}
          {step < totalSteps ? (
            <button type="button" className="btn-primary" onClick={() => setStep(step + 1)}>
              Next Step
            </button>
          ) : (
            <button type="submit" className="btn-primary flex-center-gap" disabled={isSubmitting}>
              {isSubmitting ? 'Calculating...' : 'Calculate Footprint'} <Sparkles size={16} />
            </button>
          )}
        </div>
      </form>
    );
  };

  const renderDetailedWizard = () => {
    const totalSteps = 5;
    return (
      <form onSubmit={handleDetailedSubmit} className="calculator-form">
        <div className="progress-bar-container">
          <div className="progress-bar" style={{ width: `${(step / totalSteps) * 100}%` }}></div>
        </div>
        <p className="step-label">Detailed Question {step} of {totalSteps}</p>

        {step === 1 && (
          <div className="wizard-step">
            <h3 className="wizard-step-title"><Car size={20} className="step-icon" /> Comprehensive Transport</h3>
            <div className="number-fields-grid scrollable-panel">
              <div>
                <label htmlFor="det_car_travel">Car Travel per week (km)</label>
                <input
                  id="det_car_travel"
                  type="number"
                  min="0"
                  value={detailedForm.car_km_per_week}
                  onChange={(e) => setDetailedForm({ ...detailedForm, car_km_per_week: Number(e.target.value) })}
                />
              </div>
              <div>
                <label htmlFor="det_car_fuel">Car Fuel Type</label>
                <select
                  id="det_car_fuel"
                  value={detailedForm.car_fuel_type}
                  onChange={(e) => setDetailedForm({ ...detailedForm, car_fuel_type: e.target.value })}
                >
                  <option value="petrol">Petrol</option>
                  <option value="diesel">Diesel</option>
                  <option value="hybrid">Hybrid</option>
                  <option value="electric">Electric</option>
                </select>
              </div>
              <div>
                <label htmlFor="det_bus_travel">Bus Travel per week (km)</label>
                <input
                  id="det_bus_travel"
                  type="number"
                  min="0"
                  value={detailedForm.bus_km_per_week}
                  onChange={(e) => setDetailedForm({ ...detailedForm, bus_km_per_week: Number(e.target.value) })}
                />
              </div>
              <div>
                <label htmlFor="det_rail_travel">Rail/Train per week (km)</label>
                <input
                  id="det_rail_travel"
                  type="number"
                  min="0"
                  value={detailedForm.rail_km_per_week}
                  onChange={(e) => setDetailedForm({ ...detailedForm, rail_km_per_week: Number(e.target.value) })}
                />
              </div>
              <div>
                <label htmlFor="det_moto_travel">Motorbike/Scooter per week (km)</label>
                <input
                  id="det_moto_travel"
                  type="number"
                  min="0"
                  value={detailedForm.motorbike_km_per_week}
                  onChange={(e) => setDetailedForm({ ...detailedForm, motorbike_km_per_week: Number(e.target.value) })}
                />
              </div>
            </div>
          </div>
        )}

        {step === 2 && (
          <div className="wizard-step">
            <h3 className="wizard-step-title"><Plane size={20} className="step-icon" /> Flying Details</h3>
            <div className="number-fields-grid">
              <div>
                <label htmlFor="det_flights_short">Short-haul Flights (per year)</label>
                <input
                  id="det_flights_short"
                  type="number"
                  min="0"
                  value={detailedForm.flights_short_haul_per_year}
                  onChange={(e) => setDetailedForm({ ...detailedForm, flights_short_haul_per_year: Number(e.target.value) })}
                />
              </div>
              <div>
                <label htmlFor="det_flights_long">Long-haul Flights (per year)</label>
                <input
                  id="det_flights_long"
                  type="number"
                  min="0"
                  value={detailedForm.flights_long_haul_per_year}
                  onChange={(e) => setDetailedForm({ ...detailedForm, flights_long_haul_per_year: Number(e.target.value) })}
                />
              </div>
            </div>
          </div>
        )}

        {step === 3 && (
          <div className="wizard-step">
            <h3 className="wizard-step-title"><Lightbulb size={20} className="step-icon" /> Household Energy</h3>
            <div className="number-fields-grid">
              <div>
                <label htmlFor="det_electricity">Electricity (kWh per month)</label>
                <input
                  id="det_electricity"
                  type="number"
                  min="0"
                  value={detailedForm.electricity_kwh_per_month}
                  onChange={(e) => setDetailedForm({ ...detailedForm, electricity_kwh_per_month: Number(e.target.value) })}
                />
              </div>
              <div>
                <label htmlFor="det_gas">Natural Gas (kWh per month)</label>
                <input
                  id="det_gas"
                  type="number"
                  min="0"
                  value={detailedForm.natural_gas_kwh_per_month}
                  onChange={(e) => setDetailedForm({ ...detailedForm, natural_gas_kwh_per_month: Number(e.target.value) })}
                />
              </div>
              <div>
                <label htmlFor="det_oil">Heating Oil (Litres per year)</label>
                <input
                  id="det_oil"
                  type="number"
                  min="0"
                  value={detailedForm.heating_oil_litres_per_year}
                  onChange={(e) => setDetailedForm({ ...detailedForm, heating_oil_litres_per_year: Number(e.target.value) })}
                />
              </div>
            </div>
          </div>
        )}

        {step === 4 && (
          <div className="wizard-step">
            <h3 className="wizard-step-title"><ShoppingBag size={20} className="step-icon" /> Diet & Goods</h3>
            <div className="number-fields-grid scrollable-panel">
              <div style={{ gridColumn: 'span 2' }}>
                <label htmlFor="det_diet">Diet Type</label>
                <select
                  id="det_diet"
                  value={detailedForm.diet_type}
                  onChange={(e) => setDetailedForm({ ...detailedForm, diet_type: e.target.value })}
                >
                  <option value="meat_heavy">Meat Heavy</option>
                  <option value="meat_medium">Meat Medium</option>
                  <option value="meat_low">Meat Low</option>
                  <option value="fish">Pescatarian</option>
                  <option value="vegetarian">Vegetarian</option>
                  <option value="vegan">Vegan</option>
                </select>
              </div>
              <div>
                <label htmlFor="det_clothes">New Clothing Items / year</label>
                <input
                  id="det_clothes"
                  type="number"
                  min="0"
                  value={detailedForm.new_clothing_items_per_year}
                  onChange={(e) => setDetailedForm({ ...detailedForm, new_clothing_items_per_year: Number(e.target.value) })}
                />
              </div>
              <div>
                <label htmlFor="det_laptops">Laptops purchased / year</label>
                <input
                  id="det_laptops"
                  type="number"
                  min="0"
                  value={detailedForm.new_electronics_laptops_per_year}
                  onChange={(e) => setDetailedForm({ ...detailedForm, new_electronics_laptops_per_year: Number(e.target.value) })}
                />
              </div>
              <div>
                <label htmlFor="det_smartphones">Smartphones purchased / year</label>
                <input
                  id="det_smartphones"
                  type="number"
                  min="0"
                  value={detailedForm.new_electronics_smartphones_per_year}
                  onChange={(e) => setDetailedForm({ ...detailedForm, new_electronics_smartphones_per_year: Number(e.target.value) })}
                />
              </div>
            </div>
          </div>
        )}

        {step === 5 && (
          <div className="wizard-step">
            <h3 className="wizard-step-title"><Trash2 size={20} className="step-icon" /> Waste & Recycling</h3>
            <div className="number-fields-grid">
              <div>
                <label htmlFor="det_waste">Total General Waste per week (kg)</label>
                <input
                  id="det_waste"
                  type="number"
                  min="0"
                  value={detailedForm.waste_kg_per_week}
                  onChange={(e) => setDetailedForm({ ...detailedForm, waste_kg_per_week: Number(e.target.value) })}
                />
              </div>
              <div>
                <label htmlFor="det_recycling">Recycling Ratio (0 to 1)</label>
                <input
                  id="det_recycling"
                  type="number"
                  min="0"
                  max="1"
                  step="0.05"
                  value={detailedForm.recycling_fraction}
                  onChange={(e) => setDetailedForm({ ...detailedForm, recycling_fraction: Number(e.target.value) })}
                />
              </div>
              <div>
                <label htmlFor="det_food_waste">Food Waste per week (kg)</label>
                <input
                  id="det_food_waste"
                  type="number"
                  min="0"
                  value={detailedForm.food_waste_kg_per_week}
                  onChange={(e) => setDetailedForm({ ...detailedForm, food_waste_kg_per_week: Number(e.target.value) })}
                />
              </div>
            </div>
          </div>
        )}

        <div className="wizard-buttons">
          {step > 1 && (
            <button type="button" className="btn-secondary" onClick={() => setStep(step - 1)}>
              Back
            </button>
          )}
          {step < totalSteps ? (
            <button type="button" className="btn-primary" onClick={() => setStep(step + 1)}>
              Next Step
            </button>
          ) : (
            <button type="submit" className="btn-primary flex-center-gap" disabled={isSubmitting}>
              {isSubmitting ? 'Calculating...' : 'Detailed Calculation'} <Sparkles size={16} />
            </button>
          )}
        </div>
      </form>
    );
  };

  return (
    <div className="calculator-view">
      <div className="calculator-header">
        <h2 className="title-gradient"><Leaf className="pulse" style={{ color: 'var(--color-green)' }} /> Calculate Your Carbon Footprint</h2>
        <p className="subtitle">Let's estimate your impact to design a custom reduction plan.</p>
      </div>

      <div className="calculator-mode-selectors">
        <button
          className={mode === 'quick' ? 'mode-tab active' : 'mode-tab'}
          onClick={() => { setMode('quick'); setStep(1); }}
        >
          Quick Mode (5 Key Qs)
        </button>
        <button
          className={mode === 'detailed' ? 'mode-tab active' : 'mode-tab'}
          onClick={() => { setMode('detailed'); setStep(1); }}
        >
          Detailed Mode (20+ Qs)
        </button>
      </div>

      <div className="glow-card calculator-wizard">
        {mode === 'quick' ? renderQuickWizard() : renderDetailedWizard()}
      </div>

      <div className="disclaimer-info-card">
        <ShieldAlert size={20} className="disclaimer-icon" />
        <div>
          <h4>Methodology & Auditability Disclaimer</h4>
          <p>
            EcoTrack calculations are based on versioned conversion factors derived directly from DEFRA 2023 greenhouse gas reporting methodologies and IPCC AR6 global benchmarks. Every calculation is fully auditable.
          </p>
        </div>
      </div>
    </div>
  );
}
