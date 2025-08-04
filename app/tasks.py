import asyncio
from celery import shared_task
from app.enums import DocumentStatus
from app.db.db import get_db
from app.analyzer.document_repository import DocumentRepository
from app import utils


@shared_task(bind=True, name="analyze_document")
def analyze_document(self, document_id: int):
    session = next(get_db())
    document_repo = DocumentRepository(session)
    try:
        doc = document_repo.get_by_id(document_id)
        if not doc:
            return

        document_repo.update_status(doc, DocumentStatus.PROCESSING)

        service = utils.create_analyzer_service()

        results = asyncio.run(
            service.analyze(
                pdf_path=doc.file_url,
                user_context=doc.user_context or ""))
        asyncio.run(utils.save_results(results, document_id))

        document_repo.update_status(doc, DocumentStatus.ANALYZED)
    except Exception as e:
        document_repo.update_status(doc, DocumentStatus.FAILED)
        raise e
    finally:
        session.close()
