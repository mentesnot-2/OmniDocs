"""Chat-related Pydantic schemas"""


from pydantic import BaseModel
from typing import List
from datetime import datetime


class MessageIn(BaseModel):
    question:str
    answer:str


class MessageOut(BaseModel):
    id:int
    role:str
    content:str
    created_at:datetime

    class Config:
        from_attributes = True


class SessionOut(BaseModel):
    id:int
    user_id:int
    created_at:datetime
    messages:List[MessageOut] = []


    class Config:
        from_attributes = True
        