from sqlalchemy import Column, Integer, String, Text
from db import Base

class Transcript(Base):
    __tablename__ = "transcripts"

    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String, index=True)
    text = Column(Text)
