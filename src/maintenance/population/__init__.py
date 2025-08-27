"""
Population Module - Modular Database Population System
====================================================

This module provides platform-specific population logic, extracted from the monolithic
database_ops.py for better maintainability and separation of concerns.

Architecture:
- base_populator.py: Abstract base class defining population interface
- Platform-specific populators: tiktok_populator.py, youtube_populator.py, etc.
- population_coordinator.py: Main coordinator that dispatches to appropriate populator

Usage:
    from src.maintenance.population import PopulationCoordinator
    
    coordinator = PopulationCoordinator()
    result = coordinator.populate(source='db', platform='tiktok', limit=100)
"""

from .population_coordinator import PopulationCoordinator
from .base_populator import BasePopulator

# Platform-specific populators
from .tiktok_populator import TikTokPopulator
from .youtube_populator import YouTubePopulator
from .instagram_populator import InstagramPopulator

__all__ = [
    'PopulationCoordinator',
    'BasePopulator',
    'TikTokPopulator',
    'YouTubePopulator', 
    'InstagramPopulator',
]

__version__ = '1.0.0'