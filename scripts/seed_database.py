"""Load the generated synthetic CSV dataset into the configured database."""
from pathlib import Path
import json
import pandas as pd
from sqlalchemy import select
from app.db.database import Base, SessionLocal, engine
from app.db.models import Account, Beneficiary, Customer, Device, Transaction
from scripts.generate_data import generate

def seed():
    Base.metadata.create_all(bind=engine)
    folder = Path(__file__).resolve().parents[1] / "data" / "synthetic"
    if not (folder / "transactions.csv").exists(): generate(output=folder)
    db = SessionLocal()
    try:
        if db.scalar(select(Customer.id).limit(1)):
            print("Database already contains customers; seed skipped to avoid duplicates.")
            return
        for row in pd.read_csv(folder / "customers.csv").to_dict("records"):
            db.add(Customer(**row))
        db.flush()
        for row in pd.read_csv(folder / "accounts.csv").to_dict("records"):
            row["created_at"] = pd.Timestamp(row["created_at"]).to_pydatetime()
            db.add(Account(**row))
        db.flush()
        for row in pd.read_csv(folder / "devices.csv").to_dict("records"):
            row["risk_flags"] = json.loads(row["risk_flags"])
            db.add(Device(**row))
        for row in pd.read_csv(folder / "beneficiaries.csv").to_dict("records"):
            db.add(Beneficiary(**row))
        db.flush()
        rows = pd.read_csv(folder / "transactions.csv").drop(columns=["synthetic_label"]).to_dict("records")
        for row in rows:
            row["timestamp"] = pd.Timestamp(row["timestamp"]).to_pydatetime()
            db.add(Transaction(**row))
        db.commit()
        print(f"Seeded {len(rows)} synthetic transactions, 1,000 accounts, customers and related entities.")
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()

if __name__ == "__main__": seed()
