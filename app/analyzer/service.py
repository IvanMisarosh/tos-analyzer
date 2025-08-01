from app.analyzer.pdf_parser import PDFParser
from app.analyzer.llm_analyzer import LLMAnalyzer
from app.analyzer.schemas import ClauseAnalysis
from typing import Generator

class AnalyzerService:
    def __init__(self, analyzer: LLMAnalyzer, parser: PDFParser):
        self.analyzer = analyzer
        self.parser = parser

    def analyze(self, pdf_path: str, user_context: str) -> Generator[ClauseAnalysis, None, None]:
        if self.parser.has_identifiable_chapters(pdf_path):
            chapter_gen = self.parser.parse_using_re(pdf_path)
            return self.analyzer.analyze_document_per_chapter(chapter_gen, user_context)
        else:
            page_text_gen = self.parser.iter_text(pdf_path)
            return self.analyzer.analyze_document_per_page(page_text_gen, user_context)