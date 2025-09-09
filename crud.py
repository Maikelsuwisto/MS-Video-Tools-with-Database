from sqlalchemy.ext.asyncio import AsyncSession
from models import Transcript

async def create_transcript(db: AsyncSession, filename: str, text: str):
    transcript = Transcript(filename=filename, text=text)
    db.add(transcript)
    await db.commit()
    await db.refresh(transcript)
    return transcript
