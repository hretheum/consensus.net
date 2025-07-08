"""
Przykład integracji z BugBot przez API
"""

import aiohttp
import asyncio
from typing import Dict, Any, Optional
import logging
from datetime import datetime


class BugBotAPIClient:
    """Klient do komunikacji z BugBot API"""
    
    def __init__(self, base_url: str = "http://localhost:8000/api/bugbot"):
        self.base_url = base_url
        self.session = None
        
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
            
    async def report_error(self, error_data: Dict[str, Any]) -> bool:
        """Zgłasza błąd bezpośrednio do BugBot"""
        try:
            # Możesz utworzyć custom endpoint w BugBot API
            async with self.session.post(
                f"{self.base_url}/report",
                json=error_data
            ) as resp:
                return resp.status == 200
        except:
            return False
            
    async def get_bug_stats(self) -> Optional[Dict[str, Any]]:
        """Pobiera statystyki błędów"""
        try:
            async with self.session.get(f"{self.base_url}/stats") as resp:
                if resp.status == 200:
                    return await resp.json()
        except:
            return None
            
    async def check_similar_bugs(self, error_message: str) -> list:
        """Sprawdza czy podobny błąd już istnieje"""
        try:
            async with self.session.get(
                f"{self.base_url}/bugs",
                params={"search": error_message[:50]}
            ) as resp:
                if resp.status == 200:
                    return await resp.json()
        except:
            return []


# === MIDDLEWARE DLA AUTOMATYCZNEGO RAPORTOWANIA ===

# FastAPI Middleware
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
import traceback

app = FastAPI()

class BugBotMiddleware:
    """Middleware automatycznie raportujący błędy do BugBot"""
    
    def __init__(self, app: FastAPI, bugbot_url: str = "http://localhost:8000/api/bugbot"):
        self.app = app
        self.bugbot_client = BugBotAPIClient(bugbot_url)
        
    async def __call__(self, request: Request, call_next):
        try:
            response = await call_next(request)
            return response
            
        except Exception as e:
            # Przygotuj dane błędu
            error_data = {
                "timestamp": datetime.now().isoformat(),
                "endpoint": str(request.url),
                "method": request.method,
                "error_type": type(e).__name__,
                "error_message": str(e),
                "stack_trace": traceback.format_exc(),
                "request_id": request.headers.get("X-Request-ID"),
                "user_agent": request.headers.get("User-Agent"),
                "ip_address": request.client.host if request.client else None
            }
            
            # Raportuj do BugBot asynchronicznie
            asyncio.create_task(self._report_to_bugbot(error_data))
            
            # Zwróć odpowiedź błędu
            return JSONResponse(
                status_code=500,
                content={"error": "Internal server error", "request_id": error_data["request_id"]}
            )
            
    async def _report_to_bugbot(self, error_data: Dict[str, Any]):
        """Raportuje błąd do BugBot w tle"""
        async with self.bugbot_client as client:
            await client.report_error(error_data)


# Użycie middleware
app.add_middleware(BugBotMiddleware)


# === DEKORATOR DLA FUNKCJI ===

from functools import wraps
import inspect

def bugbot_monitor(component: str = "unknown", severity: str = "high"):
    """Dekorator monitorujący błędy w funkcjach"""
    
    def decorator(func):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                # Log błędu
                logging.error(
                    f"[{component.upper()}] Error in {func.__name__}: {e}",
                    exc_info=True,
                    extra={
                        "component": component,
                        "function": func.__name__,
                        "severity": severity,
                        "args": str(args)[:100],
                        "kwargs": str(kwargs)[:100]
                    }
                )
                raise
                
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                # Log błędu
                logging.error(
                    f"[{component.upper()}] Error in {func.__name__}: {e}",
                    exc_info=True,
                    extra={
                        "component": component,
                        "function": func.__name__,
                        "severity": severity,
                        "args": str(args)[:100],
                        "kwargs": str(kwargs)[:100]
                    }
                )
                raise
                
        return async_wrapper if inspect.iscoroutinefunction(func) else sync_wrapper
    return decorator


# Przykład użycia dekoratora
@bugbot_monitor(component="payment", severity="critical")
async def process_payment(user_id: int, amount: float):
    """Proces płatności z automatycznym monitorowaniem"""
    if amount <= 0:
        raise ValueError("Invalid payment amount")
        
    # Logika płatności...
    return {"status": "success", "transaction_id": "12345"}


@bugbot_monitor(component="database", severity="high")
def get_user_from_db(user_id: int):
    """Pobieranie użytkownika z monitorowaniem"""
    if user_id == 0:
        raise ValueError("Invalid user ID")
        
    # Symulacja błędu bazy danych
    if user_id == 999:
        raise ConnectionError("Database connection lost")
        
    return {"id": user_id, "name": f"User {user_id}"}


# === INTEGRACJA Z CELERY ===

from celery import Celery, Task
from celery.signals import task_failure

celery_app = Celery('myapp')

class BugBotTask(Task):
    """Bazowa klasa zadań Celery z integracją BugBot"""
    
    def on_failure(self, exc, task_id, args, kwargs, einfo):
        """Wywoływane gdy zadanie się nie powiedzie"""
        error_data = {
            "task_name": self.name,
            "task_id": task_id,
            "error_type": type(exc).__name__,
            "error_message": str(exc),
            "stack_trace": str(einfo),
            "args": str(args)[:200],
            "kwargs": str(kwargs)[:200],
            "timestamp": datetime.now().isoformat()
        }
        
        # Log do pliku
        logging.error(
            f"[CELERY] Task {self.name} failed: {exc}",
            extra=error_data
        )
        
        # Opcjonalnie: raportuj przez API
        # asyncio.create_task(report_to_bugbot_api(error_data))


@celery_app.task(base=BugBotTask, bind=True)
def send_email_task(self, user_id: int, subject: str, body: str):
    """Przykładowe zadanie Celery z monitorowaniem"""
    try:
        # Logika wysyłania emaila
        if not user_id:
            raise ValueError("User ID is required")
            
        # Symulacja błędu
        if user_id == 666:
            raise ConnectionError("SMTP server unreachable")
            
        return {"status": "sent", "user_id": user_id}
        
    except Exception as e:
        # Celery automatycznie wywoła on_failure
        raise


# === WEBHOOK HANDLER ===

@app.post("/webhooks/error-report")
async def receive_error_webhook(request: Request):
    """Endpoint do odbierania błędów z innych systemów"""
    try:
        data = await request.json()
        
        # Przekształć do formatu logu
        error_message = f"""
        External Error Report:
        System: {data.get('system', 'unknown')}
        Error: {data.get('error_type', 'unknown')} - {data.get('message', 'no message')}
        Severity: {data.get('severity', 'medium')}
        Timestamp: {data.get('timestamp', datetime.now().isoformat())}
        Details: {data.get('details', {})}
        """
        
        # Log błędu - BugBot go wykryje
        if data.get('severity') == 'critical':
            logging.critical(error_message)
        else:
            logging.error(error_message)
            
        return {"status": "received", "message": "Error logged for BugBot processing"}
        
    except Exception as e:
        logging.error(f"Failed to process error webhook: {e}")
        return {"status": "error"}, 500


# === HEALTH CHECK Z INTEGRACJĄ ===

@app.get("/health")
async def health_check():
    """Health check z informacjami o błędach"""
    async with BugBotAPIClient() as client:
        stats = await client.get_bug_stats()
        
        health_status = {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "error_monitoring": {
                "enabled": True,
                "recent_errors": stats.get("total_bugs", 0) if stats else "unknown",
                "critical_errors": stats.get("by_severity", {}).get("critical", 0) if stats else "unknown"
            }
        }
        
        # Ostrzeżenie jeśli za dużo błędów krytycznych
        if stats and stats.get("by_severity", {}).get("critical", 0) > 5:
            health_status["status"] = "degraded"
            health_status["warning"] = "High number of critical errors detected"
            
        return health_status