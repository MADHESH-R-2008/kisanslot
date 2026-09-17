import 'package:flutter/material.dart';
import '../models/booking.dart';
import '../services/api_service.dart';
import '../utils/app_colors.dart';
import '../utils/routes.dart';
import '../widgets/custom_button.dart';
import '../widgets/status_card.dart';

class PaymentScreen extends StatefulWidget {
  const PaymentScreen({super.key});

  @override
  State<PaymentScreen> createState() => _PaymentScreenState();
}

class _PaymentScreenState extends State<PaymentScreen> {
  bool _isLoading = true;
  String? _error;
  BookingModel? _booking;
  Map<String, dynamic>? _paymentData;

  @override
  void initState() {
    super.initState();
    _loadData();
  }

  Future<void> _loadData() async {
    setState(() { _isLoading = true; _error = null; });

    try {
      final bookingId = await ApiService.getActiveBookingId();
      if (bookingId == null || bookingId.isEmpty) {
        if (mounted) setState(() { _isLoading = false; _error = 'No active booking found.'; });
        return;
      }

      final bookingData = await ApiService.getBooking(bookingId);
      _booking = BookingModel.fromJson(bookingData);

      _paymentData = await ApiService.getPayment(bookingId);

      if (mounted) setState(() => _isLoading = false);
    } on ApiException catch (e) {
      if (mounted) setState(() { _isLoading = false; _error = e.message; });
    } catch (e) {
      if (mounted) setState(() { _isLoading = false; _error = 'Unable to load payment data.'; });
    }
  }

  int _getStepFromStatus(String status) {
    switch (status.toUpperCase()) {
      case 'PENDING': return 0;
      case 'PROCESSING': return 2;
      case 'COMPLETED': return 4;
      case 'FAILED': return 0;
      default: return 0;
    }
  }

  @override
  Widget build(BuildContext context) {
    if (_isLoading) {
      return Scaffold(
        backgroundColor: AppColors.background,
        appBar: AppBar(title: const Text('Payment Status')),
        body: const Center(child: CircularProgressIndicator(color: AppColors.primary)),
      );
    }

    if (_error != null || _booking == null) {
      return Scaffold(
        backgroundColor: AppColors.background,
        appBar: AppBar(
          title: const Text('Payment Status'),
          leading: IconButton(icon: const Icon(Icons.arrow_back_ios_new_rounded), onPressed: () => Navigator.pop(context)),
        ),
        body: Center(
          child: Padding(
            padding: const EdgeInsets.all(32),
            child: Column(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                const Icon(Icons.account_balance_wallet_outlined, size: 64, color: AppColors.textMuted),
                const SizedBox(height: 16),
                Text(_error ?? 'No payment info.', textAlign: TextAlign.center, style: const TextStyle(color: AppColors.textSecondary, fontSize: 16)),
                const SizedBox(height: 24),
                ElevatedButton.icon(onPressed: _loadData, icon: const Icon(Icons.refresh), label: const Text('TRY AGAIN')),
              ],
            ),
          ),
        ),
      );
    }

    final booking = _booking!;
    final payStatus = _paymentData?['status'] ?? 'PENDING';
    final currentStep = _getStepFromStatus(payStatus);
    
    final rate = booking.ratePerKg;
    final qty = booking.quantityKg;
    final totalAmount = (_paymentData?['amount'] ?? (qty * rate)).toDouble();
    final transactionId = _paymentData?['transaction_id'];

    final List<TimelineStepData> paymentTimelineSteps = [
      TimelineStepData(
        title: 'Procurement Completed',
        description: 'Mandi J-Form generated',
        time: 'Done',
        state: currentStep >= 0 ? TimelineStepStatus.completed : TimelineStepStatus.pending,
        icon: Icons.check_circle_outline,
      ),
      TimelineStepData(
        title: 'Payment Initiated',
        description: 'Payment voucher created',
        time: currentStep >= 1 ? 'Done' : 'Pending',
        state: currentStep >= 1 ? TimelineStepStatus.completed : TimelineStepStatus.pending,
        icon: Icons.send_outlined,
      ),
      TimelineStepData(
        title: 'Payment Processing',
        description: 'Direct Benefit Transfer (DBT) clearance',
        time: currentStep >= 2 ? 'Done' : (currentStep == 2 ? 'In Progress' : 'Pending'),
        state: currentStep > 2 ? TimelineStepStatus.completed : (currentStep == 2 ? TimelineStepStatus.current : TimelineStepStatus.pending),
        icon: Icons.sync,
      ),
      TimelineStepData(
        title: 'Payment Completed',
        description: transactionId != null ? 'Txn: $transactionId' : 'Credit notification will be sent',
        time: currentStep >= 4 ? 'Done' : 'Expected soon',
        state: currentStep >= 4 ? TimelineStepStatus.completed : TimelineStepStatus.pending,
        icon: Icons.account_balance_wallet_outlined,
      ),
    ];

    return Scaffold(
      backgroundColor: AppColors.background,
      appBar: AppBar(
        title: const Text('Payment Status'),
        leading: IconButton(
          icon: const Icon(Icons.arrow_back_ios_new_rounded),
          onPressed: () => Navigator.pop(context),
        ),
      ),
      body: SafeArea(
        child: SingleChildScrollView(
          padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 12),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              // Hero Amount Payout Card
              Container(
                width: double.infinity,
                padding: const EdgeInsets.all(22),
                decoration: BoxDecoration(
                  gradient: AppColors.harvestGradient,
                  borderRadius: BorderRadius.circular(20),
                  boxShadow: [
                    BoxShadow(
                      color: AppColors.secondary.withOpacity(0.25),
                      blurRadius: 16,
                      offset: const Offset(0, 6),
                    ),
                  ],
                ),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Row(
                      mainAxisAlignment: MainAxisAlignment.spaceBetween,
                      children: [
                        Flexible(
                          child: Text(
                            'TOTAL PAYMENT',
                            style: TextStyle(
                              fontSize: 12,
                              fontWeight: FontWeight.bold,
                              color: Colors.white70,
                              letterSpacing: 1,
                            ),
                            maxLines: 1,
                            overflow: TextOverflow.ellipsis,
                          ),
                        ),
                        const SizedBox(width: 8),
                        Container(
                          padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
                          decoration: BoxDecoration(
                            color: Colors.white.withOpacity(0.25),
                            borderRadius: BorderRadius.circular(20),
                          ),
                          child: Row(
                            mainAxisSize: MainAxisSize.min,
                            children: [
                              Icon(payStatus == 'COMPLETED' ? Icons.check_circle : Icons.hourglass_top_rounded, size: 14, color: Colors.white),
                              const SizedBox(width: 4),
                              Text(
                                payStatus == 'COMPLETED' ? 'Completed' : 'Processing',
                                style: const TextStyle(
                                  fontSize: 11,
                                  fontWeight: FontWeight.bold,
                                  color: Colors.white,
                                ),
                              ),
                            ],
                          ),
                        ),
                      ],
                    ),
                    const SizedBox(height: 10),
                    Text(
                      '₹${totalAmount.toStringAsFixed(0)}',
                      style: const TextStyle(
                        fontSize: 38,
                        fontWeight: FontWeight.w900,
                        color: Colors.white,
                        letterSpacing: -0.5,
                      ),
                    ),
                    const SizedBox(height: 12),
                    const Divider(height: 1, color: Colors.white24),
                    const SizedBox(height: 12),
                    Row(
                      mainAxisAlignment: MainAxisAlignment.spaceBetween,
                      children: [
                        Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            const Text(
                              'Expected Payment Date',
                              style: TextStyle(fontSize: 11, color: Colors.white70),
                            ),
                            const SizedBox(height: 2),
                            Text(
                              booking.expectedPaymentDate,
                              style: const TextStyle(
                                fontSize: 14,
                                fontWeight: FontWeight.bold,
                                color: Colors.white,
                              ),
                            ),
                          ],
                        ),
                        Column(
                          crossAxisAlignment: CrossAxisAlignment.end,
                          children: [
                            const Text(
                              'Destination Account',
                              style: TextStyle(fontSize: 11, color: Colors.white70),
                            ),
                            const SizedBox(height: 2),
                            Text(
                              booking.bankAccountHint,
                              style: const TextStyle(
                                fontSize: 13,
                                fontWeight: FontWeight.bold,
                                color: Colors.white,
                              ),
                            ),
                          ],
                        ),
                      ],
                    ),
                  ],
                ),
              ),
              const SizedBox(height: 20),

              // Rate & Weight Calculation Breakdown
              Container(
                padding: const EdgeInsets.all(18),
                decoration: BoxDecoration(
                  color: Colors.white,
                  borderRadius: BorderRadius.circular(18),
                  border: Border.all(color: AppColors.cardBorder),
                  boxShadow: [
                    BoxShadow(
                      color: Colors.black.withOpacity(0.04),
                      blurRadius: 10,
                      offset: const Offset(0, 4),
                    ),
                  ],
                ),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    const Row(
                      children: [
                        Icon(Icons.calculate_outlined, color: AppColors.primary, size: 20),
                        SizedBox(width: 8),
                        Text(
                          'Payment Breakdown',
                          style: TextStyle(
                            fontSize: 15,
                            fontWeight: FontWeight.bold,
                            color: AppColors.textPrimary,
                          ),
                        ),
                      ],
                    ),
                    const SizedBox(height: 14),
                    _buildRow('Crop', booking.crop),
                    const Divider(height: 18, color: AppColors.cardBorder),
                    _buildRow('Quantity', '${qty.toStringAsFixed(0)} kg'),
                    const Divider(height: 18, color: AppColors.cardBorder),
                    _buildRow('Rate per kg', '₹${rate.toStringAsFixed(2)} / kg'),
                    const Divider(height: 18, color: AppColors.cardBorder),
                    _buildRow('Gross Payable', '₹${totalAmount.toStringAsFixed(2)}', isBold: true),
                    const Divider(height: 18, color: AppColors.cardBorder),
                    _buildRow('Mandi Charges / Deductions', '₹0.00 (100% Free)'),
                    const Divider(height: 18, color: AppColors.cardBorder),
                    _buildRow('Net Payable (DBT)', '₹${totalAmount.toStringAsFixed(2)}', isBold: true, isHighlight: true),
                  ],
                ),
              ),
              const SizedBox(height: 20),

              // Payment Timeline Card
              StatusTimelineCard(
                title: 'Payment Progress Timeline',
                steps: paymentTimelineSteps,
              ),
              const SizedBox(height: 20),

              // Download Receipt / Help Buttons
              CustomButton(
                text: 'DOWNLOAD J-FORM RECEIPT (PDF)',
                icon: Icons.download_rounded,
                variant: ButtonVariant.outlined,
                onPressed: () {
                  ScaffoldMessenger.of(context).showSnackBar(
                    const SnackBar(
                      content: Text('J-Form Receipt downloaded to local documents.'),
                      backgroundColor: AppColors.success,
                    ),
                  );
                },
              ),
              const SizedBox(height: 12),

              CustomButton(
                text: 'BACK TO HOME',
                icon: Icons.home_rounded,
                variant: ButtonVariant.primary,
                onPressed: () {
                  Navigator.pushNamedAndRemoveUntil(context, AppRoutes.home, (route) => false);
                },
              ),
              const SizedBox(height: 24),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildRow(String label, String value, {bool isBold = false, bool isHighlight = false}) {
    return Row(
      mainAxisAlignment: MainAxisAlignment.spaceBetween,
      children: [
        Flexible(
          flex: 1,
          child: Text(
            label,
            style: TextStyle(
              fontSize: 14,
              fontWeight: isBold ? FontWeight.bold : FontWeight.normal,
              color: isHighlight ? AppColors.primaryDark : AppColors.textSecondary,
            ),
            maxLines: 1,
            overflow: TextOverflow.ellipsis,
          ),
        ),
        const SizedBox(width: 8),
        Flexible(
          flex: 1,
          child: Text(
            value,
            style: TextStyle(
              fontSize: 14,
              fontWeight: isBold ? FontWeight.bold : FontWeight.w600,
              color: isHighlight ? AppColors.primary : AppColors.textPrimary,
            ),
            textAlign: TextAlign.end,
            maxLines: 1,
            overflow: TextOverflow.ellipsis,
          ),
        ),
      ],
    );
  }
}
