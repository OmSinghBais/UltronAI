"""
ATLAS — Face Gate Module
Provides local face enrollment and verification with encryption at rest using cryptography.fernet.
All face features/embeddings remain on-device and encrypted.
"""

import json
import math
import os
from typing import Any, Dict, List, Optional, Union

try:
    from cryptography.fernet import Fernet
except ImportError:
    Fernet = None


def generate_face_key() -> bytes:
    """
    Generates a new Fernet key for encrypting face embeddings at rest.
    """
    if Fernet is None:
        raise ImportError("cryptography module is not installed")
    return Fernet.generate_key()


def _calculate_euclidean_distance(v1: List[float], v2: List[float]) -> float:
    if len(v1) != len(v2):
        raise ValueError("Vector dimensions do not match")
    return math.sqrt(sum((a - b) ** 2 for a, b in zip(v1, v2)))


def enroll_face(
    face_vector: List[float],
    key: bytes,
    storage_path: str = "./storage/face_embedding.enc",
) -> Dict[str, Any]:
    """
    Encrypts and stores a face feature embedding at rest.
    """
    action_name = "enroll_face"
    if Fernet is None:
        return {"status": "error", "error": "cryptography module is not installed"}

    if not face_vector or not isinstance(face_vector, list):
        return {"status": "error", "error": "Invalid face vector data"}

    if not key:
        return {"status": "error", "error": "Encryption key is required"}

    try:
        fernet = Fernet(key)
        serialized_data = json.dumps({"embedding": face_vector}).encode("utf-8")
        encrypted_data = fernet.encrypt(serialized_data)

        abs_path = os.path.abspath(storage_path)
        out_dir = os.path.dirname(abs_path)
        if out_dir:
            os.makedirs(out_dir, exist_ok=True)

        with open(abs_path, "wb") as f:
            f.write(encrypted_data)

        return {
            "status": "ok",
            "action": action_name,
            "data": {
                "storage_path": abs_path,
                "vector_length": len(face_vector),
                "encrypted": True,
            },
        }
    except Exception as e:
        return {
            "status": "error",
            "error": f"Failed to enroll face embedding: {str(e)}",
        }


def verify_face(
    candidate_vector: List[float],
    key: bytes,
    storage_path: str = "./storage/face_embedding.enc",
    tolerance: float = 0.6,
) -> Dict[str, Any]:
    """
    Decrypts enrolled face embedding and verifies candidate face vector against it.
    """
    action_name = "verify_face"
    if Fernet is None:
        return {"status": "error", "error": "cryptography module is not installed"}

    if not candidate_vector or not isinstance(candidate_vector, list):
        return {"status": "error", "error": "Invalid candidate face vector"}

    if not key:
        return {"status": "error", "error": "Decryption key is required"}

    abs_path = os.path.abspath(storage_path)
    if not os.path.exists(abs_path):
        return {
            "status": "error",
            "error": f"Enrolled face embedding file not found at: {abs_path}",
        }

    try:
        fernet = Fernet(key)
        with open(abs_path, "rb") as f:
            encrypted_data = f.read()

        decrypted_data = fernet.decrypt(encrypted_data)
        enrolled_payload = json.loads(decrypted_data.decode("utf-8"))
        enrolled_vector = enrolled_payload.get("embedding", [])

        distance = _calculate_euclidean_distance(
            candidate_vector, enrolled_vector
        )
        is_match = distance <= tolerance

        return {
            "status": "ok",
            "action": action_name,
            "data": {
                "match": is_match,
                "distance": round(distance, 4),
                "tolerance": tolerance,
            },
        }
    except Exception as e:
        return {
            "status": "error",
            "error": f"Face verification failed: {str(e)}",
        }
