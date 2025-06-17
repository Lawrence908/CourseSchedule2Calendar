from abc import ABC, abstractmethod
from typing import Dict, Any, Optional

class CalendarProvider(ABC):
    """Base class for calendar providers."""
    
    @abstractmethod
    def get_auth_url(self) -> tuple[str, str, Any]:
        """Get the authorization URL for the provider."""
        pass
    
    @abstractmethod
    def handle_callback(self, auth_response: str, flow: Any) -> Any:
        """Handle the OAuth callback and return the service."""
        pass
    
    @abstractmethod
    def create_event(self, service: Any, event_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create an event in the calendar."""
        pass
    
    @abstractmethod
    def get_provider_name(self) -> str:
        """Get the name of the provider."""
        pass
    
    @abstractmethod
    def get_provider_icon(self) -> str:
        """Get the icon URL for the provider."""
        pass

    @abstractmethod
    def get_provider_key(self) -> str:
        """Return a unique key for this provider (used in URLs and dicts)."""
        pass 