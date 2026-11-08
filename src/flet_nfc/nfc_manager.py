from typing import Optional

import flet as ft
from flet.controls.base_control import control
from flet.controls.services.service import Service

from flet_nfc.types import NfcAvailability, NfcPollingOption

__all__ = ["NfcManager"]


@control("NfcManager")
class NfcManager(Service):
    """
    Service to manage NFC features on Android and iOS.
    Based on the `nfc_manager` Flutter package.
    """

    on_discovered: Optional[ft.EventHandler[ft.ControlEvent]] = None
    """Fired when an NFC tag is discovered. `e.data` contains tag details."""

    async def check_availability(self) -> NfcAvailability:
        """Check if NFC is available on the device."""
        res = await self._invoke_method("check_availability")
        return NfcAvailability(res)

    async def start_session(
        self,
        polling_options: Optional[list[NfcPollingOption]] = None,
        alert_message_ios: Optional[str] = None,
    ) -> None:
        """
        Start an NFC session.
        Note: An active session blocks until stopped or a tag is discovered.
        """
        opts = [o.value for o in (polling_options or [NfcPollingOption.ISO14443])]
        await self._invoke_method(
            "start_session",
            {"polling_options": opts, "alert_message_ios": alert_message_ios},
        )

    async def stop_session(self, error_message: Optional[str] = None) -> None:
        """Stop the active NFC session."""
        await self._invoke_method("stop_session", {"error_message": error_message})

    async def read_tag(self) -> dict:
        """Read NDEF data from the currently discovered tag."""
        return await self._invoke_method("read_tag")

    async def write_tag(
        self, text: Optional[str] = None, url: Optional[str] = None
    ) -> bool:
        """Write an NDEF message to the currently discovered tag."""
        return await self._invoke_method("write_tag", {"text": text, "url": url})
