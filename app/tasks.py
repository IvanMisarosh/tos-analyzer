from celery import shared_task
from app.models import Document
from app.enums import DocumentStatus
from app.analyzer.pdf_parser import PDFParser
from app.analyzer.llm_analyzer import LLMAnalyzer
from app.db.db import get_db
from app.db.sync_mongo import clauses_collection


@shared_task(bind=True, name="analyze_document")
def analyze_document(self, document_id: int):
    session = next(get_db())
    try:
        doc_obj = session.query(Document).filter(Document.id == document_id).first()
        if not doc_obj:
            return

        doc_obj.status = DocumentStatus.PROCESSING
        session.commit()

        parser = PDFParser()
        analyzer = LLMAnalyzer()
        pdf_path = doc_obj.file_url

        page_text_gen = parser.iter_text(pdf_path)
        results = analyzer.analyze_document_per_page(page_text_gen)

        for clause_analysis in results:
            dict_clause = clause_analysis.model_dump()
            dict_clause["document_id"] = document_id
            clauses_collection.insert_one(dict_clause)

        doc_obj.status = DocumentStatus.ANALYZED
        session.commit()

    except Exception as e:
        doc_obj = session.query(Document).filter(Document.id == document_id).first()
        if doc_obj:
            doc_obj.status = DocumentStatus.FAILED
            session.commit()
        raise e
    finally:
        session.close()
