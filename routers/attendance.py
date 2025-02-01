from bson.errors import InvalidId

from datetime import datetime

from beanie import PydanticObjectId
from beanie.operators import And

from fastapi import APIRouter, Security, status, HTTPException, Query
from fastapi.responses import JSONResponse

from typing import Annotated, Literal
from pydantic import ValidationError, Field


from security.helpers import get_current_active_user


from pprint import pprint

from schemas.attendance import MarkAttendance

from models.learner import Learners
from models.attendance import Attendance
from models.staff import Staff


router = APIRouter(
    prefix='/api/v1/attendance',
    tags=['Attendance']
)
current_date = datetime.now()

@router.post("")
async def mark_attendance(request: MarkAttendance, current_user: Annotated[Staff, Security(get_current_active_user, scopes=["mark-a"])]):
    """Marks `present` True for `activity` for all learners who's IDs are in `present_learner` and False for those not in `present_learners`"""
    try:
        user_role = current_user.role
        
        if request.present_learners:
            present_learners = [await Learners.get(PydanticObjectId(learner_id)) for learner_id in request.present_learners]        
            
            for learner in present_learners:
                
                #* Skip None values for non existent IDs
                if not learner:
                    continue
                
                block = learner.block
                
                #* Ensure user's mark attendance for their designated blocks
                if not learner or (user_role == "jr-matron" and (block == "C" or block == "D")) or (user_role == "sr-matron" and (block == "A" or block == "B")):
                    continue
                
                learner_already_marked = await Attendance.find_one(And(
                    Attendance.learner_details.id == str(learner.id),
                    Attendance.day == current_date.day,
                    Attendance.week_day == current_date.weekday(),
                    Attendance.month == current_date.month,
                    Attendance.activity == request.activity,
                ))
                
                if learner_already_marked:

                    #* Skip None values for learner IDs not found in DB and learners already marked present
                    if not learner or learner_already_marked.present == True:
                        continue
                    elif learner_already_marked.present == False:
                        #* If learner was marked absent, mark present and move on to next
                        learner_already_marked.present = True
                        await learner_already_marked.save()
                        continue
                
                attendance = Attendance(
                    activity=request.activity,
                    day=current_date.day,
                    week_day=current_date.weekday(),
                    month=current_date.month,
                    year=current_date.year,
                    present=True,
                    learner_details=learner.model_dump(exclude=["present", "image"])
                )
                
                await attendance.save()
                        
        if request.absent_learners:
            absent_learners = [await Learners.get(PydanticObjectId(learner_id)) for learner_id in request.absent_learners]
            
            for learner in absent_learners:
                block = learner.block
                
                #* Skip None values for non existent IDs and
                #* Ensure user's mark attendance for their designated blocks
                if not learner or (user_role == "jr-matron" and (block == "C" or block == "D")) or (user_role == "sr-matron" and (block == "A" or block == "B")):
                    continue                
                
                learner_already_marked = await Attendance.find_one(And(
                    Attendance.learner_details.id == str(learner.id),
                    Attendance.day == current_date.day,
                    Attendance.week_day == current_date.weekday(),
                    Attendance.month == current_date.month,
                    Attendance.activity == request.activity
                ))
                
                if learner_already_marked:                
                    #* Skip None values for learner IDs not found in DB and learners already marked absent
                    if not learner or learner_already_marked.present == False:
                        continue
                    elif learner_already_marked.present == True:
                        #* If learner was marked present, mark absent and move on to next
                        learner_already_marked.present = False
                        await learner_already_marked.save()
                        continue
                
                attendance = Attendance(
                    activity=request.activity,
                    day=current_date.day,
                    week_day=current_date.weekday(),
                    month=current_date.month,
                    year=current_date.year,
                    present=False,
                    learner_details=learner.model_dump(exclude=["present", "image"])
                )
                
                await attendance.save()
         
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "status": "success",
                "message": f"Attendance marked for {request.activity}"
            }
        )
    except ConnectionError:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                "status": "failed",
                "message": "Oops, can't perform action now, try again later"
            }
        )
    except InvalidId:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={
                "status": "failed",
                "message": "Invalid learner IDs provided"
            }
        )
        

@router.get("")
async def get_attendance(
    current_user: Annotated[Staff, Security(get_current_active_user, scopes=["get-a"])],
    activity: Annotated[Literal["evening-study", "afternoon-study", "church", "supper", "breakfast"] | None, Query(description="Activity that attendance was taken for")] = None,
    day: Annotated[int | None, Query(description="Day of the month attendance was taken", ge=1, le=31)] = None,
    weekday: Annotated[int | None, Query(description="Day of the week attendance was taken", ge=0, le=6)] = None,
    month: Annotated[int | None, Query(description="Month attendance was taken", ge=1, le=12)] = None,
    year: Annotated[int | None, Query(description="Year attendance for the activity was taken")] = None
):
    """Returns all Attendance documents matching query parameters. If no query parameters
       provided, all attendance taken for all activities on the day is returned
    """
    query_params = [activity, day, weekday, month, year]
    query_values = {}
    user_role = current_user.role
    
    for query_param in query_params:
        if not query_param:
            continue
        
        param_index = query_params.index(query_param)
        
        if param_index == 0:
            query_values.update({"activity": query_param})
        elif param_index == 1:
            query_values.update({"day": query_param})
        elif param_index == 2:
            query_values.update({"week_day": query_param})
        elif param_index == 3:
            query_values.update({"month": query_param})
        elif param_index == 4:
            query_values.update({"year": query_param})

    if not query_values:
        attendances = await Attendance.find(
            Attendance.day == current_date.day,
            Attendance.month == current_date.month,
            Attendance.year == current_date.year
        ).to_list()
        
        serialized_attendance = []
        
        for attendance in attendances:
            block = attendance.learner_details.get("block")
            
            #* Skip None values for non existent IDs and
            #* Ensure user's get attendance for their designated blocks
            if (user_role == "jr-matron" and (block == "C" or block == "D")) or (user_role == "sr-matron" and (block == "A" or block == "B")):
                continue
            
            serialized_attendance.append(attendance.model_dump())
        
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "status": "success",
                "message": "Retrieved attendance taken for all activities for the day",
                "detail": serialized_attendance
            }
        )
    
    attendances = await Attendance.find(query_values).to_list()
    serialized_attendance = []
            
    if not attendances:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "status": "failed",
                "message": "No attendance matching your query was found"
            }
        )
        
    for attendance in attendances:
        block = attendance.learner_details.get("block")
        
        #* Skip None values for non existent IDs and
        #* Ensure user's get attendance for their designated blocks
        if (user_role == "jr-matron" and (block == "C" or block == "D")) or (user_role == "sr-matron" and (block == "A" or block == "B")):
            continue
        
        serialized_attendance.append(attendance)
    
    return {"details": serialized_attendance}