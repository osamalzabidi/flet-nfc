from dataclasses import dataclass
from enum import Enum


class NfcAvailability(Enum):
    ENABLED = "enabled"
    DISABLED = "disabled"
    UNSUPPORTED = "unsupported"


class NfcPollingOption(Enum):
    ISO14443 = "iso14443"
    ISO18092 = "iso18092"
    ISO15693 = "iso15693"


@dataclass
class NfcTagData:
    """Generic wrapper for data returned by the NFC session."""

    tech: str
    data: dict
