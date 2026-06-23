import os
import sys

if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
    os.chdir(sys._MEIPASS)

from GUI import mainGUI

def main():
    gui = mainGUI()
    gui.run()


if __name__ == "__main__":
    main()
