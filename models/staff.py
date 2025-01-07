from beanie import Document

from typing import Annotated, Literal
from pydantic import Field

from utils.models import UserBaseModel


class Staff(Document, UserBaseModel):
    id: Annotated[str, Field(min_length=6, max_length=100, description="The username of a staff member")]
    password: Annotated[str, Field(min_length=6, max_length=100, examples=["Password@123"])]
    role: Annotated[Literal["jr-matron", "sr-matron", "super-user", "chief-matron"], Field()]
    active: Annotated[bool, Field(description="bool field to mark if user account is active")] = True
    present: Annotated[bool, Field(description="Marks if the staff member is present at work")] = True
    permissions: Annotated[list, Field(description="A list of permissions the staff member has")]