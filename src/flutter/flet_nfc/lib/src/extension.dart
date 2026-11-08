import 'package:flet/flet.dart';
import 'package:flutter/widgets.dart';

import 'nfc_service.dart';

class Extension extends FletExtension {
  @override
  FletService? createService(Control control) {
    switch (control.type) {
      case "NfcManager":
        return NfcService(control: control);
      default:
        return null;
    }
  }
}
