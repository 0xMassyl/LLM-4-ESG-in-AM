from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Text
from sqlalchemy.orm import declarative_base, sessionmaker
from datetime import datetime
from typing import Dict, Any, cast
from config.settings import get_settings

settings = get_settings()


# -------------------------------------------------------------------------
# 1. Database Connection Setup
# -------------------------------------------------------------------------
# We build the PostgreSQL URL from environment variables.
# This makes the project portable: same code works locally and inside Docker.
DATABASE_URL = (
    f"postgresql://{settings.DB_USER}:{settings.DB_PASSWORD}"
    f"@{settings.DB_HOST}:{settings.DB_PORT}/{settings.DB_NAME}"
)

try:
    # Create SQLAlchemy engine and session factory.
    engine = create_engine(DATABASE_URL)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base = declarative_base()

except Exception as e:
    # If Docker/Postgres isn't running, the project should still import fine.
    print(f"Database connection failed. Error: {e}")
    Base = declarative_base()
    SessionLocal = None


# -------------------------------------------------------------------------
# 2. ESGScore Table Definition
# -------------------------------------------------------------------------
class ESGScore(Base):
    """
    Simple SQL table storing ESG analysis outputs.
    Each row represents one evaluation of a company's ESG profile.
    """
    __tablename__ = "esg_scores"

    id = Column(Integer, primary_key=True, index=True)
    ticker = Column(String, index=True)
    date_analyzed = Column(DateTime, default=datetime.utcnow)

    # ESG score computed by the analyzer (0–100 scale)
    score = Column(Float, nullable=False)

    # Text explanation returned by the LLM
    rationale = Column(Text)

    # Additional metadata
    source_url = Column(String, nullable=True)
    model_used = Column(String, default="gpt-4-turbo-mock")


# -------------------------------------------------------------------------
# 3. CRUD Utility Functions
# -------------------------------------------------------------------------
def init_db():
    """
    Creates the database tables if they do not exist already.
    Called once at startup.
    """
    if engine:
        try:
            Base.metadata.create_all(bind=engine)
            print("Database tables created successfully.")
        except Exception as e:
            print(f"Database initialization failed: {e}")


def save_score(ticker: str, score: float, rationale: str, source: str = "manual"):
    """
    Saves a new ESG score into the database.
    The function uses a session to ensure changes are committed safely.
    """
    if not SessionLocal:
        print("No database session available.")
        return

    session = SessionLocal()
    try:
        entry = ESGScore(
            ticker=ticker,
            score=score,
            rationale=rationale,
            source_url=source
        )
        session.add(entry)
        session.commit()
        print(f"[DB] Saved ESG score for {ticker}: {score}/100")
    except Exception as e:
        print(f"[DB] Save error: {e}")
        session.rollback()
    finally:
        session.close()


def get_latest_scores() -> Dict[str, float]:
    """
    Loads the most recent ESG score per ticker.
    Used in the FastAPI endpoint to filter the investment universe.
    """
    if not SessionLocal:
        return {}

    session = SessionLocal()
    try:
        rows = session.query(ESGScore).all()

        # SQLAlchemy ORM types are not always recognized by linters,
        # so we cast values to make sure they behave like normal Python types.
        return {
            str(cast(Any, row.ticker)): float(cast(Any, row.score))
            for row in rows
        } if rows else {}

    except Exception as e:
        print(f"[DB] Read error: {e}")
        return {}

    finally:
        session.close()
