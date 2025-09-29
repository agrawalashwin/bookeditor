#!/usr/bin/env python3
"""
Seed script to create demo data for BookEditor
"""
import asyncio
import os
import sys
from datetime import datetime

# Add the app directory to the path
sys.path.append(os.path.dirname(__file__))

from app.database import SessionLocal, engine
from app.models import Base, Manuscript, ManuscriptVersion, StylePref
from app.services.embeddings import EmbeddingService


async def create_demo_manuscript():
    """Create a demo manuscript with sample content."""
    
    demo_content = """# The Great Adventure

## Chapter 1: The Beginning

It was a dark and stormy night when Sarah first discovered the mysterious letter hidden beneath the floorboards of her grandmother's attic. The parchment was yellowed with age, and the ink had faded to a rusty brown, but the words were still legible.

"My dearest Sarah," it began, "if you are reading this, then the time has come for you to learn the truth about our family's greatest secret."

Sarah's hands trembled as she continued reading. The letter spoke of hidden treasures, ancient curses, and a quest that had been passed down through generations of her family. Each word seemed to pull her deeper into a world she never knew existed.

The wind howled outside, rattling the old windows of the Victorian house. Sarah pulled her sweater tighter around her shoulders and moved closer to the single bare bulb that illuminated the dusty attic. She had come up here looking for Christmas decorations, but instead had found something far more intriguing.

## Chapter 2: The Discovery

The next morning, Sarah couldn't shake the feeling that her life had changed forever. She sat at her kitchen table, the letter spread out before her, trying to make sense of what she had read. The handwriting was definitely her grandmother's, but the story it told seemed impossible.

According to the letter, their family had been guardians of a powerful artifact for over two centuries. The artifact, known as the Moonstone of Eldara, was said to possess the ability to reveal hidden truths and unlock doors to other realms.

Sarah had always thought her grandmother's stories were just fairy tales, but now she wasn't so sure. The letter contained specific details about the artifact's location and the rituals required to activate its power. It also warned of the dangers that came with such knowledge.

"The Moonstone chooses its guardian," the letter continued. "It has been waiting for you, Sarah. You have the gift, just as I did, and my grandmother before me. But with great power comes great responsibility. There are those who would use the Moonstone for evil purposes, and it is our duty to protect it."

## Chapter 3: The Quest Begins

Sarah spent the rest of the morning researching her family's history online. She discovered records of her ancestors dating back to the early 1800s, many of whom had been involved in archaeological expeditions and mysterious disappearances. The pattern was clear: every generation had produced at least one family member who seemed to vanish from public records for extended periods.

Her grandmother, Eleanor Blackwood, had been no exception. According to the records, Eleanor had spent several years in her twenties traveling through remote parts of Scotland and Ireland, supposedly studying ancient Celtic traditions. But the letter suggested there had been much more to these journeys than academic research.

As Sarah delved deeper into the mystery, she began to notice strange coincidences. Books about ancient artifacts would appear in her local library's new arrivals section. She would overhear conversations about mysterious stones and hidden treasures. It was as if the universe was conspiring to guide her toward her destiny.

That evening, Sarah made her decision. She would follow the clues in her grandmother's letter and begin the quest to find the Moonstone of Eldara. She had no idea what dangers lay ahead, but she knew she couldn't ignore the calling any longer."""

    db = SessionLocal()
    try:
        # Create manuscript
        manuscript = Manuscript(
            title="The Great Adventure",
            author="Demo Author"
        )
        db.add(manuscript)
        db.commit()
        
        # Create initial version
        version_tag = datetime.now().isoformat()
        initial_version = ManuscriptVersion(
            manuscript_id=manuscript.id,
            version_tag=version_tag,
            content=demo_content
        )
        db.add(initial_version)
        db.commit()
        
        # Update manuscript to point to current version
        manuscript.current_version_id = initial_version.id
        db.commit()
        
        # Add some style preferences
        style_prefs = [
            StylePref(manuscript_id=manuscript.id, key="tone", value="adventurous and mysterious"),
            StylePref(manuscript_id=manuscript.id, key="reading_level", value="young adult"),
            StylePref(manuscript_id=manuscript.id, key="pacing", value="moderate with building tension"),
            StylePref(manuscript_id=manuscript.id, key="voice", value="third person limited"),
        ]
        
        for pref in style_prefs:
            db.add(pref)
        db.commit()
        
        print(f"Created demo manuscript: {manuscript.id}")
        print(f"Title: {manuscript.title}")
        print(f"Content length: {len(demo_content)} characters")
        
        # Process embeddings if OpenAI API key is available
        if os.getenv("OPENAI_API_KEY"):
            print("Processing embeddings...")
            embedding_service = EmbeddingService()
            await embedding_service.process_manuscript_version(db, str(initial_version.id))
            print("Embeddings processed successfully!")
        else:
            print("No OpenAI API key found, skipping embeddings")
        
        return manuscript.id
        
    except Exception as e:
        print(f"Error creating demo manuscript: {e}")
        db.rollback()
        raise
    finally:
        db.close()


async def main():
    """Main function to run the seed script."""
    print("Creating database tables...")
    Base.metadata.create_all(bind=engine)
    
    print("Creating demo manuscript...")
    manuscript_id = await create_demo_manuscript()
    
    print(f"\nDemo manuscript created successfully!")
    print(f"Manuscript ID: {manuscript_id}")
    print("\nYou can now start the API server and web frontend to test the application.")


if __name__ == "__main__":
    asyncio.run(main())
