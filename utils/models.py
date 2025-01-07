"""General models inheritable by any defined entity"""

from pydantic import BaseModel, Field, field_validator, model_validator, field_validator

from typing import Annotated

from beanie import Document


class UserBaseModel(BaseModel):
    first_name: Annotated[str, Field(min_length=2, max_length=20, examples=['John'])]
    last_name: Annotated[str, Field(min_length=2, max_length=20, examples=['Doe'])]
    image: Annotated[bytes, Field(description="A dictionary with information about the user's picture", alias="image")]
    
    
class DefaultDocs(Document):
    id: str
    total: int