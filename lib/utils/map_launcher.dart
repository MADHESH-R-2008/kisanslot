import 'package:flutter/material.dart';
import 'package:url_launcher/url_launcher.dart';

class MapLauncher {
  /// Launches Google Maps to navigate to a procurement centre.
  /// Prioritizes [mapUrl], then coordinates ([latitude], [longitude]), then [address] search.
  static Future<void> openGoogleMaps({
    String? mapUrl,
    double? latitude,
    double? longitude,
    required String name,
    required String address,
    BuildContext? context,
  }) async {
    Uri? uri;

    // 1. If explicit Google Maps URL is provided
    if (mapUrl != null && mapUrl.trim().isNotEmpty) {
      String formattedUrl = mapUrl.trim();
      if (!formattedUrl.startsWith('http://') && !formattedUrl.startsWith('https://')) {
        formattedUrl = 'https://$formattedUrl';
      }
      uri = Uri.tryParse(formattedUrl);
    }

    // 2. Fallback to coordinates
    if (uri == null && latitude != null && longitude != null && (latitude != 0.0 || longitude != 0.0)) {
      uri = Uri.parse('https://www.google.com/maps/search/?api=1&query=$latitude,$longitude');
    }

    // 3. Fallback to address search
    if (uri == null) {
      final query = Uri.encodeComponent('$name, $address');
      uri = Uri.parse('https://www.google.com/maps/search/?api=1&query=$query');
    }

    try {
      final launched = await launchUrl(uri, mode: LaunchMode.externalApplication);
      if (!launched) {
        await launchUrl(uri);
      }
    } catch (e) {
      if (context != null && context.mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text('Could not open Google Maps: $e'),
            behavior: SnackBarBehavior.floating,
          ),
        );
      }
    }
  }
}
