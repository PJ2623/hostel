from pprint import pprint
import secrets
from datetime import datetime

from pymongo.errors import DuplicateKeyError, ConnectionFailure

from fastapi import APIRouter, Query,Security, status, HTTPException, Path, Body, BackgroundTasks
from fastapi.responses import JSONResponse
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm

from typing import Annotated
from pydantic import ValidationError, Field

from models.requests import Duty, DutyUpdate, SpecialDuties
from utils.security import get_current_active_user
from utils.background_tasks import save_assigned_duties_in_db 
from utils.helpers import assign_duties_to_learners
from database import database


router = APIRouter(
    prefix="/api/v1/duty",
    tags=["Duty"]
)


@router.post("")
async def add_duty(request: Duty,  current_user: Annotated[dict, Security(get_current_active_user, scopes=["add-d"])]):
    
    error_msg = HTTPException(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        detail="Failed to create duty, Try again"
    )

    new_duty = request.model_dump()
    new_duty.update({
        "_id": new_duty.get("id")
    })
    
    new_duty.pop("id")
    
    try:
        total_participants = await database.duties.find_one({"_id": "total participants"})
        
        participants = total_participants.get("participants") + new_duty.get("participants")
        
        await database.duties.update_one({"_id": "total participants"}, {"$set": {"participants": participants}}) # * Update total participants count
        
        insert_duty_response = await database.duties.insert_one(new_duty)
        
        if insert_duty_response:
            return JSONResponse(
                status_code=status.HTTP_201_CREATED,
                content={
                    "id": insert_duty_response.inserted_id
                }
            )
            
        raise error_msg
    except DuplicateKeyError:
        
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Duty with id {request.id} already exists"
        )
    except ConnectionFailure:
        raise error_msg
    

@router.post("/assign")
async def assign_special_duties(request: SpecialDuties,  current_user: Annotated[dict, Security(get_current_active_user, scopes=["assign-s-d"])]):
    
    total_learners = len(request.learners)
    total_participants = 0
    request_dump = request.model_dump(by_alias=True)
    
    for duty in request.duties:
        total_participants += duty.participants
        
    if not total_participants >= total_learners:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Not enough duties to assign to learners"
        )
        
    assigned_duties = assign_duties_to_learners(learners=request_dump.get("learners"), duties=request_dump.get("duties"))
    
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content=assigned_duties
    )


@router.post("/mark")
async def mark_assigned_duty(learners: Annotated[list[str], Body(description="The id of the learner")],  current_user: Annotated[dict, Security(get_current_active_user, scopes=["mark"])]):
    failed_mark = []
    successful_mark = []
    user_role = current_user.get("role")
    
    for learner in learners:
        learner_in_db = await database.users.find_one({"_id": learner})
        learner_block = learner_in_db.get("block")

        if not user_role == "jr-matron" and learner_block in ["A", "B"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot mark attendance for learners in blocks A or B"
            )
        elif not user_role == "sr-matron" and learner_block in ["C", "D"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot mark attendance for learners in blocks C or D"
            )

        update_response = await database.assigned_duties.update_one({"id": learner}, {"$set": {"completed": True}})
        
        if not update_response:
            failed_mark.append(learner)
            continue
        
        successful_mark.append(learner)

    
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={
            "successful-mark": successful_mark,
            "failed-mark": failed_mark
        }
    )


@router.get("/assign")
async def assign_duties(background_tasks: BackgroundTasks,  current_user: Annotated[dict, Security(get_current_active_user, scopes=["assign-d"])]):
    
    date = datetime.now()
    week_day = date.strftime("%A")
    
    if not week_day == "Saturday":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Duties not assigned today"
        )
        
    find_one_response = await database.duties.find_one({"_id": "total participants"})
    
    Duty(**find_one_response)
    
    if not find_one_response:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Something went wrong. Could not generate duties."
        )
        
    total_participants = find_one_response.get("participants")
    total_learners = await database.users.count_documents({"type": "learner"})
    
    if not total_participants >= total_learners:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Not enough duties to assign to learners"
        )

    duties = await database.duties.find({'_id': {'$ne': 'total participants'}}).to_list(length=None)
    learners = await database.users.find({"type": "learner"}).to_list(length=None)
    learners = [learner.get("_id") for learner in learners]
    assigned_duties = assign_duties_to_learners(learners=learners, duties=duties)
    
    background_tasks.add_task(save_assigned_duties_in_db, duties=assigned_duties)
        
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={"duties": assigned_duties}
    )
       
       
@router.get("/assigned")
async def get_assigned_duties(current_user: Annotated[dict, Security(get_current_active_user, scopes=["get-a-d"])], id: Annotated[str | None, Query(description="The name of the duty", min_length=6, max_length=50)] = None):
    
    if not id:
        assigned_duties = await database.assigned_duties.find({}).to_list(None)
        
        return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={
            "duties": assigned_duties
        }
    )  
    
    assigned_duties = await database.assigned_duties.find({"_id": id}).to_list(None)
    
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={
            "duties": assigned_duties
        }
    )


@router.get("")
async def get_duties(current_user: Annotated[dict, Security(get_current_active_user, scopes=["add-u-i"])],id: Annotated[str | None, Query(description="The name of the duty", min_length=6, max_length=50)] = None):
    if id == "total participants":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Duty not found"
        )
        
    if id:
        try:
            find_duty_response = await database.duties.find_one({"_id": id})
            
            if find_duty_response:
                duty = Duty(**find_duty_response)
                
                return JSONResponse(
                    status_code=status.HTTP_200_OK,
                    content=duty.model_dump()
                )
        except ValidationError:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Invalid response"
            )
        except:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Failed to retrieve duty"
            )
            
    cursor_response = database.duties.find({'_id': {'$ne': 'total participants'}})
    find_duties_response = await cursor_response.to_list(length=None)
    duties = []
    invalid_responses = 0
    
    if not find_duties_response:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Failed to retrieve duties. Try again"
        )
        
    for duty in find_duties_response:
        
        try:
            Duty(**duty)
            duties.append(duty)
        except ValidationError:
            invalid_responses += 1
            continue
    
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={
            "duties": duties,
            "invalid_responses": invalid_responses
        }
    )


@router.put("/{id}")
async def update_duty(id: Annotated[str, Path(description="The name of the duty",min_length=6, max_length=50)], request: DutyUpdate,  current_user: Annotated[dict, Security(get_current_active_user, scopes=["update-d"])]):
    
    # * Updating the total participants document
    if request.participants:
        find_duty_response = await database.duties.find_one({"_id": "total participants"})
        
        total_participants = find_duty_response.get("participants") # new - old
        find_response = await database.duties.find_one({"_id": id})
        participants = find_response.get("participants")
        
        # * Update total participants by subtracting from it
        # * The current participants amount and then adding to it the submitted participants amount
        await database.duties.update_one({"_id": "total participants"}, {"$set": {"participants": (total_participants - participants) + request.participants}})
        
    if (not request.description or request.description) and request.participants == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Delete the duty instead"
        )
        
    update_response = await database.duties.update_one({"_id": id}, {"$set": request.model_dump(exclude_none=True)})
    
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content=update_response.raw_result
    )
    

@router.delete("/{id}")
async def delete_duty(id: Annotated[str, Path(description="The name of the duty",min_length=6, max_length=50)], current_user: Annotated[dict, Security(get_current_active_user, scopes=["delete-d"])]):
    # * Remember to update the total participants count when deleting a document
    find_one_response = await database.duties.find_one({"_id": id})
    duty_participants = find_one_response.get("participants")
    delete_response = await database.duties.delete_one({"_id": id})
    
    if not delete_response.deleted_count:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Duty not found"
        )
        
    find_one_response = await database.duties.find_one({"_id": "total participants"})
    total_participants = find_one_response.get("participants")
    
    await database.duties.update_one({"_id": "total participants"}, {"$set": {"participants": total_participants - duty_participants}})
    
    return JSONResponse(
        status_code=status.HTTP_204_NO_CONTENT,
        content=None
    )