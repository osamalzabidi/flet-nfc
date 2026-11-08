import 'package:flet/flet.dart';
import 'package:flutter/widgets.dart';

import 'flet_nfc.dart';

class Extension extends FletExtension {
  @override
  Widget? createWidget(Key? key, Control control) {
    switch (control.type) {
      case "FletNfc":
        return FletNfcControl(control: control);
      default:
        return null;
    }
  }
}
