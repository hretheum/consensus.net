"""
API endpoints dla BugBot
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks, Depends
from typing import Dict, List, Any, Optional
from datetime import datetime
import asyncio
import logging

from services.bugbot import BugBot
from services.bugbot.config import BugBotConfig
from pydantic import BaseModel


router = APIRouter(
    prefix="/bugbot",
    tags=["bugbot"]
)

logger = logging.getLogger(__name__)

# Globalna instancja BugBot (singleton)
_bugbot_instance: Optional[BugBot] = None
_bugbot_lock = asyncio.Lock()


class BugBotStatus(BaseModel):
    """Status BugBot"""
    running: bool
    bugs_count: int
    last_scan: Optional[datetime]
    monitored_files: int
    config: Dict[str, Any]


class BugSummary(BaseModel):
    """Podsumowanie błędu"""
    id: str
    title: str
    severity: str
    category: str
    component: str
    frequency: int
    first_seen: datetime
    last_seen: datetime
    status: str
    assigned_to: Optional[str]
    github_issue_id: Optional[int]


class BugStats(BaseModel):
    """Statystyki błędów"""
    total_bugs: int
    by_severity: Dict[str, int]
    by_category: Dict[str, int]
    by_status: Dict[str, int]
    by_component: Dict[str, int]
    recent_bugs: List[Dict[str, Any]]


class ErrorPattern(BaseModel):
    """Wzorzec błędu"""
    name: str
    pattern: str
    severity: str
    category: str


async def get_bugbot() -> BugBot:
    """Pobiera instancję BugBot"""
    global _bugbot_instance
    
    async with _bugbot_lock:
        if _bugbot_instance is None:
            # Inicjalizuj BugBot z domyślną konfiguracją
            config = BugBotConfig.from_env()
            _bugbot_instance = BugBot(config)
            
            # Uruchom w tle
            asyncio.create_task(_bugbot_instance.start())
            logger.info("BugBot instance created and started")
            
    return _bugbot_instance


@router.get("/status", response_model=BugBotStatus)
async def get_status(bugbot: BugBot = Depends(get_bugbot)):
    """Pobiera status BugBot"""
    stats = await bugbot.get_bug_stats()
    monitored_files = await bugbot.monitor.get_monitored_files()
    
    return BugBotStatus(
        running=bugbot.running,
        bugs_count=stats['total_bugs'],
        last_scan=datetime.now() if bugbot.running else None,
        monitored_files=len(monitored_files),
        config=bugbot.config.to_dict()
    )


@router.get("/bugs", response_model=List[BugSummary])
async def get_bugs(
    severity: Optional[str] = None,
    category: Optional[str] = None,
    component: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = 100,
    bugbot: BugBot = Depends(get_bugbot)
):
    """Pobiera listę błędów z opcjonalnym filtrowaniem"""
    bugs = []
    
    for bug in bugbot.bugs_cache.values():
        # Filtrowanie
        if severity and bug.severity != severity:
            continue
        if category and bug.category != category:
            continue
        if component and bug.component != component:
            continue
        if status and bug.status != status:
            continue
            
        bugs.append(BugSummary(
            id=bug.id,
            title=bug.title,
            severity=bug.severity,
            category=bug.category,
            component=bug.component,
            frequency=bug.frequency,
            first_seen=bug.first_seen,
            last_seen=bug.last_seen,
            status=bug.status,
            assigned_to=bug.assigned_to,
            github_issue_id=bug.github_issue_id
        ))
        
        if len(bugs) >= limit:
            break
            
    # Sortuj według ostatniego wystąpienia
    bugs.sort(key=lambda b: b.last_seen, reverse=True)
    
    return bugs


@router.get("/bugs/{bug_id}")
async def get_bug_details(bug_id: str, bugbot: BugBot = Depends(get_bugbot)):
    """Pobiera szczegóły konkretnego błędu"""
    if bug_id not in bugbot.bugs_cache:
        raise HTTPException(status_code=404, detail="Bug not found")
        
    bug = bugbot.bugs_cache[bug_id]
    
    return {
        "id": bug.id,
        "title": bug.title,
        "description": bug.description,
        "severity": bug.severity,
        "category": bug.category,
        "component": bug.component,
        "frequency": bug.frequency,
        "first_seen": bug.first_seen,
        "last_seen": bug.last_seen,
        "status": bug.status,
        "assigned_to": bug.assigned_to,
        "github_issue_id": bug.github_issue_id,
        "stack_trace": bug.stack_trace,
        "metadata": bug.metadata
    }


@router.patch("/bugs/{bug_id}/status")
async def update_bug_status(
    bug_id: str,
    status: str,
    comment: Optional[str] = None,
    bugbot: BugBot = Depends(get_bugbot)
):
    """Aktualizuje status błędu"""
    if bug_id not in bugbot.bugs_cache:
        raise HTTPException(status_code=404, detail="Bug not found")
        
    valid_statuses = ["new", "assigned", "in_progress", "resolved"]
    if status not in valid_statuses:
        raise HTTPException(
            status_code=400, 
            detail=f"Invalid status. Must be one of: {valid_statuses}"
        )
        
    bug = bugbot.bugs_cache[bug_id]
    bug.status = status
    
    # Jeśli rozwiązany, zamknij issue w GitHub
    if status == "resolved" and bug.github_issue_id and bugbot.github:
        close_comment = f"Bug resolved. {comment or 'No additional comment.'}"
        await bugbot.github.close_issue(bug.github_issue_id, close_comment)
        
    # Zapisz zmiany
    await bugbot._persist_bug(bug)
    
    return {"message": "Bug status updated", "bug_id": bug_id, "new_status": status}


@router.patch("/bugs/{bug_id}/assign")
async def assign_bug(
    bug_id: str,
    assignee: str,
    bugbot: BugBot = Depends(get_bugbot)
):
    """Przypisuje błąd do dewelopera"""
    if bug_id not in bugbot.bugs_cache:
        raise HTTPException(status_code=404, detail="Bug not found")
        
    bug = bugbot.bugs_cache[bug_id]
    bug.assigned_to = assignee
    
    # Zaktualizuj w GitHub jeśli istnieje issue
    if bug.github_issue_id and bugbot.github:
        await bugbot.github.update_issue(
            bug.github_issue_id,
            {"assignees": [assignee]}
        )
        
    # Zapisz zmiany
    await bugbot._persist_bug(bug)
    
    return {"message": "Bug assigned", "bug_id": bug_id, "assignee": assignee}


@router.get("/stats", response_model=BugStats)
async def get_stats(bugbot: BugBot = Depends(get_bugbot)):
    """Pobiera statystyki błędów"""
    stats = await bugbot.get_bug_stats()
    return BugStats(**stats)


@router.post("/patterns")
async def add_custom_pattern(
    pattern: ErrorPattern,
    bugbot: BugBot = Depends(get_bugbot)
):
    """Dodaje niestandardowy wzorzec błędu"""
    await bugbot.monitor.add_custom_pattern(
        name=pattern.name,
        pattern=pattern.pattern,
        severity=pattern.severity,
        category=pattern.category
    )
    
    return {"message": "Pattern added successfully", "pattern": pattern.name}


@router.get("/monitored-files")
async def get_monitored_files(bugbot: BugBot = Depends(get_bugbot)):
    """Pobiera listę monitorowanych plików"""
    files = await bugbot.monitor.get_monitored_files()
    return {"files": files, "total": len(files)}


@router.post("/scan")
async def trigger_scan(
    background_tasks: BackgroundTasks,
    bugbot: BugBot = Depends(get_bugbot)
):
    """Wymusza natychmiastowe skanowanie"""
    async def run_scan():
        # Symuluj zdarzenie które wymusi skanowanie
        errors = await bugbot.monitor.get_errors()
        for error in errors:
            await bugbot._process_error(error)
            
    background_tasks.add_task(run_scan)
    
    return {"message": "Scan triggered"}


@router.post("/test-notification")
async def test_notification(
    channel: str,
    bugbot: BugBot = Depends(get_bugbot)
):
    """Testuje powiadomienia"""
    # Utwórz testowy błąd
    from services.bugbot.bugbot import Bug
    
    test_bug = Bug(
        id="test-bug-001",
        title="Test Bug for Notification",
        description="This is a test bug to verify notification system",
        severity="medium",
        category="test",
        component="notification",
        timestamp=datetime.now()
    )
    
    # Wyślij powiadomienie
    valid_channels = ["slack", "discord", "email", "teams", "webhook"]
    if channel not in valid_channels:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid channel. Must be one of: {valid_channels}"
        )
        
    if channel not in bugbot.notifier.channels:
        raise HTTPException(
            status_code=400,
            detail=f"Channel {channel} is not configured"
        )
        
    await bugbot.notifier._send_to_channel(
        channel,
        bugbot.notifier.channels[channel],
        bugbot.notifier._format_new_bug_message(test_bug),
        test_bug
    )
    
    return {"message": f"Test notification sent to {channel}"}


@router.post("/daily-summary")
async def send_daily_summary(bugbot: BugBot = Depends(get_bugbot)):
    """Wysyła dzienny raport"""
    stats = await bugbot.get_bug_stats()
    await bugbot.notifier.send_daily_summary(stats)
    
    return {"message": "Daily summary sent"}


@router.post("/shutdown")
async def shutdown_bugbot(bugbot: BugBot = Depends(get_bugbot)):
    """Wyłącza BugBot"""
    global _bugbot_instance
    
    await bugbot.stop()
    _bugbot_instance = None
    
    return {"message": "BugBot stopped"}