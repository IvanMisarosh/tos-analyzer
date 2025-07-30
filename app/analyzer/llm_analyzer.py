from typing import Generator
from langchain_google_genai import ChatGoogleGenerativeAI
from app.analyzer.schemas import ClauseAnalysis
from app.config import settings
from app.analyzer.templates import prompt_template


class LLMAnalyzer:
    def __init__(self):
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-2.5-flash-lite",
            google_api_key=settings.GOOGLE_API_KEY,
            temperature=0.3
        )
        self.structured_llm = self.llm.with_structured_output(ClauseAnalysis)

        self.chain = prompt_template | self.structured_llm

    def analyze_document_per_page(
            self, page_text_gen: Generator[str]) -> Generator[ClauseAnalysis, None, None]:
        """Analyze a PDF document using the generator from PDFParser."""

        for page_text in page_text_gen:
            analysis = self.chain.invoke({"text": page_text})
            yield analysis
