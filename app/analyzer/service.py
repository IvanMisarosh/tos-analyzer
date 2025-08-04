from app.analyzer.pdf_parser import PDFParser
from app.analyzer.llm_analyzer import LLMAnalyzer
from app.analyzer import schemas
from typing import List, Union


class AnalyzerService:
    def __init__(self, analyzer: LLMAnalyzer, parser: PDFParser):
        self.analyzer = analyzer
        self.parser = parser

    async def analyze(self,
                      pdf_path: str,
                      user_context: str) -> Union[List[schemas.ClauseAnalysis],
                                                  List[schemas.ChapterAnalysis]]:
        if self.parser.has_identifiable_chapters(pdf_path):
            chapter_gen = self.parser.parse_using_re(pdf_path)
            return await self.analyzer.analyze_document_per_chapter(chapter_gen, user_context)
        else:
            page_text_gen = self.parser.iter_text(pdf_path)
            return await self.analyzer.analyze_document_per_page(page_text_gen, user_context)
