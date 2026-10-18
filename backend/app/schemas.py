from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict

class LoginIn(BaseModel):
    email: str
    password: str

class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: dict

class ItemCreate(BaseModel):
    title: str = Field(min_length=3, max_length=200)
    description: str = Field(default="", max_length=10000)
    item_type: str = "Task"
    priority: str = "Medium"
    team_id: int
    assignee_id: int | None = None
    due_date: datetime | None = None

class ItemUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=3, max_length=200)
    description: str | None = Field(default=None, max_length=10000)
    priority: str | None = None
    assignee_id: int | None = None
    due_date: datetime | None = None
    version: int

class TransitionIn(BaseModel):
    status: str
    version: int

class ClaimIn(BaseModel):
    pass

class CommentIn(BaseModel):
    body: str = Field(min_length=1, max_length=5000)

class ItemOut(BaseModel):
    id: int
    title: str
    description: str
    item_type: str
    priority: str
    status: str
    team_id: int
    assignee_id: int | None
    created_by: int
    due_date: datetime | None
    version: int
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)
