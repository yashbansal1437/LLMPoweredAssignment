import os
import mimetypes
from datetime import datetime
from typing import Dict, List, Optional

import PyPDF2
import docx


def _get_file_metadata(filepath: str) -> Dict:
    stat = os.stat(filepath)
    return {
        "name": os.path.basename(filepath),
        "size_bytes": stat.st_size,
        "modified_at": datetime.fromtimestamp(stat.st_mtime).isoformat(),
        "absolute_path": os.path.abspath(filepath),
    }


def read_file(filepath: str) -> Dict:
    """
    Read PDF, TXT, DOCX files and extract text content.
    Returns structured dict with metadata and content.
    """

    if not os.path.exists(filepath):
        return {"success": False, "error": "File does not exist."}

    try:
        content = ""
        extension = os.path.splitext(filepath)[1].lower()

        if extension == ".txt":
            with open(filepath, "r", encoding="utf-8") as f:
                content = f.read()

        elif extension == ".pdf":
            with open(filepath, "rb") as f:
                reader = PyPDF2.PdfReader(f)
                content = "\n".join(
                    page.extract_text() or "" for page in reader.pages
                )

        elif extension == ".docx":
            doc = docx.Document(filepath)
            content = "\n".join([para.text for para in doc.paragraphs])

        else:
            return {"success": False, "error": f"Unsupported file type: {extension}"}

        return {
            "success": True,
            "metadata": _get_file_metadata(filepath),
            "content": content,
        }

    except Exception as e:
        return {"success": False, "error": str(e)}


def list_files(directory: str, extension: Optional[str] = None) -> List[Dict]:
    """
    List files in directory. Optional extension filter.
    """

    if not os.path.exists(directory):
        return []

    files_data = []

    for root, _, files in os.walk(directory):
        for file in files:
            if extension and not file.lower().endswith(extension.lower()):
                continue

            filepath = os.path.join(root, file)
            files_data.append(_get_file_metadata(filepath))

    return files_data


def write_file(filepath: str, content: str) -> Dict:
    """
    Write content to file. Creates directories if needed.
    """

    try:
        os.makedirs(os.path.dirname(filepath), exist_ok=True)

        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)

        return {
            "success": True,
            "message": "File written successfully.",
            "metadata": _get_file_metadata(filepath),
        }

    except Exception as e:
        return {"success": False, "error": str(e)}


def search_in_file(filepath: str, keyword: str) -> Dict:
    """
    Case-insensitive keyword search with context.
    """

    file_data = read_file(filepath)

    if not file_data.get("success"):
        return file_data

    content = file_data["content"]
    keyword_lower = keyword.lower()

    matches = []
    lines = content.split("\n")

    for i, line in enumerate(lines):
        if keyword_lower in line.lower():
            context = "\n".join(
                lines[max(0, i - 2): min(len(lines), i + 3)]
            )
            matches.append({
                "line_number": i + 1,
                "context": context
            })

    return {
        "success": True,
        "keyword": keyword,
        "total_matches": len(matches),
        "matches": matches
    }
