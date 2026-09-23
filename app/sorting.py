def surname_key(full_name: str) -> tuple[str, str]:
    """Sortierschlüssel für Nutzernamen: letztes Wort (Nachname) alphabetisch."""
    parts = full_name.split()
    surname = parts[-1] if parts else full_name
    return (surname.lower(), full_name.lower())


def _split_athlete_name(name: str) -> tuple[str, str]:
    """Trennt einen Athletennamen in (Vorname(n), Nachname). Der Nachname ist der
    GROSSBUCHSTABEN-Teil (so exportieren WRL-Listen ihn, z.B. "Dayanara CURBELO TRAVIESO").
    Ist kein Grossbuchstaben-Teil erkennbar, ist der Vorname leer."""
    parts = name.split()
    start = len(parts)
    for i, part in enumerate(parts):
        if part.isupper():
            start = i
            break
    given = " ".join(parts[:start])
    surname = " ".join(parts[start:]) or name
    return (given, surname)


def athlete_surname_key(name: str) -> tuple[str, str]:
    """Sortierschlüssel für Athleten: alphabetisch nach Nachname."""
    _, surname = _split_athlete_name(name)
    return (surname.lower(), name.lower())


def athlete_display_name(name: str) -> str:
    """Formatiert einen Athletennamen als 'NACHNAME, Vorname' für Auswahllisten."""
    given, surname = _split_athlete_name(name)
    if not given:
        return name
    return f"{surname}, {given}"
