from fastapi import APIRouter, HTTPException, status, Depends
from models.model import register_model, forget_password_model
from db.mongo import connection
from core.utills import password_tools, jwt_tools
from datetime import datetime
from fastapi.security import OAuth2PasswordRequestForm
from schemas.auth_repo import authentication

router = APIRouter(prefix='/authentication', tags=["Authentication api"])


@router.post('/login')
async def login(login: OAuth2PasswordRequestForm = Depends()):
    user_info = await authentication.find_user(login.username)

    if user_info is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="user not found")
    if not password_tools.verify_password(login.password,
                                          user_info['password']):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail="invalid password")
    if jwt_tools.is_token_valid(user_info["username"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token is still valid. Cannot issue a new token.")

    access_token = jwt_tools.encode(user_info["username"], "access_token",
                                    expire=10)

    return {"access_token": access_token}
    # "token_type": "bearer"} #refresh token comin
    # return user_info["username"]


@router.post('/register')
async def register(register: register_model):
    try:
        if await connection.site_database.users.find_one({"username": register.username}):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="نام کاربری وارد شده قبلاً استفاده شده است. لطفاً نام دیگری را انتخاب کنید."
            )

        if await connection.site_database.users.find_one({"email": register.email}):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="این ایمیل قبلاً استفاده شده است. لطفاً از ایمیل دیگری استفاده کنید.")

        if await connection.site_database.users.find_one({
                "phone_number": register.phone_number}):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="این شماره تلفن قبلا استفاده شده است .لطفا از شماره دیگری استفاده کنید ")

        register.password = password_tools.encode_password(register.password)
        user_data = register.dict()
        user_data["registration_time"] = datetime.utcnow()

        connection.site_database.users.insert_one(user_data)
        hidden = register.dict()
        hidden.pop("password")
        return hidden
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="خطایی در سرور رخ داده است. لطفاً بعداً دوباره تلاش کنید."
        )


@router.put('/forget_password')
async def forget_password(forget: forget_password_model):

    user = await connection.site_database.users.find_one({"username": forget.username})
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    if forget.password != forget.confirm_password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Passwords do not match")

    forget.password = password_tools.encode_password(forget.password)

    await connection.site_database.users.update_one(
        {"username": forget.username},
        {"$set": {"password": forget.password}}
    )

    return {"detail": "Password changed successfully"}
