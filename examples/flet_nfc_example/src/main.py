import logging

import flet as ft

from flet_nfc import NfcAvailability, NfcManager, NfcPollingOption

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)

# Raise Flet's own logger to DEBUG so framework/transport details are visible.
logging.getLogger("flet").setLevel(logging.DEBUG)

# Enable these only when you need deep control-tree or component diagnostics.
# logging.getLogger("flet_object_patch").setLevel(logging.DEBUG)
# logging.getLogger("flet_components").setLevel(logging.DEBUG)

# App-specific logger. Keeping a named logger makes it easy to filter your
# own messages from Flet's framework logs via `adb logcat -s python | grep nfc_demo`.
logger = logging.getLogger("nfc_demo")


def main(page: ft.Page):
    page.title = "NFC Demo"

    status = ft.Text("Checking NFC availability...")
    log = ft.ListView(expand=True, spacing=4)

    nfc = NfcManager()

    def add_log(msg: str):
        log.controls.append(ft.Text(msg, size=12))
        page.update()

    def on_discovered(e: ft.ControlEvent):
        data = e.data or {}
        logger.info(
            "Tag discovered: NDEF=%s, writable=%s, tech=%s",
            data.get("is_ndef"),
            data.get("is_writable"),
            data.get("raw_tech"),
        )
        add_log(
            f"✅ Tag discovered: NDEF={data.get('is_ndef')} writable={data.get('is_writable')}"
        )
        for rec in data.get("records", []):
            if rec.get("type") == "text":
                logger.debug("  Text record: %s", rec.get("text"))
                add_log(f"   📝 Text: {rec.get('text')}")
            elif rec.get("type") == "uri":
                logger.debug("  URI record: %s", rec.get("uri"))
                add_log(f"   🔗 URI: {rec.get('uri')}")
            elif rec.get("type") == "mime":
                logger.debug("  MIME record: %s", rec.get("mime_type"))
                add_log(f"   📎 MIME: {rec.get('mime_type')}")
        status.value = "Tag read — hold another tag or stop the session."
        page.update()

    def on_error(e: ft.ControlEvent):
        logger.error("NFC error: %s", e.data)
        add_log(f"❌ Error: {e.data}")
        status.value = "Session error."

    def on_session_end(e: ft.ControlEvent):
        logger.info("NFC session ended.")
        add_log("⏹️ Session ended.")
        status.value = "Session stopped."

    nfc.on_discovered = on_discovered
    nfc.on_error = on_error
    nfc.on_session_end = on_session_end

    async def setup():
        logger.info("Checking NFC availability...")
        try:
            avail = await nfc.check_availability()
            logger.info("NFC availability: %s", avail.value)
            status.value = f"NFC: {avail.value}"
            if avail != NfcAvailability.ENABLED:
                logger.warning("NFC is not enabled on this device.")
                add_log("⚠️ NFC is not enabled on this device.")
        except Exception:
            logger.exception("Failed to check NFC availability")
            add_log("❌ Failed to check NFC availability (see logs).")
        page.update()

    async def start_scan(_):
        logger.info("Starting NFC scan...")
        try:
            ok = await nfc.start_session(
                polling_options=[NfcPollingOption.ISO14443],
                alert_message_ios="Hold your iPhone near the tag.",
            )
            if ok:
                logger.info("NFC session started successfully.")
                status.value = "Scanning..."
            else:
                logger.warning("NFC session could not be started.")
                status.value = "Could not start session."
        except Exception:
            logger.exception("Exception while starting NFC session")
            status.value = "Could not start session."
        page.update()

    async def stop_scan(_):
        logger.info("Stopping NFC scan...")
        try:
            await nfc.stop_session()
        except Exception:
            logger.exception("Exception while stopping NFC session")
        page.update()

    async def write_demo(_):
        logger.info("Writing text record: 'Hello from Flet!'")
        try:
            res = await nfc.write_text("Hello from Flet!")
            logger.info("Write result: %s", res)
            add_log(f"Write result: {res}")
        except Exception:
            logger.exception("Exception while writing NFC tag")
            add_log("❌ Write failed (see logs).")

    page.add(
        ft.SafeArea(
            content=ft.Column(
                [
                    status,
                    ft.Row(
                        [
                            ft.FilledButton("Start scan", on_click=start_scan),
                            ft.OutlinedButton("Stop", on_click=stop_scan),
                            ft.FilledButton("Write 'Hello Flet'", on_click=write_demo),
                        ],
                        wrap=True,
                    ),
                    ft.Divider(),
                    log,
                ],
                expand=True,
            )
        )
    )

    page.run_task(setup)


if __name__ == "__main__":
    logger.info("Starting NFC demo app")
    ft.run(main)
