from pydantic import BaseModel

class User(BaseModel):
    id: int
    name: str
    email: str

class Password(BaseModel):
    id: int
    user_id: int
    password_hash: str
