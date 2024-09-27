# my_project/pyinstaller_build.py

import PyInstaller.__main__
from pathlib import Path


def build():
    HERE = Path(__file__).parent.absolute()
    path_to_main = str(
        HERE / "app.py"
    )  # Modifier selon l'emplacement de votre fichier Streamlit

    PyInstaller.__main__.run(
        [
            path_to_main,
            "--onefile",  # Crée un seul fichier exécutable
            "--windowed",  # Évite d'ouvrir une fenêtre console
            "--name",
            "my_streamlit_app",  # Nom de l'exécutable
            # Ajoutez d'autres options si nécessaire
        ]
    )
