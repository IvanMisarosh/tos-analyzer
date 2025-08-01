# app/repositories/document_repository.py
from app.models import Document
from app.enums import DocumentStatus
from sqlalchemy.orm import Session
from typing import Optional


class DocumentRepository:
    def __init__(self, session: Session):
        self.session = session

    def get_by_id(self, document_id: int) -> Optional[Document]:
        return self.session.query(Document).filter(Document.id == document_id).first()

    def update_status(self, document: Document, status: DocumentStatus):
        document.status = status
        self.session.commit()
