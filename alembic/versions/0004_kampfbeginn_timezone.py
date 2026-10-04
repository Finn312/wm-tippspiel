"""make kampfbeginn timezone-aware

Der naive Timestamp wurde serverseitig faktisch als UTC behandelt
(datetime.now()), waehrend die Browser-Anzeige (new Date(isoString)
ohne Offset) ihn als lokale Browserzeit interpretiert hat. Gemeint
war durchgehend Europe/Berlin-Wandzeit ("10:00 Uhr"), daher werden
bestehende Werte als Europe/Berlin interpretiert und nach UTC
konvertiert; die Spalte wird auf timestamptz umgestellt.

Revision ID: 0004
Revises: 0003
Create Date: 2026-10-04

"""
from typing import Sequence, Union

from alembic import op

revision: str = "0004"
down_revision: Union[str, None] = "0003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        "ALTER TABLE weight_classes "
        "ALTER COLUMN kampfbeginn TYPE timestamptz "
        "USING kampfbeginn AT TIME ZONE 'Europe/Berlin'"
    )


def downgrade() -> None:
    op.execute(
        "ALTER TABLE weight_classes "
        "ALTER COLUMN kampfbeginn TYPE timestamp "
        "USING kampfbeginn AT TIME ZONE 'Europe/Berlin'"
    )
