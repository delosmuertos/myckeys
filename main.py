import sys
sys.dont_write_bytecode = True

from database.db import SessionLocal, init_db
from database.models import User

from app.UserManager import UserManager

from PyQt5.QtWidgets import QApplication

from resources.views.auth_window import AuthWindow

def main():
    init_db()
    
    #UserManager.create_user("A", "a")
    
    app = QApplication(sys.argv)
    window = AuthWindow()
    window.show()
    
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()


