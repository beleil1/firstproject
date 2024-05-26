from fastapi import APIRouter, HTTPException, status, Depends
from mongo import connection
from utills import jwt_tools
from auth_repo import authentication

router = APIRouter(prefix='/user', tags=["User Api"])


@router.post('/me')
async def user_info(current_user=Depends
                    (authentication.authenticate_token())):

    current_user.pop("password")
    return current_user
