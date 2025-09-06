from pydantic import BaseModel

class User(BaseModel):
    username: str

class ActionRequest(BaseModel):
    action: str
