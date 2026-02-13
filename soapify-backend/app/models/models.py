from sqlalchemy import (
    Column,
    Integer,
    String,
    Text,
    DateTime,
    ForeignKey,
    UniqueConstraint
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.core.database import Base


# 1. Users (Doctors)
class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    full_name = Column(String, nullable=False)
    role = Column(String, default="doctor", nullable=False)
    specialization = Column(String, nullable=True)

    transcripts = relationship(
        "Transcript",
        back_populates="doctor",
        cascade="all, delete-orphan"
    )

    patients = relationship(
        "Patient",
        cascade="all, delete-orphan"
    )


# 2. Patients (Doctor-scoped)
class Patient(Base):
    __tablename__ = "patients"

    id = Column(Integer, primary_key=True, index=True)

    doctor_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False
    )

    name = Column(String, index=True, nullable=False)
    age = Column(Integer, nullable=False)
    gender = Column(String, nullable=True)

    transcripts = relationship(
        "Transcript",
        back_populates="patient",
        cascade="all, delete-orphan"
    )


# 3. Transcripts (Raw Input)
class Transcript(Base):
    __tablename__ = "transcripts"

    id = Column(Integer, primary_key=True, index=True)

    doctor_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False
    )

    patient_id = Column(
        Integer,
        ForeignKey("patients.id", ondelete="CASCADE"),
        nullable=False
    )

    text = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    doctor = relationship("User", back_populates="transcripts")
    patient = relationship("Patient", back_populates="transcripts")

    soap_note = relationship(
        "SOAPNote",
        uselist=False,
        back_populates="transcript",
        cascade="all, delete-orphan"
    )


# 4. SOAP Notes (Doctor-wise Visit Numbering)
class SOAPNote(Base):
    __tablename__ = "soap_notes"

    id = Column(Integer, primary_key=True, index=True)

    transcript_id = Column(
        Integer,
        ForeignKey("transcripts.id", ondelete="CASCADE"),
        nullable=False,
        unique=True
    )

    doctor_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    # Doctor-visible visit number (SOAP #1, #2, ...)
    doctor_soap_number = Column(Integer, nullable=False)

    content = Column(Text, nullable=True)

    # PROCESSING | COMPLETED | FAILED
    status = Column(String, default="PROCESSING", nullable=False)

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    transcript = relationship("Transcript", back_populates="soap_note")
    doctor = relationship("User")

    __table_args__ = (
        UniqueConstraint(
            "doctor_id",
            "doctor_soap_number",
            name="uq_doctor_soap_number"
        ),
    )
