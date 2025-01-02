from pydantic import BaseModel, Field

from typing import Annotated

from . requests import LearnerBlock, UserBase, StaffRole


class UserInDB(UserBase):
    permissions: Annotated[list, Field(description="A list of the user's permissions", alias="permissions")]
    image: Annotated[dict, Field(description="A dictionary with information about the user's picture", alias="image")]
    active: bool
    
    
class LearnerInDB(UserInDB):
    grade: Annotated[int, Field(ge=8 ,le=12)]
    block: Annotated[LearnerBlock, Field(description='The block the learner is in', examples=['D'])]

   
class StaffInDB(UserInDB):
    role: Annotated[StaffRole, Field(description='The role of the staff member being created')]


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    username: str | None = None
    scopes: list[str] = []