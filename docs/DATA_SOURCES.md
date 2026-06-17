# EcoTrack — Emission Factor Data Sources

> **Document version:** 1.0.0  
> **Last reviewed:** 2026-06-17  
> **Maintained by:** EcoTrack Data Team  
> **Review cadence:** Annually (or upon major IPCC / DEFRA release)

---

## Table of Contents

1. [Overview](#overview)
2. [Emission Factors](#emission-factors)
   - [DEFRA / BEIS 2023](#1-defra--beis-2023)
   - [Scarborough et al. 2023 (Nature Food)](#2-scarborough-et-al-2023-nature-food)
   - [CEA India Electricity Grid](#3-cea-india-electricity-grid)
   - [IEA World Energy Outlook](#4-iea-world-energy-outlook)
   - [WRAP Food Waste Methodology](#5-wrap-food-waste-methodology)
   - [Apple Environmental Product Declarations](#6-apple-environmental-product-declarations)
3. [Government & National Average Data](#government--national-average-data)
   - [Our World in Data](#7-our-world-in-data)
   - [World Bank Development Indicators](#8-world-bank-development-indicators)
   - [CEEW India Consumption Studies](#9-ceew-india-consumption-studies)
4. [Scientific References](#scientific-references)
   - [IPCC Sixth Assessment Report (AR6)](#10-ipcc-sixth-assessment-report-ar6)
   - [Paris Agreement Carbon Budgets](#11-paris-agreement-carbon-budgets)
5. [Update Policy](#update-policy)
   - [Change Trigger Criteria](#change-trigger-criteria)
   - [Review & Approval Process](#review--approval-process)
   - [Changelog](#changelog)
6. [License Compatibility Matrix](#license-compatibility-matrix)

---

## Overview

EcoTrack calculates individual and household carbon footprints across seven life-cycle domains:

| Domain | Primary Source |
|--------|---------------|
| Electricity consumption | CEA / IEA / DEFRA |
| Dietary choices | Scarborough et al. 2023 |
| Road transport | DEFRA BEIS 2023 |
| Air travel | DEFRA BEIS 2023 |
| Home energy (gas, oil, LPG) | DEFRA BEIS 2023 |
| Consumer goods & devices | Apple EPDs / WRAP |
| Waste & recycling | WRAP / DEFRA |

All emission factors are expressed in **kg CO₂-equivalent (CO₂e) per functional unit** unless otherwise noted. EcoTrack uses the GWP-100 characterisation factors from IPCC AR6 WG1 (2021), Table 7.SM.7.

> **Disclaimer:** Emission factors are periodically revised as scientific understanding and energy mixes evolve. The version of each factor used for any historical footprint record is persisted in the database (`EmissionFactor.version` field) so that results remain reproducible even after factors are updated.

---

## Emission Factors

### 1. DEFRA / BEIS 2023

| Attribute | Value |
|-----------|-------|
| **Full title** | UK Government GHG Conversion Factors for Company Reporting |
| **Publisher** | UK Department for Environment, Food & Rural Affairs (DEFRA) & Department for Energy Security and Net Zero (BEIS/DESNZ) |
| **Version / Year** | 2023 (dataset version 1.0, published August 2023) |
| **URL** | <https://www.gov.uk/government/publications/greenhouse-gas-reporting-conversion-factors-2023> |
| **Date accessed** | 2024-01-15 |
| **File format** | Microsoft Excel (.xlsx) |
| **License** | Open Government Licence v3.0 — free to use with attribution |
| **Coverage** | UK-specific factors; used as global proxy for transport & hotel stay where country-specific data unavailable |

**Factors used from this source:**

| Category | Factor name | Value | Unit |
|----------|-------------|-------|------|
| Transport | Car — average petrol | 0.1732 | kg CO₂e / km |
| Transport | Car — average diesel | 0.1688 | kg CO₂e / km |
| Transport | Car — battery EV (UK grid) | 0.0535 | kg CO₂e / km |
| Transport | Motorcycle (average) | 0.1140 | kg CO₂e / km |
| Transport | Bus (local) | 0.1027 | kg CO₂e / km |
| Transport | National rail | 0.0354 | kg CO₂e / km |
| Air travel | Short-haul economy (<3700 km) | 0.2551 | kg CO₂e / pkm |
| Air travel | Long-haul economy (≥3700 km) | 0.1951 | kg CO₂e / pkm |
| Air travel | Long-haul business class | 0.4286 | kg CO₂e / pkm |
| Home energy | Natural gas | 2.0441 | kg CO₂e / kWh (gross) |
| Home energy | LPG | 1.5550 | kg CO₂e / litre |
| Home energy | Heating oil | 2.5202 | kg CO₂e / litre |
| Electricity | UK grid average | 0.2120 | kg CO₂e / kWh |

> **Note on air travel radiative forcing:** EcoTrack applies a Radiative Forcing Index (RFI) multiplier of **2.0** to all aviation emissions in line with DEFRA guidance (Annex 6, 2023 dataset) to account for high-altitude non-CO₂ warming effects (contrails, cirrus cloud formation). Users are informed of this multiplier in the UI tooltip.

---

### 2. Scarborough et al. 2023 (Nature Food)

| Attribute | Value |
|-----------|-------|
| **Full citation** | Scarborough, P., Clark, M., Cobiac, L., Papier, K., Knuppel, A., Lynch, J., Harrington, R., Key, T., & Springmann, M. (2023). Vegans, vegetarians, fish-eaters and meat-eaters in the UK show discrepant environmental impacts. *Nature Food*, 4, 565–574. |
| **DOI** | <https://doi.org/10.1038/s43016-023-00795-w> |
| **Publisher** | Springer Nature |
| **Date accessed** | 2024-02-01 |
| **License** | Creative Commons Attribution 4.0 (CC BY 4.0) — open access |
| **Sample size** | 55,504 UK Biobank participants |
| **Methodology** | Life-cycle assessment (LCA) of 570+ food items; supply-chain upstream emissions |

**Dietary tier emission factors (kg CO₂e / day):**

| Dietary pattern | Mean | 95% CI |
|-----------------|------|--------|
| High meat (>100 g/day) | 7.19 | 6.63 – 7.75 |
| Medium meat (50–99 g/day) | 5.63 | 5.22 – 6.04 |
| Low meat (<50 g/day) | 4.67 | 4.30 – 5.04 |
| Fish-eater (no meat) | 3.91 | 3.53 – 4.29 |
| Vegetarian | 3.81 | 3.45 – 4.17 |
| Vegan | 2.89 | 2.58 – 3.20 |

**Implementation note:** EcoTrack maps user-selected dietary archetype to the mean value from Table 2 of the paper. The CI bounds are surfaced in the "uncertainty range" indicator in the footprint breakdown UI. Annual dietary footprint = daily factor × 365.

---

### 3. CEA India Electricity Grid

| Attribute | Value |
|-----------|-------|
| **Full title** | CO₂ Baseline Database for the Indian Power Sector, Version 18 |
| **Publisher** | Central Electricity Authority (CEA), Ministry of Power, Government of India |
| **Version** | 18.0 (March 2023) |
| **URL** | <https://cea.nic.in/wp-content/uploads/baseline/2023/CO2_Baseline_Database_Version_18.pdf> |
| **Date accessed** | 2024-01-20 |
| **License** | Government of India Open Data Licence — free to use with attribution |

**Grid emission factors (kg CO₂ / kWh):**

| Region | Combined Margin (CM) factor |
|--------|---------------------------|
| Northern | 0.8218 |
| Western | 0.9087 |
| Southern | 0.8498 |
| Eastern | 1.0024 |
| North-Eastern | 0.5963 |
| **National average** | **0.8160** |

EcoTrack uses the national average for user onboarding when state is unknown, and switches to regional factors once the user's state is confirmed.

---

### 4. IEA World Energy Outlook

| Attribute | Value |
|-----------|-------|
| **Full title** | Electricity Generation by Source — CO₂ Intensity of Electricity Generation |
| **Publisher** | International Energy Agency (IEA) |
| **Edition** | World Energy Outlook 2023 (WEO 2023) |
| **URL** | <https://www.iea.org/data-and-statistics/data-product/world-energy-statistics-and-balances> |
| **Date accessed** | 2024-01-25 |
| **License** | IEA Terms and Conditions — data may be cited with attribution; redistribution of raw datasets requires permission |

**Selected national grid intensity factors (g CO₂ / kWh):**

| Country / Region | 2022 value |
|-----------------|-----------|
| World average | 436 |
| EU27 | 251 |
| USA | 386 |
| China | 581 |
| India (IEA) | 708 |
| Germany | 385 |
| France | 85 |
| Australia | 584 |
| Canada | 149 |
| Brazil | 87 |

> **Precedence rule:** For India, CEA Version 18 (regional breakdown) takes precedence over IEA where regional data is available. IEA is used as the fallback for all countries not covered by CEA.

---

### 5. WRAP Food Waste Methodology

| Attribute | Value |
|-----------|-------|
| **Full title** | The Food We Waste — Quantification and Carbon Metrics |
| **Publisher** | Waste & Resources Action Programme (WRAP) |
| **Version** | 2022 revision |
| **URL** | <https://wrap.org.uk/resources/report/food-surplus-and-waste-uk-key-facts> |
| **Date accessed** | 2024-01-18 |
| **License** | © WRAP 2022 — available for non-commercial use with attribution |

**Factors used:**

| Item | Emission factor | Unit |
|------|----------------|------|
| Food waste to landfill | 3.8 | kg CO₂e / kg food wasted |
| Food waste composted | 0.5 | kg CO₂e / kg food wasted |
| Food waste to anaerobic digestion | 0.1 | kg CO₂e / kg food wasted |
| Plastic to landfill | 0.01 | kg CO₂e / kg |
| Plastic recycled | −0.5 | kg CO₂e / kg (avoided emissions) |
| Paper/cardboard recycled | −1.1 | kg CO₂e / kg |

> **Avoided emissions:** Recycling factors are negative, representing emissions avoided compared to landfilling. EcoTrack presents these as "savings" in the waste category breakdown rather than subtracting from gross footprint to prevent confusion.

---

### 6. Apple Environmental Product Declarations

| Attribute | Value |
|-----------|-------|
| **Full title** | Apple Product Environmental Reports (EPDs) |
| **Publisher** | Apple Inc. |
| **URL** | <https://www.apple.com/environment/resources/> |
| **Scope** | Cradle-to-grave LCA per device model (manufacturing + transport + use + end-of-life) |
| **Date accessed** | 2024-02-10 |
| **License** | © Apple Inc. — publicly disclosed data; cited with attribution per fair use |

**Devices modelled in EcoTrack (manufacturing + use phase, kg CO₂e):**

| Device | Manufacturing | Expected lifespan | Per-year amortised |
|--------|--------------|-------------------|-------------------|
| iPhone 15 | 61 | 4 years | 15.25 |
| iPhone 15 Pro | 70 | 4 years | 17.50 |
| MacBook Pro 14" (M3) | 185 | 5 years | 37.00 |
| MacBook Air 13" (M2) | 147 | 5 years | 29.40 |
| iPad Pro 12.9" | 97 | 5 years | 19.40 |
| AirPods Pro (2nd gen) | 28 | 3 years | 9.33 |

> **Methodology note:** EcoTrack uses the amortised manufacturing carbon (device total ÷ expected lifespan) per year of ownership. Use-phase electricity is calculated separately from the user's electricity factor. End-of-life is excluded in Phase 1 (roadmap item).

---

## Government & National Average Data

### 7. Our World in Data

| Attribute | Value |
|-----------|-------|
| **Full title** | Per Capita CO₂ and GHG Emissions — Our World in Data |
| **Publisher** | Our World in Data (University of Oxford / Global Change Data Lab) |
| **URL** | <https://ourworldindata.org/co2-and-greenhouse-gas-emissions> |
| **Dataset** | Based on Global Carbon Budget 2023 (GCP) |
| **Date accessed** | 2024-01-30 |
| **License** | Creative Commons BY 4.0 |

Used for: national per-capita benchmarks displayed in the "how do you compare?" dashboard widget. Updated annually.

---

### 8. World Bank Development Indicators

| Attribute | Value |
|-----------|-------|
| **Full title** | World Development Indicators — CO₂ emissions (metric tons per capita) |
| **Publisher** | The World Bank Group |
| **Indicator code** | EN.ATM.CO2E.PC |
| **URL** | <https://data.worldbank.org/indicator/EN.ATM.CO2E.PC> |
| **Date accessed** | 2024-01-30 |
| **License** | Creative Commons Attribution 4.0 (CC BY 4.0) |

Used for: fallback national benchmark where Our World in Data does not have granular sub-national breakdowns.

---

### 9. CEEW India Consumption Studies

| Attribute | Value |
|-----------|-------|
| **Full title** | India's Household Carbon Footprints — CEEW Working Paper |
| **Publisher** | Council on Energy, Environment and Water (CEEW) |
| **Authors** | Ramakrishna, G., & Kaur, M. (2023) |
| **URL** | <https://www.ceew.in/publications/indias-net-zero-target> |
| **Date accessed** | 2024-02-05 |
| **License** | © CEEW — available for research use with attribution |

Used for: India-specific dietary and household energy consumption distributions used to calibrate the "lifestyle tier" defaults on user onboarding.

---

## Scientific References

### 10. IPCC Sixth Assessment Report (AR6)

| Attribute | Value |
|-----------|-------|
| **Full citation** | IPCC (2021). Climate Change 2021: The Physical Science Basis. Contribution of Working Group I to the Sixth Assessment Report. Masson-Delmotte, V. et al. (Eds.). Cambridge University Press. |
| **DOI** | <https://doi.org/10.1017/9781009157896> |
| **Relevant chapters** | Chapter 7 (The Earth's Energy Budget, Climate Feedbacks and Climate Sensitivity); Table 7.SM.7 (GWP-100 values) |
| **License** | © IPCC 2021 — freely available for educational and research use |

**GWP-100 values used in EcoTrack (AR6 WG1, Table 7.SM.7):**

| Gas | GWP-100 (AR6) |
|-----|---------------|
| CO₂ | 1 |
| CH₄ (fossil) | 29.8 |
| CH₄ (biogenic) | 27.9 |
| N₂O | 273 |
| HFC-134a | 1526 |
| SF₆ | 25,200 |

> **Upgrade note:** EcoTrack migrated from AR5 GWP-100 values to AR6 values in data migration `0012`. If you are integrating third-party datasets that still use AR5, apply the conversion factor documented in `ecotrack/emissions/ar5_to_ar6_conversion.py`.

---

### 11. Paris Agreement Carbon Budgets

| Attribute | Value |
|-----------|-------|
| **Full citation** | Rogelj, J. et al. (2018). Scenarios towards limiting global mean temperature increase below 1.5°C. *Nature Climate Change*, 8, 325–332. |
| **DOI** | <https://doi.org/10.1038/s41558-018-0091-3> |
| **Updated in** | IPCC SR1.5 (2018), Table 2.2; IPCC AR6 WG3 (2022), Chapter 3 |
| **License** | © Springer Nature 2018 — open access, CC BY 4.0 |

Used for: the "personal carbon budget" indicator showing how a user's annual footprint compares with the per-capita allocation consistent with 1.5°C warming (approximately **2.1 t CO₂e/year/person** by 2030, based on equity-weighted global budget allocation).

---

## Update Policy

### Change Trigger Criteria

Emission factors are reviewed and potentially updated when **any** of the following occur:

1. **DEFRA publishes a new annual conversion factor dataset** (typically August each year).
2. **CEA publishes a new version** of the CO₂ Baseline Database (typically Q1 each year).
3. **IEA publishes the annual World Energy Outlook** (typically November each year).
4. **IPCC publishes a new Assessment Report or Special Report.**
5. A factor is found to differ from the most recent source by **>5%** at the category level.
6. A **regulatory or legal change** in a target country requires factor revision.

Minor corrections (typos, unit conversions) may be applied without a full review cycle but must still be logged in the changelog below.

---

### Review & Approval Process

```
Data Engineer proposes update
         │
         ▼
Opens a GitHub PR with:
  - Updated factor in emissions/constants.py
  - Updated version field in migration
  - Updated this DATA_SOURCES.md
         │
         ▼
Technical Lead reviews for:
  - Source credibility
  - Unit consistency (kg CO₂e, GWP basis)
  - Impact on existing user footprints
         │
         ▼
Product Owner reviews for:
  - User-facing communication (if change >10%)
  - Changelog entry language
         │
         ▼
Merge → triggers data migration
  - Old records retain historical factor version
  - New calculations use updated factor
  - Admin dashboard shows version diff
```

**Communication rule:** If any single factor changes by more than **10%**, a notification is sent to affected users explaining the recalculation. Their historical records are **not** retroactively changed; only future calculations use the new factor.

---

### Changelog

| Date | Version | Changed factor | Old value | New value | Source | Author |
|------|---------|---------------|-----------|-----------|--------|--------|
| 2024-01-15 | 1.0.0 | Initial dataset — all factors | — | See above | Multiple | EcoTrack Data Team |
| *(future entries added here)* | | | | | | |

---

## License Compatibility Matrix

| Source | License | Can redistribute? | Attribution required? | Commercial use? |
|--------|---------|------------------|-----------------------|-----------------|
| DEFRA/BEIS 2023 | OGL v3.0 | ✅ Yes | ✅ Yes | ✅ Yes |
| Scarborough et al. 2023 | CC BY 4.0 | ✅ Yes | ✅ Yes | ✅ Yes |
| CEA India | Govt. of India Open Data | ✅ Yes | ✅ Yes | ✅ Yes |
| IEA WEO 2023 | IEA Terms | ⚠️ Cite only | ✅ Yes | ⚠️ Check IEA ToC |
| WRAP 2022 | © WRAP (non-commercial) | ❌ No | ✅ Yes | ❌ No |
| Apple EPDs | © Apple (public disclosure) | ❌ No | ✅ Yes | ⚠️ Fair use only |
| Our World in Data | CC BY 4.0 | ✅ Yes | ✅ Yes | ✅ Yes |
| World Bank | CC BY 4.0 | ✅ Yes | ✅ Yes | ✅ Yes |
| CEEW | © CEEW (research use) | ❌ No | ✅ Yes | ❌ No |
| IPCC AR6 | © IPCC (educational) | ⚠️ Cite only | ✅ Yes | ⚠️ Check IPCC ToU |

> **Legal note:** WRAP and Apple data are used solely for emission factor derivation within EcoTrack's calculation engine. No raw WRAP or Apple datasets are redistributed to users or third parties. Consult legal counsel before any commercial sublicensing.

---

*End of DATA_SOURCES.md — EcoTrack v1.0.0*
