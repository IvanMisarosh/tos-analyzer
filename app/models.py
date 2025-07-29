from sqlalchemy import Column, Integer, String
from app.db.db import Base


class Document(Base):
    __tablename__ = 'documents'

    id = Column(Integer, primary_key=True)
    user_context = Column(String(500), nullable=False)
    file_url = Column(String(250), nullable=False)
    status = Column(String(50), nullable=False)
