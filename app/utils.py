from fastapi import UploadFile
from pathlib import Path
from app.config import settings
from app.analyzer.schemas import ClauseAnalysis
from app.db.sync_mongo import clauses_collection
from typing import Generator
from app.analyzer.service import AnalyzerService
from app.analyzer.pdf_parser import PDFParser
from app.analyzer.llm_analyzer import LLMAnalyzer
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.rate_limiters import InMemoryRateLimiter


async def save_upload_file(upload_file: UploadFile) -> str:
    uploads_folder: Path = settings.UPLOADS_FOLDER
    uploads_folder.mkdir(parents=True, exist_ok=True)
    file_path = uploads_folder / upload_file.filename

    with open(file_path, "wb") as buffer:
        while chunk := await upload_file.read(1024 * 1024):
            buffer.write(chunk)
    await upload_file.close()
    return str(file_path)

def save_results(results: Generator[ClauseAnalysis, None, None], document_id: int):
    for clause_analysis in results:
        clause_dict = clause_analysis.model_dump()
        clause_dict["document_id"] = document_id
        clauses_collection.insert_one(clause_dict)


def create_analyzer_service():
    parser = PDFParser()
    llm = get_llm()
    analyzer = LLMAnalyzer(llm=llm, max_chapter_length=settings.LLM_MAX_CHAPTER_LENGTH)
    return AnalyzerService(analyzer, parser)


def get_llm():
    rate_limiter = InMemoryRateLimiter(
        requests_per_second=settings.LLM_REQUESTS_PER_MINUTE / 60,
        check_every_n_seconds=0.1,
        max_bucket_size=5
    )
    return ChatGoogleGenerativeAI(
        model=settings.LLM_MODEL_NAME,
        temperature=settings.LLM_TEMPERATURE,
        rate_limiter=rate_limiter,
        max_retries=settings.LLM_MAX_RETRIES,
        google_api_key=settings.GOOGLE_API_KEY,
    )