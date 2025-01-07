from pprint import pprint
import secrets

from beanie import PydanticObjectId

from io import BytesIO

from datetime import datetime

from bson.errors import InvalidId

from datetime import datetime

from fastapi import HTTPException, status

from models.duty import AssignedDuties, Duties
from models.staff import Staff
from models.learner import Learners
from utils.models import DefaultDocs


USER_NOT_FOUND_EXCEPTION = HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User not found"
            )

    
async def assign_duties_to_learners(learners: list[Learners], duties: list[dict]):
    '''
    Assigns `duties` to `learners`
    '''
    assigned_duties: list[AssignedDuties] = []
    current_date = datetime.now()
        
    for duty in duties:
        
        while not duty["participants"] == 0:
            random_learner = secrets.choice(learners)
            
            #* Ensure learners are not assigned duties they were assigned previously
            while random_learner.last_duty == duty.get("id"):
                random_learner = secrets.choice(learners)
            
            assigned_duties.append(AssignedDuties(
                learner_details=random_learner.model_dump(exclude=["present", "image"]),
                assigned_duty=duty.get("id"),
                week_day=current_date.weekday(),
                day=current_date.day,
                month=current_date.month,
                year=current_date.year,
                completed=False
            ))

            #* Update participants for duty         
            duty["participants"] -= 1
    
    for duty in assigned_duties:
        await duty.save()


async def assign_saturday_duties():
    """Assigns Saturday duties"""
    duties_in_db = Duties.find_many()
    duties = [] #* Convert Duties documents to dictionaries
    
    default_duty = await DefaultDocs.find_one(DefaultDocs.id == "total-participants")
    
    learners_in_db = Learners.find(Learners.present == True)
    learners = []
    
    async for learner in learners_in_db:
        learners.append(learner)
        
    async for duty in duties_in_db:
        duties.append(duty.model_dump())
        
    
    if not len(learners) == default_duty.total:
        return
    
    await assign_duties_to_learners(learners, duties)


async def get_learners_in_blocks(block1: str, block2:str):
    '''
    Retrieves all learners in `block1` and `block2`
    which a `sr-matron` or `jr-matron` may be in charge of
    '''
    pass


async def get_learner_or_staff(id: str) -> Staff | Learners | None:
    '''
    Retrieves a learner or staff from the database with `id`
    '''
    
    try:
        user_in_db = await Learners.find_one(Learners.id == PydanticObjectId(id))

        return user_in_db
    except ConnectionError:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Oops, you cannot perform this action at the moment"
        )
    except InvalidId:
        user_in_db = await Staff.find_one(Staff.id == id)
        
        return user_in_db