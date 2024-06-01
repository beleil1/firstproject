from passlib.context import CryptContext
from jose import jwt
from fastapi import HTTPException, status
from datetime import datetime, timedelta
from db.mongo import connection

SECRET_KEY = "e696e8226097643b00dc04f8bfa899e5bbf42e46dfcdf387b2ffadddc6913e71"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 50


class password_tools:

    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

    def verify_password(plain_password, hashed_password):
        try:
            return password_tools.pwd_context.verify(plain_password, hashed_password)
        except:
            return False

    def encode_password(password):
        try:

            return password_tools.pwd_context.hash(password)
        except:
            return False


class jwt_tools:
    tokens = {}

    @staticmethod
    def encode(username: str, type_token: str, expire: float):
        exp_time = datetime.now() + timedelta(minutes=expire)
        jwt_data = {"sub": type_token, "iss": username,
                    "iat": datetime.now(),
                    "exp": exp_time}
        token = jwt.encode(jwt_data, SECRET_KEY, algorithm=ALGORITHM)
        jwt_tools.tokens[username] = exp_time
        connection.site_database.users.update_one(
            {"username": username},
            {"$set": {"token": token, "token_expiry": exp_time}},
            upsert=True
        )
        return token

    @staticmethod
    def decode(token: str):

        try:
            data = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            return data
        except:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
                headers={"WWW-Authenticate": "Bearer"})

    @staticmethod
    def is_token_valid(username: str):
        if username in jwt_tools.tokens:
            exp_time = jwt_tools.tokens[username]
            current_time = datetime.now()
            if current_time < exp_time:
                return True
            else:
                del jwt_tools.tokens[username]
                return False
        else:
            return False
