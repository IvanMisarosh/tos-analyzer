from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from app.db.db import Base


class User(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, nullable=False)
    hashed_password = Column(String(128), nullable=False)

    documents = relationship("Document", back_populates="user")


class Document(Base):
    __tablename__ = 'documents'

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    user_context = Column(String(500), nullable=False)
    file_url = Column(String(250), nullable=False)
    status = Column(String(50), nullable=False)

    user = relationship("User", back_populates="documents")
