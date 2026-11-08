from typing import Optional

import flet as ft
from flet.controls.services.service import Service

from flet_nfc.types import (
    NfcAvailability,
    NfcPollingOption,
)

__all__ = ["NfcManager"]


@ft.control("NfcManager")
class NfcManager(Service):
    """
    A service for reading and writing NFC tags on Android and iOS.

    Wraps the [`nfc_manager`](https://pub.dev/packages/nfc_manager) Flutter
    package with full NDEF support via `nfc_manager_ndef`.

    Danger:
        Platform support

        **Android and iOS only.** On other platforms every method raises
        :class:`RuntimeError`.

    See also:

    * :class:`~flet_nfc.types.NfcTagData` - payload delivered to
      :attr:`on_discovered`.
    """

    on_discovered: Optional[ft.EventHandler[ft.ControlEvent]] = None
    """
    Fired when a tag is discovered and successfully parsed.

    ``e.data`` is a dict matching :class:`~flet_nfc.types.NfcTagData`.
    """

    on_error: Optional[ft.EventHandler[ft.ControlEvent]] = None
    """
    Fired when an NFC operation fails.

    ``e.data`` is a human-readable error string.
    """

    on_session_end: Optional[ft.EventHandler[ft.ControlEvent]] = None
    """
    Fired when the NFC session ends (either manually or because a tag was
    handled and the session auto-stopped).
    """

    async def check_availability(self) -> NfcAvailability:
        """
        Check whether NFC is available and enabled on this device.

        Always call this before :meth:`start_session`.
        """
        raw = await self._invoke_method("check_availability")
        return NfcAvailability(raw)

    async def start_session(
        self,
        polling_options: Optional[list[NfcPollingOption]] = None,
        alert_message_ios: Optional[str] = None,
        invalidate_after_first_read: bool = False,
    ) -> bool:
        """
        Start an NFC scanning session.

        Args:
            polling_options: Tag technologies to poll for. Defaults to
                ``[NfcPollingOption.ISO14443]``.
            alert_message_ios: Message shown in the iOS NFC sheet. iOS only.
            invalidate_after_first_read: If ``True``, the session stops
                automatically after the first tag is read.

        Returns:
            ``True`` if the session started, ``False`` if NFC is unavailable.
        """
        opts = [o.value for o in (polling_options or [NfcPollingOption.ISO14443])]
        return await self._invoke_method(
            "start_session",
            {
                "polling_options": opts,
                "alert_message_ios": alert_message_ios,
                "invalidate_after_first_read": invalidate_after_first_read,
            },
        )

    async def stop_session(self, error_message_ios: Optional[str] = None) -> None:
        """
        Stop the active NFC session.

        On iOS, if the system sheet is open, it will close immediately.
        """
        await self._invoke_method(
            "stop_session", {"error_message_ios": error_message_ios}
        )

    async def write_text(self, text: str, tag: Optional[dict] = None) -> dict:
        """
        Write a text NDEF record to the tag.

        If ``tag`` is omitted, the most recently discovered tag is used.

        Returns:
            A dict matching :class:`~flet_nfc.types.NfcWriteResult`.
        """
        return await self._invoke_method("write_text", {"text": text, "tag": tag})

    async def write_uri(self, uri: str, tag: Optional[dict] = None) -> dict:
        """
        Write a URI NDEF record to the tag.

        If ``tag`` is omitted, the most recently discovered tag is used.

        Returns:
            A dict matching :class:`~flet_nfc.types.NfcWriteResult`.
        """
        return await self._invoke_method("write_uri", {"uri": uri, "tag": tag})
