# Django GraphQL

Instructions for setting up GraphQL in a Django Project

---

**Table of Contents**

1. [Why Graphql?](#why-graphql)
1. [Graphene Installation](#graphene-installation)
1. [Creating Schemas](#creating-schemas)
1. Using Graphiql

## Graphene Installation

Install Graphene: `pip install django_graphene`

## Why Graphql?

- Get only the data that you want
- Easier to manage endpoints

## Creating Schemas

```py
import re
import enum

from fastapi import status, HTTPException

from pydantic import BaseModel, Field, field_validator, model_validator, field_validator

from typing import Annotated, Optional

from typing_extensions import Self
    
    
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

```

[![Patrick Mateus](me.jpg)](http://127.0.0.1:8000/docs)

| Light Color | Current State | Next State |
| :------ | :------ | :------ |
| Green | Green | Yellow |
| Yellow | Yellow | Red |

<details>
<summary>Section Header</summary>

Section Body text.

- Hello
- World
</details>