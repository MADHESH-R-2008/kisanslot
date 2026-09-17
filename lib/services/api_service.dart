import 'dart:convert';
import 'package:http/http.dart' as http;
import 'package:flutter_secure_storage/flutter_secure_storage.dart';

/// Central API service for communicating with the FastAPI backend.
/// All methods include proper error handling and JWT token management.
class ApiService {
  // ──────────────────────────────────────────────
  //  IMPORTANT: Change this to your computer's WiFi IP
  //  when testing on a physical device.
  //
  //  To find your IP:
  //    Windows CMD:  ipconfig → look for IPv4 Address
  //  Example:      http://192.168.1.100:8000
  //
  //  For Android Emulator use: http://10.0.2.2:8000
  // ──────────────────────────────────────────────
  // static const String baseUrl = 'http://192.168.31.244:8000';
  static const String baseUrl = 'https://kisanslot-backend.onrender.com';

  static const _storage = FlutterSecureStorage();
  static const _tokenKey = 'jwt_token';
  static const _farmerIdKey = 'farmer_id';
  static const _farmerNameKey = 'farmer_name';
  static const _farmerFarmerId = 'farmer_farmer_id';
  static const _bookingIdKey = 'active_booking_id';
  
  // Admin Keys
  static const _isAdminKey = 'is_admin';
  static const _centreIdKey = 'admin_centre_id';

  // ──────────────────────────────────────────────
  //  Token Management
  // ──────────────────────────────────────────────

  static Future<void> saveToken(String token) async {
    await _storage.write(key: _tokenKey, value: token);
  }

  static Future<String?> getToken() async {
    return await _storage.read(key: _tokenKey);
  }

  static Future<void> clearToken() async {
    await _storage.deleteAll();
  }

  static Future<bool> hasToken() async {
    final token = await getToken();
    return token != null && token.isNotEmpty;
  }

  static Future<void> saveFarmerInfo(int id, String name, String farmerId) async {
    await _storage.write(key: _farmerIdKey, value: id.toString());
    await _storage.write(key: _farmerNameKey, value: name);
    await _storage.write(key: _farmerFarmerId, value: farmerId);
  }

  static Future<String?> getSavedFarmerName() async {
    return await _storage.read(key: _farmerNameKey);
  }

  static Future<void> saveActiveBookingId(String bookingId) async {
    await _storage.write(key: _bookingIdKey, value: bookingId);
  }

  static Future<String?> getActiveBookingId() async {
    return await _storage.read(key: _bookingIdKey);
  }

  static Future<void> saveAdminInfo(int? centreId) async {
    await _storage.write(key: _isAdminKey, value: 'true');
    if (centreId != null) {
      await _storage.write(key: _centreIdKey, value: centreId.toString());
    }
  }

  static Future<bool> isAdmin() async {
    final val = await _storage.read(key: _isAdminKey);
    return val == 'true';
  }

  // ──────────────────────────────────────────────
  //  HTTP Helpers
  // ──────────────────────────────────────────────

  static Future<Map<String, String>> _authHeaders() async {
    final token = await getToken();
    return {
      'Content-Type': 'application/json',
      if (token != null) 'Authorization': 'Bearer $token',
    };
  }

  static dynamic _handleResponse(http.Response response) {
    if (response.statusCode >= 200 && response.statusCode < 300) {
      if (response.body.isEmpty) return {};
      return jsonDecode(response.body);
    } else {
      String message = 'Something went wrong.';
      try {
        final body = jsonDecode(response.body);
        message = body['detail'] ?? message;
      } catch (_) {}
      throw ApiException(response.statusCode, message);
    }
  }

  // ──────────────────────────────────────────────
  //  Auth APIs
  // ──────────────────────────────────────────────

  /// Register a new farmer. Returns the full response map.
  static Future<Map<String, dynamic>> register({
    required String name,
    required String mobile,
    required String farmerId,
    required String village,
    required String district,
    required String state,
    required String crop,
    required double expectedQuantity,
    required String password,
  }) async {
    final response = await http.post(
      Uri.parse('$baseUrl/api/auth/register'),
      headers: {'Content-Type': 'application/json'},
      body: jsonEncode({
        'name': name,
        'mobile': mobile,
        'farmer_id': farmerId,
        'village': village,
        'district': district,
        'state': state,
        'crop': crop,
        'expected_quantity': expectedQuantity,
        'password': password,
      }),
    );

    final data = _handleResponse(response);

    // Store token and farmer info
    await saveToken(data['access_token']);
    final farmer = data['farmer'];
    await saveFarmerInfo(farmer['id'], farmer['name'], farmer['farmer_id']);

    return data;
  }

  /// Login with mobile + password. Returns the full response map.
  static Future<Map<String, dynamic>> login({
    required String mobile,
    required String password,
  }) async {
    final response = await http.post(
      Uri.parse('$baseUrl/api/auth/login'),
      headers: {'Content-Type': 'application/json'},
      body: jsonEncode({
        'mobile': mobile,
        'password': password,
      }),
    );

    final data = _handleResponse(response);

    // Store token and farmer info
    await saveToken(data['access_token']);
    final farmer = data['farmer'];
    await saveFarmerInfo(farmer['id'], farmer['name'], farmer['farmer_id']);

    return data;
  }

  /// Login as Admin.
  static Future<Map<String, dynamic>> adminLogin({
    required String username,
    required String password,
  }) async {
    final response = await http.post(
      Uri.parse('$baseUrl/api/auth/admin/login'),
      headers: {'Content-Type': 'application/json'},
      body: jsonEncode({
        'username': username,
        'password': password,
      }),
    );

    final data = _handleResponse(response);

    await saveToken(data['access_token']);
    await saveAdminInfo(data['centre_id']);

    return data;
  }

  /// Logout — clears all stored credentials.
  static Future<void> logout() async {
    await clearToken();
  }

  // ──────────────────────────────────────────────
  //  Farmer APIs
  // ──────────────────────────────────────────────

  /// Get the logged-in farmer's profile.
  static Future<Map<String, dynamic>> getProfile() async {
    final response = await http.get(
      Uri.parse('$baseUrl/api/farmers/me'),
      headers: await _authHeaders(),
    );
    return _handleResponse(response);
  }

  /// Update the logged-in farmer's profile.
  static Future<Map<String, dynamic>> updateProfile({
    String? name,
    String? village,
    String? district,
    String? state,
    String? crop,
    double? expectedQuantity,
  }) async {
    final body = <String, dynamic>{};
    if (name != null) body['name'] = name;
    if (village != null) body['village'] = village;
    if (district != null) body['district'] = district;
    if (state != null) body['state'] = state;
    if (crop != null) body['crop'] = crop;
    if (expectedQuantity != null) body['expected_quantity'] = expectedQuantity;

    final response = await http.put(
      Uri.parse('$baseUrl/api/farmers/me'),
      headers: await _authHeaders(),
      body: jsonEncode(body),
    );
    return _handleResponse(response);
  }

  // ──────────────────────────────────────────────
  //  Centre APIs
  // ──────────────────────────────────────────────

  /// Get all active procurement centres with optional location-based distance.
  static Future<List<dynamic>> getCentres({double? lat, double? lon}) async {
    String url = '$baseUrl/api/centres';
    if (lat != null && lon != null) {
      url += '?lat=$lat&lon=$lon';
    }
    final response = await http.get(
      Uri.parse(url),
      headers: await _authHeaders(),
    );
    return _handleResponse(response);
  }

  // ──────────────────────────────────────────────
  //  Slot APIs
  // ──────────────────────────────────────────────

  /// Get available slots for a centre on a specific date.
  static Future<List<dynamic>> getSlots(int centreId, String date) async {
    final response = await http.get(
      Uri.parse('$baseUrl/api/centres/$centreId/slots?date=$date'),
      headers: await _authHeaders(),
    );
    return _handleResponse(response);
  }

  // ──────────────────────────────────────────────
  //  Booking APIs
  // ──────────────────────────────────────────────

  /// Create a new booking.
  static Future<Map<String, dynamic>> createBooking({
    required int centreId,
    required int slotId,
    required String crop,
    required double expectedQuantity,
    required String vehicleNumber,
  }) async {
    final response = await http.post(
      Uri.parse('$baseUrl/api/bookings'),
      headers: await _authHeaders(),
      body: jsonEncode({
        'centre_id': centreId,
        'slot_id': slotId,
        'crop': crop,
        'expected_quantity': expectedQuantity,
        'vehicle_number': vehicleNumber,
      }),
    );

    final data = _handleResponse(response);

    // Save the active booking ID
    await saveActiveBookingId(data['booking_id']);

    return data;
  }

  /// Get booking details by booking ID (e.g. "KS1025").
  static Future<Map<String, dynamic>> getBooking(String bookingId) async {
    final response = await http.get(
      Uri.parse('$baseUrl/api/bookings/$bookingId'),
      headers: await _authHeaders(),
    );
    return _handleResponse(response);
  }

  /// List all bookings for the logged-in farmer.
  static Future<List<dynamic>> getMyBookings() async {
    final response = await http.get(
      Uri.parse('$baseUrl/api/bookings'),
      headers: await _authHeaders(),
    );
    return _handleResponse(response);
  }

  /// Cancel a booking.
  static Future<Map<String, dynamic>> cancelBooking(String bookingId) async {
    final response = await http.put(
      Uri.parse('$baseUrl/api/bookings/$bookingId/cancel'),
      headers: await _authHeaders(),
    );
    return _handleResponse(response);
  }

  // ──────────────────────────────────────────────
  //  Queue APIs
  // ──────────────────────────────────────────────

  /// Get live queue position for a booking.
  static Future<Map<String, dynamic>> getQueue(String bookingId) async {
    final response = await http.get(
      Uri.parse('$baseUrl/api/queue/$bookingId'),
      headers: await _authHeaders(),
    );
    return _handleResponse(response);
  }

  /// Admin: Get live queue for centre
  static Future<List<dynamic>> getAdminQueue() async {
    final response = await http.get(
      Uri.parse('$baseUrl/api/queue/admin/list'),
      headers: await _authHeaders(),
    );
    return _handleResponse(response);
  }

  /// Admin: Update booking status
  static Future<Map<String, dynamic>> updateBookingStatus(String bookingId, String status) async {
    final response = await http.put(
      Uri.parse('$baseUrl/api/queue/admin/booking/$bookingId/status'),
      headers: await _authHeaders(),
      body: jsonEncode({'status': status}),
    );
    return _handleResponse(response);
  }

  // ──────────────────────────────────────────────
  //  Procurement APIs
  // ──────────────────────────────────────────────

  /// Get procurement status for a booking.
  static Future<Map<String, dynamic>> getProcurement(String bookingId) async {
    final response = await http.get(
      Uri.parse('$baseUrl/api/procurement/$bookingId'),
      headers: await _authHeaders(),
    );
    return _handleResponse(response);
  }

  /// Admin: Update procurement details
  static Future<Map<String, dynamic>> updateProcurement(
      String bookingId, Map<String, dynamic> data) async {
    final response = await http.put(
      Uri.parse('$baseUrl/api/procurement/admin/$bookingId'),
      headers: await _authHeaders(),
      body: jsonEncode(data),
    );
    return _handleResponse(response);
  }

  // ──────────────────────────────────────────────
  //  Payment APIs
  // ──────────────────────────────────────────────

  /// Get payment status for a booking.
  static Future<Map<String, dynamic>> getPayment(String bookingId) async {
    final response = await http.get(
      Uri.parse('$baseUrl/api/payments/$bookingId'),
      headers: await _authHeaders(),
    );
    return _handleResponse(response);
  }

  // ──────────────────────────────────────────────
  //  Notifications APIs
  // ──────────────────────────────────────────────

  /// Get notifications for logged-in user with pagination and optional unread filter.
  static Future<Map<String, dynamic>> getNotifications({
    bool unreadOnly = false,
    int page = 1,
    int limit = 20,
  }) async {
    final response = await http.get(
      Uri.parse('$baseUrl/api/notifications?unread_only=$unreadOnly&page=$page&limit=$limit'),
      headers: await _authHeaders(),
    );
    final data = _handleResponse(response);
    if (data is List) {
      return {
        'items': data,
        'unread_count': data.where((n) => n['is_read'] == false).length,
        'total': data.length,
      };
    }
    return data;
  }

  /// Get real-time unread notification count.
  static Future<int> getUnreadNotificationCount() async {
    try {
      final response = await http.get(
        Uri.parse('$baseUrl/api/notifications/unread-count'),
        headers: await _authHeaders(),
      );
      final data = _handleResponse(response);
      return data['unread_count'] ?? 0;
    } catch (_) {
      return 0;
    }
  }

  /// Mark notification as read.
  static Future<Map<String, dynamic>> markNotificationRead(int id) async {
    final response = await http.put(
      Uri.parse('$baseUrl/api/notifications/$id/read'),
      headers: await _authHeaders(),
    );
    return _handleResponse(response);
  }

  /// Mark all notifications as read.
  static Future<Map<String, dynamic>> markAllNotificationsRead() async {
    final response = await http.put(
      Uri.parse('$baseUrl/api/notifications/read-all'),
      headers: await _authHeaders(),
    );
    return _handleResponse(response);
  }
}

/// Custom exception for API errors with HTTP status code.
class ApiException implements Exception {
  final int statusCode;
  final String message;

  ApiException(this.statusCode, this.message);

  @override
  String toString() => message;
}
