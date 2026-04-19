"""
core/scheduler.py — APScheduler singleton for session timers
"""
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.jobstores.memory import MemoryJobStore

# Global scheduler instance
_scheduler: AsyncIOScheduler | None = None


def get_scheduler() -> AsyncIOScheduler:
    """Get or create the global APScheduler instance"""
    global _scheduler
    if _scheduler is None:
        jobstores = {
            'default': MemoryJobStore()
        }
        _scheduler = AsyncIOScheduler(jobstores=jobstores)
    return _scheduler


def start_scheduler():
    """Start the scheduler (called on app startup)"""
    scheduler = get_scheduler()
    if not scheduler.running:
        scheduler.start()


def shutdown_scheduler():
    """Shutdown the scheduler gracefully (called on app shutdown)"""
    scheduler = get_scheduler()
    if scheduler.running:
        scheduler.shutdown(wait=True)
