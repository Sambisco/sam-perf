import json
import os


def load_or_generate_database(generate_func, filepath="database.json"):
    if not os.path.exists(filepath):
        print(f"{filepath} introuvable, génération en cours...")
        generate_func()
        print("Génération terminée.")
    else:
        print(f"{filepath} trouvé, chargement direct.")

    with open(filepath, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data
