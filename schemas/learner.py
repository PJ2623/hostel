from fastapi import status, HTTPException

from pydantic import BaseModel, Field, field_validator, model_validator, field_validator
from typing import Annotated, Optional, Literal

from typing_extensions import Self

from utils.schemas import UserBaseSchema


class NewLearner(UserBaseSchema):
    block: Annotated[Literal["A", "B", "C", "D"], Field(description='The block the learner is in', examples=['D'])]
    grade: Annotated[int, Field(description="Learner's grade", ge=8, le=12)]
    room: Annotated[int, Field(description="The room the learner is in", ge=1, le=6)]
    
    
    # * Checks if learner assigned block and grade are valid
    @model_validator(mode='after')
    def validate_learner_assigned_block_and_grade(self) -> Self:
        block = self.block
        grade = self.grade
        
        error_msg =  HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Learner in grade {grade} cannot be in block {block}"
        )
        
        if  block == "A" and not ( grade == 8 ):
            raise error_msg
        elif block == "B" and not ( grade == 9 ):
            raise error_msg
        elif block == "C" and not ( grade == 10 ):
            raise error_msg
        elif block == "D" and not ( grade >= 11 ):
            raise error_msg
        
        return self


class GetLearnerResponse(BaseModel):
    id: str
    first_name: str
    last_name: str
    block: str
    grade: int
    room: int
    present: bool

class NewLearnerResponse(BaseModel):
    learner_id: str
    message: str = "Learner added successfully"