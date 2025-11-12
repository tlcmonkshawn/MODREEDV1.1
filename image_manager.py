"""Image storage and management system."""
import os
import base64
from datetime import datetime
from typing import Optional, List, Dict, Any
from sqlalchemy import create_engine, Column, Integer, String, DateTime, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from PIL import Image
import io
import config

Base = declarative_base()


class CapturedImage(Base):
    """Database model for captured images."""
    __tablename__ = 'captured_images'
    
    id = Column(Integer, primary_key=True)
    filename = Column(String(255), nullable=False)
    filepath = Column(String(500), nullable=False)
    name = Column(String(255), nullable=True)
    category = Column(String(100), nullable=True)
    state = Column(String(50), default='CAPTURED')  # CAPTURED, USED, DISCARDED
    captured_at = Column(DateTime, default=datetime.utcnow)
    image_metadata = Column(Text, nullable=True)  # JSON string for additional metadata

class ImageManager:
    """Manages image storage and retrieval."""
    
    def __init__(self, db_url: str = None):
        """Initialize image manager.
        
        Args:
            db_url: Database URL (defaults to config value)
        """
        self.db_url = db_url or config.DATABASE_URL
        self.engine = create_engine(self.db_url)
        Base.metadata.create_all(self.engine)
        self.SessionLocal = sessionmaker(bind=self.engine)
        
        # Ensure storage directory exists
        os.makedirs(config.IMAGE_STORAGE_DIR, exist_ok=True)
    
    def _get_session(self) -> Session:
        """Get a database session."""
        return self.SessionLocal()
    
    def store_image(self, image_data: bytes, name: Optional[str] = None, 
                   category: Optional[str] = None, metadata: Optional[Dict] = None) -> CapturedImage:
        """Store a captured image.
        
        Args:
            image_data: Image bytes (JPEG/PNG)
            name: Optional name for the image
            category: Optional category
            metadata: Optional metadata dictionary
            
        Returns:
            CapturedImage instance
        """
        # Generate filename
        timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S_%f')
        filename = f"snapshot_{timestamp}.jpg"
        filepath = os.path.join(config.IMAGE_STORAGE_DIR, filename)
        
        # Save image file
        with open(filepath, 'wb') as f:
            f.write(image_data)
        
        # Store in database
        db = self._get_session()
        try:
            image_record = CapturedImage(
                filename=filename,
                filepath=filepath,
                name=name,
                category=category,
                state='CAPTURED',
                image_metadata=str(metadata) if metadata else None
            )
            db.add(image_record)
            db.commit()
            db.refresh(image_record)
            return image_record
        finally:
            db.close()
    
    def update_image(self, image_id: int, name: Optional[str] = None,
                    category: Optional[str] = None, state: Optional[str] = None) -> Optional[CapturedImage]:
        """Update image metadata.
        
        Args:
            image_id: Image ID
            name: New name (optional)
            category: New category (optional)
            state: New state (optional)
            
        Returns:
            Updated CapturedImage instance, or None if not found
        """
        db = self._get_session()
        try:
            image = db.query(CapturedImage).filter(CapturedImage.id == image_id).first()
            if image:
                if name is not None:
                    image.name = name
                if category is not None:
                    image.category = category
                if state is not None:
                    image.state = state
                db.commit()
                db.refresh(image)
                return image
            return None
        finally:
            db.close()
    
    def get_image(self, image_id: int) -> Optional[CapturedImage]:
        """Get image by ID.
        
        Args:
            image_id: Image ID
            
        Returns:
            CapturedImage instance, or None if not found
        """
        db = self._get_session()
        try:
            return db.query(CapturedImage).filter(CapturedImage.id == image_id).first()
        finally:
            db.close()
    
    def get_last_image(self) -> Optional[CapturedImage]:
        """Get the most recently captured image.
        
        Returns:
            Most recent CapturedImage instance, or None if no images
        """
        db = self._get_session()
        try:
            return db.query(CapturedImage).order_by(CapturedImage.captured_at.desc()).first()
        finally:
            db.close()
    
    def get_recent_images(self, limit: int = 10) -> List[CapturedImage]:
        """Get recent captured images.
        
        Args:
            limit: Maximum number of images to return
            
        Returns:
            List of CapturedImage instances
        """
        db = self._get_session()
        try:
            return db.query(CapturedImage).order_by(CapturedImage.captured_at.desc()).limit(limit).all()
        finally:
            db.close()
    
    def mark_as_used(self, image_id: int) -> bool:
        """Mark an image as used.
        
        Args:
            image_id: Image ID
            
        Returns:
            True if successful, False otherwise
        """
        return self.update_image(image_id, state='USED') is not None
    
    def mark_as_discarded(self, image_id: int) -> bool:
        """Mark an image as discarded.
        
        Args:
            image_id: Image ID
            
        Returns:
            True if successful, False otherwise
        """
        return self.update_image(image_id, state='DISCARDED') is not None

