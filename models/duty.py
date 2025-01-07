"""### Contains all `Learner` models
"""
from beanie import Document, PydanticObjectId

from typing import Annotated, Literal
from pydantic import Field, field_serializer


class Duties(Document):
    id: Annotated[str, Field(description="The name of the duty",min_length=6, max_length=50)]
    description: Annotated[str, Field(description="Description of the duty",min_length=6, max_length=100)]
    participants: Annotated[int, Field(description="Number of learners who should be assigned to the duty")]
    
    
class AssignedDuties(Document):
    learner_details: Annotated[dict, Field(description="Details of the learner")]
    assigned_duty: Annotated[str, Field(description="Duty assigned to the learner")]
    week_day: Annotated[int, Field("Day of the week the duty was assigned")]
    day: Annotated[int, Field(description="Day of the month the duty was assigned")]
    month: Annotated[int, Field(description="Month the duty was assigned")]
    year: Annotated[int, Field(description="Year the duty was assigned")]
    completed: Annotated[bool, Field(description="Indicates if the duty has been completed")]
    
    @field_serializer("id")
    def convert_pydantic_object_id_to_string(self, id:PydanticObjectId):
        return str(id)