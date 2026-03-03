# Generated manually for this project (compatible with Django 5.x)
from __future__ import annotations

from django.db import migrations, models
import django.db.models.deletion

class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ("auth", "0012_alter_user_first_name_max_length"),
    ]

    operations = [
        migrations.CreateModel(
            name="Election",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("title", models.CharField(max_length=200)),
                ("description", models.TextField(blank=True)),
                ("start_at", models.DateTimeField()),
                ("end_at", models.DateTimeField()),
                ("status", models.CharField(choices=[("DRAFT", "Draft"), ("RUNNING", "Running"), ("ENDED", "Ended")], default="DRAFT", max_length=10)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
            ],
        ),
        migrations.CreateModel(
            name="Party",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name_en", models.CharField(max_length=200)),
                ("name_np", models.CharField(blank=True, max_length=200)),
                ("abbreviation", models.CharField(max_length=20)),
                ("symbol_text", models.CharField(blank=True, max_length=50)),
            ],
        ),
        migrations.CreateModel(
            name="AuditLog",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("action", models.CharField(max_length=50)),
                ("object_type", models.CharField(max_length=80)),
                ("object_id", models.CharField(blank=True, max_length=80)),
                ("meta_json", models.JSONField(blank=True, default=dict)),
                ("ip", models.GenericIPAddressField(blank=True, null=True)),
                ("ua", models.TextField(blank=True)),
                ("prev_hash", models.CharField(blank=True, max_length=64)),
                ("hash", models.CharField(blank=True, max_length=64)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("actor", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="audit_logs", to="auth.user")),
            ],
        ),
        migrations.CreateModel(
            name="Constituency",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=150)),
                ("code", models.CharField(max_length=20)),
                ("election", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="constituencies", to="voting.election")),
            ],
            options={"unique_together": {("election", "code")}},
        ),
        migrations.CreateModel(
            name="Candidate",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("full_name_en", models.CharField(max_length=200)),
                ("full_name_np", models.CharField(blank=True, max_length=200)),
                ("photo", models.ImageField(blank=True, null=True, upload_to="candidate_photos/")),
                ("constituency", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="candidates", to="voting.constituency")),
                ("party", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="candidates", to="voting.party")),
            ],
        ),
        migrations.CreateModel(
            name="VoterProfile",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("citizenship_id", models.CharField(blank=True, max_length=40)),
                ("phone", models.CharField(blank=True, max_length=30)),
                ("is_verified", models.BooleanField(default=False)),
                ("constituency", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to="voting.constituency")),
                ("user", models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name="voter_profile", to="auth.user")),
            ],
        ),
        migrations.CreateModel(
            name="VoterParticipation",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("has_voted", models.BooleanField(default=False)),
                ("voted_at", models.DateTimeField(blank=True, null=True)),
                ("election", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="participations", to="voting.election")),
                ("voter", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="participations", to="auth.user")),
            ],
        ),
        migrations.AddConstraint(
            model_name="voterparticipation",
            constraint=models.UniqueConstraint(fields=("voter", "election"), name="uniq_voter_election_participation"),
        ),
        migrations.CreateModel(
            name="EncryptedBallot",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("encrypted_payload", models.TextField()),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("constituency", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="ballots", to="voting.constituency")),
                ("election", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="ballots", to="voting.election")),
            ],
        ),
        migrations.CreateModel(
            name="ResultTally",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("votes", models.PositiveIntegerField(default=0)),
                ("candidate", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="tallies", to="voting.candidate")),
                ("constituency", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="tallies", to="voting.constituency")),
                ("election", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="tallies", to="voting.election")),
            ],
        ),
        migrations.AddConstraint(
            model_name="resulttally",
            constraint=models.UniqueConstraint(fields=("election", "constituency", "candidate"), name="uniq_tally_triplet"),
        ),
    ]