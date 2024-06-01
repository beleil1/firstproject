from fastapi.security import OAuth2PasswordBearer
from fastapi import Depends
from core.utills import jwt_tools
from db.mongo import connection


class authentication:
    oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/authentication/login")

    async def find_user(username):
        return await connection.site_database.users.find_one(
            {"username": username},
            # dict(login),
            {"_id": 0})

    def authenticate_token():
        async def _inner(token: str = Depends(authentication.oauth2_scheme)):
            token_info = jwt_tools.decode(token)
            user_info = await authentication.find_user(username=token_info["iss"])
            return user_info
        return _inner
