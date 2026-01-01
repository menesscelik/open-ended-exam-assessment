"""
BERTurk Semantic Similarity Module
Uses sentence-transformers for Turkish text similarity analysis
"""

import logging
from typing import Tuple
import numpy as np

logger = logging.getLogger(__name__)

# Model loading (lazy initialization)
_model = None


def get_model():
    """Lazy load the sentence transformer model."""
    global _model
    if _model is None:
        try:
            from sentence_transformers import SentenceTransformer
            logger.info("Loading BERTurk model...")
            # Using multilingual model that supports Turkish well
            _model = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')
            logger.info("BERTurk model loaded successfully")
        except ImportError:
            logger.error("sentence-transformers not installed. Run: pip install sentence-transformers")
            raise
        except Exception as e:
            logger.error(f"Failed to load model: {e}")
            raise
    return _model


def get_embeddings(text: str) -> np.ndarray:
    """
    Generate embeddings for a given text using BERTurk.
    
    Args:
        text: Input text string
        
    Returns:
        numpy array of embeddings
    """
    model = get_model()
    return model.encode(text, convert_to_numpy=True)


def cosine_similarity(vec1: np.ndarray, vec2: np.ndarray) -> float:
    """
    Calculate cosine similarity between two vectors.
    
    Args:
        vec1: First embedding vector
        vec2: Second embedding vector
        
    Returns:
        Cosine similarity score (0-1)
    """
    dot_product = np.dot(vec1, vec2)
    norm1 = np.linalg.norm(vec1)
    norm2 = np.linalg.norm(vec2)
    
    if norm1 == 0 or norm2 == 0:
        return 0.0
    
    similarity = dot_product / (norm1 * norm2)
    # Clamp to [0, 1] range
    return float(max(0.0, min(1.0, similarity)))


def calculate_bert_score(ideal_cevap: str, ogrenci_cevabi: str) -> float:
    """
    Calculate semantic similarity between ideal answer and student answer.
    
    Args:
        ideal_cevap: The ideal/expected answer
        ogrenci_cevabi: The student's answer
        
    Returns:
        bert_skoru: Similarity score between 0 and 1
    """
    if not ideal_cevap or not ogrenci_cevabi:
        return 0.0
    
    try:
        # Get embeddings for both texts
        ideal_embedding = get_embeddings(ideal_cevap)
        student_embedding = get_embeddings(ogrenci_cevabi)
        
        # Calculate cosine similarity
        bert_skoru = cosine_similarity(ideal_embedding, student_embedding)
        
        logger.info(f"BERT similarity calculated: {bert_skoru:.4f}")
        return bert_skoru
        
    except Exception as e:
        logger.error(f"Error calculating BERT score: {e}")
        return 0.0


def calculate_keyword_score(anahtar_kelimeler: str, ogrenci_cevabi: str) -> float:
    """
    Calculate keyword matching score.
    
    Args:
        anahtar_kelimeler: Comma-separated keywords
        ogrenci_cevabi: Student's answer
        
    Returns:
        Score between 0 and 1 based on keyword coverage
    """
    if not anahtar_kelimeler or not ogrenci_cevabi:
        return 0.0
    
    keywords = [k.strip().lower() for k in anahtar_kelimeler.split(',') if k.strip()]
    if not keywords:
        return 0.0
    
    answer_lower = ogrenci_cevabi.lower()
    matched = sum(1 for kw in keywords if kw in answer_lower)
    
    return matched / len(keywords)
