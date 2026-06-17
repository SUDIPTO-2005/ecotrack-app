import os

import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')
django.setup()

from apps.accounts.models import User
from apps.ai_coach.models import AiCoachingSession
from apps.calculator.models import FootprintEntry

print("=== DB CHECK ===")
users = User.objects.all()
print(f"Total users: {users.count()}")
for u in users:
    fp_count = FootprintEntry.objects.filter(user=u).count()
    session_count = AiCoachingSession.objects.filter(user=u).count()
    print(f"  User: {u.email} | footprints: {fp_count} | ai_sessions: {session_count}")

print()
print("=== FOOTPRINT ENTRIES ===")
for fp in FootprintEntry.objects.all():
    cats = fp.categories.all()
    print(f"  {fp.date} | {fp.mode} | {fp.total_co2e_kg} kg | {cats.count()} categories")
    for c in cats:
        print(f"    {c.category}: {c.co2e_kg} kg ({c.percentage}%)")

print()
print("=== AI COACH SESSIONS ===")
for s in AiCoachingSession.objects.all():
    print(f"  {s.generated_at} | fallback={s.was_fallback} | tips={len(s.tips)}")
    for t in s.tips:
        print(f"    [{t.get('category')}] {t.get('recommendation', t.get('action', '?'))[:60]}")
