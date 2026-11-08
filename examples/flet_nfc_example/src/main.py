import flet as ft

from flet_nfc import NfcManager, NfcPollingOption


async def main(page: ft.Page):
    status = ft.Text("Checking NFC availability...")
    log = ft.ListView(expand=True)

    nfc = NfcManager()

    async def setup():
        avail = await nfc.check_availability()
        status.value = f"NFC Status: {avail.value}"
        page.update()

    def on_discovered(e: ft.ControlEvent):
        log.controls.append(ft.Text(f"Tag Discovered! Data: {e.data}"))
        page.update()

    nfc.on_discovered = on_discovered

    async def start_scan(_):
        status.value = "Scanning... Tap a tag to the back of your phone."
        page.update()
        try:
            # Start session in a background task so UI doesn't freeze
            await nfc.start_session(polling_options=[NfcPollingOption.ISO14443])
        except Exception as ex:
            log.controls.append(ft.Text(f"Error: {ex}"))
            page.update()

    async def stop_scan(_):
        await nfc.stop_session()
        status.value = "Session stopped."
        page.update()

    async def write_data(_):
        try:
            success = await nfc.write_tag(text="Hello Flet!", url="https://flet.dev")
            log.controls.append(ft.Text(f"Write success: {success}"))
        except Exception as ex:
            log.controls.append(ft.Text(f"Write error: {ex}"))
        page.update()

    page.add(
        ft.SafeArea(
            content=ft.Column(
                [
                    status,
                    ft.Row(
                        [
                            ft.FilledButton("Start Scan", on_click=start_scan),
                            ft.OutlinedButton("Stop", on_click=stop_scan),
                            ft.FilledButton("Write Tag", on_click=write_data),
                        ]
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
