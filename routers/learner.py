from pymongo.errors import DuplicateKeyError

from beanie import PydanticObjectId
from beanie.operators import Inc

from fastapi import APIRouter, Security, status, HTTPException, UploadFile, Form, File, Path
from fastapi.responses import JSONResponse, StreamingResponse

from typing import Annotated
from pydantic import ValidationError, Field

from io import BytesIO

from PIL import Image

from dotenv import load_dotenv


from security.helpers import get_current_active_user

from utils.helpers import get_learners_in_blocks, get_learner_or_staff, USER_NOT_FOUND_EXCEPTION

from pprint import pprint

from schemas.learner import GetLearnerResponse, NewLearner, NewLearnerResponse

from models.learner import Learners
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
    except DuplicateKeyError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail='User already exists'
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
async def get_learner_image(id: Annotated[str, Path(description="The id of the learner")]):
    """Fetches the image of the learner with the provided `id` from the database"""
    
    try:
        user_in_db = await Learners.find_one(Learners.id == PydanticObjectId(id))

        if not user_in_db:
            raise USER_NOT_FOUND_EXCEPTION
        
        image_bytes = user_in_db.image  #* Get the binary image data
        image_stream = BytesIO(image_bytes)
        
        return StreamingResponse(image_stream, media_type="image/jpeg")
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Error processing image")
    except ConnectionError:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Oops, you can't complete this action at the moment"
        )


@router.get('/{id}', response_model=GetLearnerResponse)
async def get_learner(id: Annotated[str, Path(description="_id of the learner")]):
    """Fetches a learner from the database by the `id` provided in the path url"""
    learner_in_db = await get_learner_or_staff(id)
    
    if not learner_in_db or not isinstance(learner_in_db, Learners):
        raise USER_NOT_FOUND_EXCEPTION
    
    return learner_in_db.model_dump(exclude=["image"])        


@router.delete('/{id}')
async def delete_learner(id: str):
    pass