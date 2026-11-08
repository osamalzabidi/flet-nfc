from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


class NfcAvailability(Enum):
    """
    Represents the current NFC availability state of the device.
    """

    ENABLED = "enabled"
    """NFC is available and enabled."""

    DISABLED = "disabled"
    """NFC hardware exists but is turned off in system settings."""

    UNSUPPORTED = "unsupported"
    """The device does not have NFC hardware (e.g., most iPads, simulators)."""


class NfcPollingOption(Enum):
    """
    NFC tag technologies to poll for during a session.
    """

    ISO14443 = "iso14443"
    """Polls for ISO 14443 tags (Mifare, NfcA, NfcB, etc.)."""

    ISO18092 = "iso18092"
    """Polls for FeliCa tags (Sony). Requires extra iOS configuration."""

    ISO15693 = "iso15693"
    """Polls for ISO 15693 (NFC Vicinity) tags."""


class NfcRecordType(Enum):
    TEXT = "text"
    URI = "uri"
    MIME = "mime"
    UNKNOWN = "unknown"


@dataclass
class NfcRecord:
    """
    A single record from an NDEF message.
    """

    type: NfcRecordType
    """The kind of NDEF record."""

    text: Optional[str] = None
    """Decoded text content, if `type` is TEXT."""

    uri: Optional[str] = None
    """Decoded URI string, if `type` is URI."""

    mime_type: Optional[str] = None
    """MIME type, if `type` is MIME."""

    payload: Optional[str] = None
    """Raw payload as a hex string, useful for debugging unknown records."""


@dataclass
class NfcTagData:
    """
    The result delivered to `on_discovered` when a tag is found.

    ``raw_tech`` lists the platform-specific tag technologies available on this
    tag (e.g. ``["NdefAndroid", "MifareClassicAndroid"]`` on Android,
    ``["NdefIos"]`` on iOS). This lets Python code branch on what the tag
    actually supports.
    """

    is_ndef: bool
    """True if the tag can be read/written as NDEF."""

    is_writable: bool
    """True if the tag is currently writable (only meaningful when ``is_ndef`` is True)."""

    raw_tech: list[str] = field(default_factory=list)
    """Platform-specific tag technology names."""

    records: list[NfcRecord] = field(default_factory=list)
    """Parsed NDEF records (empty if the tag is not NDEF-formatted)."""

    def __str__(self) -> str:
        return (
            f"NfcTagData(is_ndef={self.is_ndef}, is_writable={self.is_writable}, "
            f"tech={self.raw_tech}, records={len(self.records)})"
        )


@dataclass
class NfcWriteResult:
    success: bool
    """True if the write completed without throwing."""

    error: Optional[str] = None
    """Human-readable error message when ``success`` is False."""
