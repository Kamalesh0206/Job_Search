from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from profile_manager import ProfileManager

class BaseATSHandler(ABC):
    def __init__(self, profile_manager: ProfileManager):
        self.profile = profile_manager

    @abstractmethod
    def can_handle(self, url: str, content: str = "") -> bool:
        """Return True if this handler matches the given job URL or page content."""
        pass

    @abstractmethod
    async def fill_form(self, page, cover_letter: str = "") -> Dict[str, Any]:
        """
        Fill the application form using Playwright Page object.
        Returns result dict: {'success': bool, 'fields_filled': int, 'notes': str}
        """
        pass

    @abstractmethod
    async def submit_form(self, page) -> bool:
        """Click submit button if present."""
        pass
