from datetime import datetime

from models.learner import Learners
from models.attendance import Attendance


async def mark_absent_for_activity(present_learners: list[Learners], activity):
    present_learners_ids = [learner.id for learner in present_learners]
    absent_learners = await Learners.find({"_id": {"$nin": present_learners_ids}}).to_list()
    current_date = datetime.now()
    
    for learner in absent_learners:
        attendance = Attendance(
            activity=activity,
            day=current_date.day,
            month=current_date.month,
            week_day=current_date.weekday(),
            year=current_date.year,
            learner_details=learner.model_dump(exclude=["present", "image"])
        )
        
        await attendance.save()