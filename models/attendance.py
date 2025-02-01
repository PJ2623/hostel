from beanie import Document, PydanticObjectId

from typing import Annotated, Literal
from pydantic import Field, field_serializer


class Attendance(Document):
    activity: Annotated[Literal["evening-study", "afternoon-study", "church", "supper", "breakfast"], Field(description="The activity attendance is being taken for")]
    learner_details: dict
    present: bool = False #* Mark whether learner is present or absent for activity 
    week_day: int
    day: int 
    month: int
    year: int
    
    @field_serializer("id")
    def convert_pydantic_object_id_to_string(self, id:PydanticObjectId) -> str:
        return str(id)