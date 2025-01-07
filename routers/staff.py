from pymongo.errors import DuplicateKeyError

from fastapi import APIRouter, Security, status, HTTPException, UploadFile, File,Path, Form, Query
from fastapi.responses import JSONResponse, StreamingResponse

from typing import Annotated
from pydantic import ValidationError

from io import BytesIO
from PIL import Image

from dotenv import load_dotenv


from security.helpers import get_current_active_user, get_password_hash

from utils.helpers import get_learners_in_blocks, get_learner_or_staff, USER_NOT_FOUND_EXCEPTION

from schemas.staff import NewStaff, NewStaffResponse
from models.staff import Staff

from pprint import pprint


load_dotenv()


router = APIRouter(
    prefix='/api/v1/staff',
    tags=['Staff']
)

@router.post('', status_code=status.HTTP_201_CREATED, response_model=NewStaffResponse)
async def add_staff(
    profile: Annotated[UploadFile, File(description="An image to be used as the profile picture")],
    first_name: Annotated[str, Form(description="The new staff member's first name")],
    last_name: Annotated[str, Form(description="The new staff member's last name")],
    username: Annotated[str, Form(description="The new staff member's username")],
    role: Annotated[str, Form(description="The position of the new staff member")],
    password: Annotated[str, Form(description="The password to be used to log into the account")],
    verify_password: Annotated[str, Form(description="Should match `password`")],
):
    """Create new staff account 
    """
    
    try:
        request = NewStaff(
            first_name=first_name,
            last_name=last_name,
            username=username,
            role=role,
            password=password,
            verify_password=verify_password
        )
        
        new_staff = Staff(
            image=profile.file.read(),
            id=request.username,
            first_name=request.first_name,
            last_name=request.last_name,
            role=request.role,
            password=get_password_hash(request.password),
            permissions=["me"]
        )
        
        await new_staff.save()
        
        return JSONResponse(
            content={
                "username": new_staff.id,
                "message": "Account created successfully"
            },
            status_code=status.HTTP_201_CREATED
        )
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={
                "error_count": e.error_count(),
                "errors": e.errors()
            }
        )
    except DuplicateKeyError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already exists"
        )
    except ConnectionError:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Oops, you can't complete this action at the moment"
        )
        
        
@router.get('/{id}/image')
async def get_staff_image(id: Annotated[str, Path(min_length=4, max_length=20, description='`id` of the user')]):
    try:
        user_in_db = await Staff.find_one(Staff.id == id)

        if not user_in_db:
            raise USER_NOT_FOUND_EXCEPTION
        
        image_bytes = user_in_db.image  #* Get the binary image data
        image_stream = BytesIO(image_bytes)
        
        return StreamingResponse(image_stream, media_type="image/jpeg")
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Error processing image")


@router.get('/{id}')
async def get_staff(id: Annotated[str, Path(min_length=4, max_length=20, description='`id` of the user')]):
    staff_in_db = await get_learner_or_staff(id)
    
    if not staff_in_db or not isinstance(staff_in_db, Staff):
        raise USER_NOT_FOUND_EXCEPTION
        
    return staff_in_db.model_dump(exclude=["image", "password", "permissions", "active"])
            

@router.delete('/{id}')
async def delete_staff(id: Annotated[str, Path(min_length=4, max_length=20, description='`id` of the user')]):
    delete_response = await Staff.delete(Staff.id == id)
    
    if delete_response.deleted_count == 0:
        raise USER_NOT_FOUND_EXCEPTION
        
    return JSONResponse(
        content={
            "message": "User deleted successfully"
        },
        status_code=status.HTTP_200_OK
    )