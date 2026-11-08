import flet as ft

from flet_nfc import NfcAvailability, NfcManager, NfcPollingOption


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
        add_log(
            f"✅ Tag discovered: NDEF={data.get('is_ndef')} writable={data.get('is_writable')}"
        )
        for rec in data.get("records", []):
            if rec.get("type") == "text":
                add_log(f"   📝 Text: {rec.get('text')}")
            elif rec.get("type") == "uri":
                add_log(f"   🔗 URI: {rec.get('uri')}")
            elif rec.get("type") == "mime":
                add_log(f"   📎 MIME: {rec.get('mime_type')}")
        status.value = "Tag read — hold another tag or stop the session."
        page.update()

    def on_error(e: ft.ControlEvent):
        add_log(f"❌ Error: {e.data}")
        status.value = "Session error."

    def on_session_end(e: ft.ControlEvent):
        add_log("⏹️ Session ended.")
        status.value = "Session stopped."

    nfc.on_discovered = on_discovered
    nfc.on_error = on_error
    nfc.on_session_end = on_session_end

    async def setup():
        avail = await nfc.check_availability()
        status.value = f"NFC: {avail.value}"
        if avail != NfcAvailability.ENABLED:
            add_log("⚠️ NFC is not enabled on this device.")
        page.update()

    async def start_scan(_):
        ok = await nfc.start_session(
            polling_options=[NfcPollingOption.ISO14443],
            alert_message_ios="Hold your iPhone near the tag.",
        )
        status.value = "Scanning..." if ok else "Could not start session."
        page.update()

    async def stop_scan(_):
        await nfc.stop_session()

    async def write_demo(_):
        res = await nfc.write_text("Hello from Flet!")
        add_log(f"Write result: {res}")

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


ft.run(main)
