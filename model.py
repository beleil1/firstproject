from pydantic import BaseModel, validator, ValidationError, field_validator
import re


class login_model(BaseModel):
    username: str
    password: str

    @field_validator('password')
    def validate_password(cls, value):
        min_length = 6
        require_upper = True
        require_lower = True
        require_digit = True
        require_special = True
        special_characters = "!@#$%^&*()-_+="

        if len(value) < min_length:
            raise ValueError(
                f"Password must be at least {min_length} characters long.")
        if require_upper and not re.search(r"[A-Z]", value):
            raise ValueError(
                "Password must contain at least one uppercase letter.")
        if require_lower and not re.search(r"[a-z]", value):
            raise ValueError(
                "Password must contain at least one lowercase letter.")
        if require_digit and not re.search(r"\d", value):
            raise ValueError("Password must contain at least one digit.")
        if require_special and not re.search(rf"[{re.escape(special_characters)}]", value):
            raise ValueError(
                "Password must contain at least one special character.")

        return value

    @field_validator('username')
    def check_username(cls, v):
        if len(v) < 3:
            raise ValueError("Username must be at least 3 characters long.")
        if len(v) > 20:
            raise ValueError("Username must be at most 20 characters long.")
        return v


class register_model(login_model):
    email: str

    @field_validator('email')
    def check_email(cls, v):
        if len(v) > 3276:
            raise ValueError("Email address is too long.")
        if not re.match(r'^[\w\.-]+@[\w\.-]+\.\w+$', v):
            raise ValueError("Invalid email address.")
        # Add more validation logic if needed
        return v


class forget_password_model(login_model):
    confirm_password: str


class FileResponse(BaseModel):
    filename: str
    content_type: str
    minio_url: str
