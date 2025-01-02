import secrets

from datetime import datetime

from fastapi import HTTPException, status

from models.responses import LearnerInDB, StaffInDB

def serialize_user_in_db(user_in_db: dict):
    '''Serializes `user_in_db`

    Args:
        user_in_db (`dict`): The user document retrieved from the database

    Returns:
        `dict`: returns `user_in_db`
    '''
    if user_in_db.get("type") == "learner":
        
        user_in_db = LearnerInDB(**user_in_db).model_dump(exclude=["password", "image", "permissions", "active"])
        user_in_db.update({"type": user_in_db.get("type").value, "block": user_in_db.get("block").value})
        
    elif user_in_db.get("type") == "staff":
        
        user_in_db = StaffInDB(**user_in_db).model_dump(exclude=["password", "image", "permissions", "active"])
        user_in_db.update({"type": user_in_db.get("type").value, "role": user_in_db.get("role").value})
        
    return user_in_db
    
    
def assign_duties_to_learners(learners: list, duties: list):
    '''
    Assigns `duties` to `learners`    
    '''
    assigned_duties = []
        
    for learner in learners:
        random_duty = secrets.choice(duties)
        
        # * Check if duty has been assigned to max participants
        if random_duty.get("participants") == 0:
            duties.remove(random_duty)
            random_duty = secrets.choice(duties) # * Choose another duty
        
        assigned_duties.append({
            "_id": learner,
            "assigned-duty": random_duty.get("_id"),
            "date": datetime.now().isoformat(),
            "completed": False
        })
        
        # * Reducing the participants of the duty
        random_duty.update({
            "participants": random_duty.get("participants") - 1
        })
        
    return assigned_duties


async def get_learners_in_blocks(block1: str, block2:str):
    '''
    Retrieves all learners in `block1` and `block2`    
    '''
    learners = []
    learners_in_db = database.users.find({"block": {"$in": [block1, block2]}})
    
    for learner in await learners_in_db.to_list(None):
        learner = LearnerInDB(**learner).model_dump(exclude=["password", "image", "active", "permissions", "type"])
        learner.update({"block": learner.get("block").value})
        learners.append(learner)
        
    return learners


async def find_user(id: str, role: str) -> dict:
    '''
    Retrieves a user from the database with `id` and `role`    
    '''
    pass
 

def is_user_accessing_own_account(id: str, current_user_id: str):
    '''
    Ensures user is accessing their own account. If
    `id` and `current_user_id` are not equal it raises `HTTPException`
    '''
    if not id == str(current_user_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot perform action"
        )

   
async def update_a_user(id: str, role: str, update_data):
    '''
    Updates a user from the database that the user with `id` and `role`
    Is allowed to update
    '''
    if role == "super-user":
        update_response = await database.users.update_one({'_id': id}, {"$set": update_data})
    elif role == "jr-matron":
        update_response = await database.users.update_one({'_id': id, "type": "learner", "block": {"$in": ["A", "B"]}}, {"$set": update_data})
    else:
        update_response = await database.users.update_one({'_id': id, "type": "learner", "block": {"$in": ["C", "D"]}}, {"$set": update_data})
        
    return update_response