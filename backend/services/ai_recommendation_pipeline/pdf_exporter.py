# pdf_exporter.py

"""
Maduk Business Intelligence - PDF Exporter Engine
Compiles HTML strings with static resources into multi-page PDF documents.
"""

import os
import re
import logging
from typing import Optional
from xhtml2pdf import pisa

logger = logging.getLogger("MadukBI.PDFExporter")


class PDFExporter:
    """Exports compiled HTML reports into PDF files using xhtml2pdf (pisa)."""

    def _django_link_callback(self, uri: str, rel: str) -> str:
        """
        Converts relative URLs in HTML (e.g., images, CSS) into absolute file system paths 
        so xhtml2pdf can reliably load them during PDF rendering.
        """
        # Clean file protocol if present
        cleaned_uri = uri.replace("file://", "") if uri.startswith("file://") else uri

        # Return exact path if it's already an absolute path and exists
        if os.path.isabs(cleaned_uri) and os.path.exists(cleaned_uri):
            return cleaned_uri

        # Fallback to absolute normalization relative to working directory
        abs_path = os.path.abspath(cleaned_uri)
        if os.path.exists(abs_path):
            return abs_path

        logger.warning(f"PDF Exporter asset not found: {uri} (resolved to: {abs_path})")
        return cleaned_uri

    def _sanitize_html_for_xhtml2pdf(self, html_content: str) -> str:
        """
        Strips or replaces unsupported CSS syntax (e.g., page margin boxes,
        CSS custom variables, linear gradients) that cause xhtml2pdf parser crashes.
        """
        # Remove CSS variable declarations (:root { --var: val; })
        sanitized = re.sub(r':root\s*\{[^}]*\}', '', html_content, flags=re.IGNORECASE)
        
        # Replace var(--custom-color) references with fallback dark hex
        sanitized = re.sub(r'var\([^)]+\)', '#0f172a', sanitized, flags=re.IGNORECASE)

        # Replace linear-gradient functions with solid fallback background
        sanitized = re.sub(r'linear-gradient\([^;]+?\)', '#0f172a', sanitized, flags=re.IGNORECASE)

        # Remove unsupported page margin boxes inside @page blocks
        sanitized = re.sub(r'@(top|bottom|left|right)-(left|right|center|middle|top|bottom)\s*\{[^}]*\}', '', sanitized, flags=re.IGNORECASE)

        return sanitized

    def export(
        self,
        html_content: str,
        output_path: str,
        base_url: Optional[str] = None
    ) -> str:
        """
        Converts rendered HTML string to a PDF file on disk using xhtml2pdf.

        Args:
            html_content: Fully rendered HTML string.
            output_path: Output path where the PDF will be created.
            base_url: Base directory for relative asset resolution (e.g., images/CSS).

        Returns:
            Absolute file path to the compiled PDF document.
        """
        output_dir = os.path.dirname(os.path.abspath(output_path))
        os.makedirs(output_dir, exist_ok=True)

        base_dir = base_url or output_dir

        # Sanitize HTML to prevent parser crashes in xhtml2pdf
        cleaned_html = self._sanitize_html_for_xhtml2pdf(html_content)

        try:
            logger.info(f"Compiling PDF report to path: {output_path}")

            with open(output_path, "wb") as output_file:
                pisa_status = pisa.CreatePDF(
                    src=cleaned_html,
                    dest=output_file,
                    path=base_dir,
                    encoding="utf-8",
                    link_callback=self._django_link_callback
                )

            if pisa_status.err:
                logger.error(f"xhtml2pdf compilation encountered {pisa_status.err} error(s).")
                if os.path.exists(output_path):
                    os.remove(output_path)
                raise RuntimeError(f"xhtml2pdf PDF compilation failed with {pisa_status.err} error(s).")

            logger.info("PDF document compilation successfully finished.")
            return os.path.abspath(output_path)

        except Exception as e:
            logger.error(f"Failed to export HTML to PDF: {str(e)}")
            if os.path.exists(output_path):
                os.remove(output_path)
            raise RuntimeError(f"xhtml2pdf PDF compilation failed: {str(e)}")
