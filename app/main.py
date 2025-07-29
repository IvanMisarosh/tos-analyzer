from fastapi import FastAPI, Depends, UploadFile, File, Form, HTTPException, status
from sqlalchemy.orm import Session
from app.db.db import get_db
from app import utils
from app import models
from app import schemas
from app.tasks import analyze_document
from app.enums import DocumentStatus
from app.db.mongo import clauses_collection

app = FastAPI()


@app.get("/")
async def root():
    return {"message": "Hello World"}


@app.post("/document/", response_model=schemas.DocumentCreate)
async def upload_document(db: Session = Depends(get_db),
                          document: UploadFile = File(),
                          user_context: str = Form(None)):

    if document.content_type != "application/pdf":
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail="Only PDF files are allowed."
        )

    file_url = await utils.save_upload_file(document)

    db_document = models.Document(user_context=user_context,
                                  file_url=file_url,
                                  status=models.DocumentStatus.UPLOADED)

    db.add(db_document)
    db.commit()

    return db_document


@app.post("/document/{document_id}/analyze")
async def start_analysis(document_id: int, db: Session = Depends(get_db)):
    db_document = db.query(models.Document).filter(models.Document.id == document_id).first()
    if not db_document:
        raise HTTPException(status_code=404, detail="Document not found")
    if db_document.status == DocumentStatus.UPLOADED:
        try:
            analyze_document.delay(document_id)
            pass
        except Exception as e:
            db_document.status = DocumentStatus.FAILED
            db.commit()
            raise HTTPException(status_code=500, detail=f"Failed to start analysis task. {e}")
        else:
            db_document.status = DocumentStatus.QUED_FOR_ANALYSIS
            db.commit()
            db.refresh(db_document)
            return {"status": db_document.status}
    elif db_document.status == DocumentStatus.ANALYZED:
        cursor = clauses_collection.find({"document_id": document_id})
        analysis = []
        async for doc in cursor:
            doc["_id"] = str(doc["_id"])
            analysis.append(doc)

        return {"status": db_document.status, "analysis": analysis}
    else:
        return {"status": db_document.status}
