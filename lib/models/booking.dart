enum BookingStatus {
  confirmed,
  inQueue,
  atCounter,
  procuring,
  completed,
  cancelled,
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
  final String centreId;
  final String centreName;
  final String date;
  final String timeRange;
  final String crop;
  final double quantityKg;
  final String vehicleNumber;
  final int queuePosition;
  final int farmersAhead;
  final int counterNumber;
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
    required this.waitTimeMinutes,
    this.status = BookingStatus.inQueue,
    this.currentProcurementStep = 3, // Step 4: Weighing
    this.paymentStatus = PaymentStatus.processing,
    this.ratePerKg = 21.50,
    this.totalAmount = 18275.00,
    this.expectedPaymentDate = '27 August 2026',
    this.bankAccountHint = 'SBI •••• 4921',
  });

  BookingModel copyWith({
    String? bookingId,
    int? tokenNumber,
    String? centreId,
    String? centreName,
    String? date,
    String? timeRange,
    String? crop,
    double? quantityKg,
    String? vehicleNumber,
    int? queuePosition,
    int? farmersAhead,
    int? counterNumber,
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
      centreId: 'centre_b',
      centreName: 'Centre B',
      date: '25 August 2026',
      timeRange: '10:00 AM – 11:00 AM',
      crop: 'Paddy',
      quantityKg: 850.0,
      vehicleNumber: 'TN 01 AB 1234',
      queuePosition: 17,
      farmersAhead: 16,
      counterNumber: 3,
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
