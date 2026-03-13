#!/usr/bin/env python
# voting/management/commands/seed_demo_data.py

from django.core.management.base import BaseCommand
from voting.models import Party, Candidate, Constituency, Election
from django.utils import timezone
from datetime import timedelta


DEMO_PARTIES = [
    {
        'name_en': 'Democracy Party',
        'name_np': 'लोकतन्त्र पार्टी',
        'abbreviation': 'DP',
        'symbol_text': '🐘',
    },
    {
        'name_en': 'People\'s Alliance',
        'name_np': 'जनता गठबन्धन',
        'abbreviation': 'PA',
        'symbol_text': '🦁',
    },
    {
        'name_en': 'National Front',
        'name_np': 'राष्ट्रीय मोर्चा',
        'abbreviation': 'NF',
        'symbol_text': '🐯',
    },
    {
        'name_en': 'Progressive Union',
        'name_np': 'प्रगतिशील संघ',
        'abbreviation': 'PU',
        'symbol_text': '🦅',
    },
    {
        'name_en': 'Green Party',
        'name_np': 'हरित पार्टी',
        'abbreviation': 'GP',
        'symbol_text': '🌿',
    },
]

DEMO_CANDIDATES = [
    # For Kathmandu-1
    {'full_name_en': 'Ram Kumar Sharma', 'full_name_np': 'राम कुमार शर्मा', 'party': 'DP', 'constituency_code': 'KAM-1'},
    {'full_name_en': 'Priya Singh', 'full_name_np': 'प्रिया सिंह', 'party': 'PA', 'constituency_code': 'KAM-1'},
    {'full_name_en': 'Bhim Poudel', 'full_name_np': 'भीम पौडेल', 'party': 'NF', 'constituency_code': 'KAM-1'},
    {'full_name_en': 'Smita Adhikari', 'full_name_np': 'स्मिता अधिकारी', 'party': 'PU', 'constituency_code': 'KAM-1'},
    {'full_name_en': 'Deepak Joshi', 'full_name_np': 'दीपक जोशी', 'party': 'GP', 'constituency_code': 'KAM-1'},
]


class Command(BaseCommand):
    help = "Seed demo parties and candidates for testing"

    def add_arguments(self, parser):
        parser.add_argument(
            '--election',
            type=str,
            help='Election title to link candidates to',
            default='Nepal Parliamentary Election 2024'
        )

    def handle(self, *args, **options):
        election_title = options['election']

        # Get election or create one
        try:
            election = Election.objects.get(title=election_title)
        except Election.DoesNotExist:
            self.stdout.write(self.style.WARNING(f"Election '{election_title}' not found. Creating one..."))
            now = timezone.now()
            election = Election.objects.create(
                title=election_title,
                description="Demo election for testing",
                start_at=now + timedelta(hours=1),
                end_at=now + timedelta(days=1),
                status=Election.Status.DRAFT,
            )

        # Create parties
        created_parties = 0
        for party_data in DEMO_PARTIES:
            party, created = Party.objects.get_or_create(
                abbreviation=party_data['abbreviation'],
                defaults=party_data,
            )
            if created:
                created_parties += 1
                self.stdout.write(f"✓ Created party: {party.name_en}")
            else:
                self.stdout.write(f"○ Party already exists: {party.name_en}")

        # Create candidates
        created_candidates = 0
        party_map = {p['abbreviation']: Party.objects.get(abbreviation=p['abbreviation']) for p in DEMO_PARTIES}

        for candidate_data in DEMO_CANDIDATES:
            try:
                # Find constituency
                code = candidate_data.pop('constituency_code')
                constituency = Constituency.objects.get(code=code, election=election)

                # Get party
                party_abbr = candidate_data.pop('party')
                party = party_map[party_abbr]

                # Create candidate
                candidate, created = Candidate.objects.get_or_create(
                    full_name_en=candidate_data['full_name_en'],
                    constituency=constituency,
                    defaults={**candidate_data, 'party': party},
                )
                if created:
                    created_candidates += 1
                    self.stdout.write(f"✓ Created candidate: {candidate.full_name_en}")
                else:
                    self.stdout.write(f"○ Candidate already exists: {candidate.full_name_en}")
            except Constituency.DoesNotExist:
                self.stdout.write(
                    self.style.WARNING(f"× Constituency {code} not found. Skipping {candidate_data['full_name_en']}")
                )
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"× Error creating candidate: {e}"))

        self.stdout.write(self.style.SUCCESS(
            f"\n✓ Demo data seeding complete!\n"
            f"  Parties created: {created_parties}\n"
            f"  Candidates created: {created_candidates}\n"
            f"  Election: {election.title}"
        ))

