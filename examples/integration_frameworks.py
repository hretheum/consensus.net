"""
Przykłady integracji BugBot z popularnymi frameworkami i narzędziami
"""

# === SENTRY INTEGRATION ===

import sentry_sdk
from sentry_sdk.integrations.logging import LoggingIntegration
import logging

# Konfiguruj Sentry do wysyłania błędów również do logów
logging_integration = LoggingIntegration(
    level=logging.ERROR,        # Capture errors and above
    event_level=logging.ERROR   # Send errors as events
)

sentry_sdk.init(
    dsn="your-sentry-dsn",
    integrations=[logging_integration],
    before_send=lambda event, hint: log_to_bugbot(event, hint)
)

def log_to_bugbot(event, hint):
    """Hook Sentry do logowania błędów dla BugBot"""
    if 'exc_info' in hint:
        exc_type, exc_value, tb = hint['exc_info']
        logging.error(
            f"[SENTRY] {exc_type.__name__}: {exc_value}",
            exc_info=True,
            extra={
                'sentry_event_id': event.get('event_id'),
                'level': event.get('level'),
                'platform': event.get('platform'),
                'timestamp': event.get('timestamp')
            }
        )
    return event  # Kontynuuj wysyłanie do Sentry


# === PROMETHEUS + ALERTMANAGER ===
"""
# prometheus-rules.yml
groups:
  - name: bugbot_alerts
    rules:
      - alert: HighErrorRate
        expr: rate(app_errors_total[5m]) > 0.1
        for: 5m
        labels:
          severity: warning
          component: "{{ $labels.component }}"
        annotations:
          summary: "High error rate detected"
          description: "Error rate is {{ $value }} errors/sec"
          
      - alert: CriticalErrors
        expr: increase(app_critical_errors_total[1h]) > 5
        for: 1m
        labels:
          severity: critical
        annotations:
          summary: "Multiple critical errors detected"
"""

from prometheus_client import Counter, Histogram
import time

# Metryki Prometheus
error_counter = Counter('app_errors_total', 'Total errors', ['component', 'error_type'])
critical_counter = Counter('app_critical_errors_total', 'Critical errors')
request_duration = Histogram('request_duration_seconds', 'Request duration')

def track_error(component: str, error_type: str, severity: str = "high"):
    """Śledzi błąd w Prometheus i loguje dla BugBot"""
    error_counter.labels(component=component, error_type=error_type).inc()
    
    if severity == "critical":
        critical_counter.inc()
        
    # Log dla BugBot
    logging.error(
        f"[METRICS] {component}: {error_type}",
        extra={
            'component': component,
            'error_type': error_type,
            'severity': severity,
            'prometheus_metric': 'app_errors_total'
        }
    )


# === ELASTIC APM INTEGRATION ===

from elasticapm import Client
from elasticapm.handlers.logging import LoggingHandler

# Konfiguracja Elastic APM
apm_client = Client({
    'SERVICE_NAME': 'myapp',
    'SERVER_URL': 'http://localhost:8200',
    'ENVIRONMENT': 'production'
})

# Dodaj handler do przekazywania błędów do logów
handler = LoggingHandler(client=apm_client)
handler.setLevel(logging.ERROR)
logging.getLogger().addHandler(handler)

# Dekorator do śledzenia transakcji
from elasticapm import capture_span

@capture_span()
def process_order(order_id: int):
    try:
        # Logika przetwarzania
        if order_id < 0:
            raise ValueError("Invalid order ID")
    except Exception as e:
        # APM automatycznie złapie błąd
        # Dodatkowo loguj dla BugBot
        logging.error(
            f"Order processing failed: {e}",
            extra={
                'order_id': order_id,
                'apm_trace_id': apm_client.get_trace_id()
            }
        )
        raise


# === DATADOG INTEGRATION ===

from datadog import initialize, statsd
import logging

# Inicjalizacja Datadog
initialize(
    api_key='your-api-key',
    app_key='your-app-key'
)

class DatadogBugBotHandler(logging.Handler):
    """Custom handler wysyłający błędy do Datadog i BugBot"""
    
    def emit(self, record):
        if record.levelno >= logging.ERROR:
            # Wyślij metrykę do Datadog
            statsd.increment('app.errors', tags=[
                f'severity:{record.levelname.lower()}',
                f'component:{getattr(record, "component", "unknown")}',
                f'error_type:{record.name}'
            ])
            
            # Wyślij event do Datadog
            statsd.event(
                f'Error in {record.name}',
                record.getMessage(),
                alert_type='error' if record.levelno == logging.ERROR else 'warning',
                tags=[f'component:{getattr(record, "component", "unknown")}']
            )

# Dodaj handler
logger = logging.getLogger()
logger.addHandler(DatadogBugBotHandler())


# === DJANGO INTEGRATION ===

# settings.py
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'bugbot': {
            'format': '%(asctime)s %(levelname)s [%(name)s] %(pathname)s:%(lineno)d - %(message)s'
        }
    },
    'handlers': {
        'bugbot_file': {
            'level': 'ERROR',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': '/app/logs/django_errors.log',
            'maxBytes': 10485760,  # 10MB
            'backupCount': 5,
            'formatter': 'bugbot'
        },
        'bugbot_critical': {
            'level': 'CRITICAL',
            'class': 'logging.handlers.SMTPHandler',
            'mailhost': 'localhost',
            'fromaddr': 'bugbot@example.com',
            'toaddrs': ['admin@example.com'],
            'subject': 'CRITICAL ERROR in Django App'
        }
    },
    'loggers': {
        'django': {
            'handlers': ['bugbot_file'],
            'level': 'ERROR',
            'propagate': True,
        },
        'myapp': {
            'handlers': ['bugbot_file', 'bugbot_critical'],
            'level': 'WARNING',
        }
    }
}

# middleware.py
import logging
import traceback
from django.utils.deprecation import MiddlewareMixin

class BugBotErrorMiddleware(MiddlewareMixin):
    """Middleware do lepszego logowania błędów Django"""
    
    def process_exception(self, request, exception):
        logger = logging.getLogger('django.request')
        
        logger.error(
            f"Unhandled exception in view",
            exc_info=True,
            extra={
                'status_code': 500,
                'request_method': request.method,
                'request_path': request.path,
                'user_id': request.user.id if request.user.is_authenticated else None,
                'ip_address': self.get_client_ip(request),
                'user_agent': request.META.get('HTTP_USER_AGENT', ''),
                'exception_type': type(exception).__name__,
                'exception_message': str(exception)
            }
        )
        
    def get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip


# === FLASK INTEGRATION ===

from flask import Flask, g, request
import logging
from werkzeug.exceptions import HTTPException

app = Flask(__name__)

# Konfiguracja logowania
if not app.debug:
    file_handler = logging.handlers.RotatingFileHandler(
        'logs/flask_errors.log',
        maxBytes=10240000,
        backupCount=10
    )
    file_handler.setFormatter(logging.Formatter(
        '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
    ))
    file_handler.setLevel(logging.ERROR)
    app.logger.addHandler(file_handler)

@app.errorhandler(Exception)
def handle_exception(e):
    """Global error handler dla Flask"""
    # Obsłuż błędy HTTP inaczej
    if isinstance(e, HTTPException):
        return e
        
    # Log błędu dla BugBot
    app.logger.error(
        f"Unhandled exception: {e}",
        exc_info=True,
        extra={
            'url': request.url,
            'method': request.method,
            'ip': request.remote_addr,
            'user_agent': request.user_agent.string,
            'endpoint': request.endpoint,
            'view_args': request.view_args
        }
    )
    
    return {"error": "Internal server error"}, 500

@app.before_request
def before_request():
    g.start_time = time.time()
    
@app.after_request
def after_request(response):
    if hasattr(g, 'start_time'):
        duration = time.time() - g.start_time
        # Log slow requests
        if duration > 1.0:  # requests longer than 1 second
            app.logger.warning(
                f"Slow request detected",
                extra={
                    'duration': duration,
                    'url': request.url,
                    'method': request.method,
                    'status_code': response.status_code
                }
            )
    return response


# === SQLALCHEMY INTEGRATION ===

from sqlalchemy import event
from sqlalchemy.engine import Engine
import logging

logger = logging.getLogger('sqlalchemy.bugbot')

@event.listens_for(Engine, "handle_error")
def handle_db_exception(exception_context):
    """Przechwytuje błędy bazy danych"""
    logger.error(
        f"Database error occurred",
        exc_info=exception_context.original_exception,
        extra={
            'statement': str(exception_context.statement)[:500],
            'parameters': str(exception_context.parameters)[:200],
            'connection_invalidated': exception_context.connection_invalidated,
            'dialect': exception_context.dialect.name
        }
    )

# Logowanie wolnych zapytań
@event.listens_for(Engine, "before_cursor_execute")
def before_cursor_execute(conn, cursor, statement, parameters, context, executemany):
    conn.info.setdefault('query_start_time', []).append(time.time())

@event.listens_for(Engine, "after_cursor_execute")
def after_cursor_execute(conn, cursor, statement, parameters, context, executemany):
    total = time.time() - conn.info['query_start_time'].pop(-1)
    if total > 1.0:  # Zapytania dłuższe niż 1 sekunda
        logger.warning(
            f"Slow query detected",
            extra={
                'duration': total,
                'statement': statement[:500],
                'parameters': str(parameters)[:200]
            }
        )


# === PYTEST INTEGRATION ===

# conftest.py
import pytest
import logging
import json
from datetime import datetime

class BugBotTestReporter:
    """Raportuje błędy testów do BugBot"""
    
    def __init__(self):
        self.failed_tests = []
        
    def pytest_runtest_logreport(self, report):
        if report.failed:
            self.failed_tests.append({
                'test_name': report.nodeid,
                'stage': report.when,
                'duration': report.duration,
                'error_message': str(report.longrepr),
                'timestamp': datetime.now().isoformat()
            })
            
    def pytest_sessionfinish(self, session, exitstatus):
        if self.failed_tests:
            # Log wszystkie błędy testów
            for test in self.failed_tests:
                logging.error(
                    f"Test failed: {test['test_name']}",
                    extra={
                        'test_stage': test['stage'],
                        'duration': test['duration'],
                        'error': test['error_message'][:500]
                    }
                )
            
            # Zapisz raport
            with open('logs/test_failures.json', 'w') as f:
                json.dump(self.failed_tests, f, indent=2)

def pytest_configure(config):
    config.pluginmanager.register(BugBotTestReporter())


# === AWS LAMBDA INTEGRATION ===

import json
import logging
import os
from functools import wraps

logger = logging.getLogger()
logger.setLevel(logging.ERROR)

def bugbot_lambda_handler(func):
    """Dekorator dla Lambda handlers z integracją BugBot"""
    
    @wraps(func)
    def wrapper(event, context):
        try:
            # Log request
            logger.info(f"Lambda invoked: {context.function_name}")
            
            # Wywołaj funkcję
            result = func(event, context)
            
            return result
            
        except Exception as e:
            # Log błędu z kontekstem Lambda
            logger.error(
                f"Lambda execution failed",
                exc_info=True,
                extra={
                    'function_name': context.function_name,
                    'function_version': context.function_version,
                    'request_id': context.aws_request_id,
                    'remaining_time': context.get_remaining_time_in_millis(),
                    'memory_limit': context.memory_limit_in_mb,
                    'event': json.dumps(event)[:500]
                }
            )
            
            # Re-raise dla Lambda
            raise
            
    return wrapper

# Użycie
@bugbot_lambda_handler
def lambda_handler(event, context):
    # Twoja logika
    if 'error' in event:
        raise ValueError("Simulated error")
    
    return {
        'statusCode': 200,
        'body': json.dumps('Success')
    }