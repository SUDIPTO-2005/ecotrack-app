import pytest
from django.core.management import call_command
from apps.challenges.models import Challenge, Badge

def test_seed_challenges_command(db):
    # Call the management command
    call_command("seed_challenges")
    
    # Assert badges and challenges are created
    assert Badge.objects.count() > 0
    assert Challenge.objects.count() > 0
