from pydantic import BaseModel, Field
from schemas import ChapterExtractionRequest
from typing import List

class PagePayload(BaseModel):
    chapters: List[ChapterExtractionRequest]