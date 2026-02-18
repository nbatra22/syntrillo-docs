"""
Shared FastAPI dependencies for patient identity resolution.

The temporary_lookup_code system mirrors the legacy PostManager flow:
  temporary_lookup_code
      → TemporaryLookUpCodesManagement.retrieve_syntrillo_internal_key()
      → LookUpCodesManagement.retrieve_entry_by_internal_key()
      → pseudonyms dict (contains healthie_user_id, etc.)

NOTE: Auth will be extended with AWS Cognito in a future sprint.
"""

import sys
from pathlib import Path

from fastapi import Depends, HTTPException, Query, status

SOURCES_PATH = Path(__file__).resolve().parents[2] / "sources"
sys.path.insert(0, str(SOURCES_PATH))

from syntrillo.pseudonyms_management.temporary_lookup_codes_management import TemporaryLookUpCodesManagement
from syntrillo.pseudonyms_management.lookup_codes_management import LookUpCodesManagement


def get_syntrillo_internal_key(
    temporary_lookup_code: str = Query(..., description="Temporary patient lookup code from Healthie"),
) -> str:
    """Resolves a temporary_lookup_code to a syntrillo_internal_key."""
    try:
        manager = TemporaryLookUpCodesManagement()
        internal_key = manager.retrieve_syntrillo_internal_key(
            temporary_lookup_code,
            purpose=TemporaryLookUpCodesManagement.PURPOSE_HEALTHIE_IFRAME,
        )
        if internal_key is None:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Invalid or expired lookup code.",
            )
        return internal_key
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to resolve patient identity.",
        )


def get_pseudonyms(
    internal_key: str = Depends(get_syntrillo_internal_key),
) -> dict:
    """
    Returns the full pseudonyms entry for a patient.
    FastAPI caches get_syntrillo_internal_key per request, so the
    temporary_lookup_code lookup only runs once even when both
    dependencies are used in the same endpoint.
    """
    try:
        lookup_manager = LookUpCodesManagement()
        pseudonyms = lookup_manager.retrieve_entry_by_internal_key(internal_key)
        if pseudonyms is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Patient not found.",
            )
        return pseudonyms
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve patient record.",
        )