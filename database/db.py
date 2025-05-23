from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from config.database import SQLALCHEMY_DATABASE_URI, SQLALCHEMY_ECHO

engine = create_engine(
    SQLALCHEMY_DATABASE_URI,
    echo=SQLALCHEMY_ECHO,
    future=True
)

SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)
Base = declarative_base()

def init_db() -> None:
    """Créée toutes les tables s’il n’y en a pas encore."""
    import database.models  # noqa: F401 – force le chargement des classes
    Base.metadata.create_all(bind=engine)
