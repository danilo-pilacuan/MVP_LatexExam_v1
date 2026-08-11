import uuid
from sqlalchemy import String, Text, ForeignKey, DateTime, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID
from pgvector.sqlalchemy import Vector

class Base(DeclarativeBase):
    pass

class Subject(Base):
    __tablename__ = "subjects"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(200))
    syllabus: Mapped[list["SyllabusTopic"]] = relationship(back_populates="subject")

class SyllabusTopic(Base):
    __tablename__ = "syllabus_topics"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    subject_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("subjects.id"))
    subject: Mapped["Subject"] = relationship(back_populates="syllabus")
    title: Mapped[str] = mapped_column(String(200))
    weight: Mapped[float] = mapped_column(default=1.0)

class GeneratedQuestion(Base):
    __tablename__ = "generated_questions"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    subject_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("subjects.id"))
    topic: Mapped[str] = mapped_column(String(200))
    bloom_level: Mapped[str] = mapped_column(String(50))
    difficulty: Mapped[str] = mapped_column(String(50))
    question_text: Mapped[str] = mapped_column(Text)
    embedding: Mapped[list[float]] = mapped_column(Vector(1536))
    created_at: Mapped[str] = mapped_column(DateTime, server_default=func.now())