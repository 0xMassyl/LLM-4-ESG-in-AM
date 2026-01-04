# -------------------------------------------------
# SQLAlchemy core imports
# Used to define tables, columns and database engine
# -------------------------------------------------
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Text
from sqlalchemy.orm import declarative_base, sessionmaker

# -------------------------------------------------
# Standard library imports
# -------------------------------------------------
from datetime import datetime
from typing import Dict, Any, cast

# -------------------------------------------------
# Project configuration
# Used to load database credentials from environment
# -------------------------------------------------
from config.settings import get_settings

# Load application settings (DB credentials, host, port, etc.)
settings = get_settings()

# =================================================
# 1. Database Connection Setup
# =================================================

# Build the PostgreSQL connection URL dynamically.
# This avoids hardcoding credentials and allows:
# - local development
# - Docker deployment
# - CI/CD environments
DATABASE_URL = (
    f"postgresql://{settings.DB_USER}:{settings.DB_PASSWORD}"
    f"@{settings.DB_HOST}:{settings.DB_PORT}/{settings.DB_NAME}"
)

try:
    # Create the SQLAlchemy engine.
    # The engine manages the actual DB connection pool.
    engine = create_engine(DATABASE_URL)

    # Create a session factory.
    # Each session represents a transactional DB interaction.
    SessionLocal = sessionmaker(
        autocommit=False,  # Explicit commit required (safer)
        autoflush=False,   # Avoid implicit writes
        bind=engine
    )

    # Base class used to declare ORM models
    Base = declarative_base()

except Exception as e:
    # If the database is not reachable at import time
    # we still want the application to start.
    # This is important for:
    # - demo mode
    # - backend startup order in Docker
    print(f"[DB] Connection initialization failed: {e}")

    # We still define Base to avoid crashes elsewhere
    Base = declarative_base()
    SessionLocal = None


# =================================================
# 2. ESGScore Table Definition
# =================================================
class ESGScore(Base):
    """
    ORM model representing one ESG score entry.

    Each row corresponds to:
    - one ticker
    - one ESG score value
    - the explanation (rationale)
    - metadata about how the score was produced
    """

    # Name of the table in PostgreSQL
    __tablename__ = "esg_scores"

    # Primary key
    id = Column(Integer, primary_key=True, index=True)

    # Financial instrument identifier (AAPL, MSFT, etc.)
    ticker = Column(String, index=True)

    # Timestamp of when the score was generated
    # Default is UTC time at insertion
    date_analyzed = Column(DateTime, default=datetime.utcnow)

    # ESG score between 0 and 100
    score = Column(Float, nullable=False)

    # Textual explanation justifying the score
    rationale = Column(Text)

    # Optional reference to external data source
    source_url = Column(String, nullable=True)

    # Metadata field to track which model/process produced the score
    model_used = Column(String, default="gpt-4-turbo-mock")


# =================================================
# 3. Database Utility Functions
# =================================================

def init_db():
    """
    Creates all database tables if they do not exist.

    This function is typically called:
    - at application startup
    - during first deployment
    - in local development environments
    """
    if engine:
        try:
            # Generates SQL CREATE TABLE statements
            # based on ORM model definitions
            Base.metadata.create_all(bind=engine)
            print("[DB] Tables created successfully.")
        except Exception as e:
            print(f"[DB] Initialization failed: {e}")


def save_score(ticker: str, score: float, rationale: str, source: str = "manual"):
    """
    Persists a new ESG score in the database.

    Why this function exists:
    - centralizes DB write logic
    - avoids duplicated session handling
    - ensures transaction safety
    """
    # If database is unavailable, skip write safely
    if not SessionLocal:
        print("[DB] No session available. Entry skipped.")
        return

    # Create a new transactional session
    session = SessionLocal()

    try:
        # Build ORM object from function inputs
        entry = ESGScore(
            ticker=ticker,
            score=score,
            rationale=rationale,
            source_url=source
        )

        # Stage object for insertion
        session.add(entry)

        # Commit transaction
        session.commit()

        print(f"[DB] ESG score saved for {ticker}: {score}/100")

    except Exception as e:
        # Rollback transaction on error
        # Prevents partial or corrupted writes
        print(f"[DB] Save error: {e}")
        session.rollback()

    finally:
        # Always close the session
        # Prevents connection leaks
        session.close()


def get_latest_scores() -> Dict[str, float]:
    """
    Fetches ESG scores from the database.

    Output format:
        { "AAPL": 82.0, "MSFT": 76.5, ... }

    This function is used by:
    - the portfolio optimizer
    - the ESG filtering step
    """
    # If DB is unavailable, return empty result
    if not SessionLocal:
        return {}

    session = SessionLocal()

    try:
        # Query all ESG score rows
        # Note: no time filtering here (latest overwrite logic upstream)
        rows = session.query(ESGScore).all()

        # If table is empty, return empty dict
        if not rows:
            return {}

        # Convert ORM objects to plain Python types
        # This avoids serialization issues later
        return {
            str(cast(Any, row.ticker)): float(cast(Any, row.score))
            for row in rows
        }

    except Exception as e:
        print(f"[DB] Read error: {e}")
        return {}

    finally:
        # Close session in all cases
        session.close()
