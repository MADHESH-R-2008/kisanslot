import 'package:flutter/material.dart';
import '../models/booking.dart';
import '../services/api_service.dart';
import '../utils/app_colors.dart';
import '../utils/routes.dart';
import '../widgets/custom_button.dart';
import '../widgets/status_card.dart';

class ProcurementScreen extends StatefulWidget {
  const ProcurementScreen({super.key});

  @override
  State<ProcurementScreen> createState() => _ProcurementScreenState();
}

class _ProcurementScreenState extends State<ProcurementScreen> {
  bool _isLoading = true;
  String? _error;
  BookingModel? _booking;
  Map<String, dynamic>? _procurementData;

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

      _procurementData = await ApiService.getProcurement(bookingId);

      if (mounted) setState(() => _isLoading = false);
    } on ApiException catch (e) {
      if (mounted) setState(() { _isLoading = false; _error = e.message; });
    } catch (e) {
      if (mounted) setState(() { _isLoading = false; _error = 'Unable to load procurement data.'; });
    }
  }

  int _getStepFromStatus(String status) {
    switch (status.toUpperCase()) {
      case 'PENDING': return 0;
      case 'QUALITY_CHECK': return 2;
      case 'WEIGHING': return 3;
      case 'COMPLETED': return 6;
      default: return 0;
    }
  }

  @override
  Widget build(BuildContext context) {
    if (_isLoading) {
      return Scaffold(
        backgroundColor: AppColors.background,
        appBar: AppBar(title: const Text('Procurement Status')),
        body: const Center(child: CircularProgressIndicator(color: AppColors.primary)),
      );
    }

    if (_error != null || _booking == null) {
      return Scaffold(
        backgroundColor: AppColors.background,
        appBar: AppBar(
          title: const Text('Procurement Status'),
          leading: IconButton(icon: const Icon(Icons.arrow_back_ios_new_rounded), onPressed: () => Navigator.pop(context)),
        ),
        body: Center(
          child: Padding(
            padding: const EdgeInsets.all(32),
            child: Column(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                const Icon(Icons.grass_outlined, size: 64, color: AppColors.textMuted),
                const SizedBox(height: 16),
                Text(_error ?? 'No active booking.', textAlign: TextAlign.center, style: const TextStyle(color: AppColors.textSecondary, fontSize: 16)),
                const SizedBox(height: 24),
                ElevatedButton.icon(onPressed: _loadData, icon: const Icon(Icons.refresh), label: const Text('TRY AGAIN')),
              ],
            ),
          ),
        ),
      );
    }

    final booking = _booking!;
    final procStatus = _procurementData?['status'] ?? 'PENDING';
    final currentStep = _getStepFromStatus(procStatus);
    final rate = (_procurementData?['rate'] ?? booking.ratePerKg).toDouble();
    final totalAmount = (_procurementData?['total_amount'] ?? (booking.quantityKg * rate)).toDouble();
    final actualWeight = _procurementData?['actual_weight'];
    final qualityStatus = _procurementData?['quality_status'] ?? 'PENDING';

    List<TimelineStepData> procurementSteps = [
      TimelineStepData(
        title: 'Booking Confirmed',
        description: 'Slot booked for ${booking.date}',
        time: 'Done',
        state: currentStep >= 0 ? TimelineStepStatus.completed : TimelineStepStatus.pending,
        icon: Icons.check_circle_outline,
      ),
      TimelineStepData(
        title: 'Farmer Verified',
        description: 'Farmer ID (${booking.bookingId}) verified',
        time: currentStep >= 1 ? 'Done' : 'Pending',
        state: currentStep >= 1 ? TimelineStepStatus.completed : TimelineStepStatus.pending,
        icon: Icons.verified_user_outlined,
      ),
      TimelineStepData(
        title: 'Quality Check',
        description: qualityStatus == 'PENDING' ? 'Awaiting quality inspection' : 'Quality: $qualityStatus',
        time: currentStep >= 2 ? 'Done' : (currentStep == 2 ? 'In Progress' : 'Pending'),
        state: currentStep > 2 ? TimelineStepStatus.completed : (currentStep == 2 ? TimelineStepStatus.current : TimelineStepStatus.pending),
        icon: Icons.fact_check_outlined,
      ),
      TimelineStepData(
        title: 'Weighing',
        description: actualWeight != null ? 'Actual weight: ${actualWeight.toStringAsFixed(1)} kg' : 'Weight measurement in progress',
        time: currentStep >= 3 ? (currentStep > 3 ? 'Done' : 'In Progress') : 'Pending',
        state: currentStep > 3 ? TimelineStepStatus.completed : (currentStep == 3 ? TimelineStepStatus.current : TimelineStepStatus.pending),
        icon: Icons.scale_outlined,
      ),
      TimelineStepData(
        title: 'Procurement Finalized',
        description: 'Official Mandi receipt issuance',
        time: currentStep >= 4 ? 'Done' : 'Upcoming',
        state: currentStep >= 4 ? TimelineStepStatus.completed : TimelineStepStatus.pending,
        icon: Icons.receipt_long_outlined,
      ),
      TimelineStepData(
        title: 'Payment Processing',
        description: 'Direct Benefit Transfer (DBT) to bank account',
        time: currentStep >= 5 ? 'Done' : 'Pending',
        state: currentStep >= 5 ? TimelineStepStatus.completed : TimelineStepStatus.pending,
        icon: Icons.account_balance_outlined,
      ),
      TimelineStepData(
        title: 'Payment Completed',
        description: 'Amount credited via PFMS',
        time: currentStep >= 6 ? 'Done' : 'Pending',
        state: currentStep >= 6 ? TimelineStepStatus.completed : TimelineStepStatus.pending,
        icon: Icons.payments_outlined,
      ),
    ];

    return Scaffold(
      backgroundColor: AppColors.background,
      appBar: AppBar(
        title: const Text('Procurement Status'),
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
              // Booking Header Tag
              Container(
                padding: const EdgeInsets.all(14),
                decoration: BoxDecoration(
                  color: AppColors.primaryContainer,
                  borderRadius: BorderRadius.circular(14),
                  border: Border.all(color: AppColors.primary.withValues(alpha: 0.2)),
                ),
                child: Row(
                  children: [
                    Expanded(
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text(
                            '${booking.centreName} • Token #${booking.tokenNumber}',
                            style: const TextStyle(
                              fontSize: 15,
                              fontWeight: FontWeight.bold,
                              color: AppColors.primaryDark,
                            ),
                            maxLines: 1,
                            overflow: TextOverflow.ellipsis,
                          ),
                          const SizedBox(height: 2),
                          Text(
                            'Booking ID: ${booking.bookingId}',
                            style: const TextStyle(fontSize: 12, color: AppColors.textSecondary),
                            maxLines: 1,
                            overflow: TextOverflow.ellipsis,
                          ),
                        ],
                      ),
                    ),
                    const SizedBox(width: 8),
                    Container(
                      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
                      decoration: BoxDecoration(
                        color: AppColors.warningContainer,
                        borderRadius: BorderRadius.circular(8),
                        border: Border.all(color: AppColors.warning.withValues(alpha: 0.3)),
                      ),
                      child: Row(
                        mainAxisSize: MainAxisSize.min,
                        children: [
                          const Icon(Icons.sync, size: 14, color: AppColors.warning),
                          const SizedBox(width: 4),
                          Text(
                            '🟡 Step ${currentStep + 1} of 7',
                            style: const TextStyle(
                              fontSize: 11,
                              fontWeight: FontWeight.bold,
                              color: AppColors.warning,
                            ),
                          ),
                        ],
                      ),
                    ),
                  ],
                ),
              ),
              const SizedBox(height: 18),

              // Produce Information & Valuation Card
              ProduceSummaryCard(
                crop: booking.crop,
                expectedQuantity: booking.quantityKg,
                actualWeightText: actualWeight != null ? '${actualWeight.toStringAsFixed(1)} kg' : 'Pending (Weighing)',
                ratePerKg: rate,
                totalAmount: totalAmount,
              ),
              const SizedBox(height: 18),

              // 7-Step Vertical Timeline
              StatusTimelineCard(
                title: 'Procurement Process Stages',
                steps: procurementSteps,
              ),
              const SizedBox(height: 20),

              // Next Action: View Payment Status
              CustomButton(
                text: 'VIEW PAYMENT STATUS',
                icon: Icons.payments_rounded,
                variant: ButtonVariant.primary,
                onPressed: () {
                  Navigator.pushNamed(context, AppRoutes.payment);
                },
              ),
              const SizedBox(height: 20),
            ],
          ),
        ),
      ),
    );
  }
}
