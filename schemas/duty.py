"""### Contains all `Learner` models
"""

from typing import Annotated, Optional
from pydantic import Field, BaseModel

class NewDuty(BaseModel):
    id: Annotated[str, Field(description="The name of the duty",min_length=6, max_length=50)]
    description: Annotated[str, Field(description="Description of the duty",min_length=6, max_length=100)]
    participants: Annotated[int, Field(description="Number of learners who should be assigned to the duty")]


class NewDutyResponse(BaseModel):
    """
    Response model for adding a new duty to the database

    ## Attributes:
    - message (str): A message indicating the status of the request
    """
    duty: NewDuty
    
    
class SpecialDuties(BaseModel):
    """
    Special duties are performed when not all
    learners are present in the hostel
    
    ## Attributes:
    - duties (list[`NewDuty`]): A list of duties to be performed by learners
    - learners (list): A list with names of learners present in the hostel
    """
    duties: list[NewDuty] # * A list duties to be performed by the learners
    

class DutyUpdate(BaseModel):
    """
    Request model to update a duty's `description` and `participants`

    ## Attributes:
    - description (str): Description of the duty
    - participants (int): Total number of learners assigned to duty
    """
    description: Optional[str | None] = Field(description="Description of the duty", min_length=6, max_length=100)
    participants: Optional[int | None] = Field(description="Number of learners who should be assigned to the duty") 
    
    
class GetAssignedDutiesResponse(BaseModel):
    status: str = "success"
    assigned_duties: list[dict]