"""
tests/test_person_service.py — Unit tests for PersonService

Run with: pytest tests/test_person_service.py
"""
import pytest
import numpy as np
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.models.user import User
from app.models.person import KnownPerson
from app.models.face_encoding import FaceEncoding
from app.models.junction_tables import userknownperson
from app.services.person_service import PersonService
from app.db.base import Base


@pytest.fixture
def db_session():
    """Create an in-memory SQLite database for testing"""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()
    
    # Create test user
    user = User(userid=1, name="Test User", medicalcondition="Short-term memory loss")
    session.add(user)
    session.commit()
    
    yield session
    
    session.close()


def test_register_person(db_session):
    """Test person registration with face encoding"""
    service = PersonService(db_session)
    
    # Generate random 128-d encoding
    encoding = np.random.rand(128).tolist()
    
    person_id = service.register_person(
        user_id=1,
        name="John Doe",
        encoding=encoding,
        relationship_type="friend",
        priority_level=3,
        confidence_score=0.95,
    )
    
    assert person_id is not None
    
    # Verify person was created
    person = db_session.get(KnownPerson, person_id)
    assert person is not None
    assert person.name == "John Doe"
    assert person.relationshiptype == "friend"
    assert person.prioritylevel == 3
    
    # Verify face encoding was stored
    face_enc = db_session.query(FaceEncoding).filter_by(personid=person_id).first()
    assert face_enc is not None
    assert face_enc.confidencescore == 0.95
    
    # Verify encoding can be deserialized
    stored_encoding = face_enc.get_encoding_vector()
    assert len(stored_encoding) == 128
    assert np.allclose(stored_encoding, encoding)


def test_identify_person_match(db_session):
    """Test person identification with matching encoding"""
    service = PersonService(db_session)
    
    # Register a person
    original_encoding = np.random.rand(128).tolist()
    person_id = service.register_person(
        user_id=1,
        name="Jane Smith",
        encoding=original_encoding,
        relationship_type="family",
    )
    
    # Try to identify with similar encoding (high similarity)
    similar_encoding = (np.array(original_encoding) + np.random.rand(128) * 0.01).tolist()
    
    matched_id, confidence, person = service.identify_person(
        encoding=similar_encoding,
        user_id=1,
    )
    
    # Should match (cosine similarity should be > 0.6)
    assert matched_id == person_id
    assert confidence is not None
    assert confidence > 0.6
    assert person.name == "Jane Smith"


def test_identify_person_no_match(db_session):
    """Test person identification with no matching encoding"""
    service = PersonService(db_session)
    
    # Register a person
    original_encoding = np.random.rand(128).tolist()
    service.register_person(
        user_id=1,
        name="Bob Johnson",
        encoding=original_encoding,
    )
    
    # Try to identify with completely different encoding
    different_encoding = np.random.rand(128).tolist()
    
    matched_id, confidence, person = service.identify_person(
        encoding=different_encoding,
        user_id=1,
    )
    
    # Should not match (cosine similarity should be < 0.6)
    assert matched_id is None
    assert confidence is None
    assert person is None


def test_identify_person_no_encodings(db_session):
    """Test person identification when no encodings exist"""
    service = PersonService(db_session)
    
    encoding = np.random.rand(128).tolist()
    
    matched_id, confidence, person = service.identify_person(
        encoding=encoding,
        user_id=1,
    )
    
    assert matched_id is None
    assert confidence is None
    assert person is None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
