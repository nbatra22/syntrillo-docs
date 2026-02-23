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

from config import settings

FAST_ENV = settings.fast_env

SOURCES_PATH = Path(__file__).resolve().parents[2] / "sources"
sys.path.insert(0, str(SOURCES_PATH))

from syntrillo.pseudonyms_management.temporary_lookup_codes_management import TemporaryLookUpCodesManagement
from syntrillo.pseudonyms_management.lookup_codes_management import LookUpCodesManagement


def get_syntrillo_internal_key(
    temporary_lookup_code: str = Query(..., description="Temporary patient lookup code from Healthie"),
) -> str:
    """Resolves a temporary_lookup_code to a syntrillo_internal_key."""
    try:
        if FAST_ENV == "development":
            print("Handling dev environment user...")
            dev_internal_key = handle_dev_env_user()
            if dev_internal_key is not None:
                return dev_internal_key

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

def handle_dev_env_user():
    """
    In development, allow bypassing the temporary_lookup_code flow by using a special query parameter.
    This is useful for testing with a known patient without needing to generate a temporary code.
    """
    # healthie_user_id = "1035117" # with onboarding forms
    # healthie_user_id = "1209727" # with syntrillo_internal_key
    # healthie_user_id = "1525423" # Patient AWS Test
    # healthie_user_id = "1966294" # Patient AWS Test 3
    # healthie_user_id = "2062692" # Patient AWS Test 5
    # healthie_user_id = "2062877" # Patient AWS Test 6 (hypertensive)
    healthie_user_id = "1562903" # Crispy Bacon with syntrillo_internal_key: 99fddf03-9304-4e48-8711-0cc4d825eb94
    # healthie_user_id = "2315391" # Bob Barker

    print(f"Dev environment: using healthie_user_id {healthie_user_id} to look up syntrillo_internal_key")

    look_up_codes_management = LookUpCodesManagement()
    entry = look_up_codes_management.retrieve_entry_by_healthie_user_id(healthie_user_id)

    print(f"Dev env lookup for healthie_user_id {healthie_user_id}: {entry}")

    if entry is not None:
        return entry['syntrillo_internal_key']

    return None
