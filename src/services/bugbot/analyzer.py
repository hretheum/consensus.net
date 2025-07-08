"""
Analizator błędów - analizuje wykryte błędy i dostarcza wgląd
"""

import re
import hashlib
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
import logging


class ErrorAnalyzer:
    """
    Analizuje wykryte błędy i dostarcza szczegółowe informacje
    """
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # Słowniki do mapowania komponentów
        self.component_patterns = self._load_component_patterns()
        
        # Cache analizowanych błędów
        self.analysis_cache: Dict[str, Dict[str, Any]] = {}
        
    def _load_component_patterns(self) -> Dict[str, List[re.Pattern]]:
        """Ładuje wzorce do identyfikacji komponentów"""
        patterns = {
            'api': [
                re.compile(r'/api/'),
                re.compile(r'\.api\.'),
                re.compile(r'FastAPI|flask|django'),
            ],
            'database': [
                re.compile(r'\.db\.|database|sql|postgres|mysql|mongo'),
                re.compile(r'Model\.|Repository\.|DAO'),
            ],
            'auth': [
                re.compile(r'auth|login|permission|token|jwt'),
                re.compile(r'unauthorized|forbidden'),
            ],
            'frontend': [
                re.compile(r'\.js|\.jsx|\.ts|\.tsx|\.vue|\.css'),
                re.compile(r'React|Vue|Angular'),
            ],
            'services': [
                re.compile(r'\.services\.|service\.'),
                re.compile(r'worker|queue|task'),
            ],
            'agents': [
                re.compile(r'\.agents\.|agent\.'),
                re.compile(r'Agent|Bot'),
            ],
            'config': [
                re.compile(r'config|settings|env'),
                re.compile(r'Configuration|Settings'),
            ],
            'network': [
                re.compile(r'socket|connection|timeout|network'),
                re.compile(r'HTTP|TCP|UDP'),
            ],
        }
        
        # Dodaj niestandardowe wzorce z konfiguracji
        custom_patterns = self.config.get('component_patterns', {})
        for component, patterns_list in custom_patterns.items():
            if component not in patterns:
                patterns[component] = []
            for pattern in patterns_list:
                patterns[component].append(re.compile(pattern))
                
        return patterns
        
    async def analyze(self, error_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analizuje błąd i zwraca szczegółową analizę"""
        # Sprawdź cache
        cache_key = self._generate_cache_key(error_data)
        if cache_key in self.analysis_cache:
            cached = self.analysis_cache[cache_key]
            # Aktualizuj tylko timestamp
            cached['timestamp'] = datetime.now()
            return cached
            
        # Przeprowadź analizę
        analysis = {
            'timestamp': datetime.now(),
            'title': self._generate_title(error_data),
            'description': self._generate_description(error_data),
            'severity': self._analyze_severity(error_data),
            'category': error_data.get('category', 'unknown'),
            'component': self._identify_component(error_data),
            'root_cause': self._analyze_root_cause(error_data),
            'potential_fix': self._suggest_fix(error_data),
            'related_files': self._extract_related_files(error_data),
            'metadata': self._extract_metadata(error_data)
        }
        
        # Zapisz w cache
        self.analysis_cache[cache_key] = analysis
        
        # Ogranicz rozmiar cache
        if len(self.analysis_cache) > 1000:
            # Usuń najstarsze wpisy
            oldest_keys = sorted(
                self.analysis_cache.keys(), 
                key=lambda k: self.analysis_cache[k]['timestamp']
            )[:100]
            for key in oldest_keys:
                del self.analysis_cache[key]
                
        return analysis
        
    def _generate_cache_key(self, error_data: Dict[str, Any]) -> str:
        """Generuje klucz cache dla błędu"""
        key_parts = [
            error_data.get('pattern', ''),
            error_data.get('error_text', '')[:100],
            error_data.get('source', '')
        ]
        key = '|'.join(key_parts)
        return hashlib.md5(key.encode()).hexdigest()[:16]
        
    def _generate_title(self, error_data: Dict[str, Any]) -> str:
        """Generuje tytuł błędu"""
        error_text = error_data.get('error_text', '')
        pattern = error_data.get('pattern', '')
        
        # Wyciągnij główną część błędu
        if 'Exception' in error_text:
            # Dla wyjątków Python
            match = re.search(r'(\w+(?:Exception|Error))', error_text)
            if match:
                exception_type = match.group(1)
                # Spróbuj znaleźć komunikat
                msg_match = re.search(f'{exception_type}:(.+?)(?:\\n|$)', error_text)
                if msg_match:
                    message = msg_match.group(1).strip()[:50]
                    return f"{exception_type}: {message}"
                return exception_type
                
        elif 'ERROR' in error_text or 'CRITICAL' in error_text:
            # Dla logów
            match = re.search(r'(?:ERROR|CRITICAL)[^:]*:(.+?)(?:\\n|$)', error_text)
            if match:
                return match.group(1).strip()[:80]
                
        elif pattern == 'http_error_5xx':
            match = re.search(r'HTTP.*?(5\d{2})', error_text)
            if match:
                return f"HTTP {match.group(1)} Server Error"
                
        elif pattern == 'http_error_4xx':
            match = re.search(r'HTTP.*?(4\d{2})', error_text)
            if match:
                return f"HTTP {match.group(1)} Client Error"
                
        # Domyślny tytuł
        return error_text.split('\n')[0][:80] if error_text else "Unknown Error"
        
    def _generate_description(self, error_data: Dict[str, Any]) -> str:
        """Generuje opis błędu"""
        context = error_data.get('context', '')
        error_text = error_data.get('error_text', '')
        source = error_data.get('source', '')
        line_number = error_data.get('line_number', 0)
        
        description_parts = []
        
        # Podstawowe informacje
        description_parts.append(f"Błąd wykryty w pliku: {source}")
        if line_number:
            description_parts.append(f"Linia: {line_number}")
            
        # Analiza treści błędu
        if 'Traceback' in error_text:
            description_parts.append("\nSzczegóły stack trace:")
            # Wyciągnij najważniejsze linie
            lines = error_text.split('\n')
            for line in lines:
                if 'File' in line and '.py' in line:
                    description_parts.append(f"  {line.strip()}")
                    
        # Dodaj kontekst
        if context and context != error_text:
            description_parts.append(f"\nKontekst:\n{context[:200]}...")
            
        return '\n'.join(description_parts)
        
    def _analyze_severity(self, error_data: Dict[str, Any]) -> str:
        """Analizuje i ewentualnie modyfikuje poziom severity"""
        base_severity = error_data.get('severity', 'medium')
        error_text = error_data.get('error_text', '')
        
        # Zwiększ severity dla niektórych przypadków
        severity_upgrades = {
            'critical': ['OutOfMemory', 'SegmentationFault', 'SystemExit', 'CRITICAL'],
            'high': ['DatabaseError', 'ConnectionError', 'AuthenticationError'],
            'medium': ['TimeoutError', 'ValidationError']
        }
        
        for level, keywords in severity_upgrades.items():
            for keyword in keywords:
                if keyword in error_text:
                    # Upgrade severity jeśli znaleziono słowo kluczowe
                    if level == 'critical':
                        return 'critical'
                    elif level == 'high' and base_severity in ['medium', 'low']:
                        return 'high'
                    elif level == 'medium' and base_severity == 'low':
                        return 'medium'
                        
        return base_severity
        
    def _identify_component(self, error_data: Dict[str, Any]) -> str:
        """Identyfikuje komponent na podstawie błędu"""
        source = error_data.get('source', '')
        error_text = error_data.get('error_text', '')
        context = error_data.get('context', '')
        
        # Sprawdź wszystkie dostępne informacje
        full_text = f"{source} {error_text} {context}"
        
        # Sprawdź wzorce komponentów
        component_scores = {}
        for component, patterns in self.component_patterns.items():
            score = 0
            for pattern in patterns:
                if pattern.search(full_text):
                    score += 1
            if score > 0:
                component_scores[component] = score
                
        # Wybierz komponent z najwyższym score
        if component_scores:
            return max(component_scores.items(), key=lambda x: x[1])[0]
            
        # Spróbuj wywnioskować z path
        if '/' in source:
            parts = source.split('/')
            for part in parts:
                if part in ['api', 'services', 'agents', 'config', 'database']:
                    return part
                    
        return 'unknown'
        
    def _analyze_root_cause(self, error_data: Dict[str, Any]) -> Optional[str]:
        """Analizuje główną przyczynę błędu"""
        error_text = error_data.get('error_text', '')
        stack_trace = error_data.get('stack_trace', '')
        
        # Słownik znanych przyczyn
        root_causes = {
            r'NoneType.*has no attribute': "Próba dostępu do atrybutu obiektu None",
            r'division by zero': "Dzielenie przez zero",
            r'list index out of range': "Indeks listy poza zakresem",
            r'KeyError': "Brak klucza w słowniku",
            r'FileNotFoundError': "Plik nie został znaleziony",
            r'ConnectionRefusedError': "Połączenie zostało odrzucone",
            r'timeout': "Przekroczono limit czasu operacji",
            r'PermissionError': "Brak uprawnień do wykonania operacji",
            r'ImportError|ModuleNotFoundError': "Brak wymaganego modułu",
            r'SyntaxError': "Błąd składni w kodzie",
            r'MemoryError': "Brak dostępnej pamięci",
            r'disk.*full': "Brak miejsca na dysku",
            r'authentication.*failed': "Błąd uwierzytelniania",
            r'invalid.*token': "Nieprawidłowy token autoryzacji",
            r'database.*locked': "Baza danych jest zablokowana",
            r'connection.*closed': "Połączenie zostało zamknięte",
            r'invalid.*json': "Nieprawidłowy format JSON",
            r'encoding.*error': "Błąd kodowania znaków",
        }
        
        # Sprawdź znane przyczyny
        full_text = f"{error_text} {stack_trace or ''}"
        for pattern, cause in root_causes.items():
            if re.search(pattern, full_text, re.IGNORECASE):
                return cause
                
        # Spróbuj wyciągnąć przyczynę z komunikatu błędu
        if ':' in error_text:
            parts = error_text.split(':', 1)
            if len(parts) > 1:
                return parts[1].strip()[:100]
                
        return None
        
    def _suggest_fix(self, error_data: Dict[str, Any]) -> Optional[str]:
        """Sugeruje potencjalne rozwiązanie"""
        error_text = error_data.get('error_text', '')
        root_cause = self._analyze_root_cause(error_data)
        
        # Słownik sugestii napraw
        fix_suggestions = {
            "Próba dostępu do atrybutu obiektu None": 
                "Sprawdź czy obiekt nie jest None przed dostępem do atrybutu. Użyj warunku if lub metody get().",
            "Dzielenie przez zero": 
                "Dodaj warunek sprawdzający czy dzielnik nie jest zerem przed wykonaniem dzielenia.",
            "Indeks listy poza zakresem": 
                "Sprawdź długość listy przed dostępem do elementu. Użyj try/except lub warunku sprawdzającego.",
            "Brak klucza w słowniku": 
                "Użyj metody get() z wartością domyślną lub sprawdź istnienie klucza operatorem 'in'.",
            "Plik nie został znaleziony": 
                "Sprawdź czy ścieżka do pliku jest poprawna i czy plik istnieje. Użyj os.path.exists().",
            "Połączenie zostało odrzucone": 
                "Sprawdź czy usługa docelowa działa i czy adres/port są poprawne.",
            "Przekroczono limit czasu operacji": 
                "Zwiększ timeout lub zoptymalizuj operację. Sprawdź połączenie sieciowe.",
            "Brak uprawnień do wykonania operacji": 
                "Sprawdź uprawnienia pliku/katalogu. Uruchom z odpowiednimi uprawnieniami.",
            "Brak wymaganego modułu": 
                "Zainstaluj brakujący moduł używając pip install lub sprawdź requirements.txt.",
            "Błąd składni w kodzie": 
                "Sprawdź składnię kodu w wskazanej linii. Zwróć uwagę na nawiasy, wcięcia i znaki.",
            "Brak dostępnej pamięci": 
                "Zwolnij pamięć lub zwiększ limit. Zoptymalizuj kod aby używał mniej pamięci.",
            "Brak miejsca na dysku": 
                "Zwolnij miejsce na dysku lub przenieś dane na inny dysk.",
            "Błąd uwierzytelniania": 
                "Sprawdź dane logowania i konfigurację uwierzytelniania.",
            "Nieprawidłowy token autoryzacji": 
                "Odnów token lub sprawdź jego ważność i format.",
            "Baza danych jest zablokowana": 
                "Poczekaj na zakończenie innych operacji lub zrestartuj bazę danych.",
            "Połączenie zostało zamknięte": 
                "Sprawdź stabilność połączenia. Zaimplementuj reconnect logic.",
            "Nieprawidłowy format JSON": 
                "Sprawdź poprawność formatu JSON. Użyj walidatora JSON.",
            "Błąd kodowania znaków": 
                "Określ poprawne kodowanie (np. UTF-8) przy otwieraniu pliku.",
        }
        
        # Znajdź sugestię na podstawie przyczyny
        if root_cause:
            for cause, fix in fix_suggestions.items():
                if cause in root_cause:
                    return fix
                    
        # Dodatkowe sugestie na podstawie wzorców
        if re.search(r'404|not found', error_text, re.IGNORECASE):
            return "Sprawdź czy zasób istnieje i czy ścieżka URL jest poprawna."
        elif re.search(r'500|internal server', error_text, re.IGNORECASE):
            return "Sprawdź logi serwera. Może to być problem z konfiguracją lub kodem serwera."
        elif re.search(r'async|await', error_text):
            return "Sprawdź poprawność użycia async/await. Upewnij się że funkcja jest oznaczona jako async."
            
        return None
        
    def _extract_related_files(self, error_data: Dict[str, Any]) -> List[str]:
        """Wyciąga listę plików związanych z błędem"""
        related_files = []
        
        # Z source
        source = error_data.get('source', '')
        if source:
            related_files.append(source)
            
        # Ze stack trace
        stack_trace = error_data.get('stack_trace', '')
        if stack_trace:
            # Znajdź wszystkie ścieżki do plików Python
            file_pattern = re.compile(r'File "([^"]+\.py)"')
            matches = file_pattern.findall(stack_trace)
            related_files.extend(matches)
            
        # Z kontekstu
        context = error_data.get('context', '')
        if context:
            # Szukaj importów
            import_pattern = re.compile(r'from\s+(\S+)\s+import|import\s+(\S+)')
            matches = import_pattern.findall(context)
            for match in matches:
                module = match[0] or match[1]
                if module:
                    # Konwertuj moduł na ścieżkę
                    file_path = module.replace('.', '/') + '.py'
                    related_files.append(file_path)
                    
        # Usuń duplikaty zachowując kolejność
        seen = set()
        unique_files = []
        for file in related_files:
            if file not in seen:
                seen.add(file)
                unique_files.append(file)
                
        return unique_files
        
    def _extract_metadata(self, error_data: Dict[str, Any]) -> Dict[str, Any]:
        """Wyciąga dodatkowe metadane z błędu"""
        metadata = {}
        
        error_text = error_data.get('error_text', '')
        context = error_data.get('context', '')
        
        # Wyciągnij numery linii
        line_matches = re.findall(r'line (\d+)', error_text)
        if line_matches:
            metadata['error_lines'] = [int(line) for line in line_matches]
            
        # Wyciągnij nazwy funkcji
        func_matches = re.findall(r'in (\w+)\s*\(', error_text)
        if func_matches:
            metadata['functions'] = func_matches
            
        # Wyciągnij adresy IP
        ip_pattern = re.compile(r'\b(?:\d{1,3}\.){3}\d{1,3}\b')
        ip_matches = ip_pattern.findall(f"{error_text} {context}")
        if ip_matches:
            metadata['ip_addresses'] = list(set(ip_matches))
            
        # Wyciągnij URLe
        url_pattern = re.compile(r'https?://[^\s]+')
        url_matches = url_pattern.findall(f"{error_text} {context}")
        if url_matches:
            metadata['urls'] = list(set(url_matches))
            
        # Wyciągnij nazwy tabel/kolekcji DB
        db_pattern = re.compile(r'(?:table|collection)\s+["\']?(\w+)["\']?', re.IGNORECASE)
        db_matches = db_pattern.findall(f"{error_text} {context}")
        if db_matches:
            metadata['database_objects'] = list(set(db_matches))
            
        # Czas trwania (jeśli dostępny)
        duration_match = re.search(r'(\d+(?:\.\d+)?)\s*(?:seconds?|ms|milliseconds?)', error_text)
        if duration_match:
            metadata['duration'] = duration_match.group(0)
            
        # Rozmiar (jeśli dostępny)
        size_match = re.search(r'(\d+(?:\.\d+)?)\s*(?:MB|GB|KB|bytes?)', error_text)
        if size_match:
            metadata['size'] = size_match.group(0)
            
        return metadata