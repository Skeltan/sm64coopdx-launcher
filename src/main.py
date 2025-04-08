import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from gui.app_window import AppWindow

def main():
    # Ensure the 'versions' directory exists
    if not os.path.exists("versions"):
        os.makedirs("versions")

    app = AppWindow()
    app.run()

if __name__ == "__main__":
    main()