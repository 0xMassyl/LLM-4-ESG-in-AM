from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Text
from sqlalchemy.orm import declarative_base, sessionmaker
from datetime import datetime
from typing import Dict, Any, cast
from config.settings import get_settings

settings = get_settings()

# -------------------------------------------------------------------------
# 1. Database Connection Setup
# -------------------------------------------------------------------------
# Builds PostgreSQL connection string dynamically from environment variables.
# This ensures the module functions both locally and within Docker.
DATABASE_URL = (
    f"postgresql://{settings.DB_USER}:{settings.DB_PASSWORD}"
    f"@{settings.DB_HOST}:{settings.DB_PORT}/{settings.DB_NAME}"
)

try:
    engine = create_engine(DATABASE_URL)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base = declarative_base()
except Exception as e:
    # Allows the application to import modules even if the DB is unavailable.
    print(f"[DB] Connection initialization failed: {e}")
    Base = declarative_base()
    SessionLocal = None


# -------------------------------------------------------------------------
# 2. ESGScore Table Definition
# -------------------------------------------------------------------------
class ESGScore(Base):
    """
    Table storing ESG analysis outputs produced by the LLM analyzer.
    Each entry records:
    - the ticker analyzed,
    - the assigned ESG score (0–100),
    - a short explanatory rationale,
    - optional metadata regarding the analysis source and model used.
    """
    __tablename__ = "esg_scores"

    id = Column(Integer, primary_key=True, index=True)
    ticker = Column(String, index=True)
    date_analyzed = Column(DateTime, default=datetime.utcnow)

    score = Column(Float, nullable=False)
    rationale = Column(Text)

    source_url = Column(String, nullable=True)
    model_used = Column(String, default="gpt-4-turbo-mock")


# -------------------------------------------------------------------------
# 3. CRUD Utility Functions
# -------------------------------------------------------------------------
def init_db():
    """
    Initializes database tables when running the project.
    Called once at startup to ensure schema availability.
    """
    if engine:
        try:
            Base.metadata.create_all(bind=engine)
            print("[DB] Tables created successfully.")
        except Exception as e:
            print(f"[DB] Initialization failed: {e}")


def save_score(ticker: str, score: float, rationale: str, source: str = "manual"):
    """
    Inserts a new ESG score entry into the database.
    Uses a transaction to guarantee atomicity and safe rollback on errors.
    """
    if not SessionLocal:
        print("[DB] No session available. Entry skipped.")
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
        print(f"[DB] ESG score saved for {ticker}: {score}/100")
    except Exception as e:
        print(f"[DB] Save error: {e}")
        session.rollback()
    finally:
        session.close()


def get_latest_scores() -> Dict[str, float]:
    """
    Loads the most recent ESG score per ticker.
    Returns a dictionary: {ticker: score}.
    Used by the FastAPI optimizer to filter the investment universe.
    """
    if not SessionLocal:
        return {}

    session = SessionLocal()
    try:
        rows = session.query(ESGScore).all()

        # Converts ORM values into native Python types to ensure consistency.
        return {
            str(cast(Any, row.ticker)): float(cast(Any, row.score))
            for row in rows
        } if rows else {}

    except Exception as e:
        print(f"[DB] Read error: {e}")
        return {}
    finally:
        session.close()
