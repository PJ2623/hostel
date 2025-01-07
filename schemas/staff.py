import re

from fastapi import status, HTTPException

from pydantic import BaseModel, Field, field_validator, model_validator, field_validator
from typing import Annotated, Optional, Literal

from typing_extensions import Self

from utils.schemas import UserBaseSchema


class NewStaff(UserBaseSchema):
    username: Annotated[str, Field(min_length=6, max_length=100, examples=["boom"])]
    role: Annotated[Literal["jr-matron", "sr-matron", "chief-matron", "super-user"], Field(description="The staff member's position")]
    password: Annotated[str, Field(min_length=6, max_length=100, examples=["Password@123"])]
    verify_password: Annotated[str, Field(min_length=6, max_length=100, examples=["Password@123"])]
    
    # * Validate the password to ensure it has at least one uppercase letter,
    # * one special character, one lowercase letter, and one number
    @field_validator('password')
    @classmethod
    def validate_password(cls, v):
        if not re.search(r'[A-Z]', v):
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail='Password must contain at least one uppercase letter'
            )
        if not re.search(r'[a-z]', v):
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail='Password must contain at least one lowercase letter'
            )
        if not re.search(r'\d', v):
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Password must contain at least one number"
            )
        if not re.search(r'[@$!%*?&#]', v):
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Password must contain at least one special character"
            )
        return v
    
    # * Check if password and verify password fields match
    @model_validator(mode='after')
    def check_password_match(self) -> Self:
        password = self.password
        verify_password = self.verify_password

        if password is not None and verify_password is not None and password != verify_password:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Passwords do not match"
            )
        return self
        
    # * Check if first name and last name in password
    @model_validator(mode='after')
    def check_first_name_last_name_in_password(self) -> Self:
        first_name = self.first_name
        last_name = self.last_name
        password = self.password

        if first_name in password:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Password contains first name"
            )
        if last_name in password:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Password contains last name"
            )
        return self
    
    
class NewStaffResponse(BaseModel):
    username: Annotated[str, Field(description="username of new staff account")]
    message: Annotated[str, Field(description="Informative message about account creation")]