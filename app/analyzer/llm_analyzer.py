from typing import Generator
from app.analyzer.schemas import ClauseAnalysis
from app.analyzer.templates import prompt_template
from app.analyzer import schemas
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.text_splitter import RecursiveCharacterTextSplitter

class LLMAnalyzer:
    def __init__(self, llm: ChatGoogleGenerativeAI, max_chapter_length: int ):
        self.llm = llm
        self.max_chapter_length = max_chapter_length
        self.structured_llm = self.llm.with_structured_output(ClauseAnalysis)
        self.chain = prompt_template | self.structured_llm

    def analyze_document_per_page(
            self, page_text_gen: Generator[str],
            user_context: str) -> Generator[ClauseAnalysis, None, None]:
        """Analyze a PDF document using the generator from PDFParser."""

        for page_text in page_text_gen:
            analysis = self.chain.invoke({"text": page_text, "user_context": user_context})
            yield analysis

    def analyze_document_per_chapter(
        self, chapter_gen: Generator[schemas.DocumentChapter], user_context: str
    ) -> Generator[schemas.ChapterAnalysis, None, None]:

        splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.max_chapter_length,
            chunk_overlap=150,
        )

        for chapter in chapter_gen:
            texts = (
                splitter.split_text(chapter.chapter_text)
                if len(chapter.chapter_text) > self.max_chapter_length
                else [chapter.chapter_text]
            )

            for text in texts:
                result = self.chain.invoke({"text": text, "user_context": user_context})
                yield schemas.ChapterAnalysis(
                    chapter_name=chapter.chapter_name,
                    page_start=chapter.page_start,
                    page_end=chapter.page_end,
                    **result.model_dump()
                )
