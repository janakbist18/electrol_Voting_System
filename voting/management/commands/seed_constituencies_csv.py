from __future__ import annotations

import csv
from pathlib import Path
from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta

from voting.models import Election, District, Constituency

def district_from_constituency_name(name: str) -> str:
    # Extract district from code (e.g., "TAP-1" -> "Taplejung")
    # Map common patterns
    code_to_district = {
        "TAP": "Taplejung",
        "PAN": "Panchthar",
        "ILL": "Ilam",
        "JHA": "Jhapa",
        "MOR": "Morang",
        "SUN": "Sunsari",
        "DHA": "Dhankuta",
        "TER": "Terhathum",
        "BAH": "Bhojpur",
        "SAP": "Saptari",
        "SIR": "Siraha",
        "DAH": "Dhanusa",
        "MAH": "Mahottari",
        "SAR": "Sarlahi",
        "Rau": "Rautahat",
        "PAR": "Parsa",
        "BAR": "Bara",
        "JAP": "Japa",
        "KAT": "Kathmandu",
        "BHA": "Bhaktapur",
        "LAL": "Lalitpur",
        "NIL": "Nila",
        "CHI": "Chitwan",
        "MAK": "Makwanpur",
        "DIT": "Ditupur",
        "NAW": "Nawalpur",
        "RAP": "Rasuwa",
        "DHA": "Dhading",
        "SIN": "Sindhupalchok",
        "OKH": "Okhaldhunga",
        "KHO": "Khotang",
        "UDA": "Udayapur",
        "JAM": "Jamt",
        "ILL": "Ilam",
        # Add more as needed
    }

    # Try to extract district from name (e.g., "Kathmandu-1" -> "Kathmandu")
    if "-" in name:
        district_name = name.rsplit("-", 1)[0].strip()
        return district_name

    return name.strip()

class Command(BaseCommand):
    help = "Seed districts + constituencies from CSV file."

    def add_arguments(self, parser):
        parser.add_argument(
            '--csv',
            type=str,
            help='Path to CSV file',
            default='data/nepal_constituencies_165.csv'
        )
        parser.add_argument(
            '--election',
            type=str,
            help='Election title',
            default='Nepal Parliamentary Election 2024'
        )

    def handle(self, *args, **options):
        csv_path = Path(options['csv'])
        election_title = options['election']

        if not csv_path.exists():
            # Try relative to project root
            base_dir = Path(__file__).resolve().parent.parent.parent.parent.parent
            csv_path = base_dir / csv_path

        if not csv_path.exists():
            self.stdout.write(self.style.ERROR(f"CSV file not found: {csv_path}"))
            return

        now = timezone.now()
        election, created = Election.objects.get_or_create(
            title=election_title,
            defaults={
                "description": "Nepal Parliamentary Election 2024",
                "start_at": now - timedelta(hours=1),
                "end_at": now + timedelta(days=1),
                "status": Election.Status.DRAFT,
            },
        )

        if not created:
            self.stdout.write(self.style.WARNING(f"Election '{election_title}' already exists"))

        created_d = 0
        created_c = 0

        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                if not row.get('code') or not row.get('name'):
                    continue

                code = row['code'].strip()
                name = row['name'].strip()
                dname = district_from_constituency_name(name)

                # Extract district name from constituency name
                # E.g., "Taplejung-1" -> "Taplejung"
                if " - " in name:
                    dname = name.split(" - ")[0].strip()
                elif "-" in name:
                    dname = name.rsplit("-", 1)[0].strip()

                d, d_created = District.objects.get_or_create(name_en=dname)
                if d_created:
                    created_d += 1

                c, c_created = Constituency.objects.get_or_create(
                    election=election,
                    code=code,
                    defaults={"name": name, "district": d},
                )
                if c_created:
                    created_c += 1
                else:
                    # keep district updated if you re-run
                    if c.district_id != d.id or c.name != name:
                        c.district = d
                        c.name = name
                        c.save(update_fields=["district", "name"])

        self.stdout.write(self.style.SUCCESS(
            f"Done! Election: {election.title}\n"
            f"Districts created: {created_d}, Constituencies created: {created_c}\n"
            f"Total constituencies: {election.constituencies.count()}"
        ))