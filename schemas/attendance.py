"""### Contains all `Attendance` schemas
"""

from typing import Annotated, Optional, Literal
from pydantic import Field, BaseModel


class MarkAttendance(BaseModel):
    activity: Annotated[Literal["evening-study", "afternoon-study", "church", "supper", "breakfast"], Field(description="The activity attendance is being taken for")]
    present_learners: Annotated[list, Field(description="List of IDs for all learners present for the activity")]
    absent_learners: Annotated[list, Field(description="List of IDs for all learners present for the activity")]