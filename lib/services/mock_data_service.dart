import 'package:flutter/material.dart';
import '../models/farmer.dart';
import '../models/centre.dart';
import '../models/slot.dart';
import '../models/booking.dart';

class MockDataService extends ChangeNotifier {
  static final MockDataService _instance = MockDataService._internal();
  factory MockDataService() => _instance;
  MockDataService._internal() {
    _initData();
  }

  FarmerModel _currentFarmer = FarmerModel.mockFarmer();
  List<ProcurementCentre> _centres = [];
  List<TimeSlot> _timeSlots = [];
  BookingModel? _activeBooking;
  List<BookingModel> _bookingHistory = [];
  bool _isLoggedIn = false;

  FarmerModel get currentFarmer => _currentFarmer;
  List<ProcurementCentre> get centres => _centres;
  List<TimeSlot> get timeSlots => _timeSlots;
  BookingModel? get activeBooking => _activeBooking;
  List<BookingModel> get bookingHistory => _bookingHistory;
  bool get isLoggedIn => _isLoggedIn;

  void _initData() {
    _centres = ProcurementCentre.getMockCentres();
    _timeSlots = TimeSlot.getMockSlots();
    _activeBooking = BookingModel.mockBooking();
    _bookingHistory = [_activeBooking!];
    _currentFarmer = FarmerModel.mockFarmer();
    _isLoggedIn = false;
  }

  void resetData() {
    _initData();
    notifyListeners();
  }

  bool login(String mobile, String password) {
    if (mobile.trim().isNotEmpty && password.trim().isNotEmpty) {
      _isLoggedIn = true;
      notifyListeners();
      return true;
    }
    return false;
  }

  void logout() {
    _isLoggedIn = false;
    notifyListeners();
  }

  void registerFarmer({
    required String name,
    required String mobile,
    required String farmerId,
    required String village,
    required String district,
    required String state,
    required String crop,
    required double expectedQuantity,
  }) {
    _currentFarmer = FarmerModel(
      name: name,
      farmerId: farmerId.isEmpty ? 'FR${DateTime.now().millisecondsSinceEpoch % 90000 + 10000}' : farmerId,
      mobile: mobile,
      village: village,
      district: district,
      state: state,
      crop: crop,
      expectedQuantity: expectedQuantity,
    );
    _isLoggedIn = true;
    notifyListeners();
  }

  BookingModel createBooking({
    required ProcurementCentre centre,
    required String date,
    required String timeRange,
    required String crop,
    required double quantityKg,
    required String vehicleNumber,
  }) {
    final int newToken = 17; // Matches mock requirement or random
    const double rate = 21.50;
    final double total = quantityKg * rate;
    
    final newBooking = BookingModel(
      bookingId: 'KS1025',
      tokenNumber: newToken,
      centreId: centre.id,
      centreName: centre.name,
      date: date,
      timeRange: timeRange,
      crop: crop,
      quantityKg: quantityKg,
      vehicleNumber: vehicleNumber.isEmpty ? 'TN 01 AB 1234' : vehicleNumber,
      queuePosition: 17,
      farmersAhead: 16,
      counterNumber: centre.activeCounters > 0 ? 3 : 1,
      waitTimeMinutes: 45,
      status: BookingStatus.inQueue,
      currentProcurementStep: 3,
      paymentStatus: PaymentStatus.processing,
      ratePerKg: rate,
      totalAmount: total,
      expectedPaymentDate: '27 August 2026',
    );

    _activeBooking = newBooking;
    _bookingHistory.insert(0, newBooking);
    notifyListeners();
    return newBooking;
  }

  /// Simulate live queue movement when user clicks "Refresh Queue"
  void refreshQueue() {
    if (_activeBooking == null) return;

    final currentPos = _activeBooking!.queuePosition;
    int nextPos;
    int nextAhead;
    int nextWait;
    BookingStatus status;

    if (currentPos > 12) {
      nextPos = 12;
      nextAhead = 11;
      nextWait = 32;
      status = BookingStatus.inQueue;
    } else if (currentPos > 8) {
      nextPos = 8;
      nextAhead = 7;
      nextWait = 20;
      status = BookingStatus.inQueue;
    } else if (currentPos > 5) {
      nextPos = 5;
      nextAhead = 4;
      nextWait = 12;
      status = BookingStatus.inQueue;
    } else if (currentPos > 2) {
      nextPos = 2;
      nextAhead = 1;
      nextWait = 5;
      status = BookingStatus.inQueue;
    } else if (currentPos > 1) {
      nextPos = 1;
      nextAhead = 0;
      nextWait = 1;
      status = BookingStatus.atCounter;
    } else {
      // Reset back to initial demo queue for demonstration cycle
      nextPos = 17;
      nextAhead = 16;
      nextWait = 45;
      status = BookingStatus.inQueue;
    }

    _activeBooking = _activeBooking!.copyWith(
      queuePosition: nextPos,
      farmersAhead: nextAhead,
      waitTimeMinutes: nextWait,
      status: status,
    );

    notifyListeners();
  }
}
