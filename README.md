# flet-nfc

flet-nfc [Flet](https://flet.dev) extension.

<!--- If your extension wraps a Flutter package, credit it here, ex: -->
It is based on the [nfc_manager](https://pub.dev/packages/nfc_manager) Flutter package.

## Platform Support

<!--- Update the table accordingly for your extension, using ✅ and ❌. -->

| Platform  | iOS | Android | Web | Windows | macOS | Linux |
|-----------|-----|---------|-----|---------|-------|-------|
| Supported | ✅   | ✅       | ❌   | ❌       | ❌     | ❌     |

## Usage

### Installation

Add `flet-nfc` dependency to the `pyproject.toml` of your Flet project:

* **From Git**

```toml
dependencies = [
  "flet-nfc @ git+https://github.com/osamalzabidi/flet-nfc",
  "flet>=1.1.0",
]
```

### Run your app

A Flet extension has two sides: its Python controls/services and the native Flutter/Dart widgets behind them.
That native code must be compiled into a Flet client before your controls can render, and the
prebuilt client that a plain `flet run` uses does **not** include this extension.

So run your app:

For iOS and Android, pass `-d <device-id>` (run `flet debug --show-devices` to list connected devices).
Edits to your **Python** code are picked up the next time you run `flet debug`.

### Examples

See the [examples](examples) directory.

### Documentation

<!--- Update the link, if your docs are elsewhere. Alternatively, you could write out all docs in this section directly. -->

Detailed documentation for this package can be found [here](https://osamalzabidi.github.io/flet-nfc/).
