"""
Management command to seed challenges and badges into the database.
Run with: python manage.py seed_challenges
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta


class Command(BaseCommand):
    help = "Seed Challenges and Badges into the database"

    def handle(self, *args, **kwargs):
        self.seed_badges()
        self.seed_challenges()
        self.stdout.write(self.style.SUCCESS("[OK] Challenges and Badges seeded successfully!"))

    def seed_badges(self):
        from apps.challenges.models import Badge

        badges = [
            {
                "name": "First Step 🌱",
                "description": "Completed your first carbon footprint calculation. Every journey starts with one step!",
                "icon": "🌱",
                "criteria": {"type": "calculation_count", "threshold": 1},
            },
            {
                "name": "Data Driven 📊",
                "description": "Completed 10 carbon footprint calculations. You're serious about tracking!",
                "icon": "📊",
                "criteria": {"type": "calculation_count", "threshold": 10},
            },
            {
                "name": "7-Day Streak 🔥",
                "description": "Tracked your footprint 7 days in a row. Consistency is key!",
                "icon": "🔥",
                "criteria": {"type": "streak_days", "threshold": 7},
            },
            {
                "name": "30-Day Champion 🏆",
                "description": "Tracked your footprint 30 days in a row. You're a carbon-tracking champion!",
                "icon": "🏆",
                "criteria": {"type": "streak_days", "threshold": 30},
            },
            {
                "name": "Paris Hero 🌍",
                "description": "Your annualised footprint is below the Paris Agreement 2-tonne target. You're saving the planet!",
                "icon": "🌍",
                "criteria": {"type": "annualised_below_kg", "threshold": 2000},
            },
            {
                "name": "Eco Warrior ⚔️",
                "description": "Your footprint is below 1 tonne CO₂e/year — top 5% of all humans on Earth!",
                "icon": "⚔️",
                "criteria": {"type": "annualised_below_kg", "threshold": 1000},
            },
            {
                "name": "Green Commuter 🚆",
                "description": "Transport emissions below 500 kg/year — you're using clean, green transport!",
                "icon": "🚆",
                "criteria": {"type": "category_below_kg", "category": "transport", "threshold": 500},
            },
            {
                "name": "Plant Pioneer 🥗",
                "description": "Diet emissions below 300 kg/year — you're eating green and loving it!",
                "icon": "🥗",
                "criteria": {"type": "category_below_kg", "category": "diet", "threshold": 300},
            },
            {
                "name": "Energy Saver ⚡",
                "description": "Home energy emissions below 400 kg/year — your home runs lean and clean!",
                "icon": "⚡",
                "criteria": {"type": "category_below_kg", "category": "energy", "threshold": 400},
            },
            {
                "name": "Community Member 👥",
                "description": "Opted into the leaderboard and joined the EcoTrack community.",
                "icon": "👥",
                "criteria": {"type": "leaderboard_opt_in"},
            },
            {
                "name": "Carbon Champion 🥇",
                "description": "Reached #1 on the global leaderboard — the ultimate eco achievement!",
                "icon": "🥇",
                "criteria": {"type": "leaderboard_rank", "threshold": 1},
            },
        ]

        created = 0
        for badge_data in badges:
            _, was_created = Badge.objects.update_or_create(
                name=badge_data["name"],
                defaults=badge_data,
            )
            if was_created:
                created += 1

        self.stdout.write(f"  Badges: {created} created / {len(badges) - created} already existed")

    def seed_challenges(self):
        from apps.challenges.models import Challenge

        today = timezone.now().date()
        challenges = [
            {
                "title": "🚗 Car-Free Week",
                "description": (
                    "Avoid using a personal car for 7 days. Use public transport, cycling, or walking instead. "
                    "Track your footprint daily to see the impact! Swapping a 20km daily car commute for a train "
                    "saves ~35 kg CO₂ per week."
                ),
                "category": "transport",
                "start_date": today,
                "end_date": today + timedelta(days=30),
                "target_reduction_pct": 20,
            },
            {
                "title": "🥗 Meatless Month",
                "description": (
                    "Go meat-free for 30 days! Replace meat with plant-based proteins like lentils, "
                    "chickpeas, tofu, and paneer. A plant-based diet can save 50+ kg CO₂e per month — "
                    "that's like not driving 300 km!"
                ),
                "category": "diet",
                "start_date": today,
                "end_date": today + timedelta(days=60),
                "target_reduction_pct": 30,
            },
            {
                "title": "⚡ Energy Audit Week",
                "description": (
                    "Unplug all standby devices, set your AC to 24°C, switch to LED bulbs, and measure "
                    "the difference. Target: 20% less electricity this week. Small changes add up — "
                    "India's grid emits 0.71 kg CO₂ per kWh!"
                ),
                "category": "energy",
                "start_date": today,
                "end_date": today + timedelta(days=30),
                "target_reduction_pct": 20,
            },
            {
                "title": "♻️ Zero Waste Fortnight",
                "description": (
                    "For 2 weeks, separate all waste (wet/dry), compost food scraps, and aim to send zero "
                    "waste to landfill. Food waste in landfills produces methane — 80× more potent than CO₂! "
                    "Composting turns waste into soil instead."
                ),
                "category": "waste",
                "start_date": today,
                "end_date": today + timedelta(days=45),
                "target_reduction_pct": 15,
            },
            {
                "title": "🛍️ Buy Nothing New Month",
                "description": (
                    "For 30 days, avoid buying new items. Repair, borrow, or buy second-hand instead. "
                    "The fashion industry produces 10% of global carbon emissions. "
                    "Buying one fewer outfit per week saves ~35 kg CO₂e/month!"
                ),
                "category": "consumption",
                "start_date": today,
                "end_date": today + timedelta(days=60),
                "target_reduction_pct": 25,
            },
            {
                "title": "🌱 Calculator Streak Challenge",
                "description": (
                    "Track your carbon footprint every day for 7 consecutive days. "
                    "Awareness is the first step to action! Users who track consistently "
                    "reduce their footprint 3× faster than those who don't."
                ),
                "category": "awareness",
                "start_date": today,
                "end_date": today + timedelta(days=14),
                "target_reduction_pct": 10,
            },
        ]

        created = 0
        for challenge_data in challenges:
            _, was_created = Challenge.objects.update_or_create(
                title=challenge_data["title"],
                defaults=challenge_data,
            )
            if was_created:
                created += 1

        self.stdout.write(f"  Challenges: {created} created / {len(challenges) - created} already existed")
