#!/usr/bin/env python3
"""
Skrypt uruchamiający BugBot
"""

import asyncio
import logging
import signal
import sys
import os
from pathlib import Path
from typing import Optional

# Dodaj src do ścieżki
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from services.bugbot import BugBot
from services.bugbot.config import BugBotConfig


# Konfiguracja loggera
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('bugbot.log')
    ]
)

logger = logging.getLogger(__name__)


class BugBotRunner:
    """Runner dla BugBot"""
    
    def __init__(self):
        self.bugbot = None
        self.running = False
        
    async def start(self, config_path: Optional[str] = None):
        """Uruchamia BugBota"""
        try:
            # Załaduj konfigurację
            if config_path and os.path.exists(config_path):
                logger.info(f"Loading configuration from {config_path}")
                config = BugBotConfig.from_file(config_path)
            else:
                logger.info("Loading configuration from environment variables")
                config = BugBotConfig.from_env()
                
            # Waliduj konfigurację
            errors = config.validate()
            if errors:
                logger.error("Configuration errors:")
                for error in errors:
                    logger.error(f"  - {error}")
                return
                
            # Utwórz katalogi jeśli nie istnieją
            self._ensure_directories(config)
            
            # Wyświetl konfigurację (bez wrażliwych danych)
            logger.info("BugBot configuration:")
            logger.info(f"  Process interval: {config.process_interval}s")
            logger.info(f"  Log directories: {config.monitor_config.get('log_directories', [])}")
            logger.info(f"  Escalation threshold: {config.escalation_threshold}")
            
            # Utwórz i uruchom BugBota
            self.bugbot = BugBot(config)
            self.running = True
            
            logger.info("BugBot is starting...")
            await self.bugbot.start()
            
        except KeyboardInterrupt:
            logger.info("Received interrupt signal")
        except Exception as e:
            logger.error(f"Error running BugBot: {e}", exc_info=True)
        finally:
            await self.stop()
            
    async def stop(self):
        """Zatrzymuje BugBota"""
        if self.bugbot and self.running:
            logger.info("Stopping BugBot...")
            self.running = False
            await self.bugbot.stop()
            logger.info("BugBot stopped")
            
    def _ensure_directories(self, config: BugBotConfig):
        """Upewnia się że wymagane katalogi istnieją"""
        # Katalog dla storage
        storage_dir = os.path.dirname(config.bugs_storage_path)
        if storage_dir:
            os.makedirs(storage_dir, exist_ok=True)
            
        # Katalogi logów
        for log_dir in config.monitor_config.get('log_directories', []):
            os.makedirs(log_dir, exist_ok=True)
            

async def main():
    """Główna funkcja"""
    # Parsowanie argumentów
    import argparse
    parser = argparse.ArgumentParser(description='BugBot - Automatic Bug Detection and Management')
    parser.add_argument(
        '-c', '--config',
        help='Path to configuration file (JSON)',
        default=None
    )
    parser.add_argument(
        '--generate-config',
        help='Generate example configuration file',
        action='store_true'
    )
    
    args = parser.parse_args()
    
    # Generuj przykładową konfigurację
    if args.generate_config:
        generate_example_config()
        return
        
    # Uruchom BugBota
    runner = BugBotRunner()
    
    # Obsługa sygnałów
    def signal_handler(sig, frame):
        logger.info(f"Received signal {sig}")
        asyncio.create_task(runner.stop())
        
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    await runner.start(args.config)
    

def generate_example_config():
    """Generuje przykładowy plik konfiguracyjny"""
    example_config = {
        "process_interval": 10.0,
        "bugs_storage_path": "./data/bugs.json",
        "escalation_threshold": 10,
        "escalation_time_threshold": 3600,
        "bug_retention_period": 2592000,
        "default_assignee": "team-lead",
        "component_owners": {
            "api": "backend-dev",
            "frontend": "frontend-dev",
            "database": "dba",
            "auth": "security-team"
        },
        "monitor_config": {
            "log_directories": ["./logs", "/var/log/myapp"],
            "scan_interval": 10,
            "monitor_stdout": False,
            "custom_patterns": [
                {
                    "name": "custom_error",
                    "pattern": "CUSTOM_ERROR.*",
                    "severity": "high",
                    "category": "runtime"
                }
            ]
        },
        "analyzer_config": {
            "component_patterns": {
                "payment": ["payment", "stripe", "billing"],
                "user": ["user", "account", "profile"]
            }
        },
        "notification_config": {
            "rate_limit_window": 300,
            "slack": {
                "webhook_url": "https://hooks.slack.com/services/YOUR/WEBHOOK/URL",
                "channel": "#bugs",
                "enabled": True
            },
            "discord": {
                "webhook_url": "https://discord.com/api/webhooks/YOUR/WEBHOOK",
                "enabled": False
            },
            "email": {
                "smtp_server": "smtp.gmail.com",
                "smtp_port": 587,
                "username": "your-email@gmail.com",
                "password": "your-app-password",
                "from_email": "bugbot@example.com",
                "to_emails": ["dev-team@example.com"],
                "enabled": False
            },
            "teams": {
                "webhook_url": "https://outlook.office.com/webhook/YOUR/WEBHOOK",
                "enabled": False
            },
            "webhook": {
                "url": "https://your-api.com/bugbot/webhook",
                "headers": {
                    "Authorization": "Bearer YOUR_TOKEN"
                },
                "enabled": False
            }
        },
        "github_config": {
            "api_token": "YOUR_GITHUB_TOKEN",
            "repo_owner": "your-org",
            "repo_name": "your-repo"
        }
    }
    
    with open('bugbot-config.example.json', 'w') as f:
        import json
        json.dump(example_config, f, indent=2)
        
    print("Generated example configuration file: bugbot-config.example.json")
    print("\nTo use environment variables instead, set:")
    print("  BUGBOT_PROCESS_INTERVAL=10")
    print("  BUGBOT_LOG_DIRS=/path/to/logs")
    print("  BUGBOT_SLACK_WEBHOOK=https://hooks.slack.com/...")
    print("  BUGBOT_GITHUB_TOKEN=your-token")
    print("  # ... and other BUGBOT_* variables")
    

if __name__ == '__main__':
    asyncio.run(main())