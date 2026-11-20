def generate_report_pdf(report_data: dict[str, object]) -> bytes:
    """The legacy dictionary API is unsupported; use ``PDFReportGenerator``.

    Returning a PDF-looking byte string here falsely signals successful report
    generation. Fail clearly so callers cannot publish an invalid document.
    """
    raise NotImplementedError(
        "Use PDFReportGenerator.generate_pdf with a persisted Report model"
    )
