"""
Tag-Flow V2 - Database Module
Modular database operations organized by functionality
"""

from .manager import DatabaseManager, DatabaseProxy
from .core import DatabaseCore
from .videos import VideoOperations
from .deletion import DeletionOperations
from .batch import BatchOperations
from .creators import CreatorOperations
from .subscriptions import SubscriptionOperations
from .statistics import StatisticsOperations

# Main interface - backwards compatible
__all__ = [
    'DatabaseManager',
    'DatabaseProxy',
    'DatabaseCore',
    'VideoOperations',
    'DeletionOperations',
    'BatchOperations',
    'CreatorOperations',
    'SubscriptionOperations',
    'StatisticsOperations'
]

# Legacy compatibility - maintain existing import structure
# This allows existing code to continue working with:
# from src.database import DatabaseManager
def get_database_manager(db_path=None):
    """Get database manager instance"""
    return DatabaseManager(db_path)