import json

from sqlalchemy import Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from backend.app.db import Base


class StandardModel(Base):
    __tablename__ = "standards"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    is_number: Mapped[str] = mapped_column(String(64), index=True)
    part: Mapped[str] = mapped_column(String(64), nullable=True)
    title: Mapped[str] = mapped_column(String(512))
    domain: Mapped[str] = mapped_column(String(128), index=True)
    publication_date: Mapped[str] = mapped_column(String(32))
    amendment_history_json: Mapped[str] = mapped_column(Text, default="[]")
    superseded_by: Mapped[str] = mapped_column(String(256), nullable=True)
    normative_references_json: Mapped[str] = mapped_column(Text, default="[]")
    certification: Mapped[str] = mapped_column(String(256))
    abstract: Mapped[str] = mapped_column(Text)
    tags_json: Mapped[str] = mapped_column(Text, default="[]")
    pdf_url: Mapped[str] = mapped_column(String(512), nullable=True)
    search_text: Mapped[str] = mapped_column(Text, index=False)

    @property
    def amendment_history(self) -> list[str]:
        return json.loads(self.amendment_history_json or "[]")

    @property
    def normative_references(self) -> list[str]:
        return json.loads(self.normative_references_json or "[]")

    @property
    def tags(self) -> list[str]:
        return json.loads(self.tags_json or "[]")

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "is_number": self.is_number,
            "part": self.part,
            "title": self.title,
            "domain": self.domain,
            "publication_date": self.publication_date,
            "amendment_history": self.amendment_history,
            "superseded_by": self.superseded_by,
            "normative_references": self.normative_references,
            "certification": self.certification,
            "abstract": self.abstract,
            "tags": self.tags,
            "pdf_url": self.pdf_url,
        }
