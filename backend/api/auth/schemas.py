from pydantic import BaseModel, EmailStr


class SignupRequest(BaseModel):
    username: str
    email: EmailStr
    password: str


class SigninRequest(BaseModel):
    username: str
    password: str


class SignupResponse(BaseModel):
    pass


class SigninResponse(BaseModel):
    pass
