from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from src.database import get_db

router = APIRouter()

@router.get("")
async def health_check(db: AsyncSession = Depends(get_db)):
    """Check system health"""
    try:
        # Test database connection
        await db.execute(text("SELECT 1"))
        return {"status": "healthy", "database": "connected"}
    except Exception as e:
        return {"status": "unhealthy", "database": "disconnected", "error": str(e)}

@router.get("/metrics")
async def get_metrics(db: AsyncSession = Depends(get_db)):
    """Get basic usage metrics"""
    try:
        # Get record count
        result = await db.execute(text("SELECT COUNT(*) FROM insurance_policies"))
        count = result.scalar()
        
        return {
            "total_policies": count,
            "database_status": "connected"
        }
    except Exception as e:
        return {"error": f"Failed to retrieve metrics: {str(e)}"}

@router.get("/data-summary")
async def get_data_summary(db: AsyncSession = Depends(get_db)):
    """Get database statistics"""
    try:
        result = await db.execute(text("""
            SELECT 
                COUNT(*) as total_policies,
                AVG(premium) as avg_premium,
                SUM(premium) as total_premium,
                MIN(insurance_period_start_date) as earliest_policy,
                MAX(insurance_period_end_date) as latest_policy
            FROM insurance_policies
        """))
        
        summary = result.fetchone()
        
        return {
            "total_policies": summary[0],
            "average_premium": float(summary[1]) if summary[1] else 0,
            "total_premium": float(summary[2]) if summary[2] else 0,
            "earliest_policy": summary[3],
            "latest_policy": summary[4]
        }
    except Exception as e:
        return {"error": f"Failed to retrieve data summary: {str(e)}"}