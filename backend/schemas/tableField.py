from pydantic import BaseModel, Field

class TableField(BaseModel):
    field_name: str = Field(
        description="The exact printed label or header of the form field (e.g., 'm Tara', 'm Netto', 'Bearbeitet')."
    )
    value: str = Field(
        description="The handwritten value entered for this field. If blank, write 'EMPTY'."
    )