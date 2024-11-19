from gui_setup import setup_main_window
import globals
import atexit
import shutil
import os


def cleanup_temp_dir():
    if os.path.exists(globals.TEMP_DIR):
        shutil.rmtree(globals.TEMP_DIR)


if __name__ == "__main__":
    globals.setup_temp_dir()
    atexit.register(cleanup_temp_dir)
    setup_main_window()
