import 'dart:async';
import 'package:flet/flet.dart';
import 'package:flutter/foundation.dart';
import 'package:nfc_manager/nfc_manager.dart';

class NfcService extends FletService {
  NfcService({required super.control});
  
  NfcTag? _currentTag;
  bool _initialized = false;

  Future<void> _ensureInitialized() async {
    if (_initialized) return;
    _initialized = true;
    control.addInvokeMethodListener(_invokeMethod);
  }

  @override
  void init() {
    super.init();
    unawaited(_ensureInitialized());
  }

  Future<dynamic> _invokeMethod(String name, dynamic args) async {
    await _ensureInitialized();

    switch (name) {
      case "check_availability":
        final availability = await NfcManager.instance.checkAvailability();
        if (availability == NfcAvailability.enabled) return "enabled";
        if (availability == NfcAvailability.disabled) return "disabled";
        return "unsupported";

      case "start_session":
        final pollingOptionsRaw = args["polling_options"] as List? ?? [];
        final pollingOptions = pollingOptionsRaw.map((e) {
          switch (e) {
            case "iso14443": return NfcPollingOption.iso14443;
            case "iso18092": return NfcPollingOption.iso18092;
            case "iso15693": return NfcPollingOption.iso15693;
            default: return NfcPollingOption.iso14443;
          }
        }).toSet();

        await NfcManager.instance.startSession(
          pollingOptions: pollingOptions,
          alertMessageIOS: args["alert_message_ios"] as String?,
          onDiscovered: (NfcTag tag) async {
            _currentTag = tag;
            control.triggerEvent("discovered", tag.data.toString());
          },
        );
        return null;

      case "stop_session":
        await NfcManager.instance.stopSession(
          errorMessageIOS: args["error_message"] as String?,
        );
        _currentTag = null;
        return null;

      case "read_tag":
        if (_currentTag == null) throw Exception("No active tag");
        final ndef = Ndef.from(_currentTag!);
        if (ndef == null) throw Exception("Tag is not NDEF formatted");
        
        final message = ndef.cachedMessage;
        if (message == null) return {};
        
        // Simplified parsing for example purposes
        return {"records_count": message.records.length};

      case "write_tag":
        if (_currentTag == null) throw Exception("No active tag");
        final ndef = Ndef.from(_currentTag!);
        if (ndef == null || !ndef.isWritable) {
          throw Exception("Tag is not NDEF writable");
        }

        final records = <NdefRecord>[];
        if (args["text"] != null) records.add(NdefRecord.createText(args["text"]));
        if (args["url"] != null) records.add(NdefRecord.createUri(Uri.parse(args["url"])));

        if (records.isEmpty) return false;

        try {
          await ndef.write(NdefMessage(records));
          return true;
        } catch (e) {
          return false;
        }

      default:
        throw Exception("Unknown NfcManager method: $name");
    }
  }

  @override
  void dispose() {
    unawaited(NfcManager.instance.stopSession());
    control.removeInvokeMethodListener(_invokeMethod);
    super.dispose();
  }
}