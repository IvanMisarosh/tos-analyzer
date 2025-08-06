from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException, status
from sqlalchemy.orm import Session
from app.analyzer import schemas
from app.db.db import get_db
from app import utils, models
from app.tasks import analyze_document
from app.enums import DocumentStatus
from app.db.mongo import clauses_collection
from app.auth.dependencies import get_current_user
from app.auth.schemas import User
from typing import List

router = APIRouter()


@router.post("/document/", response_model=schemas.Document)
async def upload_document(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    document: UploadFile = File(...),
    user_context: str = Form(None)
):
    if document.content_type != "application/pdf":
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail="Only PDF files are allowed."
        )

    file_url = await utils.save_upload_file(document)

    db_document = models.Document(
        user_context=user_context,
        user_id=current_user.id,
        file_url=file_url,
        status=DocumentStatus.UPLOADED
    )

    db.add(db_document)
    db.commit()
    db.refresh(db_document)
    return db_document


@router.post("/document/{document_id}/analyze")
async def start_analysis(
    document_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    db_document = db.query(models.Document).filter(
        models.Document.id == document_id,
        models.Document.user_id == current_user.id
    ).first()

    if not db_document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )

    if db_document.status == DocumentStatus.UPLOADED or db_document.status == DocumentStatus.FAILED:
        try:
            analyze_document.delay(document_id)
            db_document.status = DocumentStatus.QUED_FOR_ANALYSIS
            db.commit()
            db.refresh(db_document)
            return {"status": db_document.status}
        except Exception:
            db_document.status = DocumentStatus.FAILED
            db.commit()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to start analysis task"
            )
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Document is already being analyzed or has been analyzed."
        )


@router.get("/document/{document_id}/status", response_model=schemas.DocumentStatusResponse)
async def get_document_status(
    document_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    db_document = db.query(models.Document).filter(
        models.Document.id == document_id,
        models.Document.user_id == current_user.id
    ).first()
    if not db_document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )
    return schemas.DocumentStatusResponse(id=db_document.id, status=db_document.status)


@router.get("/document/{document_id}", response_model=schemas.Document)
async def get_document(
    document_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    db_document = db.query(models.Document).filter(
        models.Document.id == document_id,
        models.Document.user_id == current_user.id
    ).first()
    if not db_document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )
    return db_document


@router.get("/documents/", response_model=List[schemas.Document])
async def get_documents(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    db_documents = db.query(models.Document).filter(
        models.Document.user_id == current_user.id
    ).all()
    return db_documents


@router.get("/document/{document_id}/clauses", response_model=List[schemas.ClauseAnalysisResponse])
async def get_clauses(
    document_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    db_document = db.query(models.Document).filter(
        models.Document.id == document_id,
        models.Document.user_id == current_user.id
    ).first()

    if not db_document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )

    if db_document.status != DocumentStatus.ANALYZED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Document has not been analyzed yet"
        )
    cursor = clauses_collection.find({"document_id": document_id})
    analysis = []
    async for clause in cursor:
        clause["id"] = str(clause["_id"])
        analysis.append(schemas.ClauseAnalysisResponse(**clause))

    return analysis
