from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Union

class Document(BaseModel):
    source_url: str
    content_type: str
    text: Optional[str] = Field(None, alias="raw_text")  # Handles both raw_text and text fields
    cleaned_text: Optional[str] = None
    language: Optional[str] = None
    metadata: Dict[str, Union[str, int]] = {}  # Allow both strings and numbers
    tables: List = []
    figures: List = []
    visual_data: List = []
    document_type: Optional[str] = None
    keywords: List[str] = []

    class Config:
        allow_population_by_field_name = True
        extra = 'ignore'  # Ignore extra fields in the input