from database import database



async def save_assigned_duties_in_db(duties):
    await database.assigned_duties.insert_many(documents=duties)