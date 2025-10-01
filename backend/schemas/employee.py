from pydantic import BaseModel

class User(BaseModel):
    username: str

class ActionRequest(BaseModel):
    action: str
    account_id: str
    amount: int
