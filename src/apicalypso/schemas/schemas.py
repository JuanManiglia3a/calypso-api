# models/schemas.py
'''
Esquemas de SQLModel para definir los esquemas para interactuar con la base de datos (SQLModel)
'''

from sqlmodel import SQLModel

#========= Autenticación ======== 
class User(SQLModel):
    username: str
    deshabilitado: bool | None = None
    isAdmin: bool | None = None

class Token(SQLModel):
    access_token: str
    refresh_token: str
    token_type: str

class TokenData(SQLModel):
    username: str | None = None

class UserInDB(User):
    passhash: str
    
class UserInResponse(SQLModel):
    username: str
    passhash: str
    deshabilitado: bool = False
    isAdmin: bool = False
