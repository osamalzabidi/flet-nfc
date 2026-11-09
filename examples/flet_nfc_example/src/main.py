import logging

import flet as ft

from flet_nfc import NfcAvailability, NfcManager, NfcPollingOption

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logging.getLogger("flet").setLevel(logging.DEBUG)
logger = logging.getLogger("nfc_lab")


def main(page: ft.Page):
    page.title = "NFC Comprehensive Lab"
    page.theme_mode = ft.ThemeMode.DARK
    page.padding = 20

    nfc = NfcManager()
    last_read_tag = None

    status_icon = ft.Icon(ft.Icons.NFC, size=40, color=ft.Colors.GREY)
    status_text = ft.Text(
        "Checking Availability...", size=18, weight=ft.FontWeight.BOLD
    )
    session_indicator = ft.ProgressBar(visible=False, width=200)

    log_view = ft.ListView(expand=True, spacing=4, padding=10, auto_scroll=True)

    polling_iso14443 = ft.Checkbox(label="ISO 14443 (Mifare/NfcA/B)", value=True)
    polling_iso18092 = ft.Checkbox(label="ISO 18092 (FeliCa)", value=False)
    polling_iso15693 = ft.Checkbox(label="ISO 15693 (Vicinity)", value=False)

    alert_msg_ios = ft.TextField(
        label="iOS Alert Message", value="Hold your iPhone near the tag.", width=400
    )
    invalidate_first_read = ft.Switch(
        label="Invalidate session after first read (iOS)", value=False
    )
    stop_error_msg = ft.TextField(
        label="iOS Error Message (on stop)",
        value="Session cancelled by user.",
        width=400,
    )

    text_input = ft.TextField(
        label="Text to write", value="Hello from Flet NFC!", width=400
    )
    uri_input = ft.TextField(label="URI to write", value="https://flet.dev", width=400)

    def add_log(msg: str, color=ft.Colors.ON_SURFACE):
        log_view.controls.append(ft.Text(msg, size=12, color=color))
        page.update()

    def update_status_ui(avail: NfcAvailability):
        status_icon.color = (
            ft.Colors.GREEN
            if avail == NfcAvailability.ENABLED
            else (
                ft.Colors.ORANGE if avail == NfcAvailability.DISABLED else ft.Colors.RED
            )
        )
        status_icon.icon = (
            ft.Icons.NFC
            if avail != NfcAvailability.UNSUPPORTED
            else ft.Icons.OFFLINE_BOLT
        )
        status_text.value = f"NFC Status: {avail.value.upper()}"

        # Disable scan buttons if not enabled
        btn_start_scan.disabled = avail != NfcAvailability.ENABLED
        page.update()

    def get_selected_polling_options() -> list[NfcPollingOption]:
        opts = []
        if polling_iso14443.value:
            opts.append(NfcPollingOption.ISO14443)
        if polling_iso18092.value:
            opts.append(NfcPollingOption.ISO18092)
        if polling_iso15693.value:
            opts.append(NfcPollingOption.ISO15693)
        return opts

    def on_state_changed(e: ft.ControlEvent):
        new_state = e.data
        add_log(
            f"🔔 [SYSTEM EVENT] NFC state changed to: {new_state.upper() if isinstance(new_state, str) else new_state}",
            ft.Colors.BLUE,
        )
        if new_state == "enabled":
            page.run_task(check_avail)
        elif new_state == "disabled":
            update_status_ui(NfcAvailability.DISABLED)

    def on_discovered(e: ft.ControlEvent):
        nonlocal last_read_tag
        data = e.data or {}
        last_read_tag = data
        add_log(
            f"✅ Tag Discovered! NDEF={data.get('is_ndef')}, Writable={data.get('is_writable')}",
            ft.Colors.GREEN,
        )
        add_log(f"   Tech: {data.get('raw_tech')}")

        for rec in data.get("records", []):
            rtype = rec.get("type")
            if rtype == "text":
                add_log(f"   📝 Text: {rec.get('text')}")
            elif rtype == "uri":
                add_log(f"   🔗 URI: {rec.get('uri')}")
            elif rtype == "mime":
                add_log(f"   📎 MIME: {rec.get('mime_type')}")
            else:
                add_log(f"   ❓ Unknown payload: {rec.get('payload')}")

    def on_error(e: ft.ControlEvent):
        add_log(f"❌ [SERVICE ERROR] {e.data}", ft.Colors.RED)

    def on_session_end(e: ft.ControlEvent):
        add_log("⏹️ [SERVICE] NFC session ended.", ft.Colors.ORANGE)
        session_indicator.visible = False
        page.update()

    nfc.on_discovered = on_discovered
    nfc.on_error = on_error
    nfc.on_session_end = on_session_end
    nfc.on_state_changed = on_state_changed

    async def check_avail():
        try:
            avail = await nfc.check_availability()
            update_status_ui(avail)
            logger.info("Availability checked: %s", avail.value)
        except Exception as ex:
            add_log(f"Failed to check availability: {ex}", ft.Colors.RED)

    async def start_scan(_):
        opts = get_selected_polling_options()
        if not opts:
            add_log("⚠️ Please select at least one polling option.", ft.Colors.ORANGE)
            return

        add_log(f"▶️ Starting session with options: {[o.value for o in opts]}...")
        session_indicator.visible = True
        page.update()

        ok = await nfc.start_session(
            polling_options=opts,
            alert_message_ios=alert_msg_ios.value,
            invalidate_after_first_read=invalidate_first_read.value,
        )

        if not ok:
            add_log("❌ Failed to start session.", ft.Colors.RED)
            session_indicator.visible = False
            page.update()

    async def stop_scan(_):
        add_log("⏹️ Stopping session manually...")
        await nfc.stop_session(error_message_ios=stop_error_msg.value)

    async def write_text(_):
        if not text_input.value:
            return
        add_log(f"✍️ Writing text: '{text_input.value}'...")
        res = await nfc.write_text(text_input.value)
        if res.get("success"):
            add_log("✅ Text written successfully!", ft.Colors.GREEN)
        else:
            add_log(f"❌ Write failed: {res.get('error')}", ft.Colors.RED)

    async def write_uri(_):
        if not uri_input.value:
            return
        add_log(f"✍️ Writing URI: '{uri_input.value}'...")
        res = await nfc.write_uri(uri_input.value)
        if res.get("success"):
            add_log("✅ URI written successfully!", ft.Colors.GREEN)
        else:
            add_log(f"❌ Write failed: {res.get('error')}", ft.Colors.RED)

    btn_start_scan = ft.FilledButton(
        "Start Scan", on_click=start_scan, icon=ft.Icons.SEARCH, disabled=True
    )

    tab_scan_content = ft.Column(
        controls=[
            ft.Text(
                "Polling Options (Technologies to look for):", weight=ft.FontWeight.BOLD
            ),
            polling_iso14443,
            polling_iso18092,
            polling_iso15693,
            ft.Divider(),
            ft.Row(
                [
                    btn_start_scan,
                    ft.OutlinedButton(
                        "Stop Session", on_click=stop_scan, icon=ft.Icons.STOP
                    ),
                ]
            ),
            ft.Divider(),
            ft.Text("Event Log", weight=ft.FontWeight.BOLD),
            log_view,
        ],
        expand=True,
    )

    tab_write_content = ft.Column(
        [
            ft.Text("Write Data to Tag", weight=ft.FontWeight.BOLD),
            ft.Text(
                "Ensure you have scanned a writable tag first.",
                italic=True,
                color=ft.Colors.ON_SURFACE_VARIANT,
            ),
            ft.Divider(),
            text_input,
            ft.FilledTonalButton(
                "Write Text Record", on_click=write_text, icon=ft.Icons.EDIT
            ),
            ft.Divider(),
            uri_input,
            ft.FilledTonalButton(
                "Write URI Record", on_click=write_uri, icon=ft.Icons.LINK
            ),
        ],
        expand=True,
    )

    tab_settings_content = ft.Column(
        [
            ft.Text("iOS Specific Settings", weight=ft.FontWeight.BOLD),
            alert_msg_ios,
            invalidate_first_read,
            ft.Divider(),
            ft.Text("Session Termination Settings", weight=ft.FontWeight.BOLD),
            stop_error_msg,
            ft.Text(
                "Note: These options only affect iOS devices.",
                italic=True,
                color=ft.Colors.ON_SURFACE_VARIANT,
            ),
        ],
        expand=True,
    )

    tabs_control = ft.Tabs(
        length=3,
        selected_index=0,
        animation_duration=300,
        expand=True,
        content=ft.Column(
            expand=True,
            controls=[
                ft.TabBar(
                    tabs=[
                        ft.Tab(label="Scan & Read", icon=ft.Icons.SENSORS),
                        ft.Tab(label="Write", icon=ft.Icons.EDIT),
                        ft.Tab(label="Settings", icon=ft.Icons.SETTINGS),
                    ]
                ),
                ft.TabBarView(
                    expand=True,
                    controls=[
                        tab_scan_content,
                        tab_write_content,
                        tab_settings_content,
                    ],
                ),
            ],
        ),
    )

    page.add(
        ft.SafeArea(
            content=ft.Column(
                controls=[
                    ft.Row(
                        controls=[status_icon, status_text],
                        alignment=ft.MainAxisAlignment.CENTER,
                    ),
                    session_indicator,
                    tabs_control,
                ],
                expand=True,
            )
        )
    )

    page.run_task(check_avail)


if __name__ == "__main__":
    logger.info("Starting NFC Comprehensive Lab")
    ft.run(main)
