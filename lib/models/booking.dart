enum BookingStatus {
  confirmed,
  inQueue,
  called,
  serving,
  atCounter,
  procuring,
  completed,
  cancelled,
  noShow,
  skipped,
}

enum PaymentStatus {
  pending,
  initiated,
  processing,
  completed,
}

class BookingModel {
  final String bookingId;
  final int tokenNumber;
  final String tokenDisplay; // Phase 3.2
  final int centreId;
  final String centreName;
  final String date;
  final String timeRange;
  final String crop;
  final double quantityKg;
  final String vehicleNumber;
  final int queuePosition;
  final int farmersAhead;
  final int counterNumber; // Active counters
  final String? assignedCounterName; // Phase 3.2
  final int waitTimeMinutes;
  final BookingStatus status;
  final int currentProcurementStep; // 0 to 6 (7 steps)
  final PaymentStatus paymentStatus;
  final double ratePerKg;
  final double totalAmount;
  final String expectedPaymentDate;
  final String bankAccountHint;

  const BookingModel({
    required this.bookingId,
    required this.tokenNumber,
    this.tokenDisplay = '',
    required this.centreId,
    required this.centreName,
    required this.date,
    required this.timeRange,
    required this.crop,
    required this.quantityKg,
    required this.vehicleNumber,
    required this.queuePosition,
    required this.farmersAhead,
    required this.counterNumber,
    this.assignedCounterName,
    required this.waitTimeMinutes,
    this.status = BookingStatus.inQueue,
    this.currentProcurementStep = 3, // Step 4: Weighing
    this.paymentStatus = PaymentStatus.processing,
    this.ratePerKg = 21.50,
    this.totalAmount = 18275.00,
    this.expectedPaymentDate = '27 August 2026',
    this.bankAccountHint = 'SBI ••• 4921',
  });

  /// Create from booking detail API response
  factory BookingModel.fromJson(Map<String, dynamic> json) {
    final statusStr = (json['status'] ?? 'CONFIRMED').toString().toUpperCase();
    BookingStatus bookingStatus;
    switch (statusStr) {
      case 'CONFIRMED':
        bookingStatus = BookingStatus.confirmed;
        break;
      case 'ARRIVED':
      case 'VERIFIED':
      case 'WAITING':
        bookingStatus = BookingStatus.inQueue;
        break;
      case 'CALLED':
        bookingStatus = BookingStatus.called;
        break;
      case 'SERVING':
        bookingStatus = BookingStatus.serving;
        break;
      case 'PROCESSING':
        bookingStatus = BookingStatus.procuring;
        break;
      case 'COMPLETED':
        bookingStatus = BookingStatus.completed;
        break;
      case 'CANCELLED':
        bookingStatus = BookingStatus.cancelled;
        break;
      case 'NO_SHOW':
        bookingStatus = BookingStatus.noShow;
        break;
      case 'SKIPPED':
        bookingStatus = BookingStatus.skipped;
        break;
      default:
        bookingStatus = BookingStatus.confirmed;
    }

    return BookingModel(
      bookingId: json['booking_id'] ?? '',
      tokenNumber: json['token_number'] ?? 0,
      tokenDisplay: json['token_display'] ?? '',
      centreId: json['centre_id'] ?? 0,
      centreName: json['centre'] ?? '',
      date: json['date'] ?? '',
      timeRange: json['time'] ?? '${json['start_time'] ?? ''} - ${json['end_time'] ?? ''}',
      crop: json['crop'] ?? '',
      quantityKg: (json['quantity'] ?? json['expected_quantity'] ?? 0).toDouble(),
      vehicleNumber: json['vehicle_number'] ?? '',
      queuePosition: json['queue_position'] ?? 0,
      farmersAhead: json['farmers_ahead'] ?? 0,
      counterNumber: json['active_counters'] ?? 3,
      assignedCounterName: json['counter_name'],
      waitTimeMinutes: json['estimated_wait_minutes'] ?? 0,
      status: bookingStatus,
    );
  }

  /// Create from booking creation API response
  factory BookingModel.fromCreateResponse(Map<String, dynamic> json) {
    return BookingModel(
      bookingId: json['booking_id'] ?? '',
      tokenNumber: json['token_number'] ?? 0,
      tokenDisplay: json['token_display'] ?? '',
      centreId: 0,
      centreName: json['centre'] ?? '',
      date: json['date'] ?? '',
      timeRange: '${json['start_time'] ?? ''} - ${json['end_time'] ?? ''}',
      crop: json['crop'] ?? '',
      quantityKg: (json['expected_quantity'] ?? 0).toDouble(),
      vehicleNumber: json['vehicle_number'] ?? '',
      queuePosition: json['token_number'] ?? 0,
      farmersAhead: (json['token_number'] ?? 1) - 1,
      counterNumber: 3,
      assignedCounterName: null,
      waitTimeMinutes: 0,
      status: BookingStatus.confirmed,
    );
  }

  BookingModel copyWith({
    String? bookingId,
    int? tokenNumber,
    String? tokenDisplay,
    int? centreId,
    String? centreName,
    String? date,
    String? timeRange,
    String? crop,
    double? quantityKg,
    String? vehicleNumber,
    int? queuePosition,
    int? farmersAhead,
    int? counterNumber,
    String? assignedCounterName,
    int? waitTimeMinutes,
    BookingStatus? status,
    int? currentProcurementStep,
    PaymentStatus? paymentStatus,
    double? ratePerKg,
    double? totalAmount,
    String? expectedPaymentDate,
    String? bankAccountHint,
  }) {
    return BookingModel(
      bookingId: bookingId ?? this.bookingId,
      tokenNumber: tokenNumber ?? this.tokenNumber,
      tokenDisplay: tokenDisplay ?? this.tokenDisplay,
      centreId: centreId ?? this.centreId,
      centreName: centreName ?? this.centreName,
      date: date ?? this.date,
      timeRange: timeRange ?? this.timeRange,
      crop: crop ?? this.crop,
      quantityKg: quantityKg ?? this.quantityKg,
      vehicleNumber: vehicleNumber ?? this.vehicleNumber,
      queuePosition: queuePosition ?? this.queuePosition,
      farmersAhead: farmersAhead ?? this.farmersAhead,
      counterNumber: counterNumber ?? this.counterNumber,
      assignedCounterName: assignedCounterName ?? this.assignedCounterName,
      waitTimeMinutes: waitTimeMinutes ?? this.waitTimeMinutes,
      status: status ?? this.status,
      currentProcurementStep: currentProcurementStep ?? this.currentProcurementStep,
      paymentStatus: paymentStatus ?? this.paymentStatus,
      ratePerKg: ratePerKg ?? this.ratePerKg,
      totalAmount: totalAmount ?? this.totalAmount,
      expectedPaymentDate: expectedPaymentDate ?? this.expectedPaymentDate,
      bankAccountHint: bankAccountHint ?? this.bankAccountHint,
    );
  }

  static BookingModel mockBooking() {
    return const BookingModel(
      bookingId: 'KS1025',
      tokenNumber: 17,
      tokenDisplay: 'C002-017',
      centreId: 2,
      centreName: 'Centre B',
      date: '25 August 2026',
      timeRange: '10:00 AM – 11:00 AM',
      crop: 'Paddy',
      quantityKg: 850.0,
      vehicleNumber: 'TN 01 AB 1234',
      queuePosition: 17,
      farmersAhead: 16,
      counterNumber: 3,
      assignedCounterName: null,
      waitTimeMinutes: 45,
      status: BookingStatus.inQueue,
      currentProcurementStep: 3, // Weighing (🟡)
      paymentStatus: PaymentStatus.processing,
      ratePerKg: 21.50,
      totalAmount: 18275.00,
      expectedPaymentDate: '27 August 2026',
      bankAccountHint: 'State Bank of India (••• 4921)',
    );
  }
}
