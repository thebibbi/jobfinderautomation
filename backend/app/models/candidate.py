from sqlalchemy import Column, Integer, String, Text, JSON, DateTime
from datetime import datetime
from ..database import Base


class Candidate(Base):
    """Stores candidate information and reference materials"""
    __tablename__ = "candidates"

    id = Column(Integer, primary_key=True, index=True)

    # Basic Info
    name = Column(String)
    email = Column(String, unique=True, index=True)
    phone = Column(String, nullable=True)

    # Resume Data
    experience_inventory = Column(JSON)  # From CSV
    skills_taxonomy = Column(JSON)  # From CSV
    corporate_translation = Column(JSON)  # From CSV
    achievement_library = Column(JSON)  # From CSV

    # Voice Profile
    voice_profile = Column(Text)  # Writing samples and style guide

    # Resume Templates
    resume_templates = Column(JSON)  # Store template IDs and types

    # Preferences
    target_roles = Column(JSON)  # List of desired job titles
    preferred_locations = Column(JSON)
    min_salary = Column(Integer, nullable=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<Candidate {self.name}>"
