"""
Legal document templates and prompts for subpoena field extraction.
"""

FIELD_EXTRACTION_PROMPT = """You are a legal document analyst. Given a subpoena PDF, extract ALL of the following fields:

1. case_number - The court case number (e.g. "24-C-12345")
2. court_name - Full name of the court (e.g. "Circuit Court for Baltimore City")
3. subpoena_type - Type: "Subpoena to Appear" or "Subpoena for Production" or both
4. issue_date - Date the subpoena was issued
5. respondent_name - Full legal name of the person being subpoenaed
6. respondent_address - Complete address of the subpoenaed person
7. respondent_phone - Phone number (if shown)
8. respondent_email - Email address (if shown)
9. attorney_name - Name of the attorney who issued the subpoena
10. attorney_bar_number - Attorney's bar number
11. hearing_date - Date of the hearing/attendance required
12. hearing_time - Time of the hearing (e.g. "9:00 AM")
13. hearing_location - Where to appear
14. documents_requested - List of specific documents requested (for production subpoena)
15. penalty_clause - Any penalty language for failure to comply
16. notes - Any other relevant observations

Return a JSON object with all found fields. If a field is not found, use null. Add a confidence field."""

SUBJECT_EXTRACTION_PROMPT = """You are a legal document analyst. Given the text of a subpoena document, identify the FULL LEGAL NAME of the person this subpoena is about (the subpoena subject / respondent / person whose information is being sought).

Look for patterns like:
- "IN THE MATTER OF [NAME]"
- "SUBPOENA TO: [NAME]"
- "RE: [NAME]"
- "Subpoena for: [NAME]"

Return a JSON object with:
- subject_name: the full legal name
- subject_role: the role this person plays (e.g. respondent, witness, deponent)
- confidence: high, medium, or low
- reasoning: brief explanation of how you identified the name

Respond ONLY with valid JSON."""

FILING_CHECKLIST_PROMPT = """Given extracted subpoena fields and supporting data sources, generate a filing checklist for the paralegal.

Consider:
1. Is the subpoena properly addressed with respondent info?
2. Are all required fields filled in?
3. Is the case number consistent across documents?
4. Does the court name match the expected jurisdiction?
5. Are there any red flags or inconsistencies?

Return a JSON object with:
- is_complete: boolean
- missing_fields: list of fields that are null/missing
- warnings: list of potential issues
- filing_ready: boolean indicating if subpoena is ready to file
- checklist_items: ordered list of steps to complete before filing
"""
