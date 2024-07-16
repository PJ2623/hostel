import re
import enum

from fastapi import status, HTTPException

from pydantic import BaseModel, Field, field_validator, model_validator, field_validator

from typing import Annotated, Optional

from typing_extensions import Self


class LearnerBlock(enum.Enum):
    A = 'A'
    B = 'B'
    C = 'C'
    D = 'D'
    

class UserType(enum.Enum):
    LEARNER = 'learner'
    STAFF = 'staff'


class StaffRole(enum.Enum):
    JR_MATRON = 'jr-matron'
    SR_MATRON = 'sr-matron'
    SUPER_USER = 'super-user'
    
    
class UserBase(BaseModel):
    id: Annotated[str, Field(min_length=4, max_length=20, examples=['John'], alias='_id')]
    first_name: Annotated[str, Field(min_length=2, max_length=20, examples=['John'])]
    last_name: Annotated[str, Field(min_length=2, max_length=20, examples=['Doe'])]
    type: Annotated[UserType, Field(description="The user's type", examples=["learner"])]
    password: Annotated[str, Field(min_length=6, max_length=100, examples=["Password@123"], alias="password")]


class User(UserBase):
    verify_password: Annotated[str, Field(min_length=6, max_length=100, examples=["Password@123"], alias="verify_password")]
    
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
    
    # * Checks if password and verify password fields match
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
    
    
class Learner(User):
    block: Annotated[LearnerBlock, Field(description='The block the learner is in', examples=['D'])]
    grade: Annotated[int, Field(description="Learner's grade")]
    
    
    # * Checks if learner assigned block and grade are valid
    @model_validator(mode='after')
    def validate_learner_assigned_block_and_grade(self) -> Self:
        block = self.block
        grade = self.grade
        
        error_msg =  HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Learner in grade {grade} cannot be in block {block.value}"
        )
        
        if  block == LearnerBlock.A and not ( grade == 8 ):
            raise error_msg
        elif block == LearnerBlock.B and not ( grade == 9 ):
            raise error_msg
        elif block == LearnerBlock.C and not ( grade == 10 ):
            raise error_msg
        elif block == LearnerBlock.D and not ( grade >= 11 ):
            raise error_msg
        
        return self
    
    @field_validator("grade")
    @classmethod
    def validate_grade(clv, grade):
        if not ( grade >= 8 and grade <= 12):
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Invalid grade. Grade range is 8 - 12, inclusive."
            )
            
        return grade


class StaffMember(User):
    role: Annotated[StaffRole, Field(description='The role of the staff member being created')]
    
    @model_validator(mode='after')
    def checks_user_type_is_valid_for_staff_member(self) -> Self:
        type = self.type
        role = self.role
        
        if not (type.value == "staff"):
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"User type has to be staff to assign {role.value} role"
            )
        return self

class UserUpdate(BaseModel):
    first_name: Optional[str | None] = Field(min_length=2, max_length=20, examples=['John'])
    last_name: Optional[str | None] = Field(min_length=2, max_length=20, examples=['Doe'])
    
    
class Duty(BaseModel):
    id: Annotated[str, Field(description="The name of the duty",min_length=6, max_length=50, alias="_id")]
    description: Annotated[str, Field(description="Description of the duty",min_length=6, max_length=100)]
    participants: Annotated[int, Field(description="Number of learners who should be assigned to the duty")]
    
    
class SpecialDuties(BaseModel):
    duties: list[Duty]
    learners: list[str]
    
    
class DutyUpdate(BaseModel):
    description: Optional[str | None] = Field(description="Description of the duty", min_length=6, max_length=100)
    participants: Optional[int | None] = Field(description="Number of learners who should be assigned to the duty")