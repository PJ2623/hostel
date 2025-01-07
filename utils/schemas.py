from pydantic import BaseModel, Field, field_validator, model_validator, field_validator

from typing import Annotated


class UserBaseSchema(BaseModel):
    first_name: Annotated[str, Field(min_length=2, max_length=20, examples=['John'])]
    last_name: Annotated[str, Field(min_length=2, max_length=20, examples=['Doe'])]
    
    
class GenericResponse(BaseModel):
    status: str = "success"
    message: str = "Action completed successfully"