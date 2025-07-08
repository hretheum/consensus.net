"""
Przykład integracji BugBot przez system logowania
"""

import logging
import logging.handlers
from pathlib import Path

# === KONFIGURACJA LOGOWANIA ===

def setup_bugbot_logging(app_name="myapp"):
    """Konfiguruje logowanie kompatybilne z BugBot"""
    
    # Utwórz katalog logów
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    
    # Konfiguracja formattera
    formatter = logging.Formatter(
        '%(asctime)s %(levelname)s [%(name)s] %(filename)s:%(lineno)d - %(message)s'
    )
    
    # Handler dla plików z rotacją
    file_handler = logging.handlers.RotatingFileHandler(
        f'logs/{app_name}.log',
        maxBytes=10*1024*1024,  # 10MB
        backupCount=5
    )
    file_handler.setFormatter(formatter)
    file_handler.setLevel(logging.ERROR)
    
    # Handler dla błędów krytycznych
    error_handler = logging.handlers.RotatingFileHandler(
        f'logs/{app_name}_errors.log',
        maxBytes=5*1024*1024,  # 5MB
        backupCount=3
    )
    error_handler.setFormatter(formatter)
    error_handler.setLevel(logging.ERROR)
    
    # Konfiguracja głównego loggera
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    logger.addHandler(file_handler)
    logger.addHandler(error_handler)
    
    return logger


# === PRZYKŁAD UŻYCIA W APLIKACJI ===

# Flask
from flask import Flask, jsonify

app = Flask(__name__)
logger = setup_bugbot_logging("flask-app")

@app.route('/api/users/<int:user_id>')
def get_user(user_id):
    try:
        # Symulacja błędu
        if user_id == 0:
            raise ValueError("Invalid user ID")
            
        # Logika biznesowa
        user = fetch_user_from_db(user_id)
        return jsonify(user)
        
    except Exception as e:
        logger.error(f"Failed to get user {user_id}", exc_info=True)
        return jsonify({"error": "Internal server error"}), 500


# FastAPI
from fastapi import FastAPI, HTTPException
import uvicorn

fastapi_app = FastAPI()
logger = setup_bugbot_logging("fastapi-app")

@fastapi_app.get("/api/products/{product_id}")
async def get_product(product_id: int):
    try:
        # Symulacja różnych typów błędów
        if product_id < 0:
            raise ValueError("Product ID cannot be negative")
        elif product_id == 999:
            raise TimeoutError("Database connection timeout")
        elif product_id == 0:
            # Symulacja NoneType error
            product = None
            return {"name": product.name}  # AttributeError
            
        return {"id": product_id, "name": f"Product {product_id}"}
        
    except TimeoutError as e:
        logger.error(f"Timeout fetching product {product_id}: {e}")
        raise HTTPException(status_code=504, detail="Gateway timeout")
    except AttributeError as e:
        logger.error(f"NoneType error for product {product_id}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal error")
    except Exception as e:
        logger.critical(f"Unexpected error in product API", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


# Django
import logging
logger = logging.getLogger('django')

def process_payment(request):
    try:
        amount = request.POST.get('amount')
        if not amount:
            raise ValueError("Amount is required")
            
        # Proces płatności
        result = payment_gateway.charge(amount)
        
    except payment_gateway.PaymentError as e:
        logger.error(
            f"Payment failed for user {request.user.id}: {e}",
            extra={
                'user_id': request.user.id,
                'amount': amount,
                'ip_address': request.META.get('REMOTE_ADDR')
            }
        )
        return JsonResponse({"error": "Payment failed"}, status=402)


# === HELPER: Strukturalne logowanie błędów ===

class BugBotLogger:
    """Wrapper dla łatwiejszego logowania błędów w formacie przyjaznym dla BugBot"""
    
    def __init__(self, logger):
        self.logger = logger
        
    def log_error(self, error_type, component, message, **kwargs):
        """Loguje błąd w strukturalnym formacie"""
        error_data = {
            'error_type': error_type,
            'component': component,
            'message': message,
            **kwargs
        }
        
        self.logger.error(
            f"[{component.upper()}] {error_type}: {message} | {error_data}"
        )
        
    def log_database_error(self, operation, error, query=None):
        """Specjalizowane logowanie błędów bazy danych"""
        self.log_error(
            "DatabaseError",
            "database",
            f"Operation '{operation}' failed: {error}",
            operation=operation,
            query=query
        )
        
    def log_api_error(self, endpoint, status_code, error):
        """Specjalizowane logowanie błędów API"""
        self.log_error(
            f"HTTP_{status_code}",
            "api",
            f"Endpoint {endpoint} failed: {error}",
            endpoint=endpoint,
            status_code=status_code
        )


# Użycie structured logger
bugbot_logger = BugBotLogger(logger)

# Przykłady użycia
try:
    result = db.query("SELECT * FROM users WHERE id = ?", [user_id])
except Exception as e:
    bugbot_logger.log_database_error(
        operation="fetch_user",
        error=str(e),
        query="SELECT * FROM users"
    )
    
try:
    response = external_api.call("/payment/process", data)
except requests.HTTPError as e:
    bugbot_logger.log_api_error(
        endpoint="/payment/process",
        status_code=e.response.status_code,
        error=str(e)
    )