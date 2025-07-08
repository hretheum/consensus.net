"""
Konfiguracja BugBot
"""

from dataclasses import dataclass, field
from datetime import timedelta
from typing import Dict, List, Any, Optional
import os
import json


@dataclass
class BugBotConfig:
    """
    Konfiguracja dla BugBot
    """
    
    # Ogólne ustawienia
    process_interval: float = 10.0  # Interwał przetwarzania błędów (sekundy)
    bugs_storage_path: str = "./data/bugs.json"
    
    # Eskalacja
    escalation_threshold: int = 10  # Liczba wystąpień do eskalacji
    escalation_time_threshold: float = 3600  # Czas w sekundach do eskalacji
    
    # Retencja danych
    bug_retention_period: timedelta = timedelta(days=30)
    
    # Przypisywanie błędów
    default_assignee: Optional[str] = None
    component_owners: Dict[str, str] = field(default_factory=dict)
    
    # Konfiguracje komponentów
    monitor_config: Dict[str, Any] = field(default_factory=dict)
    analyzer_config: Dict[str, Any] = field(default_factory=dict)
    notification_config: Dict[str, Any] = field(default_factory=dict)
    github_config: Optional[Dict[str, Any]] = None
    
    @classmethod
    def from_env(cls) -> 'BugBotConfig':
        """Tworzy konfigurację z zmiennych środowiskowych"""
        config = cls()
        
        # Ogólne ustawienia
        if os.getenv('BUGBOT_PROCESS_INTERVAL'):
            config.process_interval = float(os.getenv('BUGBOT_PROCESS_INTERVAL'))
        if os.getenv('BUGBOT_STORAGE_PATH'):
            config.bugs_storage_path = os.getenv('BUGBOT_STORAGE_PATH')
        if os.getenv('BUGBOT_DEFAULT_ASSIGNEE'):
            config.default_assignee = os.getenv('BUGBOT_DEFAULT_ASSIGNEE')
            
        # Eskalacja
        if os.getenv('BUGBOT_ESCALATION_THRESHOLD'):
            config.escalation_threshold = int(os.getenv('BUGBOT_ESCALATION_THRESHOLD'))
        if os.getenv('BUGBOT_ESCALATION_TIME'):
            config.escalation_time_threshold = float(os.getenv('BUGBOT_ESCALATION_TIME'))
            
        # Component owners
        if os.getenv('BUGBOT_COMPONENT_OWNERS'):
            try:
                config.component_owners = json.loads(os.getenv('BUGBOT_COMPONENT_OWNERS'))
            except:
                pass
                
        # Monitor config
        config.monitor_config = {
            'log_directories': os.getenv('BUGBOT_LOG_DIRS', './logs').split(','),
            'scan_interval': float(os.getenv('BUGBOT_SCAN_INTERVAL', '10')),
            'monitor_stdout': os.getenv('BUGBOT_MONITOR_STDOUT', 'false').lower() == 'true',
            'custom_patterns': []
        }
        
        # Analyzer config
        config.analyzer_config = {
            'component_patterns': {}
        }
        
        # Notification config
        config.notification_config = {
            'rate_limit_window': int(os.getenv('BUGBOT_RATE_LIMIT', '300'))
        }
        
        # Slack
        if os.getenv('BUGBOT_SLACK_WEBHOOK'):
            config.notification_config['slack'] = {
                'webhook_url': os.getenv('BUGBOT_SLACK_WEBHOOK'),
                'channel': os.getenv('BUGBOT_SLACK_CHANNEL', '#bugs'),
                'enabled': os.getenv('BUGBOT_SLACK_ENABLED', 'true').lower() == 'true'
            }
            
        # Discord
        if os.getenv('BUGBOT_DISCORD_WEBHOOK'):
            config.notification_config['discord'] = {
                'webhook_url': os.getenv('BUGBOT_DISCORD_WEBHOOK'),
                'enabled': os.getenv('BUGBOT_DISCORD_ENABLED', 'true').lower() == 'true'
            }
            
        # Email
        if os.getenv('BUGBOT_EMAIL_SMTP_SERVER'):
            config.notification_config['email'] = {
                'smtp_server': os.getenv('BUGBOT_EMAIL_SMTP_SERVER'),
                'smtp_port': int(os.getenv('BUGBOT_EMAIL_SMTP_PORT', '587')),
                'username': os.getenv('BUGBOT_EMAIL_USERNAME'),
                'password': os.getenv('BUGBOT_EMAIL_PASSWORD'),
                'from_email': os.getenv('BUGBOT_EMAIL_FROM'),
                'to_emails': os.getenv('BUGBOT_EMAIL_TO', '').split(','),
                'enabled': os.getenv('BUGBOT_EMAIL_ENABLED', 'true').lower() == 'true'
            }
            
        # Teams
        if os.getenv('BUGBOT_TEAMS_WEBHOOK'):
            config.notification_config['teams'] = {
                'webhook_url': os.getenv('BUGBOT_TEAMS_WEBHOOK'),
                'enabled': os.getenv('BUGBOT_TEAMS_ENABLED', 'true').lower() == 'true'
            }
            
        # Generic webhook
        if os.getenv('BUGBOT_WEBHOOK_URL'):
            config.notification_config['webhook'] = {
                'url': os.getenv('BUGBOT_WEBHOOK_URL'),
                'headers': json.loads(os.getenv('BUGBOT_WEBHOOK_HEADERS', '{}')),
                'enabled': os.getenv('BUGBOT_WEBHOOK_ENABLED', 'true').lower() == 'true'
            }
            
        # GitHub config
        if os.getenv('BUGBOT_GITHUB_TOKEN'):
            config.github_config = {
                'api_token': os.getenv('BUGBOT_GITHUB_TOKEN'),
                'repo_owner': os.getenv('BUGBOT_GITHUB_OWNER'),
                'repo_name': os.getenv('BUGBOT_GITHUB_REPO')
            }
            
        return config
        
    @classmethod
    def from_file(cls, file_path: str) -> 'BugBotConfig':
        """Tworzy konfigurację z pliku JSON"""
        with open(file_path, 'r') as f:
            data = json.load(f)
            
        config = cls()
        
        # Aktualizuj wartości z pliku
        for key, value in data.items():
            if hasattr(config, key):
                setattr(config, key, value)
                
        return config
        
    def to_dict(self) -> Dict[str, Any]:
        """Konwertuje konfigurację do słownika"""
        return {
            'process_interval': self.process_interval,
            'bugs_storage_path': self.bugs_storage_path,
            'escalation_threshold': self.escalation_threshold,
            'escalation_time_threshold': self.escalation_time_threshold,
            'bug_retention_period': self.bug_retention_period.total_seconds(),
            'default_assignee': self.default_assignee,
            'component_owners': self.component_owners,
            'monitor_config': self.monitor_config,
            'analyzer_config': self.analyzer_config,
            'notification_config': self._sanitize_notification_config(self.notification_config),
            'github_config': self._sanitize_github_config(self.github_config)
        }
        
    def _sanitize_notification_config(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Usuwa wrażliwe dane z konfiguracji powiadomień"""
        sanitized = config.copy()
        
        # Ukryj wrażliwe dane
        if 'slack' in sanitized and 'webhook_url' in sanitized['slack']:
            sanitized['slack']['webhook_url'] = '***'
        if 'discord' in sanitized and 'webhook_url' in sanitized['discord']:
            sanitized['discord']['webhook_url'] = '***'
        if 'email' in sanitized:
            if 'password' in sanitized['email']:
                sanitized['email']['password'] = '***'
            if 'username' in sanitized['email']:
                sanitized['email']['username'] = '***'
        if 'teams' in sanitized and 'webhook_url' in sanitized['teams']:
            sanitized['teams']['webhook_url'] = '***'
        if 'webhook' in sanitized and 'url' in sanitized['webhook']:
            sanitized['webhook']['url'] = '***'
            
        return sanitized
        
    def _sanitize_github_config(self, config: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """Usuwa wrażliwe dane z konfiguracji GitHub"""
        if not config:
            return None
            
        sanitized = config.copy()
        if 'api_token' in sanitized:
            sanitized['api_token'] = '***'
            
        return sanitized
        
    def save_to_file(self, file_path: str):
        """Zapisuje konfigurację do pliku JSON"""
        with open(file_path, 'w') as f:
            json.dump(self.to_dict(), f, indent=2)
            
    def validate(self) -> List[str]:
        """Waliduje konfigurację i zwraca listę błędów"""
        errors = []
        
        # Sprawdź podstawowe wartości
        if self.process_interval <= 0:
            errors.append("process_interval musi być większy od 0")
            
        if self.escalation_threshold <= 0:
            errors.append("escalation_threshold musi być większy od 0")
            
        if self.escalation_time_threshold <= 0:
            errors.append("escalation_time_threshold musi być większy od 0")
            
        # Sprawdź konfigurację monitoringu
        if not self.monitor_config.get('log_directories'):
            errors.append("Brak skonfigurowanych katalogów do monitorowania")
            
        # Sprawdź czy jest skonfigurowany przynajmniej jeden kanał powiadomień
        has_notification_channel = False
        for channel in ['slack', 'discord', 'email', 'teams', 'webhook']:
            if self.notification_config.get(channel, {}).get('enabled'):
                has_notification_channel = True
                break
                
        if not has_notification_channel:
            errors.append("Brak skonfigurowanych kanałów powiadomień")
            
        # Sprawdź konfigurację GitHub jeśli jest obecna
        if self.github_config:
            if not self.github_config.get('api_token'):
                errors.append("Brak tokenu API GitHub")
            if not self.github_config.get('repo_owner'):
                errors.append("Brak właściciela repozytorium GitHub")
            if not self.github_config.get('repo_name'):
                errors.append("Brak nazwy repozytorium GitHub")
                
        return errors