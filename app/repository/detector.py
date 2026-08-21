"""
Language aur Framework Detector
Kya karta hai:
- Repository mein kaunsi programming language hai yeh detect karta hai
- Kaunsa framework use ho raha hai yeh dhundta hai
- Entry points identify karta hai (jaise app.py, main.py, manage.py)
- Dependencies list karta hai (requirements.txt se)
"""
import os
from pathlib import Path
from collections import Counter
from app.core.logger import get_logger

logger = get_logger("detector")

# Har extension ka language naam
EXTENSION_MAP = {
    ".py": "python",
    ".js": "javascript",
    ".ts": "typescript",
    ".java": "java",
    ".go": "go",
    ".rb": "ruby",
    ".php": "php",
    ".cs": "csharp",
    ".cpp": "cpp",
    ".c": "c",
}

# Python frameworks ke signatures
# Key = framework naam, Value = file ya import jo us framework ko identify kare
PYTHON_FRAMEWORK_SIGNATURES = {
    "flask": ["flask", "Flask"],
    "django": ["django", "Django", "manage.py"],
    "fastapi": ["fastapi", "FastAPI"],
    "sqlalchemy": ["sqlalchemy", "SQLAlchemy"],
    "celery": ["celery", "Celery"],
    "pytest": ["pytest", "conftest.py"],
}

# Yeh files important entry points hain
ENTRY_POINT_FILES = [
    "main.py",
    "app.py",
    "run.py",
    "server.py",
    "manage.py",
    "wsgi.py",
    "asgi.py",
    "__main__.py",
]

# Yeh files ignore karo — analysis ke liye useful nahi
IGNORE_DIRS = {
    ".git",
    "__pycache__",
    ".venv",
    "venv",
    "env",
    "node_modules",
    ".pytest_cache",
    "dist",
    "build",
    ".eggs",
    "*.egg-info",
    "migrations",
}


def detect_language(repo_path: str) -> str:
    """
    Repository mein sabse zyada use hone wali language detect karo.
    
    Kaise: Har file ka extension count karo, jo sabse zyada wo language hai.
    
    Args:
        repo_path: Repository ka local path
        
    Returns:
        Language naam jaise "python", "javascript"
        "unknown" agar detect nahi hua
    """
    extension_counts = Counter()
    
    # Saari files scan karo
    for root, dirs, files in os.walk(repo_path):
        # Ignored directories skip karo — in-place modify karna zaroori hai
        dirs[:] = [d for d in dirs if d not in IGNORE_DIRS]
        
        for file in files:
            # File ka extension nikalo
            ext = Path(file).suffix.lower()
            # Agar yeh extension humari list mein hai toh count karo
            if ext in EXTENSION_MAP:
                extension_counts[ext] += 1
    
    if not extension_counts:
        logger.warning("No recognized file extensions found", path=repo_path)
        return "unknown"
    
    # Sabse zyada count wala extension nikalo
    most_common_ext = extension_counts.most_common(1)[0][0]
    detected = EXTENSION_MAP[most_common_ext]
    
    logger.info("Language detected", language=detected, path=repo_path)
    return detected


def detect_frameworks(repo_path: str) -> list[str]:
    """
    Python frameworks detect karo repository mein.
    
    Kaise:
    1. requirements.txt padho
    2. Import statements scan karo
    3. Special files dhundho
    
    Args:
        repo_path: Repository ka local path
        
    Returns:
        Detected frameworks ki list jaise ["flask", "sqlalchemy"]
    """
    detected_frameworks = set()
    repo = Path(repo_path)
    
    # Step 1: requirements.txt padho
    req_file = repo / "requirements.txt"
    if req_file.exists():
        try:
            content = req_file.read_text(encoding="utf-8", errors="ignore").lower()
            for framework, signatures in PYTHON_FRAMEWORK_SIGNATURES.items():
                for sig in signatures:
                    # requirements.txt mein framework ka naam dhundho
                    if sig.lower() in content:
                        detected_frameworks.add(framework)
                        break
        except Exception as e:
            logger.warning("Could not read requirements.txt", error=str(e))
    
    
    
    # Step 2: Python files mein import statements scan karo
    for root, dirs, files in os.walk(repo_path):
        dirs[:] = [d for d in dirs if d not in IGNORE_DIRS]
        
        for file in files:
            # Sirf Python files scan karo
            if not file.endswith(".py"):
                continue
            
            file_path = Path(root) / file
            try:
                # File ke pehle 50 lines padho — imports usually upar hote hain
                content = file_path.read_text(
                    encoding="utf-8", errors="ignore"
                ).split("\n")[:50]
                content_str = "\n".join(content).lower()
                
                for framework, signatures in PYTHON_FRAMEWORK_SIGNATURES.items():
                    for sig in signatures:
                        if sig.lower() in content_str:
                            detected_frameworks.add(framework)
                            break
            except Exception:
                # Ek file fail ho toh skip karo, abort mat karo
                continue
    
    result = list(detected_frameworks)
    logger.info("Frameworks detected", frameworks=result, path=repo_path)
    return result




def find_entry_points(repo_path: str) -> list[str]:
    
    entry_points = []
    repo = Path(repo_path)
    
    for root, dirs, files in os.walk(repo_path):
        dirs[:] = [d for d in dirs if d not in IGNORE_DIRS]
        
        for file in files:
            if file in ENTRY_POINT_FILES:
                # Relative path store karo — absolute path nahi
                rel_path = str(Path(root).relative_to(repo) / file)
                entry_points.append(rel_path)
    
    logger.info("Entry points found", count=len(entry_points), path=repo_path)
    return entry_points


def read_dependencies(repo_path: str) -> list[str]:
    """
    requirements.txt se dependencies padho.
    
    Args:
        repo_path: Repository ka local path
        
    Returns:
        Dependencies ki list jaise ["flask==2.0.1", "sqlalchemy>=1.4"]
    """
    dependencies = []
    req_file = Path(repo_path) / "requirements.txt"
    
    if not req_file.exists():
        logger.info("No requirements.txt found", path=repo_path)
        return dependencies
    
    try:
        lines = req_file.read_text(encoding="utf-8", errors="ignore").splitlines()
        for line in lines:
            # Empty lines aur comments skip karo
            line = line.strip()
            if line and not line.startswith("#"):
                dependencies.append(line)
    except Exception as e:
        logger.warning("Could not read dependencies", error=str(e))
    
    return dependencies