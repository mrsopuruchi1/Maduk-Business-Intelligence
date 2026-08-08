"""
Maduk Business Intelligence - Report Generator Engine
Handles Jinja2 template loading, image encoding to Base64, HTML compilation, and PDF export.
"""

import os
import base64
import logging
from typing import Dict, Any, Optional
from jinja2 import Environment, FileSystemLoader, ChoiceLoader, select_autoescape

logger = logging.getLogger("MadukBI.ReportGenerator")


def image_to_base64(image_path: str) -> str:
    """
    Converts a local file path into a Base64 Data URI string.
    Ensures PDF engines render local images without path resolution errors.
    """
    if not image_path or not os.path.exists(image_path):
        return ""

    ext = os.path.splitext(image_path)[1].lower().replace(".", "")
    mime_type = "image/png" if ext == "png" else "image/jpeg" if ext in ["jpg", "jpeg"] else f"image/{ext}"

    try:
        with open(image_path, "rb") as img_file:
            encoded_str = base64.b64encode(img_file.read()).decode("utf-8")
        return f"data:{mime_type};base64,{encoded_str}"
    except Exception as e:
        logger.warning(f"Failed to encode image at path '{image_path}' to Base64: {str(e)}")
        return ""


class ReportGenerator:
    """Renders HTML executive reports and compiles them into PDF documents."""

    def __init__(self, template_dir: Optional[str] = None):
        """
        Initializes Jinja2 environment with fallback lookup loaders and custom filters.

        Args:
            template_dir: Dynamic or temporary template directory path (optional).
        """
        current_dir = os.path.dirname(os.path.abspath(__file__))

        candidate_paths = []

        if template_dir:
            template_dir_abs = os.path.abspath(template_dir)
            candidate_paths.append(template_dir_abs)
            nested_templates = os.path.join(template_dir_abs, "templates")
            if os.path.exists(nested_templates):
                candidate_paths.append(nested_templates)

        base_template_dir = os.path.join(current_dir, "templates")
        candidate_paths.append(base_template_dir)

        backend_templates_dir = os.path.abspath(os.path.join(current_dir, "..", "..", "templates"))
        candidate_paths.append(backend_templates_dir)

        backend_dir = os.path.abspath(os.path.join(current_dir, "..", ".."))
        candidate_paths.append(backend_dir)

        project_root = os.path.abspath(os.path.join(current_dir, "..", "..", ".."))
        candidate_paths.append(project_root)

        valid_loaders = []
        seen_paths = set()

        for path in candidate_paths:
            if path not in seen_paths and os.path.exists(path):
                seen_paths.add(path)
                valid_loaders.append(FileSystemLoader(path))

        if not valid_loaders:
            logger.warning("No valid template directories found. Defaulting to current directory loader.")
            valid_loaders.append(FileSystemLoader(current_dir))

        self.env = Environment(
            loader=ChoiceLoader(valid_loaders),
            autoescape=select_autoescape(['html', 'xml'])
        )

        # Jinja2 custom formatting and encoding filters
        self.env.filters['currency'] = lambda val: f"${val:,.2f}" if isinstance(val, (int, float)) else val
        self.env.filters['pct'] = lambda val: f"{val:.1f}%" if isinstance(val, (int, float)) else val
        self.env.filters['b64image'] = image_to_base64

    def render_template(self, template_name: str, context: Dict[str, Any]) -> str:
        """
        Loads and renders HTML template with analytical context dictionary.
        Automatically converts logo and chart file paths into inline Base64 data strings.
        """
        try:
            # Create a shallow copy of context to avoid mutating the original
            render_context = dict(context)

            # 1. Base64 Encode Logo
            logo_path = render_context.get("logo_path") or render_context.get("company_logo")
            if logo_path and isinstance(logo_path, str) and os.path.exists(logo_path):
                render_context["logo_b64"] = image_to_base64(logo_path)

            # 2. Base64 Encode Charts (Visual Performance Analytics)
            charts = render_context.get("charts")
            if isinstance(charts, dict):
                encoded_charts = {}
                for chart_key, chart_path in charts.items():
                    if isinstance(chart_path, str) and os.path.exists(chart_path):
                        encoded_charts[chart_key] = image_to_base64(chart_path)
                    else:
                        encoded_charts[chart_key] = chart_path
                render_context["charts_b64"] = encoded_charts
            elif isinstance(charts, list):
                encoded_charts = []
                for item in charts:
                    if isinstance(item, str) and os.path.exists(item):
                        encoded_charts.append(image_to_base64(item))
                    elif isinstance(item, dict) and "path" in item and os.path.exists(item["path"]):
                        item_copy = dict(item)
                        item_copy["b64"] = image_to_base64(item["path"])
                        encoded_charts.append(item_copy)
                    else:
                        encoded_charts.append(item)
                render_context["charts_b64"] = encoded_charts

            template = self.env.get_template(template_name)
            rendered_html = template.render(**render_context)
            logger.info(f"Successfully rendered template '{template_name}'.")
            return rendered_html
        except Exception as e:
            logger.error(f"Template rendering failed for '{template_name}': {str(e)}")
            raise

    def compile_pdf(self, html_content: str, output_path: str) -> str:
        """
        Compiles rendered HTML content into a PDF document on disk.

        Args:
            html_content: Rendered HTML string with embedded Base64 visual assets.
            output_path: File path where the output PDF should be written.

        Returns:
            The absolute path to the generated PDF.
        """
        try:
            # Ensure target output directory exists
            output_dir = os.path.dirname(os.path.abspath(output_path))
            os.makedirs(output_dir, exist_ok=True)

            # Try WeasyPrint first (preferred for high-fidelity HTML/CSS rendering)
            try:
                from weasyprint import HTML
                HTML(string=html_content).write_pdf(output_path)
                logger.info(f"PDF successfully compiled with WeasyPrint: '{output_path}'")
                return output_path
            except ImportError:
                logger.debug("WeasyPrint not installed. Falling back to xhtml2pdf.")

            # Fallback 1: xhtml2pdf
            try:
                from xhtml2pdf import pisa
                with open(output_path, "wb") as pdf_file:
                    pisa_status = pisa.CreatePDF(html_content, dest=pdf_file)
                if not pisa_status.err:
                    logger.info(f"PDF successfully compiled with xhtml2pdf: '{output_path}'")
                    return output_path
            except ImportError:
                logger.debug("xhtml2pdf not installed. Falling back to pdfkit.")

            # Fallback 2: pdfkit (requires wkhtmltopdf binary)
            try:
                import pdfkit
                pdfkit.from_string(html_content, output_path)
                logger.info(f"PDF successfully compiled with pdfkit: '{output_path}'")
                return output_path
            except ImportError:
                logger.debug("pdfkit not installed.")

            # Fallback 3: Output HTML to file if no PDF library is installed in environment
            fallback_html_path = output_path.replace(".pdf", ".html")
            with open(fallback_html_path, "w", encoding="utf-8") as f:
                f.write(html_content)
            logger.warning(
                f"No PDF rendering library (weasyprint/xhtml2pdf/pdfkit) available. "
                f"Saved HTML report fallback to '{fallback_html_path}'."
            )
            return fallback_html_path

        except Exception as e:
            logger.error(f"Failed to compile PDF report: {str(e)}")
            raise
