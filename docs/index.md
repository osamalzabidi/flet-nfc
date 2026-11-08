# Introduction

FletNfc for Flet.

## Examples

```
import flet as ft

from flet_nfc import FletNfc


def main(page: ft.Page):
    page.vertical_alignment = ft.MainAxisAlignment.CENTER
    page.horizontal_alignment = ft.CrossAxisAlignment.CENTER

    page.add(

                ft.Container(height=150, width=300, alignment = ft.Alignment.CENTER, bgcolor=ft.Colors.PURPLE_200, content=FletNfc(
                    tooltip="My new FletNfc Control tooltip",
                    value = "My new FletNfc Flet Control",
                ),),

    )


ft.run(main)
```

## Classes

[FletNfc](FletNfc.md)
