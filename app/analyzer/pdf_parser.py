import re
import pymupdf
from typing import Generator
from app.analyzer import schemas


class PDFParser:
    def __init__(self, min_chapter_lenght: int = 100,
                 max_chapter_heading_lenght: int = 100, max_words_per_heading: int = 5):
        self.section_patterns = [
            r'^[A-Z][A-Z\s,;\–-]{8,}(?:\n|$)',         # Catch big all-caps blocks
            r'^[A-Z]\.\s+[A-Z][A-Z\s,;\-]{2,}$'     # Catch patterns like A. TERMS; PRIVACY
        ]
        self.min_chapter_lenght = min_chapter_lenght
        self.max_chapter_heading_lenght = max_chapter_heading_lenght
        self.max_words_per_heading = max_words_per_heading

    def _match_any_pattern(self, text: str) -> str:
        stripped = text.strip()

        if (
            any((re.match(pattern, stripped) for pattern in self.section_patterns))
            and len(stripped.split()) <= self.max_words_per_heading
            and not stripped.endswith(".")
            and len(stripped) < self.max_chapter_heading_lenght
        ):
            return True
        return False

    def iter_text(self, path: str) -> Generator[str, None, None]:
        """Yields text from each page of the PDF document."""
        doc = pymupdf.open(path)
        for page in doc:
            yield page.get_text()

    def _is_chapter_valid(self, chapter_text: str):
        return len(chapter_text) > self.min_chapter_lenght

    def has_identifiable_chapters(self, path: str) -> bool:
        doc = pymupdf.open(path)

        for page in doc:
            blocks = page.get_text("dict")["blocks"]

            for block in blocks:
                if "lines" not in block:
                    continue
                for line in block["lines"]:
                    line_text = " ".join(span["text"] for span in line["spans"]).strip()
                    if self._match_any_pattern(line_text):
                        return True  # Found a chapter heading
        return False  # No matching headings found

    def parse_using_re(self, path: str) -> Generator[schemas.DocumentChapter, None, None]:
        doc = pymupdf.open(path)

        current_chapter_name = "File beginning"
        current_chapter_lines = []
        current_page_start = 1

        for page_num in range(len(doc)):
            page = doc[page_num]
            blocks = page.get_text("dict")["blocks"]

            for block in blocks:
                if "lines" not in block:
                    continue

                for line in block["lines"]:
                    line_text = " ".join(span["text"] for span in line["spans"]).strip()

                    if self._match_any_pattern(line_text):
                        chapter_text = " ".join(current_chapter_lines).strip()
                        is_valid_chapter = self._is_chapter_valid(chapter_text)
                        if is_valid_chapter:
                            yield schemas.DocumentChapter(
                                chapter_name=current_chapter_name,
                                chapter_text=chapter_text,
                                page_start=current_page_start + 1,
                                page_end=page_num + 1
                            )

                        # Start new chapter
                        current_chapter_name = line_text
                        current_chapter_lines = []
                        current_page_start = page_num

                        # If chapter was not valid add to the next chapter to avoid missing context
                        if not is_valid_chapter and chapter_text:
                            current_chapter_lines.append(chapter_text)
                    else:
                        current_chapter_lines.append(line_text)

        # Emit the last chapter
        final_text = " ".join(current_chapter_lines).strip()
        if self._is_chapter_valid(final_text):
            yield schemas.DocumentChapter(
                chapter_name=current_chapter_name,
                chapter_text=final_text,
                page_start=current_page_start + 1,
                page_end=len(doc)
            )
