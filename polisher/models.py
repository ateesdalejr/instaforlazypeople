from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List
from datetime import datetime
from enum import Enum


class ContentType(Enum):
    """Types of content that can be polished"""
    IMAGE = "image"
    VIDEO = "video"
    TEXT = "text"
    CAROUSEL = "carousel"


class PolishStatus(Enum):
    """Status of the polishing process"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class PolishRequest:
    """Model for incoming polish requests"""
    content_id: str
    content_type: ContentType
    content_url: Optional[str] = None
    content_text: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            "content_id": self.content_id,
            "content_type": self.content_type.value,
            "content_url": self.content_url,
            "content_text": self.content_text,
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat()
        }


@dataclass
class PolishResult:
    """Model for polish operation results"""
    content_id: str
    status: PolishStatus
    original_content: Optional[str] = None
    polished_content: Optional[str] = None
    polished_url: Optional[str] = None
    improvements: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    error_message: Optional[str] = None
    processed_at: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            "content_id": self.content_id,
            "status": self.status.value,
            "original_content": self.original_content,
            "polished_content": self.polished_content,
            "polished_url": self.polished_url,
            "improvements": self.improvements,
            "metadata": self.metadata,
            "error_message": self.error_message,
            "processed_at": self.processed_at.isoformat()
        }


@dataclass
class PolishConfig:
    """Configuration for polishing operations"""
    enhance_quality: bool = True
    apply_filters: bool = True
    optimize_size: bool = True
    add_branding: bool = False
    custom_settings: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            "enhance_quality": self.enhance_quality,
            "apply_filters": self.apply_filters,
            "optimize_size": self.optimize_size,
            "add_branding": self.add_branding,
            "custom_settings": self.custom_settings
        }
