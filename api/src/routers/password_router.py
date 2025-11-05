from fastapi import APIRouter, HTTPException
from typing import Any, Dict, List, Optional, Union
import os

from ..models import Password
from ..config import DatabaseManager, SQLiteManager

router: APIRouter = APIRouter(prefix='/passwords', tags=['passwords'])

database: str = os.environ.get('DATABASE', 'src/data/api.db3')
db_manager = SQLiteManager

@router.get('/', response_model=List[Password])
async def get_passwords() -> List[Password]:
    with db_manager(database) as db:
        results: List[Dict[str, Any]] = db.select(table='passwords')
        passwords: List[Password] = [Password(id=result[0], password_hash=result[1], user_id=result[2]) for result in results]
        return passwords
    
@router.get('/{password_id}', response_model=Password)
async def get_password(password_id: int) -> Password:
    with db_manager(database) as db:
        try:
            result: Optional[Dict[str, Any]] = db.select(table='passwords', id=password_id)[0]
        except IndexError:
            raise HTTPException(status_code=404, detail='password not found')
        password: Password = Password(id=result[0], password_hash=result[1], user_id=result[2])
        return password