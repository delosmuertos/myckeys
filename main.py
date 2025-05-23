import sys
sys.dont_write_bytecode = True

from database.db import SessionLocal, init_db
from database.models import User

from app.UserManager import UserManager

def main():
    init_db()
    
    UserManager.create_user("Test", "motdepasse")

if __name__ == "__main__":
    main()
