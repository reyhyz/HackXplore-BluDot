from pydantic import BaseModel, Field
from typing import List
from schemas import TableField

class ChapterExtractionRequest(BaseModel):
    chapter_id: str = Field(
        description="The exact chapter or sub-section identifier found on the form (e.g., '5.3.1', '5.4', '5.4.1')."
    )
    table_data: List[TableField] = Field(
        description="A list of all key-value field pairs found within this chapter's table."
    )