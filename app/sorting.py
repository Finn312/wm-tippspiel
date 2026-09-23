def surname_key(full_name: str) -> tuple[str, str]:
    """Sortierschlüssel für Nutzernamen: letztes Wort (Nachname) alphabetisch."""
    parts = full_name.split()
    surname = parts[-1] if parts else full_name
    return (surname.lower(), full_name.lower())


def athlete_surname_key(name: str) -> tuple[str, str]:
    """Sortierschlüssel für Athleten: Nachname ist der GROSSBUCHSTABEN-Teil des Namens
    (so exportieren WRL-Listen ihn, z.B. "Dayanara CURBELO TRAVIESO")."""
    parts = name.split()
    start = len(parts)
    for i, part in enumerate(parts):
        if part.isupper():
            start = i
            break
    surname = " ".join(parts[start:]) or name
    return (surname.lower(), name.lower())
