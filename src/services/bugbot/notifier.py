"""
System powiadomień - wysyła alerty o błędach
"""

import asyncio
import logging
import json
from datetime import datetime
from typing import Dict, List, Any, Optional
import aiohttp
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import smtplib
import ssl


class NotificationManager:
    """
    Zarządza wysyłaniem powiadomień o błędach
    """
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # Kanały powiadomień
        self.channels = self._setup_channels()
        
        # Rate limiting
        self.notification_cache: Dict[str, datetime] = {}
        self.rate_limit_window = config.get('rate_limit_window', 300)  # 5 minut
        
    def _setup_channels(self) -> Dict[str, Any]:
        """Konfiguruje dostępne kanały powiadomień"""
        channels = {}
        
        # Slack
        if self.config.get('slack'):
            channels['slack'] = {
                'webhook_url': self.config['slack'].get('webhook_url'),
                'channel': self.config['slack'].get('channel', '#bugs'),
                'enabled': self.config['slack'].get('enabled', True)
            }
            
        # Discord
        if self.config.get('discord'):
            channels['discord'] = {
                'webhook_url': self.config['discord'].get('webhook_url'),
                'enabled': self.config['discord'].get('enabled', True)
            }
            
        # Email
        if self.config.get('email'):
            channels['email'] = {
                'smtp_server': self.config['email'].get('smtp_server'),
                'smtp_port': self.config['email'].get('smtp_port', 587),
                'username': self.config['email'].get('username'),
                'password': self.config['email'].get('password'),
                'from_email': self.config['email'].get('from_email'),
                'to_emails': self.config['email'].get('to_emails', []),
                'enabled': self.config['email'].get('enabled', True)
            }
            
        # Microsoft Teams
        if self.config.get('teams'):
            channels['teams'] = {
                'webhook_url': self.config['teams'].get('webhook_url'),
                'enabled': self.config['teams'].get('enabled', True)
            }
            
        # Webhook (generic)
        if self.config.get('webhook'):
            channels['webhook'] = {
                'url': self.config['webhook'].get('url'),
                'headers': self.config['webhook'].get('headers', {}),
                'enabled': self.config['webhook'].get('enabled', True)
            }
            
        return channels
        
    async def notify_new_bug(self, bug):
        """Wysyła powiadomienie o nowym błędzie"""
        # Sprawdź rate limiting
        if not self._should_notify(f"new_bug:{bug.id}"):
            self.logger.debug(f"Skipping notification for bug {bug.id} due to rate limiting")
            return
            
        # Przygotuj wiadomość
        message = self._format_new_bug_message(bug)
        
        # Wyślij do wszystkich aktywnych kanałów
        tasks = []
        for channel_name, channel_config in self.channels.items():
            if channel_config.get('enabled'):
                tasks.append(self._send_to_channel(channel_name, channel_config, message, bug))
                
        await asyncio.gather(*tasks, return_exceptions=True)
        
    async def notify_escalation(self, bug):
        """Wysyła powiadomienie o eskalacji błędu"""
        # Sprawdź rate limiting
        if not self._should_notify(f"escalation:{bug.id}"):
            return
            
        message = self._format_escalation_message(bug)
        
        # Dla eskalacji używamy tylko kanałów wysokiego priorytetu
        priority_channels = ['slack', 'email', 'teams']
        
        tasks = []
        for channel_name in priority_channels:
            if channel_name in self.channels and self.channels[channel_name].get('enabled'):
                tasks.append(
                    self._send_to_channel(
                        channel_name, 
                        self.channels[channel_name], 
                        message, 
                        bug,
                        is_escalation=True
                    )
                )
                
        await asyncio.gather(*tasks, return_exceptions=True)
        
    def _should_notify(self, key: str) -> bool:
        """Sprawdza czy można wysłać powiadomienie (rate limiting)"""
        now = datetime.now()
        
        if key in self.notification_cache:
            last_notification = self.notification_cache[key]
            if (now - last_notification).total_seconds() < self.rate_limit_window:
                return False
                
        self.notification_cache[key] = now
        
        # Czyszczenie starego cache
        cutoff = now.timestamp() - self.rate_limit_window * 2
        self.notification_cache = {
            k: v for k, v in self.notification_cache.items()
            if v.timestamp() > cutoff
        }
        
        return True
        
    def _format_new_bug_message(self, bug) -> Dict[str, str]:
        """Formatuje wiadomość o nowym błędzie"""
        severity_emoji = {
            'critical': '🔴',
            'high': '🟠',
            'medium': '🟡',
            'low': '🟢'
        }.get(bug.severity, '⚪')
        
        title = f"{severity_emoji} Nowy błąd: {bug.title}"
        
        description_parts = [
            f"**Severity:** {bug.severity.upper()}",
            f"**Kategoria:** {bug.category}",
            f"**Komponent:** {bug.component}",
            f"**Przypisany do:** {bug.assigned_to or 'Nieprzypisany'}",
        ]
        
        if bug.description:
            description_parts.append(f"\n**Opis:**\n{bug.description[:500]}...")
            
        if bug.metadata.get('potential_fix'):
            description_parts.append(f"\n**Sugerowana naprawa:**\n{bug.metadata['potential_fix']}")
            
        description = '\n'.join(description_parts)
        
        return {
            'title': title,
            'description': description,
            'color': self._get_severity_color(bug.severity),
            'fields': {
                'Bug ID': bug.id,
                'Pierwszy raz': bug.first_seen.strftime('%Y-%m-%d %H:%M:%S'),
                'Częstotliwość': str(bug.frequency)
            }
        }
        
    def _format_escalation_message(self, bug) -> Dict[str, str]:
        """Formatuje wiadomość o eskalacji błędu"""
        title = f"⚠️ ESKALACJA: {bug.title}"
        
        duration = datetime.now() - bug.first_seen
        duration_str = self._format_duration(duration)
        
        description_parts = [
            f"**Błąd został eskalowany do poziomu {bug.severity.upper()}**",
            f"",
            f"**Czas trwania:** {duration_str}",
            f"**Liczba wystąpień:** {bug.frequency}",
            f"**Komponent:** {bug.component}",
            f"**Przypisany do:** {bug.assigned_to or 'NIEPRZYPISANY'}",
            f"",
            f"**Ten błąd wymaga natychmiastowej uwagi!**"
        ]
        
        if bug.github_issue_id:
            description_parts.append(f"\n**GitHub Issue:** #{bug.github_issue_id}")
            
        description = '\n'.join(description_parts)
        
        return {
            'title': title,
            'description': description,
            'color': '#FF0000',  # Czerwony dla eskalacji
            'fields': {
                'Bug ID': bug.id,
                'Pierwszy raz': bug.first_seen.strftime('%Y-%m-%d %H:%M:%S'),
                'Ostatnio': bug.last_seen.strftime('%Y-%m-%d %H:%M:%S')
            }
        }
        
    def _get_severity_color(self, severity: str) -> str:
        """Zwraca kolor dla poziomu severity"""
        colors = {
            'critical': '#FF0000',  # Czerwony
            'high': '#FFA500',      # Pomarańczowy
            'medium': '#FFFF00',    # Żółty
            'low': '#00FF00'        # Zielony
        }
        return colors.get(severity, '#808080')  # Szary jako domyślny
        
    def _format_duration(self, duration) -> str:
        """Formatuje czas trwania"""
        total_seconds = int(duration.total_seconds())
        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        
        if hours > 0:
            return f"{hours}h {minutes}m"
        else:
            return f"{minutes}m"
            
    async def _send_to_channel(self, channel_name: str, config: Dict[str, Any], 
                               message: Dict[str, str], bug, is_escalation: bool = False):
        """Wysyła wiadomość do konkretnego kanału"""
        try:
            if channel_name == 'slack':
                await self._send_slack(config, message, bug)
            elif channel_name == 'discord':
                await self._send_discord(config, message)
            elif channel_name == 'email':
                await self._send_email(config, message, bug, is_escalation)
            elif channel_name == 'teams':
                await self._send_teams(config, message)
            elif channel_name == 'webhook':
                await self._send_webhook(config, message, bug)
                
            self.logger.info(f"Notification sent to {channel_name} for bug {bug.id}")
            
        except Exception as e:
            self.logger.error(f"Failed to send notification to {channel_name}: {e}")
            
    async def _send_slack(self, config: Dict[str, Any], message: Dict[str, str], bug):
        """Wysyła powiadomienie do Slack"""
        webhook_url = config['webhook_url']
        
        payload = {
            'channel': config.get('channel', '#bugs'),
            'username': 'BugBot',
            'icon_emoji': ':bug:',
            'attachments': [{
                'color': message['color'],
                'title': message['title'],
                'text': message['description'],
                'fields': [
                    {'title': k, 'value': v, 'short': True}
                    for k, v in message['fields'].items()
                ],
                'footer': 'BugBot',
                'ts': int(datetime.now().timestamp())
            }]
        }
        
        if bug.github_issue_id:
            payload['attachments'][0]['actions'] = [{
                'type': 'button',
                'text': 'Zobacz w GitHub',
                'url': f"https://github.com/{self.config.get('github_repo', 'org/repo')}/issues/{bug.github_issue_id}"
            }]
            
        async with aiohttp.ClientSession() as session:
            async with session.post(webhook_url, json=payload) as response:
                if response.status != 200:
                    raise Exception(f"Slack webhook returned {response.status}")
                    
    async def _send_discord(self, config: Dict[str, Any], message: Dict[str, str]):
        """Wysyła powiadomienie do Discord"""
        webhook_url = config['webhook_url']
        
        embed = {
            'title': message['title'],
            'description': message['description'],
            'color': int(message['color'].replace('#', ''), 16),
            'fields': [
                {'name': k, 'value': v, 'inline': True}
                for k, v in message['fields'].items()
            ],
            'timestamp': datetime.now().isoformat(),
            'footer': {'text': 'BugBot'}
        }
        
        payload = {
            'username': 'BugBot',
            'avatar_url': 'https://example.com/bugbot-avatar.png',
            'embeds': [embed]
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(webhook_url, json=payload) as response:
                if response.status not in [200, 204]:
                    raise Exception(f"Discord webhook returned {response.status}")
                    
    async def _send_email(self, config: Dict[str, Any], message: Dict[str, str], 
                          bug, is_escalation: bool):
        """Wysyła powiadomienie email"""
        # Tworzenie wiadomości
        msg = MIMEMultipart('alternative')
        msg['Subject'] = message['title']
        msg['From'] = config['from_email']
        msg['To'] = ', '.join(config['to_emails'])
        
        # Treść HTML
        html_body = f"""
        <html>
        <body style="font-family: Arial, sans-serif;">
            <h2 style="color: {message['color']};">{message['title']}</h2>
            <div style="background-color: #f5f5f5; padding: 15px; border-radius: 5px;">
                {message['description'].replace('\n', '<br>')}
            </div>
            <table style="margin-top: 20px;">
                {''.join(f'<tr><td><b>{k}:</b></td><td>{v}</td></tr>' 
                         for k, v in message['fields'].items())}
            </table>
            <hr>
            <p style="color: #666; font-size: 12px;">
                Ten email został wygenerowany automatycznie przez BugBot.
            </p>
        </body>
        </html>
        """
        
        msg.attach(MIMEText(html_body, 'html'))
        
        # Wysyłanie
        context = ssl.create_default_context()
        
        with smtplib.SMTP(config['smtp_server'], config['smtp_port']) as server:
            server.starttls(context=context)
            server.login(config['username'], config['password'])
            server.send_message(msg)
            
    async def _send_teams(self, config: Dict[str, Any], message: Dict[str, str]):
        """Wysyła powiadomienie do Microsoft Teams"""
        webhook_url = config['webhook_url']
        
        payload = {
            '@type': 'MessageCard',
            '@context': 'https://schema.org/extensions',
            'themeColor': message['color'].replace('#', ''),
            'summary': message['title'],
            'sections': [{
                'activityTitle': message['title'],
                'text': message['description'],
                'facts': [
                    {'name': k, 'value': v}
                    for k, v in message['fields'].items()
                ]
            }]
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(webhook_url, json=payload) as response:
                if response.status != 200:
                    raise Exception(f"Teams webhook returned {response.status}")
                    
    async def _send_webhook(self, config: Dict[str, Any], message: Dict[str, str], bug):
        """Wysyła powiadomienie do generycznego webhooka"""
        url = config['url']
        headers = config.get('headers', {})
        
        payload = {
            'event': 'bug_detected',
            'bug': {
                'id': bug.id,
                'title': bug.title,
                'description': bug.description,
                'severity': bug.severity,
                'category': bug.category,
                'component': bug.component,
                'frequency': bug.frequency,
                'first_seen': bug.first_seen.isoformat(),
                'last_seen': bug.last_seen.isoformat(),
                'assigned_to': bug.assigned_to,
                'github_issue_id': bug.github_issue_id
            },
            'message': message,
            'timestamp': datetime.now().isoformat()
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload, headers=headers) as response:
                if response.status >= 400:
                    raise Exception(f"Webhook returned {response.status}")
                    
    async def send_daily_summary(self, stats: Dict[str, Any]):
        """Wysyła dzienny raport z podsumowaniem"""
        message = self._format_daily_summary(stats)
        
        # Wysyłaj tylko przez email i Slack
        for channel_name in ['email', 'slack']:
            if channel_name in self.channels and self.channels[channel_name].get('enabled'):
                await self._send_summary_to_channel(channel_name, self.channels[channel_name], message)
                
    def _format_daily_summary(self, stats: Dict[str, Any]) -> Dict[str, str]:
        """Formatuje dzienny raport"""
        title = f"📊 Dzienny raport BugBot - {datetime.now().strftime('%Y-%m-%d')}"
        
        description_parts = [
            f"**Podsumowanie błędów z ostatnich 24 godzin:**\n",
            f"🐛 **Łączna liczba błędów:** {stats['total_bugs']}",
            f"",
            "**Według severity:**"
        ]
        
        for severity, count in stats['by_severity'].items():
            emoji = {'critical': '🔴', 'high': '🟠', 'medium': '🟡', 'low': '🟢'}.get(severity, '⚪')
            description_parts.append(f"{emoji} {severity.capitalize()}: {count}")
            
        description_parts.extend([
            f"",
            "**Według kategorii:**"
        ])
        
        for category, count in stats['by_category'].items():
            description_parts.append(f"• {category}: {count}")
            
        if stats.get('recent_bugs'):
            description_parts.extend([
                f"",
                "**Najnowsze błędy:**"
            ])
            for bug in stats['recent_bugs'][:5]:
                description_parts.append(
                    f"• [{bug['severity']}] {bug['title']} ({bug['id'][:8]})"
                )
                
        return {
            'title': title,
            'description': '\n'.join(description_parts),
            'color': '#1E90FF'  # Niebieski dla raportów
        }
        
    async def _send_summary_to_channel(self, channel_name: str, config: Dict[str, Any], 
                                       message: Dict[str, str]):
        """Wysyła podsumowanie do kanału"""
        # Tymczasowy obiekt bug dla kompatybilności
        class DummyBug:
            id = "daily-summary"
            
        await self._send_to_channel(channel_name, config, message, DummyBug())