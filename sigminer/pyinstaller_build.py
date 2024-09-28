import PyInstaller.__main__
from pathlib import Path


def build():
    HERE = Path(__file__).parent.absolute()
    path_to_main = str(
        HERE / "app.py"
    )  # Modify according to the location of your Streamlit file

    PyInstaller.__main__.run(
        [
            path_to_main,
            "--onefile",  # Create a single executable file
            "--windowed",  # Avoid opening a console window
            "--name",
            "my_streamlit_app",  # Name of the executable
            # Add other options if necessary
        ]
    )
