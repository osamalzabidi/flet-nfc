import 'dart:async';
import 'dart:convert';

import 'package:flet/flet.dart';
import 'package:flutter/foundation.dart';
import 'package:ndef_record/ndef_record.dart';
import 'package:nfc_manager_ndef/nfc_manager_ndef.dart';
import 'package:nfc_manager/nfc_manager.dart';


class NfcService extends FletService {
  NfcService({required super.control});

  bool _initialized = false;
  bool _sessionActive = false;
  NfcTag? _lastTag;

  /// Lazy initialization guard - ensures the invoke-method listener is
  /// registered exactly once, even if `init()` fires late or twice.
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
    debugPrint("NfcManager.$name($args)");
    await _ensureInitialized();

    if (!isMobilePlatform()) {
      throw Exception(
        "NfcManager is supported only on Android and iOS devices.",
      );
    }

    switch (name) {
      case "check_availability":
        final availability = await NfcManager.instance.checkAvailability();
        return availability.name;

      case "start_session":
        return _startSession(args);

      case "stop_session":
        await _safeStopSession(
          errorMessageIos: args["error_message_ios"] as String?,
        );
        return null;

      case "write_text":
        return _writeText(args["text"] as String);

      case "write_uri":
        return _writeUri(args["uri"] as String);

      default:
        throw Exception("Unknown NfcManager method: $name");
    }
  }

  // Session management
  Future<bool> _startSession(dynamic args) async {
    if (_sessionActive) {
      debugPrint("NfcService: session already active");
      return true;
    }

    final availability = await NfcManager.instance.checkAvailability();
    if (availability != NfcAvailability.enabled) {
      debugPrint("NfcService: NFC not enabled ($availability)");
      control.triggerEvent("error", "NFC is not available: ${availability.name}");
      return false;
    }

    final rawOptions = (args["polling_options"] as List? ?? const [])
        .cast<String>();
    final pollingOptions = rawOptions.map((e) {
      switch (e) {
        case "iso18092":
          return NfcPollingOption.iso18092;
        case "iso15693":
          return NfcPollingOption.iso15693;
        case "iso14443":
        default:
          return NfcPollingOption.iso14443;
      }
    }).toSet();

    _sessionActive = true;

    try {
      await NfcManager.instance.startSession(
        pollingOptions: pollingOptions,
        alertMessageIos: args["alert_message_ios"] as String?,
        invalidateAfterFirstReadIos: args["invalidate_after_first_read"] as bool? ?? false, // Fixed name
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

  // Tag payload construction
  Map<String, dynamic>? _buildTagPayload(NfcTag tag) {
    final ndef = Ndef.from(tag);
    
    // Safely extract keys
    final rawTech = tag.data is Map 
        ? (tag.data as Map).keys.map((k) => k.toString()).toList() 
        : <String>[];

    if (ndef == null) {
      return {
        "is_ndef": false,
        "is_writable": false,
        "raw_tech": rawTech,
        "records": <Map<String, dynamic>>[],
      };
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
    // Text record
    if (record.typeNameFormat == TypeNameFormat.wellKnown &&
        record.type.isNotEmpty &&
        record.type[0] == 0x54) {
      final langLen = record.payload.isNotEmpty ? record.payload[0] & 0x3F : 0;
      final text = utf8.decode(record.payload.sublist(1 + langLen),
          allowMalformed: true);
      return {
        "type": "text",
        "text": text,
        "payload": _hex(record.payload),
      };
    }

    // URI record
    if (record.typeNameFormat == TypeNameFormat.wellKnown &&
        record.type.isNotEmpty &&
        record.type[0] == 0x55) {
      final prefix = _uriPrefixes[record.payload.isNotEmpty
              ? record.payload[0]
              : 0x00] ??
          '';
      final uri = prefix + utf8.decode(record.payload.sublist(1),
          allowMalformed: true);
      return {
        "type": "uri",
        "uri": uri,
        "payload": _hex(record.payload),
      };
    }

    // MIME record
    if (record.typeNameFormat == TypeNameFormat.media) {
      final mime = utf8.decode(record.type, allowMalformed: true);
      return {
        "type": "mime",
        "mime_type": mime,
        "payload": _hex(record.payload),
      };
    }

    return {
      "type": "unknown",
      "payload": _hex(record.payload),
    };
  }

  String _hex(List<int> bytes) =>
      bytes.map((b) => b.toRadixString(16).padLeft(2, '0')).join();

  // NDEF write
  Future<Map<String, dynamic>> _writeText(String text) async {
    final tag = _lastTag;
    if (tag == null) {
      return {"success": false, "error": "No discovered tag to write to."};
    }

    final ndef = Ndef.from(tag);
    if (ndef == null) {
      return {"success": false, "error": "Tag is not NDEF-compatible."};
    }
    if (!ndef.isWritable) {
      return {"success": false, "error": "Tag is read-only."};
    }

    try {
      final record = TextRecord.create(text);
      final message = NdefMessage(records: [record]);
      await ndef.write(message: message);
      return {"success": true, "error": null};
    } catch (e) {
      return {"success": false, "error": e.toString()};
    }
  }

  Future<Map<String, dynamic>> _writeUri(String uri) async {
    final tag = _lastTag;
    if (tag == null) {
      return {"success": false, "error": "No discovered tag to write to."};
    }

    final ndef = Ndef.from(tag);
    if (ndef == null) {
      return {"success": false, "error": "Tag is not NDEF-compatible."};
    }
    if (!ndef.isWritable) {
      return {"success": false, "error": "Tag is read-only."};
    }

    try {
      final record = UriRecord.create(Uri.parse(uri));
      final message = NdefMessage(records: [record]);
      await ndef.write(message: message);
      return {"success": true, "error": null};
    } catch (e) {
      return {"success": false, "error": e.toString()};
    }
  }

  @override
  void dispose() {
    unawaited(_safeStopSession());
    control.removeInvokeMethodListener(_invokeMethod);
    super.dispose();
  }
}

// URI prefix table for NDEF URI records (per NFC Forum spec).
const Map<int, String> _uriPrefixes = {
  0x00: '',
  0x01: 'http://www.',
  0x02: 'https://www.',
  0x03: 'http://',
  0x04: 'https://',
  0x05: 'tel:',
  0x06: 'mailto:',
  0x07: 'ftp://anonymous:anonymous@',
  0x08: 'ftp://ftp.',
  0x09: 'ftps://',
  0x0A: 'sftp://',
  0x0B: 'smb://',
  0x0C: 'nfs://',
  0x0D: 'ftp://',
  0x0E: 'dav://',
  0x0F: 'news:',
  0x10: 'telnet://',
  0x11: 'imap:',
  0x12: 'rtsp://',
  0x13: 'urn:',
  0x14: 'pop:',
  0x15: 'sip:',
  0x16: 'sips:',
  0x17: 'tftp:',
  0x18: 'btspp://',
  0x19: 'btl2cap://',
  0x1A: 'btgoep://',
  0x1B: 'tcpobex://',
  0x1C: 'irdaobex://',
  0x1D: 'file://',
  0x1E: 'urn:epc:id:',
  0x1F: 'urn:epc:tag:',
  0x20: 'urn:epc:pat:',
  0x21: 'urn:epc:raw:',
  0x22: 'urn:epc:',
  0x23: 'urn:nfc:',
};