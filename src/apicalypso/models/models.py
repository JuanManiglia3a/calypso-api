"""
models/models.py

Este archivo define las clases que representan las tablas de la base de datos utilizando SQLAlchemy ORM.

Responsabilidades:
- Definir las clases que representan las tablas de la base de datos.
- Definir las relaciones entre las tablas.
"""

from sqlalchemy import (
    UniqueConstraint, LargeBinary
)
from sqlalchemy.orm import (
    Mapped, mapped_column
)
from database.db import Base

#========== Usuarios
class Usuario(Base):
    __tablename__ = 'Usuario'

    username: Mapped[str] = mapped_column(primary_key=True)
    passhash: Mapped[bytes] = mapped_column(LargeBinary)
    salt: Mapped[bytes] = mapped_column(LargeBinary)
    deshabilitado: Mapped[bool]
    isAdmin: Mapped[bool]

    __table_args__ = (
        UniqueConstraint('username'),
        {'schema': 'public'},
    )