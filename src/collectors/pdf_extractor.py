"""PDF text extraction service with multi-pass support."""

import time
from pathlib import Path
from typing import Optional
from dataclasses import dataclass

import fitz  # PyMuPDF


@dataclass
class ExtractionResult:
    """Result of PDF text extraction."""
    total_pages: int
    extracted_pages: int
    text_length: int
    extraction_time_sec: float
    quality_score: float  # 0-1 based on text density
    output_files: list[str]
    errors: list[str]

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "total_pages": self.total_pages,
            "extracted_pages": self.extracted_pages,
            "text_length": self.text_length,
            "extraction_time_sec": round(self.extraction_time_sec, 2),
            "quality_score": round(self.quality_score, 2),
            "output_files": self.output_files,
            "errors": self.errors,
        }


class PDFExtractor:
    """PDF text extraction service with multi-pass support."""

    def __init__(self, output_dir: str | Path):
        """Initialize extractor.

        Args:
            output_dir: Directory to save extracted text files
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def extract_text(
        self,
        pdf_path: str | Path,
        strategy: str = "auto",
        base_name: Optional[str] = None,
    ) -> ExtractionResult:
        """Extract text from PDF using appropriate strategy.

        Args:
            pdf_path: Path to PDF file
            strategy: Extraction strategy ("auto", "full", "multi-pass")
            base_name: Base name for output files (defaults to PDF stem)

        Returns:
            ExtractionResult with extraction details

        Raises:
            FileNotFoundError: If PDF doesn't exist
            ValueError: If invalid strategy
        """
        pdf_path = Path(pdf_path)
        if not pdf_path.exists():
            raise FileNotFoundError(f"PDF not found: {pdf_path}")

        if base_name is None:
            base_name = pdf_path.stem

        start_time = time.time()

        # Open PDF and determine strategy
        doc = fitz.open(pdf_path)
        total_pages = len(doc)

        if strategy == "auto":
            # Auto-select strategy based on page count
            if total_pages <= 100:
                strategy = "full"
            else:
                strategy = "multi-pass"

        # Execute extraction
        if strategy == "full":
            result = self._extract_full(doc, base_name)
        elif strategy == "multi-pass":
            result = self._extract_multi_pass(doc, base_name)
        else:
            doc.close()
            raise ValueError(f"Invalid strategy: {strategy}")

        doc.close()

        # Calculate quality metrics
        extraction_time = time.time() - start_time
        quality_score = self._calculate_quality_score(result["text_length"], total_pages)

        return ExtractionResult(
            total_pages=total_pages,
            extracted_pages=result["extracted_pages"],
            text_length=result["text_length"],
            extraction_time_sec=extraction_time,
            quality_score=quality_score,
            output_files=result["output_files"],
            errors=result.get("errors", []),
        )

    def _extract_full(self, doc: fitz.Document, base_name: str) -> dict:
        """Extract full text from all pages.

        Args:
            doc: PyMuPDF document object
            base_name: Base name for output file

        Returns:
            Dict with extraction results
        """
        full_text = []
        extracted_pages = 0

        for page_num in range(len(doc)):
            try:
                page = doc[page_num]
                text = page.get_text()
                if text.strip():
                    full_text.append(f"--- Page {page_num + 1} ---\n\n{text}\n")
                    extracted_pages += 1
            except Exception as e:
                full_text.append(f"--- Page {page_num + 1} ERROR: {e} ---\n\n")

        # Save to file
        output_file = self.output_dir / f"{base_name}_full.txt"
        combined_text = "\n".join(full_text)
        output_file.write_text(combined_text, encoding="utf-8")

        return {
            "text_length": len(combined_text),
            "extracted_pages": extracted_pages,
            "output_files": [str(output_file)],
        }

    def _extract_multi_pass(self, doc: fitz.Document, base_name: str) -> dict:
        """Extract text in multiple passes for large documents.

        Pass 1: Pages 1-20 (overview/summary)
        Pass 2: Pages 21-60 (mid-document details)
        Pass 3: Pages 61+ (deep sections)

        Args:
            doc: PyMuPDF document object
            base_name: Base name for output files

        Returns:
            Dict with extraction results
        """
        total_pages = len(doc)
        output_files = []
        total_text_length = 0
        extracted_pages = 0

        # Define pass ranges
        passes = [
            ("pass1", 0, min(20, total_pages)),
            ("pass2", 20, min(60, total_pages)),
            ("pass3", 60, total_pages),
        ]

        for pass_name, start_page, end_page in passes:
            if start_page >= end_page:
                continue  # Skip empty ranges

            pass_text = []
            pass_extracted = 0

            for page_num in range(start_page, end_page):
                try:
                    page = doc[page_num]
                    text = page.get_text()
                    if text.strip():
                        pass_text.append(f"--- Page {page_num + 1} ---\n\n{text}\n")
                        pass_extracted += 1
                except Exception as e:
                    pass_text.append(f"--- Page {page_num + 1} ERROR: {e} ---\n\n")

            # Save pass file
            if pass_text:
                output_file = self.output_dir / f"{base_name}_{pass_name}.txt"
                combined_text = "\n".join(pass_text)
                output_file.write_text(combined_text, encoding="utf-8")

                output_files.append(str(output_file))
                total_text_length += len(combined_text)
                extracted_pages += pass_extracted

        return {
            "text_length": total_text_length,
            "extracted_pages": extracted_pages,
            "output_files": output_files,
        }

    def _calculate_quality_score(self, text_length: int, total_pages: int) -> float:
        """Calculate quality score based on text density.

        Args:
            text_length: Total characters extracted
            total_pages: Total pages in PDF

        Returns:
            Quality score between 0 and 1
        """
        if total_pages == 0:
            return 0.0

        # Average 2000 chars per page is considered good
        avg_chars_per_page = text_length / total_pages
        expected_chars_per_page = 2000

        # Score based on how close to expected
        score = min(avg_chars_per_page / expected_chars_per_page, 1.0)

        return score

    def batch_extract(
        self,
        pdf_paths: list[str | Path],
        strategy: str = "auto",
    ) -> list[ExtractionResult]:
        """Extract text from multiple PDFs.

        Args:
            pdf_paths: List of PDF file paths
            strategy: Extraction strategy for all files

        Returns:
            List of ExtractionResult objects
        """
        results = []

        for pdf_path in pdf_paths:
            try:
                result = self.extract_text(pdf_path, strategy=strategy)
                results.append(result)
                print(f"✓ Extracted: {Path(pdf_path).name} ({result.extracted_pages}/{result.total_pages} pages)")
            except Exception as e:
                print(f"✗ Failed: {Path(pdf_path).name} - {e}")

        return results


def extract_pdf_text(
    pdf_path: str | Path,
    output_dir: str | Path,
    strategy: str = "auto",
    base_name: Optional[str] = None,
) -> ExtractionResult:
    """Convenience function to extract text from a single PDF.

    Args:
        pdf_path: Path to PDF file
        output_dir: Directory to save extracted text
        strategy: Extraction strategy ("auto", "full", "multi-pass")
        base_name: Base name for output files (defaults to PDF stem)

    Returns:
        ExtractionResult with extraction details
    """
    extractor = PDFExtractor(output_dir)
    return extractor.extract_text(pdf_path, strategy=strategy, base_name=base_name)
