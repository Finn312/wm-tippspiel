from app.models import Result, Tip


def score_tip(tip: Tip, result: Result) -> int:
    """Punktesystem:
    - Platz 1 exakt: 3 Punkte
    - Platz 2 exakt: 3 Punkte
    - Bronze (3a/3b, Reihenfolge egal) exakt: 2 Punkte
    - Athlet richtig, aber falsche Position: 1 Punkt
    """
    actual_category: dict[int, str] = {}
    if result.platz_1 is not None:
        actual_category[result.platz_1] = "1"
    if result.platz_2 is not None:
        actual_category[result.platz_2] = "2"
    if result.platz_3a is not None:
        actual_category[result.platz_3a] = "3"
    if result.platz_3b is not None:
        actual_category[result.platz_3b] = "3"

    tipped_slots = [
        (tip.platz_1, "1", 3),
        (tip.platz_2, "2", 3),
        (tip.platz_3a, "3", 2),
        (tip.platz_3b, "3", 2),
    ]

    total = 0
    for athlete_id, tip_category, exact_points in tipped_slots:
        if athlete_id is None:
            continue
        actual = actual_category.get(athlete_id)
        if actual is None:
            continue
        if actual == tip_category:
            total += exact_points
        else:
            total += 1

    return total
