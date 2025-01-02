# TODO Research possible exceptions that maybe thrown by functions such as the database connection and handle them

import os
from datetime import timedelta

from pymongo.errors import DuplicateKeyError

from fastapi import APIRouter, Security, status, HTTPException, UploadFile, File,Path, Body, Depends, Query
from fastapi.responses import JSONResponse, StreamingResponse
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm

from typing import Annotated
from pydantic import ValidationError

from io import BytesIO

from PIL import Image

from dotenv import load_dotenv

from models.requests import Learner, StaffMember, UserUpdate, UserType
from models.responses import LearnerInDB, StaffInDB
from utils.security import get_current_active_user, get_password_hash
from utils.helpers import get_learners_in_blocks, find_user, update_a_user
from utils.helpers import serialize_user_in_db

from pprint import pprint
from io import BytesIO


load_dotenv()


router = APIRouter(
    prefix='/api/v1/user',
    tags=['Learner']
)

@router.post('')
async def add_user(current_user: Annotated[dict, Security(get_current_active_user, scopes=["add-u"])], request: Annotated[Learner | StaffMember, Body(description="User is either learner or staff member")]):
    
    new_user: dict = request.model_dump(exclude=['verify_password'], by_alias=True)
    
    new_user.update({
        'password': get_password_hash(password=new_user.get('password')),
        'type': request.type.value,
        'active': True,
        'image': {}
    })
    
    if isinstance(request, Learner):
        
        # * Ensure matron can only create users in their respective blocks
        if current_user.get("role") == "jr-matron" and not request.block.value in ["A", "B"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"msg": "Failed to create user", "details": "jr-matron cannot create user in block C or D"}
            )
        elif current_user.get("role") == "sr-matron" and not request.block.value in ["C", "D"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"msg": "Failed to create user", "details": "sr-matron cannot create user in block A or B"}
            )
            
        new_user.update({
            'block': request.block.value,
            'permissions': ["view-a-d", "me"]
        })
            
    elif isinstance(request, StaffMember):
        
        if not current_user.get("role") == "super-user":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Cannot create user of type staff"
            )
        
        if request.role.value == "jr-matron" or request.role.value == "sr-matron":
            # * Assign matron permissions
            new_user.update({
                'role': request.role.value,
                'permissions': ["add-u", "add-u-i", "get-u-i", "update-u", "get-u", "get-l-s", "delete-u", "add-d", "assign-s-d","assign-d","view-a-d", "get-a-d", "get-d", "update-d", "delete-d", "mark", "me"]
            })
        else:
            # * Assign super user permissions
            new_user.update({
                "role": request.role.value,
                "permissions": ["add-u", "add-u-i", "get-u-i", "update-u", "get-u", "get-l-s", "delete-u", "me"]
            })
                
    try:
        insert_response = await database.users.insert_one(new_user) # * Save user to database
    except DuplicateKeyError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User id should be unique"
        )
    
    return JSONResponse(
        status_code=status.HTTP_201_CREATED,
        content={
            "id": str(insert_response.inserted_id)
        }
    )


@router.post('/{id}/image')
async def add_user_image(image: Annotated[UploadFile, File(description='Picture of learner')], id: Annotated[str, Path(min_length=4, max_length=20,description='`id` of the learner')], current_user: Annotated[dict, Security(get_current_active_user, scopes=["add-u-i"])]):
    
    try:
        new_image = Image.open(image.file)
        image_byte_array = BytesIO()
        new_image.save(image_byte_array, format=new_image.format)
        image_data = image_byte_array.getvalue()
        
        update_data = {"image": {'content_type': image.content_type, 'data': image_data}}
        
        
        update_one_response = await update_a_user(id=id, role=current_user.get("role"), update_data=update_data)
        
        if not update_one_response:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Failed to upload image"
            )
            
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "detail": update_one_response.raw_result
            }
        )
    except:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to upload image"
        )
        
        
@router.get('/{id}/image')
async def get_user_image(id: Annotated[str, Path(min_length=4, max_length=20,description='`id` of the user')], current_user: Annotated[dict, Security(get_current_active_user, scopes=["get-u-i"])]):
    
    try:
        user_in_db = await find_user(id=id, role=current_user.get("role"))
        
        if not user_in_db:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f'Learner with id {id} not found'
            )
            
        if not user_in_db.get("image").get("data"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No image found"
            )
        
        response = StreamingResponse(
            content=BytesIO(user_in_db.get("image").get("data")),
            media_type=user_in_db.get("image").get('content_type')
        )
            
        if user_in_db.get("type") == "learner":
            LearnerInDB(**user_in_db)
            return response
        elif user_in_db.get("type") == "staff":
            StaffInDB(**user_in_db)
            return response
    except ValidationError as e:
        pprint(e.errors())
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Invalid response. Try again"
        )


@router.put('/{id}')
async def update_user(request: UserUpdate, id: Annotated[str, Path(min_length=4, max_length=20,description='`id` of the learner')], current_user: Annotated[dict, Security(get_current_active_user, scopes=["update-u"])]):
    
    try:
        update_data = request.model_dump(exclude_none=True)
        update_response = await update_a_user(id=id, role=current_user.get("role"), update_data=update_data)
        
        if not update_response:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Failed to update user"
            )
            
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "detail": update_response.raw_result
            }
        )
    except:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update user"
        )


@router.get('/{id}')
async def get_user(id: str, current_user: Annotated[dict, Security(get_current_active_user, scopes=["get-u"])]):
    
    try:
        user_in_db = await find_user(id=id, role=current_user.get("role"))
        
        if not user_in_db:
            
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f'Learner with id {id} not found'
            )
        
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=serialize_user_in_db(user_in_db)
        )
    except ValidationError as e:
        pprint(e.errors())
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Invalid response. Try again"
        )
     
        
@router.get("/")
async def get_learners_or_staff(current_user: Annotated[dict, Security(get_current_active_user, scopes=["get-l-s"])], type: Annotated[UserType | None, Query()] = None):
    
    user_role = current_user.get("role")
    
    if ( user_role == "jr-matron" or user_role == "sr-matron") and (not type or type.value == "staff"):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"User cannot get staff"
        )
    

    if user_role == "jr-matron":
        
        return await get_learners_in_blocks(block1="A", block2="B")
    elif user_role == "sr-matron":
        
        return await get_learners_in_blocks(block1="C", block2="D")
    elif user_role == "super-user":
        
        if not type or type.value == "staff":
            
            staff = []
            staff_in_db = database.users.find({"type": "staff"})
            
            for staff_member in await staff_in_db.to_list(None):
                staff_member = StaffInDB(**staff_member).model_dump(exclude=["password", "image", "active", "permissions", "type"])
                staff_member.update({"role": staff_member.get("role").value})
                staff.append(staff_member)
                
            return JSONResponse(
                status_code=status.HTTP_200_OK,
                content={"staff": staff}
            )

        learners = {"seniors": [], "juniors": []}
        
        learners.update({
            "seniors": await get_learners_in_blocks(block1="C", block2="D"),
            "juniors": await get_learners_in_blocks(block1="A", block2="B")
        })
        
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=learners
        )
            

@router.delete('/{id}')
async def delete_user(id: str, current_user: Annotated[dict, Security(get_current_active_user, scopes=["delete-u"])]):
    # * Set active to false
    try:
        if current_user.get("role") == "super-user":
            update_one_response = await database.users.update_one({'_id': id}, {"$set": {"active": False}})
        elif current_user.get("role") == "jr-matron":
            update_one_response = await database.users.update_one({'_id': id, "type": "learner", "block": {"$in": ["A", "B"]}}, {"$set": {"active": False}})
        else:
            update_one_response = await database.users.update_one({'_id': id, "type": "learner", "block": {"$in": ["C", "D"]}}, {"$set": {"active": False}})
        
        if not update_one_response:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Failed to delete user"
            )
            
        return JSONResponse(
            status_code=status.HTTP_204_NO_CONTENT,
            content={
                "detail": "User deleted"
            }
        )
    except:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete user"
        )