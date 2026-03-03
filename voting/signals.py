from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import VoterProfile

@receiver(post_save, sender=User)
def create_voter_profile(sender, instance: User, created: bool, **kwargs):
    if created:
        VoterProfile.objects.get_or_create(user=instance)