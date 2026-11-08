import 'dart:async';
import 'dart:convert';
import 'dart:typed_data';

import 'package:flet/flet.dart';
import 'package:flutter/foundation.dart';
import 'package:flutter/services.dart';
import 'package:ndef_record/ndef_record.dart';
import 'package:nfc_manager/nfc_manager.dart';
import 'package:nfc_manager_ndef/nfc_manager_ndef.dart';

class NfcService extends FletService {
  NfcService({required super.control});

  bool _initialized = false;
  bool _sessionActive = false;
  NfcTag? _lastTag;

  // For listening to Android NFC state changes
  StreamSubscription? _adapterStateSubscription;
  static const _channel = MethodChannel('flet_nfc/state');

  Future<void> _ensureInitialized() async {
    if (_initialized) return;
    _initialized = true;
    control.addInvokeMethodListener(_invokeMethod);

    // Listen to native Android NFC adapter state changes
    if (defaultTargetPlatform == TargetPlatform.android) {
      _channel.setMethodCallHandler((call) async {
        if (call.method == 'onNfcStateChanged') {
          final isEnabled = call.arguments as bool;
          control.triggerEvent('state_changed', isEnabled ? 'enabled' : 'disabled');
        }
      });
      // Ask native side to start listening (implementation in MainActivity)
      try {
        await _channel.invokeMethod('startNfcStateListener');
      } catch (e) {
        debugPrint("NfcService: Failed to start native state listener: $e");
      }
    }
  }

  @override
  void init() {
    super.init();
    unawaited(_ensureInitialized());
  }

  Future<dynamic> _invokeMethod(String name, dynamic args) async {
    debugPrint("NfcManager.$name($args)");
    await _ensureInitialized();

    if (!isMobilePlatform()) {
      throw Exception("NfcManager is supported only on Android and iOS devices.");
    }

    switch (name) {
      case "check_availability":
        final availability = await NfcManager.instance.checkAvailability();
        return availability.name;

      case "start_session":
        return _startSession(args);

      case "stop_session":
        await _safeStopSession(errorMessageIos: args["error_message_ios"] as String?);
        return null;

      case "write_text":
        return _writeText(args["text"] as String);

      case "write_uri":
        return _writeUri(args["uri"] as String);

      default:
        throw Exception("Unknown NfcManager method: $name");
    }
  }

  Future<bool> _startSession(dynamic args) async {
    if (_sessionActive) return true;

    final availability = await NfcManager.instance.checkAvailability();
    if (availability != NfcAvailability.enabled) {
      control.triggerEvent("error", "NFC is not available: ${availability.name}");
      return false;
    }

    final rawOptions = (args["polling_options"] as List? ?? const []).cast<String>();
    final pollingOptions = rawOptions.map((e) {
      switch (e) {
        case "iso18092": return NfcPollingOption.iso18092;
        case "iso15693": return NfcPollingOption.iso15693;
        default: return NfcPollingOption.iso14443;
      }
    }).toSet();

    _sessionActive = true;

    try {
      await NfcManager.instance.startSession(
        pollingOptions: pollingOptions,
        alertMessageIos: args["alert_message_ios"] as String?,
        invalidateAfterFirstReadIos: args["invalidate_after_first_read"] as bool? ?? false,
        onDiscovered: (NfcTag tag) async {
          _lastTag = tag;
          final data = _buildTagPayload(tag);
          if (data != null) {
            control.triggerEvent("discovered", data);
          }
        },
      );
      return true;
    } catch (e, st) {
      _sessionActive = false;
      debugPrint("NfcService: startSession failed: $e\n$st");
      control.triggerEvent("error", "startSession failed: $e");
      return false;
    }
  }

  Future<void> _safeStopSession({String? errorMessageIos}) async {
    if (!_sessionActive) return;
    _sessionActive = false;
    try {
      await NfcManager.instance.stopSession(errorMessageIos: errorMessageIos);
    } catch (e) {
      debugPrint("NfcService: stopSession failed: $e");
    } finally {
      control.triggerEvent("session_end", null);
    }
  }

  Map<String, dynamic>? _buildTagPayload(NfcTag tag) {
    final ndef = Ndef.from(tag);
    final rawTech = tag.data is Map 
        ? (tag.data as Map).keys.map((k) => k.toString()).toList() 
        : <String>[];

    if (ndef == null) {
      return {"is_ndef": false, "is_writable": false, "raw_tech": rawTech, "records": []};
    }

    final records = <Map<String, dynamic>>[];
    final message = ndef.cachedMessage;
    if (message != null) {
      for (final record in message.records) {
        records.add(_parseRecord(record));
      }
    }

    return {
      "is_ndef": true,
      "is_writable": ndef.isWritable,
      "raw_tech": rawTech,
      "records": records,
    };
  }

  Map<String, dynamic> _parseRecord(NdefRecord record) {
    if (record.typeNameFormat == TypeNameFormat.wellKnown && record.type.isNotEmpty) {
      if (record.type[0] == 0x54) { // 'T' for Text
        final langLen = record.payload.isNotEmpty ? record.payload[0] & 0x3F : 0;
        final text = utf8.decode(record.payload.sublist(1 + langLen), allowMalformed: true);
        return {"type": "text", "text": text};
      } else if (record.type[0] == 0x55) { // 'U' for URI
        final prefix = _uriPrefixes[record.payload.isNotEmpty ? record.payload[0] : 0x00] ?? '';
        final uri = prefix + utf8.decode(record.payload.sublist(1), allowMalformed: true);
        return {"type": "uri", "uri": uri};
      }
    }
    return {"type": "unknown", "payload": _hex(record.payload)};
  }

  String _hex(List<int> bytes) => bytes.map((b) => b.toRadixString(16).padLeft(2, '0')).join();

  Future<Map<String, dynamic>> _writeText(String text) async {
    final ndef = _lastTag != null ? Ndef.from(_lastTag!) : null;
    if (ndef == null || !ndef.isWritable) return {"success": false, "error": "Tag not writable."};

    try {
      final langBytes = utf8.encode('en');
      final payload = Uint8List.fromList([langBytes.length & 0x3F, ...langBytes, ...utf8.encode(text)]);
      final record = NdefRecord(typeNameFormat: TypeNameFormat.wellKnown, type: Uint8List.fromList([0x54]), identifier: Uint8List(0), payload: payload);
      await ndef.write(message: NdefMessage(records: [record]));
      return {"success": true};
    } catch (e) {
      return {"success": false, "error": e.toString()};
    }
  }

  Future<Map<String, dynamic>> _writeUri(String uri) async {
    final ndef = _lastTag != null ? Ndef.from(_lastTag!) : null;
    if (ndef == null || !ndef.isWritable) return {"success": false, "error": "Tag not writable."};

    try {
      final payload = Uint8List.fromList([0x00, ...utf8.encode(uri)]);
      final record = NdefRecord(typeNameFormat: TypeNameFormat.wellKnown, type: Uint8List.fromList([0x55]), identifier: Uint8List(0), payload: payload);
      await ndef.write(message: NdefMessage(records: [record]));
      return {"success": true};
    } catch (e) {
      return {"success": false, "error": e.toString()};
    }
  }

  @override
  void dispose() {
    _adapterStateSubscription?.cancel();
    _channel.setMethodCallHandler(null);
    unawaited(_safeStopSession());
    control.removeInvokeMethodListener(_invokeMethod);
    super.dispose();
  }
}

const Map<int, String> _uriPrefixes = {
  0x00: '', 0x01: 'http://www.', 0x02: 'https://www.', 0x03: 'http://', 0x04: 'https://',
  0x05: 'tel:', 0x06: 'mailto:', 0x07: 'ftp://anonymous:anonymous@', 0x08: 'ftp://ftp.',
  0x09: 'ftps://', 0x0A: 'sftp://', 0x0B: 'smb://', 0x0C: 'nfs://', 0x0D: 'ftp://',
  0x0E: 'dav://', 0x0F: 'news:', 0x10: 'telnet://', 0x11: 'imap:', 0x12: 'rtsp://',
  0x13: 'urn:', 0x14: 'pop:', 0x15: 'sip:', 0x16: 'sips:', 0x17: 'tftp:', 0x18: 'btspp://',
  0x19: 'btl2cap://', 0x1A: 'btgoep://', 0x1B: 'tcpobex://', 0x1C: 'irdaobex://',
  0x1D: 'file://', 0x1E: 'urn:epc:id:', 0x1F: 'urn:epc:tag:', 0x20: 'urn:epc:pat:',
  0x21: 'urn:epc:raw:', 0x22: 'urn:epc:', 0x23: 'urn:nfc:',
};