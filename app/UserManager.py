from database.models import User
from database.db import SessionLocal, init_db
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class UserManager:
    @staticmethod
    def create_user(username: str, password: str) -> User:
        """Crée un utilisateur avec le nom d'utilisateur et le mot de passe donnés (mot de passe hashé).

        Args:
            username (str): Nom d'utilisateur à créer.
            password (str): Mot de passe de l'utilisateur.

        Returns:
            User: L'utilisateur créé.
        """
        hashed_password = pwd_context.hash(password)
        with SessionLocal() as session:
            user = User(username=username, password=hashed_password)
            session.add(user)
            session.commit()
            return user

    @staticmethod
    def get_all_users():
        """Récupère tous les utilisateurs.
        
        Returns:
            list: Liste de tous les utilisateurs.
        """

        with SessionLocal() as session:
            return session.query(User).all()

    @staticmethod
    def get_user_by_id(id: int) -> User | None:
        """Récupère un utilisateur par son id.
        
        Args:
            id (int): id de l'utilisateur à rechercher.
        
        Returns:
            User: L'utilisateur trouvé ou None.
        """
        
        with SessionLocal() as session:
            return session.query(User).filter_by(id=id).first()

    @staticmethod
    def delete_user(id: int):
        """Supprime un utilisateur par son id.
        
        Args:
            id (int): id de l'utilisateur à supprimer.
        
        Returns:
            bool: True si l'utilisateur a été supprimé, False sinon.
        """
        
        with SessionLocal() as session:
            user = session.query(User).filter_by(id=id).first()
            if user:
                session.delete(user)
                session.commit()
                return True
            return False