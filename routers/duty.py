from pprint import pprint
from datetime import datetime

from pymongo.errors import DuplicateKeyError, ConnectionFailure

from fastapi import APIRouter, Query,Security, status, HTTPException, Path, Body, BackgroundTasks
from fastapi.responses import JSONResponse

from typing import Annotated
from pydantic import ValidationError, Field
from beanie import PydanticObjectId

from beanie.operators import And

from security.helpers import get_current_active_user

from utils.helpers import assign_duties_to_learners
from utils.schemas import GenericResponse

from schemas.duty import NewDuty, SpecialDuties, NewDutyResponse, GetAssignedDutiesResponse

from models.duty import Duties
from utils.models import DefaultDocs
from models.duty import AssignedDuties

from models.learner import Learners

router = APIRouter(
    prefix="/api/v1/duty",
    tags=["Duty"]
)


@router.post("", status_code=status.HTTP_201_CREATED, response_model=NewDutyResponse)
async def add_duty(request: NewDuty):
    """Add a duty to the database"""
    try:
        default_duty = await DefaultDocs.find_one(DefaultDocs.id == "total-participants")
        default_learner = await DefaultDocs.find_one(DefaultDocs.id == "total_learners")
        
        if (default_duty.total + request.participants) > default_learner.total:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Total participants exceeds the number of learners, please reduce the number of participants"
            )
        
        duty = Duties(**request.model_dump())
        await duty.save()
        
        #* Update the total number of participants
        default_duty.total += duty.participants
        await default_duty.save()
        
        return JSONResponse(
            status_code=status.HTTP_201_CREATED,
            content={"duty": duty.model_dump()}
        )
    except DuplicateKeyError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Duty already exists")
    except ConnectionFailure:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail='Service Unavailable'
        )
    

@router.post("/assign", response_model=GenericResponse)
async def assign_special_duties(request: SpecialDuties):
    learners = await Learners.find(Learners.present == True).to_list()
    duties: list[dict] = [duty.model_dump() for duty in request.duties]
    total_participants = 0
        
    for duty in request.duties:
        total_participants += duty.participants
        
    if len(learners) < total_participants:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "status": "failed",
                "message": "Total participants exceeds present learners"
            }
        )
    elif len(learners) > total_participants:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "status": "failed",
                "message": "Total present learners exceeds total participants"
            }
        )

    await assign_duties_to_learners(learners=learners, duties=duties)
    
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={
            "status": "success",
            "message": "Duties assigned successfully"
        }
    )
        
        
@router.post("/mark")
async def mark_assigned_duties(learners: Annotated[list[str], Body(description="The id of the learner", examples=[["677ab82e0fcee570714969b3"]])]):
    """
    Marks the `completed` field for documents in `AssignedDuties` for
    learner id in `learners`. It does this for documents with `day`,
    `month` and `year` of the current date.
    """
    current_date = datetime.now()

    for learner_id in learners:
        assigned_duty = await AssignedDuties.find_one(
            And(
                AssignedDuties.learner_details.id == learner_id,
                AssignedDuties.day == current_date.day,
                AssignedDuties.week_day == current_date.weekday(),
                AssignedDuties.month == current_date.month,
                AssignedDuties.year == current_date.year
        ))
        
        if not assigned_duty:
            continue
        
        assigned_duty.completed = True
        await assigned_duty.save()
        
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={
            "status": "success",
            "message": "Assigned duties marked"
        }
    )
       
       
@router.get("/assign", response_model=GetAssignedDutiesResponse)
async def get_assigned_duties():
    """Retrieves all duties assigned to learners for the current date"""
    current_date = datetime.now()
    
    assigned_duties = await AssignedDuties.find(
        And(
            AssignedDuties.day == current_date.day,
            AssignedDuties.week_day == current_date.weekday(),
            AssignedDuties.month == current_date.month,
            AssignedDuties.year == current_date.year
    )).to_list()
    
    if not assigned_duties:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={
                "status": "failed",
                "message": "No duties assigned for today"
            }
        )

    duties = [duty.model_dump() for duty in assigned_duties]
    
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={
            "status": "success",
            "assigned_duties": duties
        }
    )


@router.get("")
async def get_duties(id: Annotated[str | None, Query(description="The name of the duty", min_length=6, max_length=50)] = None):
    """Get all duties or a specific duty by `id`"""
    
    
    #* If no id is provided, return all duties
    if not id:
        duties = await Duties.find().to_list()
        
        if not duties:
            return JSONResponse(
                status_code=status.HTTP_404_NOT_FOUND,
                content={
                    "status": "failed",
                    "message": "No duties found"
                }
            )
        
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "duties": [duty.model_dump() for duty in duties]
            }
        )
    
    
    duty = await Duties.get(id)
    
    if not duty:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Duty not found"
        )
    
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={
            "duty": duty.model_dump()
        }
    )
    

@router.delete("/{id}")
async def delete_duty(id: Annotated[str, Path(description="The name of the duty",min_length=6, max_length=50)]):
    pass