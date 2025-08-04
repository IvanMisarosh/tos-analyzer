from fastapi import UploadFile
from pathlib import Path
from app.config import settings
from app.analyzer import schemas
from app.db.mongo import clauses_collection
from typing import List, Union
from app.analyzer.service import AnalyzerService
from app.analyzer.pdf_parser import PDFParser
from app.analyzer.llm_analyzer import LLMAnalyzer
from langchain_google_genai import ChatGoogleGenerativeAI
from app.analyzer.concurrency_limiter import ConcurrencyLimiter


async def save_upload_file(upload_file: UploadFile) -> str:
    uploads_folder: Path = settings.UPLOADS_FOLDER
    uploads_folder.mkdir(parents=True, exist_ok=True)
    file_path = uploads_folder / upload_file.filename

    with open(file_path, "wb") as buffer:
        while chunk := await upload_file.read(1024 * 1024):
            buffer.write(chunk)
    await upload_file.close()
    return str(file_path)


async def save_results(results: Union[List[schemas.ClauseAnalysis],
                       List[schemas.ChapterAnalysis]], document_id: int) -> None:
    dict_list = []
    for res in results:
        clause_dict = res.model_dump()
        clause_dict["document_id"] = document_id
        dict_list.append(clause_dict)

    await clauses_collection.insert_many(dict_list)


def create_analyzer_service() -> AnalyzerService:
    parser = PDFParser()
    llm = get_llm()
    limiter = ConcurrencyLimiter(max_concurrent=settings.LLM_MAX_CONCURRENT_REQUESTS)
    analyzer = LLMAnalyzer(
        llm=llm,
        max_chapter_length=settings.LLM_MAX_CHUNK_LENGTH,
        chunck_text_overlap=settings.LLM_CHUNK_TEXT_OVERLAP,
        limiter=limiter)
    return AnalyzerService(analyzer, parser)


def get_llm() -> ChatGoogleGenerativeAI:
    return ChatGoogleGenerativeAI(
        model=settings.LLM_MODEL_NAME,
        temperature=settings.LLM_TEMPERATURE,
        google_api_key=settings.GOOGLE_API_KEY,
    )
