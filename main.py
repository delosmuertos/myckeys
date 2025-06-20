import sys
sys.dont_write_bytecode = True

from database.db import init_db
from PyQt5.QtWidgets import QApplication
from resources.views.auth_window import AuthWindow

def main():
    init_db()
    
    app = QApplication(sys.argv)
    window = AuthWindow()
    window.show()
    
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()


