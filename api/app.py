from fastapi import FastAPI, APIRouter
import uvicorn
import os
from typing import List, Dict

from src import *

app: FastAPI = FastAPI()

routers_to_include: list[APIRouter] = [user_router, password_router]
for rout in routers_to_include:
    app.include_router(rout)

@app.get('/')
def hello() ->  Dict[str, str]:
    return {'message': 'Hello, World!'}

def main() -> None:
    host: str = os.environ.get('HOST', '0.0.0.0')
    port: int = os.environ.get('PORT', 3000)
    uvicorn.run('app:app', host=host, port=port, reload=True)

if __name__ == '__main__':
    main()