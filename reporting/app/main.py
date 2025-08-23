
from fastapi import FastAPI, HTTPException, Depends, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy import create_engine, text, func, Column, Integer, String, Float, ForeignKey, Date, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session, relationship
from typing import List, Optional
from datetime import date, datetime, timedelta
import os

# Database Configuration
POSTGRES_USER = os.environ.get("POSTGRES_USER", "postgres")
POSTGRES_PASSWORD = os.environ.get("POSTGRES_PASSWORD", "admin")
POSTGRES_HOST = os.environ.get("POSTGRES_HOST", "localhost")
POSTGRES_PORT = os.environ.get("POSTGRES_PORT", "5432")
POSTGRES_DB = os.environ.get("POSTGRES_DB", "farmhub_db")

DATABASE_URL = f"postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"

# Print for debugging
print(f"Connecting to database: {DATABASE_URL}")

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

db_dependency = Depends(get_db)

# FastAPI App
app = FastAPI(title="FarmHub Reporting API")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Health Check Endpoint
@app.get("/health")
def health_check():
    try:
        # Test database connection
        with engine.connect() as connection:
            result = connection.execute(text("SELECT 1")).fetchone()
            if result and result[0] == 1:
                return {"status": "healthy", "database": "connected"}
    except Exception as e:
        return {"status": "unhealthy", "database": "disconnected", "error": str(e)}
    
    return {"status": "unhealthy"}

# Models
class Farm(Base):
    __tablename__ = "farms_farm"
    
    id = Column(Integer, primary_key=True)
    name = Column(String)
    location = Column(String)
    created_at = Column(DateTime)
    
    farmers = relationship("Farmer", back_populates="farm")
    
class Farmer(Base):
    __tablename__ = "farms_farmer"
    
    id = Column(Integer, primary_key=True)
    farm_id = Column(Integer, ForeignKey("farms_farm.id"))
    user_id = Column(Integer)
    created_at = Column(DateTime)
    
    farm = relationship("Farm", back_populates="farmers")
    cows = relationship("Cow", back_populates="farmer")

class Cow(Base):
    __tablename__ = "farms_cow"
    
    id = Column(Integer, primary_key=True)
    tag_id = Column(String)
    farmer_id = Column(Integer, ForeignKey("farms_farmer.id"))
    birth_date = Column(Date, nullable=True)
    created_at = Column(DateTime)
    
    farmer = relationship("Farmer", back_populates="cows")
    milk_records = relationship("MilkRecord", back_populates="cow")

class MilkRecord(Base):
    __tablename__ = "farms_milkrecord"
    
    id = Column(Integer, primary_key=True)
    cow_id = Column(Integer, ForeignKey("farms_cow.id"))
    date = Column(Date)
    liters = Column(Float)
    created_at = Column(DateTime)
    
    cow = relationship("Cow", back_populates="milk_records")

class Activity(Base):
    __tablename__ = "farms_activity"
    
    id = Column(Integer, primary_key=True)
    farmer_id = Column(Integer, ForeignKey("farms_farmer.id"))
    description = Column(String)
    created_at = Column(DateTime)
    
    farmer = relationship("Farmer")


class FarmSummary(BaseModel):
    id: int
    name: str
    farmers_count: int
    cows_count: int
    total_milk: float
    
    class Config:
        orm_mode = True

class FarmerSummary(BaseModel):
    id: int
    user_email: str
    farm_name: str
    cows_count: int
    total_milk: float
    
    class Config:
        orm_mode = True

class MilkProductionSummary(BaseModel):
    total_farms: int
    total_farmers: int
    total_cows: int
    total_milk: float
    average_per_cow: float

class MilkByDateSummary(BaseModel):
    date: date
    total_liters: float
    cow_count: int

class ActivitySummary(BaseModel):
    id: int
    farmer_name: str
    description: str
    created_at: datetime
    
    class Config:
        orm_mode = True



# Farm summary endpoint
@app.get("/farms/summary", response_model=List[FarmSummary])
def get_farms_summary(db: Session = Depends(get_db)):
    farms = db.query(Farm).all()
    
    result = []
    for farm in farms:
        # Count farmers
        farmers_count = db.query(Farmer).filter(Farmer.farm_id == farm.id).count()
        
        # Count cows and total milk
        cows_subquery = db.query(Cow.id).join(Farmer).filter(Farmer.farm_id == farm.id).subquery()
        cows_count = db.query(func.count()).select_from(cows_subquery).scalar() or 0
        
        total_milk = db.query(func.sum(MilkRecord.liters)).join(Cow).join(Farmer).filter(
            Farmer.farm_id == farm.id
        ).scalar() or 0.0
        
        result.append({
            "id": farm.id,
            "name": farm.name,
            "farmers_count": farmers_count,
            "cows_count": cows_count,
            "total_milk": float(total_milk)
        })
    
    return result

# Farm detail endpoint
@app.get("/farms/{farm_id}/summary", response_model=FarmSummary)
def get_farm_summary(farm_id: int, db: Session = Depends(get_db)):
    farm = db.query(Farm).filter(Farm.id == farm_id).first()
    if not farm:
        raise HTTPException(status_code=404, detail="Farm not found")
    
    # Count farmers
    farmers_count = db.query(Farmer).filter(Farmer.farm_id == farm.id).count()
    
    # Count cows and total milk
    cows_subquery = db.query(Cow.id).join(Farmer).filter(Farmer.farm_id == farm.id).subquery()
    cows_count = db.query(func.count()).select_from(cows_subquery).scalar() or 0
    
    total_milk = db.query(func.sum(MilkRecord.liters)).join(Cow).join(Farmer).filter(
        Farmer.farm_id == farm.id
    ).scalar() or 0.0
    
    return {
        "id": farm.id,
        "name": farm.name,
        "farmers_count": farmers_count,
        "cows_count": cows_count,
        "total_milk": float(total_milk)
    }

# Farmers summary endpoint (all farmers)
@app.get("/farmers/summary", response_model=List[FarmerSummary])
def get_farmers_summary(farm_id: Optional[int] = None, db: Session = Depends(get_db)):
    query = db.query(
        Farmer.id,
        func.count(Cow.id).label("cows_count"),
        func.coalesce(func.sum(MilkRecord.liters), 0).label("total_milk")
    ).join(Farm).outerjoin(Cow, Farmer.id == Cow.farmer_id).outerjoin(
        MilkRecord, Cow.id == MilkRecord.cow_id
    )
    
    # Only filter by farm_id, removed farmer_id parameter
    if farm_id:
        query = query.filter(Farmer.farm_id == farm_id)
    
    query = query.group_by(Farmer.id)
    
    farmer_summaries = query.all()
    
    result = []
    for summary in farmer_summaries:
        # Get user email from users_user table (instead of auth_user)
        user_email_query = text(
            "SELECT email FROM users_user WHERE id = (SELECT user_id FROM farms_farmer WHERE id = :farmer_id)"
        )
        
        # Try with users_user first, fall back to other possible table names
        try:
            user_email_result = db.execute(user_email_query, {"farmer_id": summary.id}).first()
            user_email = user_email_result[0] if user_email_result else "Unknown"
        except Exception:
            # Fallback - just get the user_id
            user_id_query = text("SELECT user_id FROM farms_farmer WHERE id = :farmer_id")
            user_id_result = db.execute(user_id_query, {"farmer_id": summary.id}).first()
            user_email = f"User #{user_id_result[0]}" if user_id_result else "Unknown"
        
        # Get farm name
        farm_name_query = text(
            "SELECT name FROM farms_farm WHERE id = (SELECT farm_id FROM farms_farmer WHERE id = :farmer_id)"
        )
        farm_name_result = db.execute(farm_name_query, {"farmer_id": summary.id}).first()
        farm_name = farm_name_result[0] if farm_name_result else "Unknown"
        
        result.append({
            "id": summary.id,
            "user_email": user_email,
            "farm_name": farm_name,
            "cows_count": summary.cows_count,
            "total_milk": float(summary.total_milk)
        })
    
    return result

# New endpoint for specific farmer summary
@app.get("/farmers/{farmer_id}/summary", response_model=FarmerSummary)
def get_farmer_summary(farmer_id: int, db: Session = Depends(get_db)):
    # Check if farmer exists
    farmer = db.query(Farmer).filter(Farmer.id == farmer_id).first()
    if not farmer:
        raise HTTPException(status_code=404, detail="Farmer not found")
    
    # Get cows count and milk total - FIX THE QUERY
    summary = db.query(
        func.count(Cow.id).label("cows_count"),
        func.coalesce(func.sum(MilkRecord.liters), 0).label("total_milk")
    ).select_from(Farmer).filter(Farmer.id == farmer_id) \
     .outerjoin(Cow, Cow.farmer_id == Farmer.id) \
     .outerjoin(MilkRecord, MilkRecord.cow_id == Cow.id) \
     .first()
    
    # Get user email safely
    try:
        user_email_query = text(
            "SELECT email FROM users_user WHERE id = (SELECT user_id FROM farms_farmer WHERE id = :farmer_id)"
        )
        user_email_result = db.execute(user_email_query, {"farmer_id": farmer_id}).first()
        user_email = user_email_result[0] if user_email_result else "Unknown"
    except Exception:
        # Fallback - just get the user_id
        user_id_query = text("SELECT user_id FROM farms_farmer WHERE id = :farmer_id")
        user_id_result = db.execute(user_id_query, {"farmer_id": farmer_id}).first()
        user_email = f"User #{user_id_result[0]}" if user_id_result else "Unknown"
    
    # Get farm name
    farm_name_query = text(
        "SELECT name FROM farms_farm WHERE id = (SELECT farm_id FROM farms_farmer WHERE id = :farmer_id)"
    )
    farm_name_result = db.execute(farm_name_query, {"farmer_id": farmer_id}).first()
    farm_name = farm_name_result[0] if farm_name_result else "Unknown"
    
    return {
        "id": farmer_id,
        "user_email": user_email,
        "farm_name": farm_name,
        "cows_count": summary.cows_count or 0,
        "total_milk": float(summary.total_milk or 0)
    }

from fastapi import Query
from datetime import datetime

def parse_date(date_str: str = Query(None)):
    if not date_str:
        return None
    try:
        # Try ISO format first (YYYY-MM-DD)
        return datetime.strptime(date_str, "%Y-%m-%d").date()
    except ValueError:
        try:
            # Try MM/DD/YYYY format
            return datetime.strptime(date_str, "%m/%d/%Y").date()
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD or MM/DD/YYYY")
from fastapi import Query
from datetime import datetime

def parse_date(
    date_str: Optional[str] = Query(
        None,
        description="Date in YYYY-MM-DD or MM/DD/YYYY format",
        example="2025-08-23"
    )
) -> Optional[date]:
    if not date_str:
        return None
    try:
        # Try ISO format first (YYYY-MM-DD)
        return datetime.strptime(date_str, "%Y-%m-%d").date()
    except ValueError:
        try:
            # Try MM/DD/YYYY format
            return datetime.strptime(date_str, "%m/%d/%Y").date()
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail="Invalid date format. Use YYYY-MM-DD or MM/DD/YYYY"
            )

# Milk production summary endpoint
@app.get("/milk/summary", response_model=MilkProductionSummary)
def get_milk_summary(
    farm_id: Optional[int] = None, 
    farmer_id: Optional[int] = None,
    db: Session = Depends(get_db)
):
    """
    Get overall milk production summary without date filtering.
    Optionally filter by farm or farmer.
    """
    # Create a base query for getting all milk records
    base_query = db.query(MilkRecord)
    
    # Add join and filter conditions carefully to avoid duplicate joins
    if farm_id or farmer_id:
        base_query = base_query.join(Cow, MilkRecord.cow_id == Cow.id)
        
        if farm_id:
            base_query = base_query.join(Farmer, Cow.farmer_id == Farmer.id)
            base_query = base_query.filter(Farmer.farm_id == farm_id)
        
        if farmer_id:
            # No need to join Farmer again if we already did for farm_id
            if not farm_id:
                base_query = base_query.join(Farmer, Cow.farmer_id == Farmer.id)
            base_query = base_query.filter(Farmer.id == farmer_id)
    
    # Get total milk using the filtered query (no date filters)
    total_milk = base_query.with_entities(func.sum(MilkRecord.liters)).scalar() or 0.0
    
    # Count farms, farmers, and cows
    total_farms = db.query(func.count(Farm.id)).scalar()
    total_farmers = db.query(func.count(Farmer.id)).scalar()
    
    # Apply filters for cow count
    cow_query = db.query(Cow)
    if farm_id:
        cow_query = cow_query.join(Farmer).filter(Farmer.farm_id == farm_id)
    if farmer_id:
        cow_query = cow_query.filter(Cow.farmer_id == farmer_id)
    
    total_cows = cow_query.count()
    
    # Calculate average per cow
    average_per_cow = total_milk / total_cows if total_cows > 0 else 0.0
    
    return {
        "total_farms": total_farms,
        "total_farmers": total_farmers,
        "total_cows": total_cows,
        "total_milk": float(total_milk),
        "average_per_cow": float(average_per_cow)
    }

# Milk production by date range
@app.get("/milk/by-date", response_model=List[MilkByDateSummary])
def get_milk_by_date(
    farm_id: Optional[int] = Query(None, description="Filter by farm ID"),
    farmer_id: Optional[int] = Query(None, description="Filter by farmer ID"),
    start_date: str = Query(
        ...,  # ... means required
        description="Start date in YYYY-MM-DD format",
        example="2025-08-01"
    ),
    end_date: str = Query(
        ...,  # ... means required
        description="End date in YYYY-MM-DD format",
        example="2025-08-31"
    ),
    db: Session = Depends(get_db)
):
    """
    Get milk production data broken down by date within a specified date range.
    """
    try:
        parsed_start_date = parse_date(start_date)
        parsed_end_date = parse_date(end_date)
    except HTTPException as e:
        raise e
    
    if not parsed_start_date or not parsed_end_date:
        raise HTTPException(
            status_code=400,
            detail="Both start_date and end_date are required"
        )

    # Rest of your existing query logic
    query = db.query(
        MilkRecord.date,
        func.sum(MilkRecord.liters).label("total_liters"),
        func.count(func.distinct(MilkRecord.cow_id)).label("cow_count")
    )
    
    # Apply filters carefully to avoid duplicate joins
    if farm_id or farmer_id:
        query = query.join(Cow, MilkRecord.cow_id == Cow.id)
        
        if farm_id:
            query = query.join(Farmer, Cow.farmer_id == Farmer.id)
            query = query.filter(Farmer.farm_id == farm_id)
        
        if farmer_id:
            # If we already joined Farmer for farm_id, don't join again
            if not farm_id:
                query = query.join(Farmer, Cow.farmer_id == Farmer.id)
            query = query.filter(Farmer.id == farmer_id)
    
    # Apply date range (required for this endpoint)
    query = query.filter(MilkRecord.date >= start_date)
    query = query.filter(MilkRecord.date <= end_date)
    
    # Group and order
    query = query.group_by(MilkRecord.date).order_by(MilkRecord.date)
    
    results = query.all()
    
    # If no results are found, return an empty list
    if not results:
        return []
    
    return [
        {
            "date": record.date,
            "total_liters": float(record.total_liters),
            "cow_count": record.cow_count
        }
        for record in results
    ]

# Recent activities endpoint
@app.get("/activities/recent", response_model=List[ActivitySummary])
def get_recent_activities(
    farm_id: Optional[int] = Query(None, description="Filter by farm ID"),
    farmer_id: Optional[int] = Query(None, description="Filter by farmer ID"),
    db: Session = Depends(get_db)
):
    """
    Get recent activities optionally filtered by farm or farmer.
    Returns activities ordered by creation date (newest first).
    """
    query = db.query(Activity).order_by(Activity.created_at.desc())
    
    if farm_id:
        query = query.join(Farmer).filter(Farmer.farm_id == farm_id)
    if farmer_id:
        query = query.filter(Activity.farmer_id == farmer_id)
    
    activities = query.all()
    
    result = []
    for activity in activities:
        # Get farmer name from users_user table through farms_farmer
        farmer_name_query = text("""
            SELECT u.first_name || ' ' || u.last_name as full_name
            FROM users_user u
            JOIN farms_farmer ff ON u.id = ff.user_id
            WHERE ff.id = :farmer_id
        """)
        
        try:
            farmer_name_result = db.execute(farmer_name_query, {"farmer_id": activity.farmer_id}).first()
            farmer_name = farmer_name_result[0] if farmer_name_result else "Unknown"
        except Exception:
            # Fallback to just showing the farmer ID if query fails
            farmer_name = f"Farmer #{activity.farmer_id}"
        
        result.append({
            "id": activity.id,
            "farmer_name": farmer_name,
            "description": activity.description,
            "created_at": activity.created_at
        })
    
    return result