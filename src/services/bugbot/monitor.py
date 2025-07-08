"""
Monitor błędów - skanuje logi i źródła danych w poszukiwaniu błędów
"""

import asyncio
import re
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional, Pattern
from collections import deque
import aiofiles
import json
from pathlib import Path


class ErrorPattern:
    """Wzorzec do wykrywania błędów"""
    
    def __init__(self, name: str, pattern: str, severity: str, category: str):
        self.name = name
        self.pattern: Pattern = re.compile(pattern, re.IGNORECASE | re.MULTILINE)
        self.severity = severity
        self.category = category


class ErrorMonitor:
    """
    Monitor błędów skanujący różne źródła danych
    """
    
    # Domyślne wzorce błędów
    DEFAULT_PATTERNS = [
        ErrorPattern(
            "python_exception",
            r"Traceback \(most recent call last\):.*?(?=\n\n|\Z)",
            "high",
            "runtime"
        ),
        ErrorPattern(
            "error_log",
            r"(?:ERROR|CRITICAL).*?:.*",
            "high",
            "runtime"
        ),
        ErrorPattern(
            "warning_log",
            r"WARNING.*?:.*",
            "medium",
            "runtime"
        ),
        ErrorPattern(
            "null_pointer",
            r"(?:NullPointerException|TypeError.*?None|AttributeError.*?NoneType)",
            "high",
            "runtime"
        ),
        ErrorPattern(
            "memory_error",
            r"(?:MemoryError|OutOfMemoryError|heap.*?exhausted)",
            "critical",
            "performance"
        ),
        ErrorPattern(
            "timeout_error",
            r"(?:TimeoutError|Request timeout|Connection timeout)",
            "medium",
            "performance"
        ),
        ErrorPattern(
            "database_error",
            r"(?:DatabaseError|OperationalError|IntegrityError)",
            "high",
            "runtime"
        ),
        ErrorPattern(
            "permission_error",
            r"(?:PermissionError|Permission denied|Access denied)",
            "medium",
            "security"
        ),
        ErrorPattern(
            "syntax_error",
            r"(?:SyntaxError|IndentationError|TabError)",
            "high",
            "syntax"
        ),
        ErrorPattern(
            "import_error",
            r"(?:ImportError|ModuleNotFoundError)",
            "high",
            "runtime"
        ),
        ErrorPattern(
            "http_error_5xx",
            r"HTTP.*?5\d{2}",
            "high",
            "runtime"
        ),
        ErrorPattern(
            "http_error_4xx",
            r"HTTP.*?4\d{2}",
            "medium",
            "runtime"
        ),
    ]
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # Inicjalizacja wzorców
        self.patterns = self._load_patterns()
        
        # Kolejka wykrytych błędów
        self.error_queue: deque = deque(maxlen=1000)
        
        # Stan monitora
        self.running = False
        self.monitored_files: Dict[str, int] = {}  # file_path -> last_position
        
        # Konfiguracja
        self.log_directories = config.get('log_directories', ['./logs'])
        self.scan_interval = config.get('scan_interval', 10)
        self.max_line_length = config.get('max_line_length', 1000)
        
    def _load_patterns(self) -> List[ErrorPattern]:
        """Ładuje wzorce błędów"""
        patterns = self.DEFAULT_PATTERNS.copy()
        
        # Załaduj dodatkowe wzorce z konfiguracji
        custom_patterns = self.config.get('custom_patterns', [])
        for cp in custom_patterns:
            patterns.append(ErrorPattern(
                name=cp['name'],
                pattern=cp['pattern'],
                severity=cp['severity'],
                category=cp['category']
            ))
            
        return patterns
        
    async def start(self):
        """Uruchamia monitor"""
        self.logger.info("Starting Error Monitor...")
        self.running = True
        
        # Uruchom skanowanie
        await self._scan_loop()
        
    async def stop(self):
        """Zatrzymuje monitor"""
        self.logger.info("Stopping Error Monitor...")
        self.running = False
        
    async def get_errors(self) -> List[Dict[str, Any]]:
        """Pobiera wykryte błędy z kolejki"""
        errors = []
        
        while self.error_queue:
            try:
                errors.append(self.error_queue.popleft())
            except IndexError:
                break
                
        return errors
        
    async def _scan_loop(self):
        """Główna pętla skanowania"""
        while self.running:
            try:
                # Skanuj wszystkie skonfigurowane katalogi
                for log_dir in self.log_directories:
                    await self._scan_directory(log_dir)
                    
                # Skanuj stdout/stderr procesów (jeśli skonfigurowane)
                if self.config.get('monitor_stdout', False):
                    await self._monitor_stdout()
                    
                await asyncio.sleep(self.scan_interval)
                
            except Exception as e:
                self.logger.error(f"Error in scan loop: {e}")
                await asyncio.sleep(5)
                
    async def _scan_directory(self, directory: str):
        """Skanuje katalog w poszukiwaniu plików logów"""
        try:
            path = Path(directory)
            if not path.exists():
                self.logger.warning(f"Log directory {directory} does not exist")
                return
                
            # Znajdź wszystkie pliki logów
            log_files = []
            for pattern in ['*.log', '*.txt', '*.err', '*.out']:
                log_files.extend(path.glob(pattern))
                
            # Skanuj każdy plik
            for log_file in log_files:
                await self._scan_file(str(log_file))
                
        except Exception as e:
            self.logger.error(f"Error scanning directory {directory}: {e}")
            
    async def _scan_file(self, file_path: str):
        """Skanuje pojedynczy plik logu"""
        try:
            # Sprawdź ostatnią pozycję
            last_position = self.monitored_files.get(file_path, 0)
            
            async with aiofiles.open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                # Przejdź do ostatniej znanej pozycji
                await f.seek(last_position)
                
                # Czytaj nowe linie
                lines = []
                current_position = last_position
                
                async for line in f:
                    lines.append(line[:self.max_line_length])
                    current_position = await f.tell()
                    
                    # Przetwarzaj w partiach
                    if len(lines) >= 100:
                        await self._process_lines(lines, file_path)
                        lines = []
                        
                # Przetwórz pozostałe linie
                if lines:
                    await self._process_lines(lines, file_path)
                    
                # Zaktualizuj pozycję
                self.monitored_files[file_path] = current_position
                
        except Exception as e:
            self.logger.error(f"Error scanning file {file_path}: {e}")
            
    async def _process_lines(self, lines: List[str], source: str):
        """Przetwarza linie w poszukiwaniu błędów"""
        text = '\n'.join(lines)
        
        for pattern in self.patterns:
            matches = pattern.pattern.finditer(text)
            
            for match in matches:
                error_text = match.group(0)
                
                # Wyciągnij kontekst (kilka linii przed i po)
                start_line = text.rfind('\n', 0, match.start())
                end_line = text.find('\n', match.end())
                
                if start_line == -1:
                    start_line = 0
                if end_line == -1:
                    end_line = len(text)
                    
                context = text[start_line:end_line].strip()
                
                # Utwórz obiekt błędu
                error_data = {
                    'timestamp': datetime.now(),
                    'source': source,
                    'pattern': pattern.name,
                    'severity': pattern.severity,
                    'category': pattern.category,
                    'error_text': error_text,
                    'context': context,
                    'line_number': text[:match.start()].count('\n') + 1
                }
                
                # Sprawdź czy to stack trace
                if 'Traceback' in error_text:
                    error_data['stack_trace'] = self._extract_stack_trace(text, match.start())
                    
                # Dodaj do kolejki
                self.error_queue.append(error_data)
                self.logger.debug(f"Detected error: {pattern.name} in {source}")
                
    def _extract_stack_trace(self, text: str, start_pos: int) -> str:
        """Wyciąga pełny stack trace"""
        # Znajdź koniec stack trace (pusta linia lub nowy log entry)
        end_patterns = ['\n\n', '\n[', '\nERROR', '\nWARNING', '\nINFO', '\nDEBUG']
        
        end_pos = len(text)
        for pattern in end_patterns:
            pos = text.find(pattern, start_pos)
            if pos != -1 and pos < end_pos:
                end_pos = pos
                
        return text[start_pos:end_pos].strip()
        
    async def _monitor_stdout(self):
        """Monitoruje stdout/stderr uruchomionych procesów"""
        # TODO: Implementacja monitorowania stdout
        # Może używać subprocess lub docker logs
        pass
        
    async def add_custom_pattern(self, name: str, pattern: str, severity: str, category: str):
        """Dodaje niestandardowy wzorzec błędu"""
        new_pattern = ErrorPattern(name, pattern, severity, category)
        self.patterns.append(new_pattern)
        self.logger.info(f"Added custom pattern: {name}")
        
    async def get_monitored_files(self) -> List[Dict[str, Any]]:
        """Zwraca listę monitorowanych plików"""
        files = []
        for file_path, position in self.monitored_files.items():
            try:
                file_stat = Path(file_path).stat()
                files.append({
                    'path': file_path,
                    'size': file_stat.st_size,
                    'last_modified': datetime.fromtimestamp(file_stat.st_mtime),
                    'bytes_read': position,
                    'percentage_read': (position / file_stat.st_size * 100) if file_stat.st_size > 0 else 100
                })
            except:
                pass
                
        return files