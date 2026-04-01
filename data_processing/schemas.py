from pydantic import BaseModel, Field
from typing import Any, Dict, List, Optional, Union

class Document(BaseModel):
    source_url: str = ""
    content_type: str = ""
    text: Optional[str] = Field(None, alias="raw_text")
    cleaned_text: Optional[str] = None
    language: Optional[str] = None
    metadata: Dict[str, Any] = {}
    tables: List[Any] = []
    figures: List[Any] = []
    visual_data: List[Any] = []
    document_type: Optional[str] = None
    keywords: List[str] = []

    class Config:
        populate_by_name = True
        extra = 'ignore'