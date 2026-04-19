"""
services/person_service.py — Face encoding matching and person identification
"""
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.models.face_encoding import FaceEncoding
from app.models.person import KnownPerson
from app.models.junction_tables import userknownperson
from app.config import get_settings


class PersonService:
    """Service for person identification and registration"""

    def __init__(self, db: Session):
        self.db = db
        self.settings = get_settings()

    def identify_person(
        self, encoding: list[float], user_id: int
    ) -> tuple[int | None, float | None, KnownPerson | None]:
        """
        Identify a person by face encoding using cosine similarity.
        
        Returns:
            (person_id, confidence_score, person_obj) or (None, None, None) if no match
        """
        # Get all face encodings for persons associated with this user
        stmt = (
            select(FaceEncoding)
            .join(KnownPerson, FaceEncoding.personid == KnownPerson.personid)
            .join(
                userknownperson,
                KnownPerson.personid == userknownperson.c.personid
            )
            .where(userknownperson.c.userid == user_id)
        )
        
        all_encodings = self.db.execute(stmt).scalars().all()
        
        if not all_encodings:
            return None, None, None

        # Compute cosine similarity for each stored encoding
        input_vec = np.array(encoding).reshape(1, -1)
        best_match_id = None
        best_score = 0.0
        
        for enc in all_encodings:
            stored_vec = np.array(enc.get_encoding_vector()).reshape(1, -1)
            score = cosine_similarity(input_vec, stored_vec)[0][0]
            
            if score > best_score:
                best_score = score
                best_match_id = enc.personid

        # Check threshold
        if best_score >= self.settings.FACE_SIMILARITY_THRESHOLD:
            person = self.db.get(KnownPerson, best_match_id)
            return best_match_id, float(best_score), person
        
        return None, None, None

    def register_person(
        self,
        user_id: int,
        name: str,
        encoding: list[float],
        relationship_type: str | None = None,
        priority_level: int | None = None,
        confidence_score: float | None = None,
    ) -> int:
        """
        Register a new person with face encoding.
        
        Returns:
            person_id of the newly created person
        """
        # Create KnownPerson record
        person = KnownPerson(
            name=name,
            relationshiptype=relationship_type,
            prioritylevel=priority_level,
        )
        self.db.add(person)
        self.db.flush()  # Get the person_id

        # Create FaceEncoding record
        face_enc = FaceEncoding(
            personid=person.personid,
            encodingdata=FaceEncoding.serialise_encoding(encoding),
            confidencescore=confidence_score,
        )
        self.db.add(face_enc)

        # Link person to user via junction table
        stmt = userknownperson.insert().values(
            userid=user_id,
            personid=person.personid
        )
        self.db.execute(stmt)
        
        self.db.commit()
        return person.personid
