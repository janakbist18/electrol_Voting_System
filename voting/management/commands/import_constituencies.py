from __future__ import annotations

import csv
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from voting.models import Election, Constituency


class Command(BaseCommand):
    help = "Import constituencies for an election from a CSV file (code,name)."

    def add_arguments(self, parser):
        parser.add_argument("--election-id", type=int, required=True)
        parser.add_argument("--csv", type=str, required=True)

    @transaction.atomic
    def handle(self, *args, **options):
        election_id = options["election_id"]
        csv_path = Path(options["csv"])

        if not csv_path.exists():
            raise CommandError(f"CSV not found: {csv_path}")

        election = Election.objects.filter(id=election_id).first()
        if not election:
            raise CommandError(f"Election not found: {election_id}")

        created = 0
        updated = 0

        with csv_path.open("r", encoding="utf-8-sig", newline="") as f:
            reader = csv.DictReader(f)
            required = {"code", "name"}
            if not required.issubset(set(reader.fieldnames or [])):
                raise CommandError("CSV must have headers: code,name")

            for row in reader:
                code = (row["code"] or "").strip()
                name = (row["name"] or "").strip()
                if not code or not name:
                    continue

                obj, was_created = Constituency.objects.update_or_create(
                    election=election,
                    code=code,
                    defaults={"name": name},
                )
                created += 1 if was_created else 0
                updated += 0 if was_created else 1

        self.stdout.write(self.style.SUCCESS(
            f"Imported constituencies for election={election_id}: created={created}, updated={updated}"
        ))