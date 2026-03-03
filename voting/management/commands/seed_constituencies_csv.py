from __future__ import annotations

from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta

from voting.models import Election, District, Constituency

CSV_TEXT = """
code,name
TAP-1,Taplejung-1
PAN-1,Panchthar-1
ILL-1,Ilam-1
ILL-2,Ilam-2
JHA-1,Jhapa-1
JHA-2,Jhapa-2
...
DAR-1,Darchula-1
""".strip()

def district_from_constituency_name(name: str) -> str:
    # "Kathmandu-1" -> "Kathmandu"
    # "Rukum East-1" -> "Rukum East"
    if "-" not in name:
        return name.strip()
    return name.rsplit("-", 1)[0].strip()

class Command(BaseCommand):
    help = "Seed districts + constituencies from embedded CSV (demo)."

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

        lines = CSV_TEXT.splitlines()
        header = lines[0].split(",")
        if [h.strip() for h in header] != ["code", "name"]:
            raise RuntimeError("CSV header must be: code,name")

        created_d = 0
        created_c = 0

        for line in lines[1:]:
            if not line.strip():
                continue
            code, name = [x.strip() for x in line.split(",", 1)]
            dname = district_from_constituency_name(name)

            d, d_created = District.objects.get_or_create(name_en=dname)
            if d_created:
                created_d += 1

            c, c_created = Constituency.objects.get_or_create(
                election=election,
                code=code,
                defaults={"name": name, "district": d},
            )
            if not c_created:
                # keep district updated if you re-run
                if c.district_id != d.id or c.name != name:
                    c.district = d
                    c.name = name
                    c.save(update_fields=["district", "name"])
            else:
                created_c += 1

        self.stdout.write(self.style.SUCCESS(
            f"Done. Districts created: {created_d}, Constituencies created: {created_c}"
        ))