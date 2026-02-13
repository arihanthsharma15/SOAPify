from pydantic import BaseModel
from typing import Optional
from datetime import datetime

#user input
class TranscriptCreate(BaseModel):
    patient_name: Optional[str] = "Unknown Patient"
    age: Optional[int] = None
    transcript_text: str 

class TranscriptInDB(TranscriptCreate):
    id: int
    soap_note: Optional[str] = None
    status: str
    created_at: datetime

    class Config: 
        from_attributes = True

#response
class TranscriptResponse(BaseModel):
    id:int
    soap_note : Optional[str] = None
    patient_name : str
    status : str