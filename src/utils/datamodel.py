"""Document metadata data model."""
from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List
from datetime import datetime


@dataclass
class AuditAlert:
    """Represents a single audit rule violation."""
    rule_name: str
    severity: str
    description: str
    affected_companies: List[str] = field(default_factory=list)
    affected_files: List[str] = field(default_factory=list)
    details: Dict[str, Any] = field(default_factory=dict)


@dataclass
class CompanyAuditResult:
    """Aggregated audit view per company."""
    company_name: str
    file_count: int = 0
    authors: List[str] = field(default_factory=list)
    last_modified_by: List[str] = field(default_factory=list)
    creation_time_range: Optional[tuple] = None
    modification_time_range: Optional[tuple] = None
    templates_used: List[str] = field(default_factory=list)
    risk_score: int = 0
    risk_level: str = "low"


@dataclass
class DocumentMeta:
    """Represents metadata extracted from a single document."""
    filename: str = ""
    filepath: str = ""
    file_format: str = ""
    
    # Core metadata
    author: Optional[str] = None
    last_modified_by: Optional[str] = None
    created: Optional[datetime] = None
    modified: Optional[datetime] = None
    title: Optional[str] = None
    subject: Optional[str] = None
    company: Optional[str] = None
    keywords: Optional[str] = None
    comments: Optional[str] = None
    template: Optional[str] = None
    revision: Optional[str] = None
    total_editing_time: Optional[int] = None
    
    # File system info
    file_size: Optional[int] = None
    
    # Parsing status
    parse_success: bool = True
    error_message: Optional[str] = None
    
    # Extra raw fields (parser-specific)
    raw_props: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'filename': self.filename or '',
            'filepath': self.filepath or '',
            'format': self.file_format or '',
            'author': self.author or '',
            'last_modified_by': self.last_modified_by or '',
            'created': self._fmt_datetime(self.created),
            'modified': self._fmt_datetime(self.modified),
            'title': self.title or '',
            'subject': self.subject or '',
            'company': self.company or '',
            'keywords': self.keywords or '',
            'comments': self.comments or '',
            'revision': self.revision or '',
            'file_size': self.file_size or 0,
            'status': '成功' if self.parse_success else f'失败: {self.error_message}'
        }
    
    def to_dict_full(self) -> Dict[str, Any]:
        """Convert to dictionary including raw properties."""
        d = self.to_dict()
        d.update(self.raw_props)
        return d
    
    @staticmethod
    def _fmt_datetime(dt: Optional[datetime]) -> str:
        if dt is None:
            return ''
        if isinstance(dt, str):
            return dt
        return dt.isoformat()
    
    @property
    def display_created(self) -> str:
        return self._fmt_datetime(self.created)
    
    @property
    def display_modified(self) -> str:
        return self._fmt_datetime(self.modified)
