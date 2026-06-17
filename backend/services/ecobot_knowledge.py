"""
Enhanced rule-based chatbot knowledge base for EcoBot.

Covers 30+ topic areas with rich, specific, evidence-based responses.
Used as the primary response engine when no Anthropic API key is set.
"""
from __future__ import annotations
import re


# ──────────────────────────────────────────────────────────────────────────────
# KNOWLEDGE BASE — topic patterns mapped to rich responses
# ──────────────────────────────────────────────────────────────────────────────

KNOWLEDGE_BASE = [
    # ── TRANSPORT ──────────────────────────────────────────────────────────────
    {
        "patterns": ["fly", "flight", "airplane", "plane", "aviation", "air travel"],
        "response": (
            "✈️ **Aviation & Carbon:**\n\n"
            "Flying is one of the most carbon-intensive activities per hour. Here's the breakdown:\n"
            "• **Short-haul flight** (e.g. Delhi→Mumbai, ~1h): ~90 kg CO₂e per passenger\n"
            "• **Long-haul flight** (e.g. Delhi→London, ~9h): ~850–1,100 kg CO₂e per passenger\n"
            "• Economy class has a **smaller footprint than business class** by ~3× (space per seat)\n\n"
            "**To reduce flight emissions:**\n"
            "1. Take trains instead of short-haul flights — 6–10× less CO₂\n"
            "2. Choose non-stop flights (take-off/landing are the most fuel-intensive phases)\n"
            "3. Fly economy, not business\n"
            "4. Use voluntary carbon offset programs like Gold Standard certified projects\n\n"
            "🌍 Aviation accounts for ~2.5% of global CO₂ but ~3.5% of effective warming when contrails are counted."
        ),
    },
    {
        "patterns": ["car", "drive", "driving", "vehicle", "petrol", "diesel", "fuel"],
        "response": (
            "🚗 **Car & Driving Emissions:**\n\n"
            "An average petrol car emits **~0.17 kg CO₂ per km** (DEFRA 2023).\n\n"
            "**Ranked by CO₂ per passenger-km (best to worst):**\n"
            "1. 🚲 Bicycle / Walking — 0 g\n"
            "2. 🚆 Electric train — ~14 g\n"
            "3. 🚌 Bus — ~89 g\n"
            "4. 🚗 Petrol car (1 person) — ~170 g\n"
            "5. ✈️ Domestic flight — ~255 g\n\n"
            "**Quick wins:**\n"
            "• Carpool with just 1 person → cut your car emissions by 50%\n"
            "• Drive at 80–90 km/h on highways → ~15% better fuel efficiency vs 120 km/h\n"
            "• Correct tyre pressure → saves up to 3% fuel\n"
            "• Turn off engine if stopped >60 seconds (idling burns ~0.3L/hour)"
        ),
    },
    {
        "patterns": ["electric car", "ev", "electric vehicle", "tesla", "electric bike"],
        "response": (
            "⚡ **Electric Vehicles (EVs):**\n\n"
            "EVs produce **zero tailpipe emissions**, but their total footprint depends on your grid.\n\n"
            "**Lifecycle CO₂ comparison (per 100,000 km driven):**\n"
            "• Petrol car: ~24 tonnes CO₂e\n"
            "• EV on India's grid: ~15 tonnes CO₂e\n"
            "• EV on renewable grid: ~4–6 tonnes CO₂e\n\n"
            "**Tips for EV owners:**\n"
            "• Charge at night when grid demand is low\n"
            "• Install home solar panels → effectively zero-emission driving\n"
            "• EVs are already cheaper to run: ~₹1.5/km vs ~₹6/km for petrol\n\n"
            "🔋 Even on India's coal-heavy grid, an EV emits **~35% less** than a petrol car over its lifetime."
        ),
    },
    {
        "patterns": ["train", "rail", "metro", "subway", "public transport", "bus"],
        "response": (
            "🚆 **Public Transport is the Climate Champion!**\n\n"
            "Switching from a personal car to public transport is one of the **biggest individual actions** you can take:\n\n"
            "| Mode | CO₂ per passenger-km |\n"
            "|------|----------------------|\n"
            "| Electric train | ~14 g |\n"
            "| Diesel train | ~41 g |\n"
            "| Bus | ~89 g |\n"
            "| Petrol car (solo) | ~170 g |\n\n"
            "**Impact:** Replacing a 30 km daily car commute with a train saves **~1.1 tonnes CO₂/year** — that's 10% of an average person's footprint!\n\n"
            "💡 Even a bus with only 10 passengers beats a solo car journey."
        ),
    },

    # ── DIET ───────────────────────────────────────────────────────────────────
    {
        "patterns": ["meat", "beef", "lamb", "pork", "chicken", "vegan", "vegetarian", "plant", "diet", "food"],
        "response": (
            "🥗 **Food & Diet Emissions:**\n\n"
            "Food accounts for ~25–30% of global greenhouse gas emissions. What you eat matters enormously.\n\n"
            "**CO₂e per kg of food (farm to fork):**\n"
            "| Food | kg CO₂e/kg |\n"
            "|------|------------|\n"
            "| Beef | 60 kg |\n"
            "| Lamb | 24 kg |\n"
            "| Cheese | 21 kg |\n"
            "| Pork | 7 kg |\n"
            "| Chicken | 6 kg |\n"
            "| Eggs | 4.5 kg |\n"
            "| Rice | 2.7 kg |\n"
            "| Tofu | 2 kg |\n"
            "| Lentils | 0.9 kg |\n"
            "| Vegetables | ~0.4 kg |\n\n"
            "**What to do:**\n"
            "1. **Meatless Monday** → saves ~300 kg CO₂/year\n"
            "2. Replace beef with chicken → cuts meal emissions by ~70%\n"
            "3. Go full plant-based → saves ~1.5 tonnes CO₂/year\n"
            "4. Buy local & seasonal produce → cuts food transport emissions"
        ),
    },
    {
        "patterns": ["food waste", "waste food", "compost", "composting", "throw food"],
        "response": (
            "♻️ **Food Waste & Composting:**\n\n"
            "**~1/3 of all food produced globally is wasted** — that's 8% of all greenhouse gas emissions!\n\n"
            "When food rots in landfill, it produces **methane** — 80× more potent than CO₂ over 20 years.\n\n"
            "**How to reduce food waste:**\n"
            "1. Plan meals before grocery shopping\n"
            "2. Use FIFO (First In, First Out) in your fridge\n"
            "3. Freeze bread, fruits, and leftovers before they go bad\n"
            "4. Compost unavoidable waste → turns waste into soil instead of methane\n\n"
            "🌱 **Impact:** The average household wastes ~70 kg of food/year. Cutting this in half saves ~120 kg CO₂e/year."
        ),
    },

    # ── ENERGY ─────────────────────────────────────────────────────────────────
    {
        "patterns": ["electricity", "energy", "power", "kwh", "grid", "coal", "solar panel"],
        "response": (
            "⚡ **Home Electricity & Energy:**\n\n"
            "India's electricity grid emits **~0.71 kg CO₂ per kWh** (CEA 2023) — one of the higher rates globally.\n\n"
            "**Average Indian household uses ~90 kWh/month** → ~64 kg CO₂/month from electricity alone.\n\n"
            "**Biggest energy consumers in your home:**\n"
            "1. Air conditioner (1.5 ton) → ~1.5 kWh/hour\n"
            "2. Water heater/geyser → ~2 kWh per use\n"
            "3. Refrigerator → ~1.2 kWh/day\n"
            "4. Washing machine → ~0.5 kWh/cycle\n\n"
            "**Top energy saving tips:**\n"
            "• Set AC to 24°C instead of 18°C → saves ~24% energy\n"
            "• Use 5-star rated appliances → 15–40% less electricity\n"
            "• Switch to LED bulbs → 80% less power than incandescent\n"
            "• Install solar rooftop → payback in 4–6 years in India, then free for 20+ years\n"
            "• Use a smart power strip to eliminate vampire/standby loads"
        ),
    },
    {
        "patterns": ["solar", "renewable", "wind", "green energy", "clean energy"],
        "response": (
            "☀️ **Renewable Energy:**\n\n"
            "Switching to renewable energy is one of the **highest-impact** actions a household can take.\n\n"
            "**Solar rooftop in India (facts):**\n"
            "• A 3 kW system costs ~₹1.8–2.5 lakh installed\n"
            "• Generates ~360 kWh/month in most Indian cities\n"
            "• Saves ~255 kg CO₂/month\n"
            "• Payback period: **4–6 years**, then free electricity for 20+ years\n"
            "• PM Surya Ghar Muft Bijli Yojana offers subsidies: up to ₹78,000 for 3 kW\n\n"
            "**Other options:**\n"
            "• Buy **Renewable Energy Certificates (RECs)** to offset your grid usage\n"
            "• Switch to a green power plan if your state offers it\n"
            "• Community solar projects for apartments\n\n"
            "🌿 If all of India's rooftops went solar, we could generate **640 GW** — more than our current total capacity!"
        ),
    },
    {
        "patterns": ["ac", "air conditioning", "air conditioner", "cooling", "heating"],
        "response": (
            "❄️ **Air Conditioning & Heating:**\n\n"
            "AC is the **fastest-growing** source of energy demand globally. Here's how to use it smarter:\n\n"
            "**Temperature settings matter a lot:**\n"
            "• Every 1°C lower than 24°C → ~6% more electricity\n"
            "• 24°C is WHO-recommended for comfort AND efficiency\n"
            "• 26°C → saves ~18% vs 18°C setting\n\n"
            "**Other AC tips:**\n"
            "1. Clean filters monthly → improves efficiency by 5–15%\n"
            "2. Use ceiling fans with AC → lets you raise temp by 2–3°C\n"
            "3. Seal window gaps → prevent cool air from escaping\n"
            "4. Use inverter AC → 30–50% less power than fixed-speed\n"
            "5. Service AC annually → dirty coils reduce efficiency by 30%\n\n"
            "💡 A 5-star inverter AC at 24°C uses ~40% less power than a 3-star fixed-speed at 18°C."
        ),
    },

    # ── WASTE ──────────────────────────────────────────────────────────────────
    {
        "patterns": ["recycle", "recycling", "plastic", "waste", "trash", "garbage", "landfill"],
        "response": (
            "♻️ **Waste & Recycling:**\n\n"
            "Waste management contributes ~5% of global greenhouse gas emissions, mainly from landfill methane.\n\n"
            "**Recycling impact per item:**\n"
            "| Material | CO₂ saved per tonne recycled |\n"
            "|----------|------------------------------|\n"
            "| Aluminium | 9,000 kg |\n"
            "| Steel | 1,500 kg |\n"
            "| Paper | 900 kg |\n"
            "| Plastic | 600 kg |\n"
            "| Glass | 300 kg |\n\n"
            "**The waste hierarchy (best to worst):**\n"
            "🥇 **Refuse** → don't buy it\n"
            "🥈 **Reduce** → buy less\n"
            "🥉 **Reuse** → use again\n"
            "4️⃣ **Recycle** → process materials\n"
            "5️⃣ **Recover energy** → burn for power\n"
            "❌ **Landfill** → worst option\n\n"
            "💡 Separating wet & dry waste at home is the first step to effective recycling in India."
        ),
    },

    # ── CONSUMPTION ────────────────────────────────────────────────────────────
    {
        "patterns": ["shopping", "clothes", "clothing", "fashion", "buy", "purchase", "consumption"],
        "response": (
            "🛍️ **Sustainable Shopping & Fashion:**\n\n"
            "The fashion industry produces **~10% of global carbon emissions** — more than aviation and shipping combined!\n\n"
            "**Carbon cost of clothing:**\n"
            "• One cotton t-shirt: ~2.1 kg CO₂e\n"
            "• One pair of jeans: ~33 kg CO₂e\n"
            "• One polyester jacket: ~7 kg CO₂e\n\n"
            "**What you can do:**\n"
            "1. Buy **second-hand** (thrift, Olx, Vinted) → 70% less carbon than new\n"
            "2. **Repair** clothes instead of replacing them\n"
            "3. Choose **natural fibres** (cotton, linen, wool) over synthetics\n"
            "4. Wash in **cold water** (90% of washing machine energy is just heating water)\n"
            "5. Air-dry instead of using a dryer → saves ~2.4 kg CO₂ per load\n"
            "6. Follow the **30-wear rule** — only buy if you'll wear it 30+ times"
        ),
    },
    {
        "patterns": ["electronics", "laptop", "phone", "smartphone", "computer", "device"],
        "response": (
            "💻 **Electronics & Gadgets:**\n\n"
            "Manufacturing electronics is extremely carbon-intensive — most of a device's lifetime footprint happens **before you even use it**.\n\n"
            "**Carbon cost of making:**\n"
            "• Smartphone: ~70 kg CO₂e\n"
            "• Laptop: ~300–400 kg CO₂e\n"
            "• LED TV (55 inch): ~500 kg CO₂e\n\n"
            "**The golden rule: keep devices longer!**\n"
            "• Using a phone 4 years instead of 2 → **cuts its annual footprint by 50%**\n"
            "• Refurbished phones/laptops: ~70% less footprint than new\n\n"
            "**Daily usage tips:**\n"
            "• Enable power-saving/dark mode → up to 20% less battery drain\n"
            "• Unplug chargers when not in use (still draws 0.1–0.5W)\n"
            "• Stream at 720p instead of 4K → 4× less data = 4× less server energy"
        ),
    },

    # ── WATER ──────────────────────────────────────────────────────────────────
    {
        "patterns": ["water", "shower", "bath", "tap", "washing"],
        "response": (
            "💧 **Water & Carbon:**\n\n"
            "Water treatment and heating uses significant energy — and water scarcity is worsened by climate change.\n\n"
            "**Energy to heat water:**\n"
            "• A 10-min hot shower: ~0.6 kWh → ~0.43 kg CO₂ (India grid)\n"
            "• A full bath: ~1.2 kWh → ~0.85 kg CO₂\n\n"
            "**Water-saving tips that also cut carbon:**\n"
            "1. Shorten showers by 2 minutes → saves ~25 litres & ~0.1 kg CO₂/day\n"
            "2. Fix leaking taps → a dripping tap wastes 15 litres/day\n"
            "3. Use a low-flow showerhead → cuts water use by 40%\n"
            "4. Wash full loads of laundry only\n"
            "5. Collect RO reject water for plants/mopping\n\n"
            "🌊 India is a **water-stressed country** — conserving water also protects ecosystems that absorb CO₂."
        ),
    },

    # ── OFFSETS ────────────────────────────────────────────────────────────────
    {
        "patterns": ["offset", "carbon credit", "carbon neutral", "neutralize", "compensate"],
        "response": (
            "🌳 **Carbon Offsets — What You Need to Know:**\n\n"
            "Carbon offsets let you fund projects that reduce emissions elsewhere to compensate for your own.\n\n"
            "**Types of offset projects:**\n"
            "• 🌲 **Reforestation** — planting trees to absorb CO₂\n"
            "• 🍳 **Clean cookstoves** — replacing wood fires in developing countries\n"
            "• ☀️ **Renewable energy** — solar/wind projects in high-coal regions\n"
            "• 🐄 **Methane capture** — capturing gas from landfills/farms\n\n"
            "**Choosing a quality offset:**\n"
            "Look for certification by:\n"
            "✅ Gold Standard\n"
            "✅ Verified Carbon Standard (VCS/Verra)\n"
            "✅ Plan Vivo\n\n"
            "**Cost:** ~$3–25 per tonne of CO₂. Average Indian footprint (~2t) = ~$6–50/year to fully offset.\n\n"
            "⚠️ Offsets are a **last resort** — always reduce first, then offset what you can't avoid."
        ),
    },

    # ── CLIMATE SCIENCE ────────────────────────────────────────────────────────
    {
        "patterns": ["climate change", "global warming", "temperature", "1.5 degree", "paris", "ipcc"],
        "response": (
            "🌍 **Climate Change — The Basics:**\n\n"
            "The Earth has already warmed **~1.2°C** above pre-industrial levels (IPCC AR6, 2021).\n\n"
            "**The Paris Agreement targets:**\n"
            "• Limit warming to **1.5°C** (safer) or well below 2°C\n"
            "• Reach **net-zero** global emissions by ~2050\n\n"
            "**What 1.5°C vs 2°C means:**\n"
            "| Impact | 1.5°C | 2°C |\n"
            "|--------|-------|-----|\n"
            "| Sea level rise by 2100 | 0.4m | 0.6m |\n"
            "| People exposed to heat stress | 700M | 2B |\n"
            "| Arctic ice-free summers | Once per century | Every decade |\n"
            "| Coral reefs lost | 70–90% | >99% |\n\n"
            "**Per-person carbon budget for 1.5°C:**\n"
            "We need to get to **~2.0 tonnes CO₂e/person/year** by 2030.\n"
            "Average Indian: ~1.9t ✅  |  Average American: ~14.9t ❌\n\n"
            "💪 Every fraction of a degree matters — and individual action at scale drives systemic change."
        ),
    },
    {
        "patterns": ["methane", "co2", "greenhouse gas", "ghg", "carbon dioxide", "nitrous oxide"],
        "response": (
            "🔬 **Greenhouse Gases Explained:**\n\n"
            "Not all greenhouse gases are equal. We measure them in **CO₂-equivalent (CO₂e)**:\n\n"
            "| Gas | GWP (100yr) | Main sources |\n"
            "|-----|------------|-------------|\n"
            "| CO₂ | 1× | Fossil fuels, deforestation |\n"
            "| Methane (CH₄) | 28× | Livestock, landfills, natural gas |\n"
            "| Nitrous oxide (N₂O) | 273× | Fertilizers, agriculture |\n"
            "| HFCs | 1,000–9,000× | Refrigerants, AC |\n\n"
            "**Why methane matters:**\n"
            "Over 20 years, methane is **80× more potent** than CO₂. Cutting methane is the fastest way to slow near-term warming.\n\n"
            "🥩 A single kg of beef produces ~6 kg of methane from cow digestion alone."
        ),
    },

    # ── INDIA SPECIFIC ─────────────────────────────────────────────────────────
    {
        "patterns": ["india", "indian", "delhi", "mumbai", "bangalore", "coal", "grid"],
        "response": (
            "🇮🇳 **India's Carbon Context:**\n\n"
            "India is the world's **3rd largest emitter** overall, but per-capita emissions are **~1.9 t CO₂e/year** — far below the global average of 4.5t.\n\n"
            "**India's energy mix (2024):**\n"
            "• Coal: ~50% of electricity\n"
            "• Renewables: ~33% (solar + wind, growing fast!)\n"
            "• Hydro: ~10%\n"
            "• Nuclear: ~3%\n\n"
            "**India's climate commitments:**\n"
            "• Net-zero by 2070\n"
            "• 50% power from renewables by 2030\n"
            "• Reduce emissions intensity by 45% vs 2005\n\n"
            "**Best actions for Indian context:**\n"
            "1. 🌞 Install solar (high irradiance + PM Surya Ghar subsidies)\n"
            "2. 🚆 Use Indian Railways (very low carbon per km)\n"
            "3. 🥗 Eat less beef/lamb (already low in India — maintain it!)\n"
            "4. 🛺 Use EVs for local commutes (e-rickshaws, e-scooters)"
        ),
    },

    # ── TIPS / GENERAL ─────────────────────────────────────────────────────────
    {
        "patterns": ["tip", "advice", "suggest", "help me", "what can i do", "how to reduce", "start"],
        "response": (
            "🌿 **Top 10 Actions to Reduce Your Carbon Footprint:**\n\n"
            "Ranked by annual CO₂e savings (high to low):\n\n"
            "1. 🚗 → 🚆 **Switch to public transport or EV** — saves 2.0–2.5t/year\n"
            "2. 🥩 → 🥗 **Go plant-based** — saves 1.5–2.0t/year\n"
            "3. ✈️ **Cut one long-haul flight** — saves 0.7–2.0t per return trip\n"
            "4. 🏠 **Improve home insulation** — saves 0.5–1.5t/year\n"
            "5. ☀️ **Install solar rooftop** — saves 0.8–1.2t/year\n"
            "6. 💡 **Switch to all-LED lighting** — saves 0.15t/year\n"
            "7. 🌡️ **AC at 24°C instead of 18°C** — saves 0.3–0.5t/year\n"
            "8. 🛍️ **Buy second-hand, repair items** — saves 0.3–0.5t/year\n"
            "9. ♻️ **Compost food waste** — saves 0.1–0.3t/year\n"
            "10. 🌳 **Offset what you can't reduce** — $6–50/year for avg Indian\n\n"
            "💬 Ask me about any of these topics for detailed guidance!"
        ),
    },
    {
        "patterns": ["footprint", "carbon footprint", "my footprint", "calculate", "measure"],
        "response": (
            "📊 **Understanding Your Carbon Footprint:**\n\n"
            "A carbon footprint is the total greenhouse gases your activities produce, measured in **kg or tonnes of CO₂-equivalent (CO₂e)**.\n\n"
            "**Average footprints worldwide:**\n"
            "• 🌍 Global average: **4.5 t CO₂e/year**\n"
            "• 🇮🇳 India: **1.9 t CO₂e/year**\n"
            "• 🇺🇸 USA: **14.9 t CO₂e/year**\n"
            "• 🇬🇧 UK: **4.7 t CO₂e/year**\n"
            "• 🎯 Paris 1.5°C target: **2.0 t CO₂e/year**\n\n"
            "**Your footprint breakdown (typical):**\n"
            "• Transport: 25–45%\n"
            "• Food: 20–30%\n"
            "• Energy (home): 15–25%\n"
            "• Goods & shopping: 10–15%\n"
            "• Waste: 5–10%\n\n"
            "💡 Use the **Calculator tab** to measure your exact footprint and get personalised tips!"
        ),
    },
    {
        "patterns": ["tree", "trees", "forest", "plant trees", "deforestation"],
        "response": (
            "🌳 **Trees & Carbon Sequestration:**\n\n"
            "Trees absorb CO₂ through photosynthesis and store it as wood and soil carbon.\n\n"
            "**How much CO₂ does a tree absorb?**\n"
            "• A mature tree absorbs **~21 kg CO₂/year** on average\n"
            "• A fast-growing tree (eucalyptus, bamboo) can absorb up to **45 kg/year**\n"
            "• To offset an average Indian footprint (1.9t) you'd need **~90 mature trees**\n\n"
            "**Important context:**\n"
            "• Trees take **20–100 years** to absorb meaningful CO₂\n"
            "• Forests can be lost to fire, disease, or deforestation\n"
            "• **Protecting existing forests** is more effective than planting new ones\n\n"
            "**Best tree initiatives in India:**\n"
            "• Green Yatra, SayTrees, Wildlife Trust of India plant verified trees\n"
            "• Cost: ~₹50–150 per tree planted + monitored"
        ),
    },
    {
        "patterns": ["hello", "hi", "hey", "good morning", "good evening", "howdy"],
        "response": (
            "👋 **Hello! I'm EcoBot, your AI carbon coach!**\n\n"
            "I can help you with:\n"
            "🚗 Transport & EV tips\n"
            "🥗 Food & diet emissions\n"
            "⚡ Home energy savings\n"
            "☀️ Solar & renewables\n"
            "🛍️ Sustainable shopping\n"
            "♻️ Waste & recycling\n"
            "✈️ Flight & travel carbon\n"
            "🌍 Climate science basics\n"
            "🌳 Carbon offsets\n\n"
            "Just ask me anything! For example: *\"How can I reduce my transport emissions?\"* or *\"What's the carbon footprint of beef?\"*"
        ),
    },
    {
        "patterns": ["thank", "thanks", "great", "awesome", "helpful", "good"],
        "response": (
            "😊 You're welcome! Every action counts — even small changes add up over a lifetime.\n\n"
            "🌿 **Remember:** You don't have to be perfect. A 50% reduction in footprint while living well is far better than an unsustainable attempt at zero.\n\n"
            "Keep asking questions — I'm here to help! 💚"
        ),
    },
]


def get_chatbot_response(message: str) -> str:
    """
    Match the user's message against the knowledge base and return
    the best matching response. Falls back to a helpful default.
    """
    msg_lower = message.lower().strip()

    # Try to match against each topic's patterns
    for topic in KNOWLEDGE_BASE:
        for pattern in topic["patterns"]:
            if len(pattern) <= 3:
                if re.search(r'\b' + re.escape(pattern) + r'(?:s\b|\b)', msg_lower):
                    return topic["response"]
            else:
                if pattern in msg_lower:
                    return topic["response"]

    # Keyword fallback for common single words
    if any(w in msg_lower for w in ["carbon", "emission", "ghg", "pollution"]):
        return get_chatbot_response("footprint")

    if any(w in msg_lower for w in ["save", "cut", "lower", "decrease", "reduce"]):
        return get_chatbot_response("tip")

    # Generic fallback
    return (
        "🌿 Great question! I'm EcoBot, your carbon coach.\n\n"
        "I can answer questions about:\n"
        "• 🚗 Transport & EVs\n"
        "• 🥗 Food & diet\n"
        "• ⚡ Home energy\n"
        "• ☀️ Solar & renewables\n"
        "• ✈️ Flights & travel\n"
        "• ♻️ Waste & recycling\n"
        "• 🛍️ Shopping & fashion\n"
        "• 🌍 Climate science\n"
        "• 🌳 Carbon offsets\n\n"
        "Try asking: *\"How can I reduce my transport emissions?\"* or *\"What's the carbon footprint of beef?\"*"
    )
