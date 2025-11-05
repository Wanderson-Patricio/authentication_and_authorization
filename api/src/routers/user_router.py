from fastapi import APIRouter, HTTPException
from typing import Any, Dict, List, Optional, Union
import os

from ..models import User
from ..config import DatabaseManager, SQLiteManager

router: APIRouter = APIRouter(prefix='/users', tags=['users'])

database: str = os.environ.get('DATABASE', 'src/data/api.db3')
db_manager = SQLiteManager

@router.get('/', response_model=List[User])
async def get_users() -> List[User]:
    with db_manager(database) as db:
        results: List[Dict[str, Any]] = db.select(table='users')
        users: List[User] = [User(id=result[0], name=result[1], email=result[2]) for result in results]
        return users
    
@router.get('/{user_id}', response_model=User)
async def get_user(user_id: int) -> User:
    with db_manager(database) as db:
        try:
            result: Optional[Dict[str, Any]] = db.select(table='users', id=user_id)[0]
        except IndexError:
            raise HTTPException(status_code=404, detail='User not found')
        user: User = User(id=result[0], name=result[1], email=result[2])
        return user