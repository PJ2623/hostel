"""### Contains all `Learner` models
"""

from beanie import Document, PydanticObjectId
from utils.models import UserBaseModel

from typing import Annotated, Literal
from pydantic import Field, field_serializer


class Learners(Document, UserBaseModel):
    grade: Annotated[int, Field(ge=8 ,le=12)]
    room: Annotated[int, Field(ge=1, le=6)]
    block: Literal["A", "B", "C", "D"]
    present: bool = True
    last_duty: str = ""
    
    @field_serializer("id")
    def convert_pydantic_object_id_to_string(self, id:PydanticObjectId):
        return str(id)