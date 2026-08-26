""""
Patch Generation Agent — Agent 5

Responsibility:
- Confirmed vulnerability ka secure fix generate karna
- Minimal patch — sirf zaroori changes
- Unified diff format mein output
- Explanation dena kyun patch sahi hai
- Confidence assign karna

Philosophy:
- Patch minimal hona chahiye — poori file rewrite mat karo
- Functionality preserve karo
- Secure coding patterns use karo (parameterized queries, etc.)
- Evidence-based — CWE se pattern lo
"""

import json
import difflib
from pathlib import Path
from dataclasses import dataclass, field
from app.agents.state import ScanState
from app.llm.factory import get_llm
from app.core.logger import get_logger

logger = get_logger("patch_generation_agent")


# Secure coding patterns — har vulnerability type ke liye
SECURE_PATTERNS = {
    "SQLI": """
SECURE PATTERN for SQL Injection:
- NEVER concatenate user input into SQL strings
- ALWAYS use parameterized queries / prepared statements

VULNERABLE:
    query = "SELECT * FROM users WHERE id=" + user_id
    conn.execute(query)

SECURE (sqlite3):
    query = "SELECT * FROM users WHERE id=?"
    conn.execute(query, (user_id,))

SECURE (psycopg2):
    query = "SELECT * FROM users WHERE id=%s"
    cursor.execute(query, (user_id,))

SECURE (SQLAlchemy):
    result = db.execute(text("SELECT * FROM users WHERE id=:id"), {"id": user_id})
""",

    "XSS": """
SECURE PATTERN for XSS:
- NEVER insert user input directly into HTML
- ALWAYS escape/sanitize output
- Use template engine's auto-escaping

VULNERABLE:
    return "<h1>" + user_input + "</h1>"

SECURE (Flask/Jinja2 — auto-escaping):
    return render_template("page.html", data=user_input)

SECURE (manual escaping):
    from markupsafe import escape
    return f"<h1>{escape(user_input)}</h1>"
""",

    "SECRETS": """
SECURE PATTERN for Hardcoded Secrets:
- NEVER hardcode secrets in source code
- ALWAYS use environment variables

VULNERABLE:
    password = "super_secret_123"
    api_key = "sk-abcdef123"

SECURE:
    import os
    password = os.environ.get("DB_PASSWORD")
    api_key = os.environ.get("API_KEY")

    # Or with python-dotenv:
    from dotenv import load_dotenv
    load_dotenv()
    password = os.getenv("DB_PASSWORD")
""",

    "SSRF": """
SECURE PATTERN for SSRF:
- NEVER use user-controlled URLs directly
- ALWAYS validate and whitelist URLs

VULNERABLE:
    url = request.args.get('url')
    response = requests.get(url)

SECURE:
    from urllib.parse import urlparse

    ALLOWED_DOMAINS = ['api.trusted.com', 'data.safe.org']

    url = request.args.get('url')
    parsed = urlparse(url)

    if parsed.netloc not in ALLOWED_DOMAINS:
        return "Invalid URL", 400

    response = requests.get(url, timeout=5)
""",

    "DESERIALIZATION": """
SECURE PATTERN for Insecure Deserialization:
- NEVER use pickle.loads() with untrusted data
- Use JSON instead of pickle for data exchange

VULNERABLE:
    data = pickle.loads(user_data)

SECURE:
    import json
    data = json.loads(user_data)

    # If pickle absolutely needed — only with signed/trusted data:
    import hmac, hashlib
    # Verify signature before deserializing
""",
}


@dataclass
class GeneratedPatch:
    """Ek generated patch ka complete result."""
    finding_id: str
    vuln_type: str
    file_path: str
    # Unified diff
    unified_diff: str
    # Original vulnerable code
    original_code: str
    # Fixed secure code
    patched_code: str
    # Explanation
    explanation: str
    # Confidence
    confidence: float
    # Secure pattern used
    pattern_used: str
    # Success?
    success: bool = True
    error: str = ""


def patch_generation_node(state: ScanState) -> dict:
    """
    LangGraph node — Patch Generation.

    Har confirmed vulnerability ke liye:
    1. Source file padho
    2. Vulnerable code extract karo
    3. LLM se secure fix generate karo
    4. Unified diff banao
    5. Patch state mein save karo

    Args:
        state: Current scan state

    Returns:
        Dict with patches list
    """
    scan_id = state["scan_id"]
    vulnerabilities = state.get("vulnerabilities", [])
    repository_path = state["repository_path"]

    logger.info(
        "Patch Generation Agent starting",
        scan_id=scan_id,
        vulnerabilities=len(vulnerabilities),
    )

    if not vulnerabilities:
        logger.info("No vulnerabilities to patch")
        return {
            "patches": [],
            "current_step": "patch_generation_complete",
            "agent_log": ["PatchGenerationAgent: No vulnerabilities to patch"],
        }

    llm = get_llm(temperature=0.1)
    patches = []

    for i, vuln in enumerate(vulnerabilities):
        try:
            logger.info(
                "Generating patch",
                vuln_type=vuln.get("vuln_type"),
                file=vuln.get("file_path"),
                line=vuln.get("line_start"),
            )

            patch = _generate_patch_for_vuln(
                vuln=vuln,
                repository_path=repository_path,
                llm=llm,
                patch_index=i,
            )

            patches.append({
                "finding_id": f"finding_{i}",
                "vuln_type": patch.vuln_type,
                "file_path": patch.file_path,
                "unified_diff": patch.unified_diff,
                "original_code": patch.original_code,
                "patched_code": patch.patched_code,
                "explanation": patch.explanation,
                "confidence": patch.confidence,
                "pattern_used": patch.pattern_used,
                "success": patch.success,
            })

            if patch.success:
                logger.info(
                    "Patch generated",
                    vuln_type=patch.vuln_type,
                    file=patch.file_path,
                    confidence=patch.confidence,
                )
            else:
                logger.warning(
                    "Patch generation failed",
                    vuln_type=patch.vuln_type,
                    error=patch.error,
                )

        except Exception as e:
            logger.error(
                "Patch generation error",
                error=str(e),
                vuln=vuln.get("vuln_type"),
            )
            continue

    logger.info(
        "Patch Generation Agent complete",
        scan_id=scan_id,
        patches_generated=len(patches),
        successful=sum(1 for p in patches if p.get("success")),
    )

    return {
        "patches": patches,
        "current_step": "patch_generation_complete",
        "agent_log": [
            f"PatchGenerationAgent: {len(patches)} patches generated, "
            f"{sum(1 for p in patches if p.get('success'))} successful"
        ],
    }


def _generate_patch_for_vuln(
    vuln: dict,
    repository_path: str,
    llm,
    patch_index: int,
) -> GeneratedPatch:
    """
    Ek vulnerability ke liye patch generate karo.

    Steps:
    1. File padho
    2. Vulnerable function extract karo
    3. Secure pattern nikalo
    4. LLM se fix generate karo
    5. Diff banao
    """
    vuln_type = vuln.get("vuln_type", "GENERAL")
    file_path = vuln.get("file_path", "")
    line_start = vuln.get("line_start", 1)
    line_end = vuln.get("line_end", line_start)

    # Full file path banao
    full_path = Path(repository_path) / file_path
    if not full_path.exists():
        # Try absolute path
        full_path = Path(file_path)

    if not full_path.exists():
        return GeneratedPatch(
            finding_id=f"finding_{patch_index}",
            vuln_type=vuln_type,
            file_path=file_path,
            unified_diff="",
            original_code="",
            patched_code="",
            explanation="File not found",
            confidence=0.0,
            pattern_used="",
            success=False,
            error=f"File not found: {full_path}",
        )

    # File padho
    original_source = full_path.read_text(encoding="utf-8", errors="ignore")
    original_lines = original_source.splitlines()

    # Vulnerable area extract karo (context ke saath)
    context_start = max(0, line_start - 5)
    context_end = min(len(original_lines), line_end + 5)
    vulnerable_code = "\n".join(original_lines[context_start:context_end])

    # Secure pattern nikalo
    secure_pattern = SECURE_PATTERNS.get(vuln_type, "Use secure coding practices.")

    # LLM se patch generate karo
    prompt = _build_patch_prompt(
        vuln=vuln,
        vulnerable_code=vulnerable_code,
        full_source=original_source,
        secure_pattern=secure_pattern,
        line_start=line_start,
        line_end=line_end,
    )

    try:
        from langchain_core.messages import HumanMessage, SystemMessage

        messages = [
            SystemMessage(content=_get_patch_system_prompt()),
            HumanMessage(content=prompt),
        ]

        response = llm.invoke(messages)
        result = _parse_patch_response(response.content)

        if not result:
            raise ValueError("Could not parse patch response")

        # Patched source banao
        patched_source = _apply_patch_to_source(
        original_source=original_source,
        original_lines=original_lines,
        patched_function=result.get("patched_code", ""),
        line_start=line_start,
        line_end=line_end,
        context_start=context_start,
        context_end=context_end,
)

        # Unified diff banao
        unified_diff = _create_unified_diff(
            original=original_source,
            patched=patched_source,
            filename=file_path,
        )

        return GeneratedPatch(
            finding_id=f"finding_{patch_index}",
            vuln_type=vuln_type,
            file_path=file_path,
            unified_diff=unified_diff,
            original_code=vulnerable_code,
            patched_code=result.get("patched_code", ""),
            explanation=result.get("explanation", ""),
            confidence=result.get("confidence", 0.7),
            pattern_used=result.get("pattern_used", ""),
            success=True,
        )

    except Exception as e:
        logger.error("LLM patch generation failed", error=str(e))
        # Fallback — template-based patch
        return _generate_template_patch(
            vuln=vuln,
            vulnerable_code=vulnerable_code,
            file_path=file_path,
            patch_index=patch_index,
            error=str(e),
        )


def _get_patch_system_prompt() -> str:
    """System prompt for patch generation."""
    return """You are an expert security engineer generating secure patches for vulnerable Python code.

RULES:
1. Generate MINIMAL patches — only change what's necessary
2. Preserve existing functionality completely
3. Use the most Pythonic secure approach
4. Explain WHY the patch is secure
5. Always respond in valid JSON format
6. Never introduce new vulnerabilities

PATCH QUALITY:
- Parameterized queries for SQL injection
- Output escaping for XSS
- Environment variables for secrets
- URL validation for SSRF
- JSON instead of pickle for deserialization"""


def _build_patch_prompt(
    vuln: dict,
    vulnerable_code: str,
    full_source: str,
    secure_pattern: str,
    line_start: int,
    line_end: int,
) -> str:
    """Build a precise patch-generation prompt."""

    return f"""Generate a sourrce patch for this vulnerabilites

VULNERABILITY:
- Type: {vuln.get('vuln_type')}
- Severity: {vuln.get('severity')}
- File: {vuln.get('file_path')}
- Vulnerability starts at line: {line_start}
- Vulnerability ends at line: {line_end}
- Description: {vuln.get('description')}
- CWE: {vuln.get('cwe_id', 'N/A')}

VULNERABLE CODE CONTEXT:
```python
{vulnerable_code}

COMPLETE FILE SOURCE:
```python
{full_source[:4000]}
```

SECURE PATTERN TO FOLLOW:
{secure_pattern}

IMPORTANT INSTRUCTIONS:
1. Return the COMPLETE fixed file in patched_code
2. Only change the vulnerable lines
3. Keep everything else exactly the same
4. Use parameterized queries for SQL injection

Respond ONLY with this JSON (no markdown outside JSON):
{{
    "patched_code": "COMPLETE fixed file content here",
    "explanation": "why this patch fixes the vulnerability",
    "pattern_used": "parameterized queries / output escaping / etc",
    "confidence": 0.0-1.0,
    "changes_summary": "brief description of what changed"
}}"""


def _parse_patch_response(response_text: str) -> dict | None:
    """
    Parse the LLM patch response safely.

    Handles:
    - plain JSON
    - ```json ... ```
    - ``` ... ```
    - <think>...</think> reasoning
    - extra text before/after JSON
    """

    try:
        text = response_text.strip()

        if not text:
            logger.error("LLM returned an empty response")
            return None

        # -------------------------------------------------
        # 1. Remove <think>...</think> reasoning
        # -------------------------------------------------
        if "<think>" in text:
            if "</think>" in text:
                text = text.split("</think>", 1)[1].strip()
            else:
                text = text.split("<think>", 1)[0].strip()

        # -------------------------------------------------
        # 2. Remove markdown code fences
        # -------------------------------------------------
        if "```json" in text:
            text = text.split("```json", 1)[1]

            if "```" in text:
                text = text.split("```", 1)[0]

            text = text.strip()

        elif "```" in text:
            parts = text.split("```")

            if len(parts) >= 3:
                text = parts[1].strip()

                # Remove optional language identifier
                if text.startswith("json"):
                    text = text[4:].strip()

        # -------------------------------------------------
        # 3. Try direct JSON parsing
        # -------------------------------------------------
        try:
            result = json.loads(text)

            if isinstance(result, dict):
                return result

        except json.JSONDecodeError:
            pass

        # -------------------------------------------------
        # 4. Extract JSON object from surrounding text
        # -------------------------------------------------
        start = text.find("{")
        end = text.rfind("}")

        if start != -1 and end != -1 and end > start:

            json_text = text[start:end + 1]

            try:
                result = json.loads(json_text)

                if isinstance(result, dict):
                    return result

            except json.JSONDecodeError as e:
                logger.error(
                    "Extracted JSON is invalid",
                    error=str(e),
                )

        # -------------------------------------------------
        # 5. Log response for debugging
        # -------------------------------------------------
        logger.error(
            "Could not parse LLM response",
            response=text[:2000],
        )

        return None

    except Exception as e:
        logger.error(
            "Patch response parsing failed",
            error=str(e),
        )
        return None


def _apply_patch_to_source(
    original_source: str,
    original_lines: list,
    patched_function: str,
    line_start: int,
    line_end: int,
    context_start: int,
    context_end: int,
) -> str:
    """
    Patched code ko original source mein apply karo.
    
    Strategy:
    - LLM ne jo patched code diya use directly use karo
    - Agar LLM ne poori file di toh wahi use karo
    - Agar sirf function diya toh context replace karo
    """
    if not patched_function:
        return original_source

    patched_stripped = patched_function.strip()
    
    # Check karo — LLM ne poori file di ya sirf snippet?
    # Agar import statements hain toh poori file hai
    original_imports = [
        l for l in original_lines[:5] 
        if l.strip().startswith(("import ", "from "))
    ]
    
    patched_first_lines = patched_stripped.splitlines()[:5]
    has_imports = any(
        l.strip().startswith(("import ", "from "))
        for l in patched_first_lines
    )
    
    # Agar LLM ne poori file di — directly use karo
    if has_imports and len(patched_stripped.splitlines()) > 5:
        return patched_stripped
    
    # Sirf vulnerable section replace karo
    before = original_lines[:context_start]
    after = original_lines[context_end:]
    patched_lines = patched_stripped.splitlines()
    
    new_lines = before + patched_lines + after
    return "\n".join(new_lines)

def _create_unified_diff(
    original: str,
    patched: str,
    filename: str,
) -> str:
    """
    Create a proper Git-style unified diff.
    """

    original_lines = original.splitlines(keepends=True)
    patched_lines = patched.splitlines(keepends=True)

    diff = difflib.unified_diff(
        original_lines,
        patched_lines,
        fromfile=f"a/{filename}",
        tofile=f"b/{filename}",
        lineterm="\n",
    )

    return "".join(diff)


def _generate_template_patch(
    vuln: dict,
    vulnerable_code: str,
    file_path: str,
    patch_index: int,
    error: str,
) -> GeneratedPatch:
    """
    LLM fail hone pe template-based patch generate karo.
    Yeh fallback hai — basic but functional.
    """
    vuln_type = vuln.get("vuln_type", "GENERAL")

    template_explanations = {
        "SQLI": "Replace string concatenation with parameterized queries using ? placeholder",
        "XSS": "Escape user input using markupsafe.escape() before rendering",
        "SECRETS": "Move hardcoded secret to environment variable",
        "SSRF": "Validate URL against whitelist before making HTTP request",
        "DESERIALIZATION": "Replace pickle.loads() with json.loads() for safe deserialization",
    }

    return GeneratedPatch(
        finding_id=f"finding_{patch_index}",
        vuln_type=vuln_type,
        file_path=file_path,
        unified_diff="",
        original_code=vulnerable_code,
        patched_code="",
        explanation=template_explanations.get(vuln_type, "Apply secure coding practices"),
        confidence=0.5,
        pattern_used="template",
        success=False,
        error=f"LLM failed: {error}",
    )