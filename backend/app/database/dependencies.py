from collections.abc import Generator

from sqlalchemy.orm import Session

from app.database.session import engine


def get_db() -> Generator[Session, None, None]:
    db = Session(bind=engine)

    try:
        yield db
    finally:
        db.close()