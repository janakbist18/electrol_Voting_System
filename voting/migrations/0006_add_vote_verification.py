# Generated migration file for new features
# This migration adds:
# 1. is_admin field to VoterProfile
# 2. VoteVerification model

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ('voting', '0005_alter_constituency_unique_together_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='voterprofile',
            name='is_admin',
            field=models.BooleanField(default=False),
        ),
        migrations.CreateModel(
            name='VoteVerification',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('status', models.CharField(choices=[('PENDING', 'Pending'), ('VERIFIED', 'Verified'), ('REJECTED', 'Rejected')], default='PENDING', max_length=10)),
                ('notes', models.TextField(blank=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('verified_at', models.DateTimeField(blank=True, null=True)),
                ('ballot', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='verification', to='voting.encryptedballot')),
                ('verified_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='votes_verified', to=settings.AUTH_USER_MODEL)),
                ('voter', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='vote_verifications', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['created_at'],
            },
        ),
    ]
