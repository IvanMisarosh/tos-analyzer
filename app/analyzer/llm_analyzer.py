import asyncio
from typing import List, Tuple, Iterable
from app.analyzer.templates import prompt_template
from app.analyzer import schemas
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.text_splitter import RecursiveCharacterTextSplitter
from app.logger import logger
from app.analyzer.rate_limiter import is_allowed
from app.config import settings
from app.analyzer.concurrency_limiter import ConcurrencyLimiter


class LLMAnalyzer:
    def __init__(self, llm: ChatGoogleGenerativeAI, max_chapter_length: int,
                 chunck_text_overlap: int, limiter: ConcurrencyLimiter):
        self.llm = llm
        self.max_chapter_length = max_chapter_length
        self.chunck_text_overlap = chunck_text_overlap
        self.structured_llm = self.llm.with_structured_output(schemas.ClauseAnalysis)
        self.chain = prompt_template | self.structured_llm
        self.limiter = limiter
        self.splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.max_chapter_length,
            chunk_overlap=self.chunck_text_overlap,
        )

    async def analyze_document_per_page(self,
                                        page_text_gen: Iterable[schemas.DocumentChapter],
                                        user_context: str) -> List[schemas.ClauseAnalysis]:
        tasks = []

        for page_text in page_text_gen:
            texts = self.splitter.split_text(page_text)
            for text in texts:
                tasks.append(self._analyze_chunk(text, user_context))
        results = await self.limiter.execute(tasks)

        successful, _, _ = self.categorise_results(results)
        if not successful:
            logger.error("No valid clauses found in the document.")
            return []
        return successful

    async def _analyze_chunk(self, text: str, user_context: str) -> schemas.ClauseAnalysis:
        for attempt in range(1, settings.MAX_RETRIES + 1):
            try:
                await self._wait_for_rate_limit(attempt)

                result = await self.chain.ainvoke({
                    "text": text,
                    "user_context": user_context
                })

                logger.info(f"Analysis completed successfully: {result}")

                return result

            except Exception as e:
                if attempt == settings.MAX_RETRIES:
                    logger.error(
                        f"Analysis failed after {
                            settings.MAX_RETRIES} attempts. Last error: {e}")
                    raise RuntimeError(
                        f"Failed to analyze chunk after {
                            settings.MAX_RETRIES} retries") from e

                wait_time = self._calculate_backoff_time(attempt)
                logger.warning(
                    f"Analysis failed (attempt {attempt}/{settings.MAX_RETRIES}): {e}."
                    f"Retrying in {wait_time}s")
                await asyncio.sleep(wait_time)

    async def _wait_for_rate_limit(self, attempt: int) -> None:
        if not is_allowed(settings.LLM_LIMIT_KEY):
            wait_time = self._calculate_backoff_time(attempt)
            logger.warning(f"Rate limit exceeded, waiting {wait_time}s (attempt {attempt})")
            await asyncio.sleep(wait_time)

    def _calculate_backoff_time(self, attempt: int) -> float:
        return settings.RETRY_BACKOFF_BASE * (3 ** attempt)

    async def _analyze_chapter(
        self, chapter_text: str, user_context: str, chapter: schemas.DocumentChapter
    ) -> schemas.ChapterAnalysis:
        clause_analysis = await self._analyze_chunk(chapter_text, user_context)
        return schemas.ChapterAnalysis(
            chapter_name=chapter.chapter_name,
            page_start=chapter.page_start,
            page_end=chapter.page_end,
            **clause_analysis.model_dump(),
        )

    async def analyze_document_per_chapter(self,
                                           chapter_gen: Iterable[schemas.DocumentChapter],
                                           user_context: str) -> List[schemas.ChapterAnalysis]:
        tasks = []
        for chapter in chapter_gen:
            texts = self.splitter.split_text(chapter.chapter_text)
            for text in texts:
                tasks.append(self._analyze_chapter(text, user_context, chapter))

        results = await self.limiter.execute(tasks)

        successful, _, _ = self.categorise_results(results)
        if not successful:
            logger.error("No valid clauses found in the document.")
            return []
        return successful

    def categorise_results(self,
                           results: List[schemas.ClauseAnalysis]) -> Tuple[
        List[schemas.ClauseAnalysis],  # valid
        List[schemas.ClauseAnalysis],  # invalid
        List[Exception],               # failed
    ]:
        valid_clauses = []
        invalid_clauses = []
        failed_clauses = []
        for clause in results:
            if isinstance(clause, Exception):
                failed_clauses.append(clause)
            elif clause.is_valid:
                valid_clauses.append(clause)
            else:
                invalid_clauses.append(clause)
        return valid_clauses, invalid_clauses, failed_clauses
