import os

import django

os.environ['DJANGO_SETTINGS_MODULE'] = 'config.settings.development'
django.setup()
from apps.challenges.models import Badge, Challenge

print('Badges:', Badge.objects.count())
print('Challenges:', Challenge.objects.count())
for b in Badge.objects.all():
    print(' -', b.name)
for c in Challenge.objects.all():
    print(' -', c.title)
