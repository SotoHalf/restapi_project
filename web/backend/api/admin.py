from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Optional
from datetime import datetime, timedelta
import random
from backend import auth

router = APIRouter(prefix="/api/admin", tags=["admin"])

# Verificar que el usuario es admin
async def verify_admin(current_user: dict = Depends(auth.get_current_user)):
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    return current_user

@router.get("/users")
async def get_all_users(
    admin: dict = Depends(verify_admin),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100)
):
    """Obtener todos los usuarios (solo admin)"""
    # Datos simulados de usuarios
    MOCK_USERS = [
        {
            "user_id": f"usr_{i:03d}",
            "username": f"user{i}",
            "email": f"user{i}@example.com",
            "role": "admin" if i == 0 else "user",
            "created_at": (datetime.now() - timedelta(days=random.randint(1, 365))).isoformat(),
            "last_login": (datetime.now() - timedelta(hours=random.randint(1, 72))).isoformat(),
            "meal_count": random.randint(5, 150),
            "status": "active"
        }
        for i in range(1, 51)
    ]
    
    # Simular paginación
    start = (page - 1) * limit
    end = start + limit
    
    return {
        "users": MOCK_USERS[start:end],
        "pagination": {
            "page": page,
            "limit": limit,
            "total": len(MOCK_USERS),
            "pages": (len(MOCK_USERS) + limit - 1) // limit
        }
    }

@router.get("/stats")
async def get_admin_stats(admin: dict = Depends(verify_admin)):
    """Obtener estadísticas de la plataforma (solo admin)"""
    current_time = datetime.now()
    
    # Datos simulados de estadísticas
    stats = {
        "platform": {
            "total_users": 154,
            "active_users_24h": 42,
            "total_meals_logged": 1284,
            "total_api_calls": 12560,
            "storage_used_mb": 247.5,
            "uptime_days": 15
        },
        "apis": {
            "themealdb": {
                "status": "healthy",
                "calls_today": 245,
                "success_rate": 98.2,
                "last_sync": (current_time - timedelta(minutes=30)).isoformat()
            },
            "openfoodfacts": {
                "status": "healthy",
                "calls_today": 187,
                "success_rate": 96.8,
                "last_sync": (current_time - timedelta(hours=1)).isoformat()
            }
        },
        "etl": {
            "active_jobs": 2,
            "total_jobs_today": 8,
            "success_rate": 100.0,
            "last_execution": (current_time - timedelta(minutes=45)).isoformat(),
            "next_scheduled": (current_time + timedelta(hours=6)).isoformat()
        },
        "performance": {
            "avg_response_time_ms": 142,
            "error_rate": 0.8,
            "requests_per_minute": 24.5
        }
    }
    
    return stats

@router.post("/etl/{source}/run")
async def run_etl_manual(
    source: str,
    admin: dict = Depends(verify_admin)
):
    """Ejecutar manualmente un proceso ETL (solo admin)"""
    valid_sources = ["themealdb", "openfoodfacts", "correlation"]
    
    if source not in valid_sources:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid source. Valid sources: {', '.join(valid_sources)}"
        )
    
    # Simular ejecución de ETL
    job_id = f"etl_{source}_{int(datetime.now().timestamp())}"
    
    return {
        "job_id": job_id,
        "source": source,
        "status": "running",
        "started_at": datetime.now().isoformat(),
        "estimated_completion": (datetime.now() + timedelta(seconds=random.randint(30, 180))).isoformat(),
        "message": f"ETL job for {source} started successfully"
    }

@router.get("/etl/history")
async def get_etl_history(
    admin: dict = Depends(verify_admin),
    limit: int = Query(20, ge=1, le=100)
):
    """Obtener historial de trabajos ETL (solo admin)"""
    # Historial simulado de ETL
    history = []
    for i in range(limit):
        hours_ago = random.randint(1, 168)  # Última semana
        source = random.choice(["themealdb", "openfoodfacts", "correlation"])
        status = random.choice(["completed", "completed", "failed"])  # 2/3 success rate
        
        history.append({
            "job_id": f"etl_{source}_{int((datetime.now() - timedelta(hours=hours_ago)).timestamp())}",
            "source": source,
            "status": status,
            "started_at": (datetime.now() - timedelta(hours=hours_ago)).isoformat(),
            "completed_at": (datetime.now() - timedelta(hours=hours_ago - 1)).isoformat() if status == "completed" else None,
            "records_processed": random.randint(50, 500),
            "error_message": "Rate limit exceeded" if status == "failed" else None
        })
    
    # Ordenar por fecha más reciente
    history.sort(key=lambda x: x["started_at"], reverse=True)
    
    # Calcular estadísticas
    total_jobs = len(history)
    completed_jobs = len([h for h in history if h["status"] == "completed"])
    
    return {
        "history": history,
        "statistics": {
            "total_jobs": total_jobs,
            "completed": completed_jobs,
            "failed": total_jobs - completed_jobs,
            "success_rate": round((completed_jobs / total_jobs) * 100, 1) if total_jobs > 0 else 0
        }
    }

@router.get("/logs")
async def get_system_logs(
    admin: dict = Depends(verify_admin),
    level: Optional[str] = Query(None, description="Filter by log level"),
    limit: int = Query(50, ge=1, le=500)
):
    """Obtener logs del sistema (solo admin)"""
    # Logs simulados
    log_levels = ["INFO", "WARNING", "ERROR", "DEBUG"]
    log_messages = [
        "User authentication successful",
        "ETL job started for themealdb",
        "API call to OpenFoodFacts completed",
        "Database connection established",
        "Rate limit warning for themealdb API",
        "User registered successfully",
        "Meal data synchronized",
        "Health score calculation completed",
        "Cache updated for meal categories",
        "Background task scheduled",
        "API key rotated",
        "Data backup initiated",
        "User session expired",
        "New ingredient added to database",
        "Correlation analysis finished"
    ]
    
    logs = []
    for i in range(limit):
        log_level = level if level else random.choice(log_levels)
        hours_ago = random.randint(0, 24)
        
        logs.append({
            "timestamp": (datetime.now() - timedelta(hours=hours_ago, minutes=random.randint(0, 59))).isoformat(),
            "level": log_level,
            "message": random.choice(log_messages),
            "source": random.choice(["auth", "etl", "api", "database", "analytics"]),
            "user_id": f"usr_{random.randint(1, 150):03d}" if random.random() > 0.5 else None
        })
    
    # Ordenar por timestamp
    logs.sort(key=lambda x: x["timestamp"], reverse=True)
    
    # Estadísticas de logs
    level_counts = {level: 0 for level in log_levels}
    for log in logs:
        level_counts[log["level"]] = level_counts.get(log["level"], 0) + 1
    
    return {
        "logs": logs,
        "statistics": {
            "total": len(logs),
            "by_level": level_counts,
            "time_range": {
                "oldest": logs[-1]["timestamp"] if logs else None,
                "newest": logs[0]["timestamp"] if logs else None
            }
        }
    }