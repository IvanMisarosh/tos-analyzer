import re
import pymupdf
from typing import List, Dict, Generator
from langchain.text_splitter import RecursiveCharacterTextSplitter


class PDFParser:
    def __init__(self):
        self.section_patterns = [r'\b[A-Z][A-Z\s]{8,}(?:\n|$)']

    def _match_any_pattern(self, text: str) -> str:
        for pattern in self.section_patterns:
            if re.match(pattern, text.strip()):
                return pattern
        return ""

    def extract_text(self, doc: pymupdf.Document) -> str:
        text = ""
        for page in doc:
            text += page.get_text()
        return text

    def chunk_text(self, text: str) -> List[str]:
        splitter = RecursiveCharacterTextSplitter(chunk_size=2000, chunk_overlap=150)
        return splitter.split_text(text)

    def parse_pdf(self, path: str) -> List[Dict]:
        doc = pymupdf.open(path)
        full_text = self.extract_text(doc)
        chunks = self.chunk_text(full_text)

        return chunks

    def iter_text(self, doc: pymupdf.Document) -> Generator[str, None, None]:
        """Yields text from each page of the PDF document."""
        for page in doc:
            yield page.get_text()

    def parse_using_re(self, doc: pymupdf.Document) -> List[str]:
        chapters = {}
        current_chapter = 'start'
        chapters[current_chapter] = list()
        for page_num in range(len(doc)):
            page = doc[page_num]
            blocks = page.get_text("dict")["blocks"]

            for block in blocks:
                if "lines" not in block:
                    continue
                for line in block["lines"]:
                    line_text = " ".join(span["text"] for span in line["spans"]).strip()
                    matched_pattern = self._match_any_pattern(line_text)
                    if matched_pattern:
                        chapters.setdefault(line_text, list())
                        current_chapter = line_text
                    else:
                        chapters[current_chapter].append(line_text)

        return chapters
