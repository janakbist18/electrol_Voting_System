from __future__ import annotations

from datetime import timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone

from voting.models import (
    Candidate,
    Constituency,
    District,
    Election,
    Party,
    ResultTally,
)


class Command(BaseCommand):
    help = "Seed demo Nepal-style election data (safe placeholders)."

    def handle(self, *args, **options):
        now = timezone.now()

        election, _ = Election.objects.get_or_create(
            title="Nepal Parliamentary Demo Election",
            defaults={
                "description": "Demo election dataset (placeholder candidates).",
                "start_at": now - timedelta(hours=1),
                "end_at": now + timedelta(hours=6),
                "status": Election.Status.RUNNING,
            },
        )

        # Parties
        parties_data = [
            ("Nepali Congress", "नेपाली कांग्रेस", "NC", "Tree"),
            ("CPN (UML)", "नेपाल कम्युनिष्ट पार्टी (एमाले)", "UML", "Sun"),
            ("Rastriya Swatantra Party", "राष्ट्रिय स्वतन्त्र पार्टी", "RSP", "Bell"),
            ("Left Alliance", "वाम गठबन्धन", "NCP", "Star"),
        ]
        parties = {}
        for name_en, name_np, abbr, symbol in parties_data:
            p, _ = Party.objects.get_or_create(
                abbreviation=abbr,
                defaults={"name_en": name_en, "name_np": name_np, "symbol_text": symbol},
            )
            parties[abbr] = p

        # Districts (demo)
        kathmandu, _ = District.objects.get_or_create(name_en="Kathmandu", defaults={"name_np": "काठमाडौँ"})
        lalitpur, _ = District.objects.get_or_create(name_en="Lalitpur", defaults={"name_np": "ललितपुर"})
        kaski, _ = District.objects.get_or_create(name_en="Kaski", defaults={"name_np": "कास्की"})
        unknown, _ = District.objects.get_or_create(name_en="Unknown", defaults={"name_np": ""})

        # Constituencies (demo)
        cons_data = [
            # district, name, code
            (kathmandu, "Kathmandu-1", "KTM-1"),
            (kathmandu, "Kathmandu-2", "KTM-2"),
            (lalitpur, "Lalitpur-1", "LTP-1"),
            (kaski, "Pokhara-1", "PKR-1"),
        ]

        constituencies = []
        for district, name, code in cons_data:
            c, _ = Constituency.objects.get_or_create(
                election=election,
                code=code,
                defaults={"name": name, "district": district or unknown},
            )
            # If it existed from earlier run and district is missing, patch it
            if c.district_id is None:
                c.district = district or unknown
                c.save(update_fields=["district"])
            constituencies.append(c)

        # Candidates (2–4 each)
        for c in constituencies:
            candidates_specs = [
                ("Candidate A (NC)", "Candidate A (NC)", "NC"),
                ("Candidate B (UML)", "Candidate B (UML)", "UML"),
                ("Candidate C (RSP)", "Candidate C (RSP)", "RSP"),
            ]
            if c.code in {"KTM-2", "PKR-1"}:
                candidates_specs.append(("Candidate D (NCP)", "Candidate D (NCP)", "NCP"))

            for en, np, abbr in candidates_specs:
                cand, _ = Candidate.objects.get_or_create(
                    full_name_en=en,
                    constituency=c,
                    defaults={"full_name_np": np, "party": parties[abbr]},
                )

                ResultTally.objects.get_or_create(
                    election=election,
                    constituency=c,
                    candidate=cand,
                    defaults={"votes": 0},
                )

        self.stdout.write(self.style.SUCCESS("Seeded demo election: districts, parties, constituencies, candidates, tallies."))