"""seed the 14 WM 2026 weight classes

Kampfbeginn ist auf 10:00 Uhr am jeweiligen Tag gesetzt (Platzhalter, da der
offizielle Sessionplan nur Tage nennt, keine Uhrzeiten). Vor dem Turnier
bitte pruefen/anpassen.

Revision ID: 0003
Revises: 0002
Create Date: 2026-09-22

"""
from datetime import datetime
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0003"
down_revision: Union[str, None] = "0002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

weight_classes_table = sa.table(
    "weight_classes",
    sa.column("name", sa.String),
    sa.column("kampfbeginn", sa.DateTime),
    sa.column("tag", sa.Date),
)

# (Datum, Maenner-Klasse, Frauen-Klasse) - Namen exakt wie in der Athleten-CSV
SCHEDULE = [
    ("2026-10-04", "Männer -60kg (Extra-lightweight)", "Frauen -48kg (Extra-lightweight)"),
    ("2026-10-05", "Männer -66kg (Half-lightweight)", "Frauen -52kg (Half-lightweight)"),
    ("2026-10-06", "Männer -73kg (Lightweight)", "Frauen -57kg (Lightweight)"),
    ("2026-10-07", "Männer -81kg (Half-middleweight)", "Frauen -63kg (Half-middleweight)"),
    ("2026-10-08", "Männer -90kg (Middleweight)", "Frauen -70kg (Middleweight)"),
    ("2026-10-09", "Männer -100kg (Half-heavyweight)", "Frauen -78kg (Half-heavyweight)"),
    ("2026-10-10", "Männer +100kg (Heavyweight)", "Frauen +78kg (Heavyweight)"),
]


def upgrade() -> None:
    rows = []
    for tag_str, mens_name, womens_name in SCHEDULE:
        tag = datetime.strptime(tag_str, "%Y-%m-%d").date()
        kampfbeginn = datetime.combine(tag, datetime.min.time().replace(hour=10))
        rows.append({"name": mens_name, "kampfbeginn": kampfbeginn, "tag": tag})
        rows.append({"name": womens_name, "kampfbeginn": kampfbeginn, "tag": tag})

    op.bulk_insert(weight_classes_table, rows)


def downgrade() -> None:
    names = [name for _, mens, womens in SCHEDULE for name in (mens, womens)]
    conn = op.get_bind()
    conn.execute(
        sa.text("DELETE FROM weight_classes WHERE name = ANY(:names)"), {"names": names}
    )
