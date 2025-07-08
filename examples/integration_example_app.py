"""
Przykładowa aplikacja z pełną integracją BugBot
"""

from fastapi import FastAPI, HTTPException, Request
import logging
import logging.handlers
from datetime import datetime
import asyncio
from typing import Optional
from pydantic import BaseModel
import random

# === KROK 1: KONFIGURACJA LOGOWANIA ===

# Utwórz katalog logów
import os
os.makedirs("logs", exist_ok=True)

# Skonfiguruj logowanie do pliku
logger = logging.getLogger("myapp")
logger.setLevel(logging.INFO)

# Handler dla błędów - to czyta BugBot
error_handler = logging.handlers.RotatingFileHandler(
    'logs/app_errors.log',
    maxBytes=10*1024*1024,  # 10MB
    backupCount=5
)
error_handler.setLevel(logging.ERROR)
error_handler.setFormatter(logging.Formatter(
    '%(asctime)s %(levelname)s [%(name)s] %(filename)s:%(lineno)d - %(message)s'
))
logger.addHandler(error_handler)

# Handler dla wszystkich logów
all_handler = logging.handlers.RotatingFileHandler(
    'logs/app.log',
    maxBytes=10*1024*1024,
    backupCount=3
)
all_handler.setFormatter(logging.Formatter(
    '%(asctime)s %(levelname)s [%(name)s] - %(message)s'
))
logger.addHandler(all_handler)

# === KROK 2: APLIKACJA Z PRZYKŁADOWYMI BŁĘDAMI ===

app = FastAPI(title="MyApp with BugBot Integration")

# Symulowana baza danych
fake_db = {
    "users": {
        1: {"id": 1, "name": "Alice", "email": "alice@example.com"},
        2: {"id": 2, "name": "Bob", "email": "bob@example.com"}
    },
    "orders": {
        101: {"id": 101, "user_id": 1, "total": 99.99, "status": "pending"},
        102: {"id": 102, "user_id": 2, "total": 149.99, "status": "completed"}
    }
}

# === KROK 3: MIDDLEWARE DLA AUTOMATYCZNEGO LOGOWANIA BŁĘDÓW ===

@app.middleware("http")
async def bugbot_error_middleware(request: Request, call_next):
    """Middleware który automatycznie loguje wszystkie błędy"""
    try:
        response = await call_next(request)
        
        # Log wolnych requestów
        if hasattr(request.state, "start_time"):
            duration = datetime.now().timestamp() - request.state.start_time
            if duration > 1.0:  # Requesty dłuższe niż 1 sekunda
                logger.warning(
                    f"Slow request detected",
                    extra={
                        "component": "api",
                        "endpoint": str(request.url),
                        "method": request.method,
                        "duration": duration
                    }
                )
        
        return response
        
    except Exception as e:
        # Loguj błąd z pełnym kontekstem
        logger.error(
            f"Unhandled exception in {request.method} {request.url.path}",
            exc_info=True,
            extra={
                "component": "api",
                "endpoint": str(request.url),
                "method": request.method,
                "client_ip": request.client.host if request.client else None,
                "user_agent": request.headers.get("user-agent"),
                "request_id": request.headers.get("x-request-id", "unknown")
            }
        )
        raise

@app.on_event("startup")
async def startup_event():
    logger.info("Application starting up...")

# === KROK 4: PRZYKŁADOWE ENDPOINTY Z RÓŻNYMI BŁĘDAMI ===

class OrderRequest(BaseModel):
    user_id: int
    items: list[str]
    payment_method: str

@app.get("/")
async def root():
    """Health check endpoint"""
    return {"status": "healthy", "service": "MyApp", "bugbot": "integrated"}

@app.get("/api/users/{user_id}")
async def get_user(user_id: int):
    """Endpoint który może generować różne błędy"""
    try:
        # Symulacja różnych błędów
        if user_id == 0:
            # ValueError - będzie złapany przez BugBot
            raise ValueError("User ID cannot be zero")
            
        if user_id == 666:
            # Symulacja timeout
            raise TimeoutError("Database connection timeout after 30s")
            
        if user_id == 999:
            # NoneType error
            user = None
            return {"name": user.name}  # AttributeError
            
        # Normalna logika
        user = fake_db["users"].get(user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
            
        logger.info(f"User {user_id} retrieved successfully")
        return user
        
    except HTTPException:
        raise  # Re-raise HTTP exceptions
    except Exception as e:
        # Log innych błędów
        logger.error(
            f"Failed to get user {user_id}: {type(e).__name__}",
            exc_info=True,
            extra={
                "component": "users",
                "operation": "get_user",
                "user_id": user_id,
                "error_type": type(e).__name__
            }
        )
        raise HTTPException(status_code=500, detail="Internal server error")

@app.post("/api/orders")
async def create_order(order: OrderRequest):
    """Endpoint do tworzenia zamówień"""
    try:
        # Walidacja
        if not order.items:
            raise ValueError("Order must contain at least one item")
            
        if order.payment_method not in ["card", "paypal", "transfer"]:
            raise ValueError(f"Invalid payment method: {order.payment_method}")
            
        # Symulacja błędu płatności
        if order.payment_method == "card" and random.random() < 0.1:
            # 10% szans na błąd płatności
            raise Exception("Payment gateway timeout - Stripe API not responding")
            
        # Symulacja błędu bazy danych
        if random.random() < 0.05:
            # 5% szans na błąd DB
            raise ConnectionError("Lost connection to PostgreSQL database")
            
        # Tworzenie zamówienia
        order_id = random.randint(1000, 9999)
        logger.info(
            f"Order {order_id} created successfully",
            extra={
                "component": "orders",
                "user_id": order.user_id,
                "items_count": len(order.items),
                "payment_method": order.payment_method
            }
        )
        
        return {
            "order_id": order_id,
            "status": "created",
            "estimated_delivery": "2-3 days"
        }
        
    except ValueError as e:
        # Błędy walidacji
        logger.warning(
            f"Order validation failed: {e}",
            extra={
                "component": "orders",
                "error_type": "validation",
                "user_id": order.user_id
            }
        )
        raise HTTPException(status_code=400, detail=str(e))
        
    except Exception as e:
        # Krytyczne błędy
        logger.critical(
            f"Critical error in order processing",
            exc_info=True,
            extra={
                "component": "orders",
                "error_type": type(e).__name__,
                "user_id": order.user_id,
                "payment_method": order.payment_method,
                "severity": "critical"  # BugBot zwróci na to uwagę
            }
        )
        raise HTTPException(status_code=500, detail="Order processing failed")

@app.get("/api/reports/daily")
async def generate_daily_report():
    """Endpoint który może generować błędy performance"""
    try:
        start_time = datetime.now()
        
        # Symulacja długiej operacji
        await asyncio.sleep(2)  # BugBot wykryje jako slow request
        
        # Symulacja błędu pamięci
        if random.random() < 0.1:
            # Próba alokacji dużej ilości pamięci
            large_data = [0] * (10**9)  # MemoryError
            
        duration = (datetime.now() - start_time).total_seconds()
        
        logger.info(
            f"Daily report generated in {duration}s",
            extra={
                "component": "reports",
                "report_type": "daily",
                "duration": duration
            }
        )
        
        return {
            "report_id": f"daily-{datetime.now().strftime('%Y%m%d')}",
            "status": "completed",
            "duration": duration
        }
        
    except MemoryError as e:
        logger.error(
            "Out of memory while generating report",
            exc_info=True,
            extra={
                "component": "reports",
                "severity": "critical",
                "error_type": "memory"
            }
        )
        raise HTTPException(status_code=507, detail="Insufficient storage")

# === KROK 5: CUSTOM ERROR HANDLER ===

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Globalny handler błędów - upewnia się że wszystko jest logowane"""
    logger.error(
        f"Unhandled exception: {type(exc).__name__}",
        exc_info=True,
        extra={
            "component": "global_handler",
            "url": str(request.url),
            "method": request.method,
            "exception_type": type(exc).__name__
        }
    )
    
    return {
        "error": "Internal server error",
        "message": "An unexpected error occurred",
        "request_id": request.headers.get("x-request-id", "unknown")
    }

# === KROK 6: HEALTH CHECK Z INTEGRACJĄ BUGBOT ===

@app.get("/health")
async def health_check():
    """Health check który może sprawdzić status BugBot"""
    try:
        # Opcjonalnie: sprawdź czy BugBot działa
        # async with aiohttp.ClientSession() as session:
        #     async with session.get("http://localhost:8000/api/bugbot/status") as resp:
        #         bugbot_status = await resp.json()
        
        return {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "services": {
                "api": "operational",
                "database": "operational",
                "bugbot": "monitoring"  # lub bugbot_status
            }
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {"status": "unhealthy", "error": str(e)}

# === KROK 7: GENERATOR TESTOWYCH BŁĘDÓW (do demonstracji) ===

@app.post("/test/generate-errors")
async def generate_test_errors():
    """Endpoint do generowania różnych błędów dla testowania BugBot"""
    errors_generated = []
    
    # 1. Database error
    try:
        raise ConnectionError("PostgreSQL connection refused on port 5432")
    except Exception as e:
        logger.error("Test database error", exc_info=True)
        errors_generated.append("database_error")
    
    # 2. Authentication error
    try:
        raise PermissionError("Invalid API key provided")
    except Exception as e:
        logger.error("Test auth error", exc_info=True, extra={"component": "auth"})
        errors_generated.append("auth_error")
    
    # 3. Performance warning
    logger.warning(
        "Slow query detected",
        extra={
            "component": "database",
            "query": "SELECT * FROM large_table",
            "duration": 5.2
        }
    )
    errors_generated.append("performance_warning")
    
    # 4. Critical business logic error
    logger.critical(
        "Payment processing failed - customer charged but order not created",
        extra={
            "component": "payment",
            "order_id": "TEST-123",
            "amount": 99.99,
            "severity": "critical"
        }
    )
    errors_generated.append("critical_payment_error")
    
    return {
        "message": "Test errors generated",
        "errors": errors_generated,
        "note": "Check BugBot dashboard for detected errors"
    }

if __name__ == "__main__":
    import uvicorn
    
    print("🚀 Starting MyApp with BugBot integration...")
    print("📁 Logs will be written to: ./logs/")
    print("🐛 BugBot will monitor: ./logs/app_errors.log")
    print("\nTo start BugBot:")
    print("  export BUGBOT_LOG_DIRS=./logs")
    print("  python src/services/bugbot/run_bugbot.py")
    
    uvicorn.run(app, host="0.0.0.0", port=8001)