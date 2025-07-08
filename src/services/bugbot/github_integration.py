"""
Integracja z GitHub - tworzenie i zarządzanie issues
"""

import asyncio
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional
import aiohttp
import json


class GitHubIntegration:
    """
    Zarządza integracją z GitHub API
    """
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # Konfiguracja API
        self.api_token = config.get('api_token')
        self.repo_owner = config.get('repo_owner')
        self.repo_name = config.get('repo_name')
        self.base_url = 'https://api.github.com'
        
        # Headers dla API
        self.headers = {
            'Authorization': f'token {self.api_token}',
            'Accept': 'application/vnd.github.v3+json',
            'Content-Type': 'application/json'
        }
        
        # Cache dla labels
        self._labels_cache = None
        self._labels_cache_time = None
        
    async def create_issue(self, bug) -> Optional[int]:
        """Tworzy nowe issue w GitHub"""
        try:
            # Przygotuj dane issue
            issue_data = {
                'title': self._format_issue_title(bug),
                'body': self._format_issue_body(bug),
                'labels': self._get_labels_for_bug(bug),
                'assignees': [bug.assigned_to] if bug.assigned_to else []
            }
            
            # Wyślij request
            url = f"{self.base_url}/repos/{self.repo_owner}/{self.repo_name}/issues"
            
            async with aiohttp.ClientSession() as session:
                async with session.post(url, headers=self.headers, json=issue_data) as response:
                    if response.status == 201:
                        data = await response.json()
                        issue_number = data['number']
                        self.logger.info(f"Created GitHub issue #{issue_number} for bug {bug.id}")
                        return issue_number
                    else:
                        error_text = await response.text()
                        self.logger.error(f"Failed to create GitHub issue: {response.status} - {error_text}")
                        return None
                        
        except Exception as e:
            self.logger.error(f"Error creating GitHub issue: {e}")
            return None
            
    def _format_issue_title(self, bug) -> str:
        """Formatuje tytuł issue"""
        severity_prefix = {
            'critical': '🔴 [CRITICAL]',
            'high': '🟠 [HIGH]',
            'medium': '🟡 [MEDIUM]',
            'low': '🟢 [LOW]'
        }.get(bug.severity, '')
        
        return f"{severity_prefix} {bug.title}"
        
    def _format_issue_body(self, bug) -> str:
        """Formatuje treść issue"""
        body_parts = [
            "## 🐛 Opis błędu",
            f"{bug.description}",
            "",
            "## 📊 Informacje",
            f"- **ID błędu:** `{bug.id}`",
            f"- **Severity:** {bug.severity}",
            f"- **Kategoria:** {bug.category}",
            f"- **Komponent:** {bug.component}",
            f"- **Pierwsza detekcja:** {bug.first_seen.strftime('%Y-%m-%d %H:%M:%S')}",
            f"- **Ostatnia detekcja:** {bug.last_seen.strftime('%Y-%m-%d %H:%M:%S')}",
            f"- **Liczba wystąpień:** {bug.frequency}",
            ""
        ]
        
        # Dodaj przyczynę jeśli znana
        if bug.metadata.get('root_cause'):
            body_parts.extend([
                "## 🔍 Analiza przyczyny",
                bug.metadata['root_cause'],
                ""
            ])
            
        # Dodaj sugerowaną naprawę
        if bug.metadata.get('potential_fix'):
            body_parts.extend([
                "## 💡 Sugerowana naprawa",
                bug.metadata['potential_fix'],
                ""
            ])
            
        # Dodaj stack trace jeśli dostępny
        if bug.stack_trace:
            body_parts.extend([
                "## 📋 Stack trace",
                "```",
                bug.stack_trace[:1000] + "..." if len(bug.stack_trace) > 1000 else bug.stack_trace,
                "```",
                ""
            ])
            
        # Dodaj powiązane pliki
        if bug.metadata.get('related_files'):
            body_parts.extend([
                "## 📁 Powiązane pliki",
                ""
            ])
            for file in bug.metadata['related_files'][:10]:
                body_parts.append(f"- `{file}`")
            body_parts.append("")
            
        # Dodaj dodatkowe metadane
        if bug.metadata:
            relevant_metadata = {k: v for k, v in bug.metadata.items() 
                               if k not in ['root_cause', 'potential_fix', 'related_files']}
            if relevant_metadata:
                body_parts.extend([
                    "## 📎 Dodatkowe informacje",
                    "```json",
                    json.dumps(relevant_metadata, indent=2),
                    "```",
                    ""
                ])
                
        # Dodaj stopkę
        body_parts.extend([
            "---",
            f"*Ten issue został automatycznie utworzony przez BugBot 🤖*",
            f"*Bug ID: {bug.id}*"
        ])
        
        return '\n'.join(body_parts)
        
    def _get_labels_for_bug(self, bug) -> List[str]:
        """Określa labels dla issue na podstawie błędu"""
        labels = []
        
        # Label dla severity
        severity_label = f"severity:{bug.severity}"
        labels.append(severity_label)
        
        # Label dla kategorii
        category_labels = {
            'runtime': 'bug',
            'syntax': 'bug',
            'performance': 'performance',
            'security': 'security',
            'unknown': 'bug'
        }
        if bug.category in category_labels:
            labels.append(category_labels[bug.category])
            
        # Label dla komponentu
        component_label = f"component:{bug.component}"
        if bug.component != 'unknown':
            labels.append(component_label)
            
        # Dodatkowe labels na podstawie metadanych
        if 'database' in bug.component.lower():
            labels.append('database')
        if 'api' in bug.component.lower():
            labels.append('api')
        if 'frontend' in bug.component.lower():
            labels.append('frontend')
            
        # Label dla automatycznie utworzonych
        labels.append('bugbot')
        
        return labels
        
    async def update_issue(self, issue_number: int, updates: Dict[str, Any]) -> bool:
        """Aktualizuje istniejące issue"""
        try:
            url = f"{self.base_url}/repos/{self.repo_owner}/{self.repo_name}/issues/{issue_number}"
            
            async with aiohttp.ClientSession() as session:
                async with session.patch(url, headers=self.headers, json=updates) as response:
                    if response.status == 200:
                        self.logger.info(f"Updated GitHub issue #{issue_number}")
                        return True
                    else:
                        error_text = await response.text()
                        self.logger.error(f"Failed to update issue: {response.status} - {error_text}")
                        return False
                        
        except Exception as e:
            self.logger.error(f"Error updating GitHub issue: {e}")
            return False
            
    async def add_comment(self, issue_number: int, comment: str) -> bool:
        """Dodaje komentarz do issue"""
        try:
            url = f"{self.base_url}/repos/{self.repo_owner}/{self.repo_name}/issues/{issue_number}/comments"
            
            data = {'body': comment}
            
            async with aiohttp.ClientSession() as session:
                async with session.post(url, headers=self.headers, json=data) as response:
                    if response.status == 201:
                        self.logger.info(f"Added comment to GitHub issue #{issue_number}")
                        return True
                    else:
                        error_text = await response.text()
                        self.logger.error(f"Failed to add comment: {response.status} - {error_text}")
                        return False
                        
        except Exception as e:
            self.logger.error(f"Error adding comment to GitHub issue: {e}")
            return False
            
    async def close_issue(self, issue_number: int, comment: Optional[str] = None) -> bool:
        """Zamyka issue"""
        try:
            # Dodaj komentarz jeśli podany
            if comment:
                await self.add_comment(issue_number, comment)
                
            # Zamknij issue
            updates = {'state': 'closed'}
            return await self.update_issue(issue_number, updates)
            
        except Exception as e:
            self.logger.error(f"Error closing GitHub issue: {e}")
            return False
            
    async def get_issue(self, issue_number: int) -> Optional[Dict[str, Any]]:
        """Pobiera informacje o issue"""
        try:
            url = f"{self.base_url}/repos/{self.repo_owner}/{self.repo_name}/issues/{issue_number}"
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=self.headers) as response:
                    if response.status == 200:
                        return await response.json()
                    else:
                        return None
                        
        except Exception as e:
            self.logger.error(f"Error getting GitHub issue: {e}")
            return None
            
    async def search_issues(self, query: str) -> List[Dict[str, Any]]:
        """Szuka issues według zapytania"""
        try:
            # Buduj zapytanie
            full_query = f"repo:{self.repo_owner}/{self.repo_name} {query}"
            url = f"{self.base_url}/search/issues"
            params = {
                'q': full_query,
                'sort': 'created',
                'order': 'desc',
                'per_page': 100
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=self.headers, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        return data.get('items', [])
                    else:
                        return []
                        
        except Exception as e:
            self.logger.error(f"Error searching GitHub issues: {e}")
            return []
            
    async def ensure_labels_exist(self, labels: List[str]):
        """Upewnia się że labels istnieją w repo"""
        try:
            # Pobierz istniejące labels
            existing_labels = await self._get_all_labels()
            existing_names = {label['name'] for label in existing_labels}
            
            # Utwórz brakujące labels
            for label in labels:
                if label not in existing_names:
                    await self._create_label(label)
                    
        except Exception as e:
            self.logger.error(f"Error ensuring labels exist: {e}")
            
    async def _get_all_labels(self) -> List[Dict[str, Any]]:
        """Pobiera wszystkie labels z repo"""
        # Sprawdź cache
        if self._labels_cache and self._labels_cache_time:
            cache_age = (datetime.now() - self._labels_cache_time).total_seconds()
            if cache_age < 3600:  # Cache ważny przez godzinę
                return self._labels_cache
                
        try:
            url = f"{self.base_url}/repos/{self.repo_owner}/{self.repo_name}/labels"
            params = {'per_page': 100}
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=self.headers, params=params) as response:
                    if response.status == 200:
                        labels = await response.json()
                        self._labels_cache = labels
                        self._labels_cache_time = datetime.now()
                        return labels
                    else:
                        return []
                        
        except Exception as e:
            self.logger.error(f"Error getting labels: {e}")
            return []
            
    async def _create_label(self, name: str):
        """Tworzy nowy label"""
        try:
            # Określ kolor na podstawie nazwy
            color = self._get_label_color(name)
            
            url = f"{self.base_url}/repos/{self.repo_owner}/{self.repo_name}/labels"
            data = {
                'name': name,
                'color': color,
                'description': f'Automatycznie utworzony przez BugBot'
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(url, headers=self.headers, json=data) as response:
                    if response.status == 201:
                        self.logger.info(f"Created label: {name}")
                        # Wyczyść cache
                        self._labels_cache = None
                    else:
                        error_text = await response.text()
                        self.logger.error(f"Failed to create label: {response.status} - {error_text}")
                        
        except Exception as e:
            self.logger.error(f"Error creating label: {e}")
            
    def _get_label_color(self, name: str) -> str:
        """Określa kolor dla label"""
        # Kolory dla severity
        if 'critical' in name.lower():
            return 'd73a4a'  # czerwony
        elif 'high' in name.lower():
            return 'ff6b00'  # pomarańczowy
        elif 'medium' in name.lower():
            return 'ffd700'  # żółty
        elif 'low' in name.lower():
            return '0e8a16'  # zielony
            
        # Kolory dla typów
        elif 'bug' in name.lower():
            return 'd73a4a'  # czerwony
        elif 'performance' in name.lower():
            return 'a2eeef'  # jasnoniebieski
        elif 'security' in name.lower():
            return 'ee0000'  # ciemnoczerwony
            
        # Kolory dla komponentów
        elif 'api' in name.lower():
            return '1d76db'  # niebieski
        elif 'database' in name.lower():
            return '5319e7'  # fioletowy
        elif 'frontend' in name.lower():
            return '0052cc'  # ciemnoniebieski
            
        # Domyślny kolor
        else:
            return 'cfd3d7'  # szary