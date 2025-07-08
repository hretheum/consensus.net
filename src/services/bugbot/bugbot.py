"""
Główna klasa BugBot - koordynuje monitorowanie, analizę i raportowanie błędów
"""

import asyncio
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
import json

from .monitor import ErrorMonitor
from .analyzer import ErrorAnalyzer
from .notifier import NotificationManager
from .github_integration import GitHubIntegration
from .config import BugBotConfig


@dataclass
class Bug:
    """Reprezentacja wykrytego błędu"""
    id: str
    title: str
    description: str
    severity: str  # critical, high, medium, low
    category: str  # runtime, syntax, performance, security
    component: str
    timestamp: datetime
    stack_trace: Optional[str] = None
    frequency: int = 1
    first_seen: datetime = field(default_factory=datetime.now)
    last_seen: datetime = field(default_factory=datetime.now)
    status: str = "new"  # new, assigned, in_progress, resolved
    assigned_to: Optional[str] = None
    github_issue_id: Optional[int] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


class BugBot:
    """
    Główny orchestrator systemu BugBot
    """
    
    def __init__(self, config: BugBotConfig):
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # Inicjalizacja komponentów
        self.monitor = ErrorMonitor(config.monitor_config)
        self.analyzer = ErrorAnalyzer(config.analyzer_config)
        self.notifier = NotificationManager(config.notification_config)
        self.github = GitHubIntegration(config.github_config) if config.github_config else None
        
        # Cache błędów
        self.bugs_cache: Dict[str, Bug] = {}
        self.running = False
        
    async def start(self):
        """Uruchamia BugBota"""
        self.logger.info("Starting BugBot...")
        self.running = True
        
        # Uruchom wszystkie komponenty
        await asyncio.gather(
            self.monitor.start(),
            self._process_loop(),
            self._cleanup_loop()
        )
        
    async def stop(self):
        """Zatrzymuje BugBota"""
        self.logger.info("Stopping BugBot...")
        self.running = False
        await self.monitor.stop()
        
    async def _process_loop(self):
        """Główna pętla przetwarzania błędów"""
        while self.running:
            try:
                # Pobierz wykryte błędy z monitora
                errors = await self.monitor.get_errors()
                
                for error in errors:
                    await self._process_error(error)
                    
                await asyncio.sleep(self.config.process_interval)
                
            except Exception as e:
                self.logger.error(f"Error in process loop: {e}")
                await asyncio.sleep(5)
                
    async def _process_error(self, error_data: Dict[str, Any]):
        """Przetwarza pojedynczy błąd"""
        try:
            # Analizuj błąd
            analysis = await self.analyzer.analyze(error_data)
            
            # Sprawdź czy błąd już istnieje
            bug_id = self._generate_bug_id(analysis)
            
            if bug_id in self.bugs_cache:
                # Aktualizuj istniejący błąd
                bug = self.bugs_cache[bug_id]
                bug.frequency += 1
                bug.last_seen = datetime.now()
                
                # Sprawdź czy należy eskalować
                if self._should_escalate(bug):
                    await self._escalate_bug(bug)
            else:
                # Utwórz nowy błąd
                bug = self._create_bug(analysis, error_data)
                self.bugs_cache[bug_id] = bug
                
                # Obsłuż nowy błąd
                await self._handle_new_bug(bug)
                
        except Exception as e:
            self.logger.error(f"Error processing error: {e}")
            
    def _generate_bug_id(self, analysis: Dict[str, Any]) -> str:
        """Generuje unikalny ID dla błędu"""
        # Używamy kombinacji kategorii, komponentu i skrótu opisu
        import hashlib
        key = f"{analysis['category']}:{analysis['component']}:{analysis['title']}"
        return hashlib.md5(key.encode()).hexdigest()[:12]
        
    def _create_bug(self, analysis: Dict[str, Any], error_data: Dict[str, Any]) -> Bug:
        """Tworzy nowy obiekt Bug"""
        return Bug(
            id=self._generate_bug_id(analysis),
            title=analysis['title'],
            description=analysis['description'],
            severity=analysis['severity'],
            category=analysis['category'],
            component=analysis['component'],
            timestamp=datetime.now(),
            stack_trace=error_data.get('stack_trace'),
            metadata=analysis.get('metadata', {})
        )
        
    async def _handle_new_bug(self, bug: Bug):
        """Obsługuje nowo wykryty błąd"""
        self.logger.info(f"New bug detected: {bug.title} (severity: {bug.severity})")
        
        # Przypisz do odpowiedniego dewelopera
        bug.assigned_to = await self._assign_developer(bug)
        
        # Utwórz issue w GitHub (jeśli skonfigurowane)
        if self.github and bug.severity in ['critical', 'high']:
            issue_id = await self.github.create_issue(bug)
            bug.github_issue_id = issue_id
            
        # Wyślij powiadomienia
        await self.notifier.notify_new_bug(bug)
        
        # Zapisz do bazy danych/pliku
        await self._persist_bug(bug)
        
    async def _escalate_bug(self, bug: Bug):
        """Eskaluje błąd jeśli występuje zbyt często"""
        self.logger.warning(f"Escalating bug: {bug.title} (frequency: {bug.frequency})")
        
        # Zwiększ priorytet
        if bug.severity == 'low':
            bug.severity = 'medium'
        elif bug.severity == 'medium':
            bug.severity = 'high'
        elif bug.severity == 'high':
            bug.severity = 'critical'
            
        # Wyślij powiadomienie o eskalacji
        await self.notifier.notify_escalation(bug)
        
    def _should_escalate(self, bug: Bug) -> bool:
        """Sprawdza czy błąd powinien być eskalowany"""
        # Eskaluj jeśli błąd występuje często
        if bug.frequency > self.config.escalation_threshold:
            return True
            
        # Eskaluj jeśli błąd trwa długo
        duration = datetime.now() - bug.first_seen
        if duration.total_seconds() > self.config.escalation_time_threshold:
            return True
            
        return False
        
    async def _assign_developer(self, bug: Bug) -> Optional[str]:
        """Przypisuje błąd do odpowiedniego dewelopera"""
        # Prosta logika przypisywania na podstawie komponentu
        component_owners = self.config.component_owners
        
        if bug.component in component_owners:
            return component_owners[bug.component]
            
        # Domyślnie przypisz do team lead
        return self.config.default_assignee
        
    async def _persist_bug(self, bug: Bug):
        """Zapisuje błąd do trwałego storage"""
        # TODO: Implementacja zapisu do bazy danych
        # Na razie zapisujemy do pliku JSON
        bugs_file = self.config.bugs_storage_path
        
        try:
            # Wczytaj istniejące błędy
            try:
                with open(bugs_file, 'r') as f:
                    bugs_data = json.load(f)
            except FileNotFoundError:
                bugs_data = {}
                
            # Dodaj/zaktualizuj błąd
            bugs_data[bug.id] = {
                'id': bug.id,
                'title': bug.title,
                'description': bug.description,
                'severity': bug.severity,
                'category': bug.category,
                'component': bug.component,
                'timestamp': bug.timestamp.isoformat(),
                'frequency': bug.frequency,
                'first_seen': bug.first_seen.isoformat(),
                'last_seen': bug.last_seen.isoformat(),
                'status': bug.status,
                'assigned_to': bug.assigned_to,
                'github_issue_id': bug.github_issue_id,
                'metadata': bug.metadata
            }
            
            # Zapisz
            with open(bugs_file, 'w') as f:
                json.dump(bugs_data, f, indent=2)
                
        except Exception as e:
            self.logger.error(f"Failed to persist bug: {e}")
            
    async def _cleanup_loop(self):
        """Pętla czyszczenia starych/rozwiązanych błędów"""
        while self.running:
            try:
                # Czyszczenie co godzinę
                await asyncio.sleep(3600)
                
                # Usuń rozwiązane błędy starsze niż X dni
                cutoff_date = datetime.now() - self.config.bug_retention_period
                
                bugs_to_remove = []
                for bug_id, bug in self.bugs_cache.items():
                    if bug.status == 'resolved' and bug.last_seen < cutoff_date:
                        bugs_to_remove.append(bug_id)
                        
                for bug_id in bugs_to_remove:
                    del self.bugs_cache[bug_id]
                    
                self.logger.info(f"Cleaned up {len(bugs_to_remove)} resolved bugs")
                
            except Exception as e:
                self.logger.error(f"Error in cleanup loop: {e}")
                
    async def get_bug_stats(self) -> Dict[str, Any]:
        """Zwraca statystyki błędów"""
        stats = {
            'total_bugs': len(self.bugs_cache),
            'by_severity': {},
            'by_category': {},
            'by_status': {},
            'by_component': {},
            'recent_bugs': []
        }
        
        for bug in self.bugs_cache.values():
            # Zliczanie według severity
            stats['by_severity'][bug.severity] = stats['by_severity'].get(bug.severity, 0) + 1
            
            # Zliczanie według kategorii
            stats['by_category'][bug.category] = stats['by_category'].get(bug.category, 0) + 1
            
            # Zliczanie według statusu
            stats['by_status'][bug.status] = stats['by_status'].get(bug.status, 0) + 1
            
            # Zliczanie według komponentu
            stats['by_component'][bug.component] = stats['by_component'].get(bug.component, 0) + 1
            
        # Ostatnie 10 błędów
        recent_bugs = sorted(
            self.bugs_cache.values(), 
            key=lambda b: b.timestamp, 
            reverse=True
        )[:10]
        
        stats['recent_bugs'] = [
            {
                'id': bug.id,
                'title': bug.title,
                'severity': bug.severity,
                'timestamp': bug.timestamp.isoformat()
            }
            for bug in recent_bugs
        ]
        
        return stats