from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, HttpUrl


class GistFile(BaseModel):
    filename: str
    language: Optional[str] = None
    raw_url: HttpUrl
    size: int


class Gist(BaseModel):
    id: str
    description: Optional[str] = None
    html_url: HttpUrl
    files: list[GistFile]

    @staticmethod
    def from_api(payload: dict) -> "Gist":
        files = []
        for f in (payload.get("files") or {}).values():
            # Some fields can be null in GitHub API
            if not f:
                continue
            raw_url = f.get("raw_url")
            filename = f.get("filename") or "unknown"
            language = f.get("language")
            size = int(f.get("size") or 0)
            if raw_url:
                files.append(GistFile(filename=filename, language=language, raw_url=raw_url, size=size))
        return Gist(
            id=str(payload.get("id")),
            description=payload.get("description"),
            html_url=payload.get("html_url"),
            files=files,
        )
