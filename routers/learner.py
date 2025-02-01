from beanie import PydanticObjectId

from fastapi import APIRouter, Security, status, HTTPException, UploadFile, Form, File, Path
from fastapi.responses import JSONResponse, StreamingResponse

from typing import Annotated
from pydantic import ValidationError, Field

from io import BytesIO

from dotenv import load_dotenv

from security.helpers import get_current_active_user

from utils.helpers import get_learners_in_blocks, get_learner_or_staff, USER_NOT_FOUND_EXCEPTION

from pprint import pprint

from schemas.learner import GetLearnerResponse, NewLearner, NewLearnerResponse

from models.learner import Learners
from models.staff import Staff
from utils.models import DefaultDocs


load_dotenv()


router = APIRouter(
    prefix='/api/v1/learner',
    tags=['Learner']
)

@router.post('', status_code=status.HTTP_201_CREATED, response_model=NewLearnerResponse)
async def add_learner(
    profile: Annotated[UploadFile, File(description="An image to be used as the profile picture")],
    first_name: Annotated[str, Form(description="The new learner first name")],
    last_name: Annotated[str, Form(description="The new learner last name")],
    block: Annotated[str, Form(description="The block the learner is in")],
    room: Annotated[int, Form(description="The room the learner is in")],
    grade: Annotated[int, Form(description="The grade the learner is in")],
    current_user: Annotated[Staff, Security(get_current_active_user, scopes=["add-l"])]
):
    """Adds a new learner to the database"""
    try:
        default_learner = await DefaultDocs.find_one(DefaultDocs.id == "total_learners")
        
        request = NewLearner(
            first_name=first_name,
            last_name=last_name,
            block=block.upper(),
            grade=grade,
            room=room
        )
        NOT_ALLOWED_TO_ADD_TO_BLOCK = HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    "status": "failed",
                    "message":f"Not allowed to add learners to block {block}"
                }
            )
        
        if current_user.role == "jr-matron" and (request.block == "C" or request.block == "D"):
            raise NOT_ALLOWED_TO_ADD_TO_BLOCK 
        elif current_user.role == "sr-matron" and (request.block == "A" or request.block == "B"):
            raise NOT_ALLOWED_TO_ADD_TO_BLOCK

        new_learner = Learners(image=profile.file.read(), **request.model_dump())
        
        await new_learner.save()
        
        #* Increment the total number of learners
        default_learner.total += 1
        await default_learner.save()
        
        return JSONResponse(
            status_code=status.HTTP_201_CREATED,
            content={
                "learner_id": str(new_learner.id),
                'message': 'Learner added successfully'
            }
        )
    except ConnectionError:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail='Service Unavailable'
        )
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail= {
                "error_count": e.error_count(),
                "errors": e.errors()
            }
        )  
       
        
@router.get('/{id}/image')
async def get_learner_image(id: Annotated[str, Path(description="The id of the learner")], current_user: Annotated[Staff, Security(get_current_active_user, scopes=["get-l-i"])]):
    """Fetches the image of the learner with the provided `id` from the database"""
    
    try:
        learner_in_db = await Learners.find_one(Learners.id == PydanticObjectId(id))
        
        if not learner_in_db:
            raise USER_NOT_FOUND_EXCEPTION
        
        NOT_ALLOWED_TO_VIEW_IMAGE = HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    "status": "failed",
                    "message":f"Not allowed to view images of learners in block {learner_in_db}"
                }
            )
        
        if current_user.role == "jr-matron" and (learner_in_db.block == "C" or learner_in_db.block == "D"):
            raise NOT_ALLOWED_TO_VIEW_IMAGE
        elif current_user.role == "sr-matron" and (learner_in_db.block == "A" or learner_in_db.block == "B"):
            raise NOT_ALLOWED_TO_VIEW_IMAGE
        
        image_bytes = learner_in_db.image  #* Get the binary image data
        image_stream = BytesIO(image_bytes)
        
        return StreamingResponse(image_stream, media_type="image/jpeg")
    except ConnectionError:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Oops, you can't complete this action at the moment"
        )


@router.get('/{id}', response_model=GetLearnerResponse)
async def get_learner(id: Annotated[str, Path(description="_id of the learner")], current_user: Annotated[Staff, Security(get_current_active_user, scopes=["get-l"])]):
    """Fetches a learner from the database by the `id` provided in the path url"""
    learner_in_db = await get_learner_or_staff(id)
    
    if not learner_in_db or not isinstance(learner_in_db, Learners):
        raise USER_NOT_FOUND_EXCEPTION
    
    NOT_ALLOWED_TO_GET_LEARNER = HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "status": "failed",
                "message":f"Not allowed to get learners in block {learner_in_db.block}"
            }
        )
    
    if current_user.role == "jr-matron" and (learner_in_db.block == "C" or learner_in_db.block == "D"):
        raise NOT_ALLOWED_TO_GET_LEARNER
    elif current_user.role == "sr-matron" and (learner_in_db.block == "A" or learner_in_db.block == "B"):
        raise NOT_ALLOWED_TO_GET_LEARNER
    
    return learner_in_db.model_dump(exclude=["image"])      


@router.get("")
async def get_all_learners(current_user: Annotated[Staff, Security(get_current_active_user, scopes=["get-l"])]):
    """Fetches all learners from the database who are in the blocks the current user is authoritative of"""
    
    if current_user.role == "jr-matron":
        learners = await get_learners_in_blocks("A", "B")
        return learners
    elif current_user.role == "sr-matron":
        learners = await get_learners_in_blocks("C", "D")
        return learners


@router.delete('/{id}')
async def delete_learner(id: Annotated[str, Path(description="The ID of the learner to delete")], current_user: Annotated[Staff, Security(get_current_active_user, scopes=["get-l"])]):
    pass