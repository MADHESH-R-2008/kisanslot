import 'package:flutter/material.dart';
import '../models/booking.dart';
import '../services/mock_data_service.dart';
import '../utils/app_colors.dart';
import '../utils/routes.dart';
import '../widgets/custom_button.dart';
import '../widgets/status_card.dart';

class ProcurementScreen extends StatelessWidget {
  const ProcurementScreen({super.key});

  @override
  Widget build(BuildContext context) {
    final booking = MockDataService().activeBooking ?? BookingModel.mockBooking();

    final List<TimelineStepData> procurementSteps = [
      const TimelineStepData(
        title: 'Booking Confirmed',
        description: 'Slot successfully booked for 25 Aug at 10:00 AM',
        time: '09:30 AM',
        state: TimelineStepStatus.completed,
        icon: Icons.check_circle_outline,
      ),
      const TimelineStepData(
        title: 'Farmer Verified',
        description: 'Farmer ID (FR10245) & Aadhaar biometric verification passed',
        time: '10:05 AM',
        state: TimelineStepStatus.completed,
        icon: Icons.verified_user_outlined,
      ),
      const TimelineStepData(
        title: 'Quality Check',
        description: 'Moisture content 13.8% • Grade A standard approved',
        time: '10:20 AM',
        state: TimelineStepStatus.completed,
        icon: Icons.fact_check_outlined,
      ),
      const TimelineStepData(
        title: 'Weighing',
        description: 'Gross weight measurement in progress at Weighbridge 2',
        time: 'In Progress',
        state: TimelineStepStatus.current,
        icon: Icons.scale_outlined,
      ),
      const TimelineStepData(
        title: 'Procurement Finalized',
        description: 'Issuance of official Mandi J-Form receipt',
        time: 'Upcoming',
        state: TimelineStepStatus.pending,
        icon: Icons.receipt_long_outlined,
      ),
      const TimelineStepData(
        title: 'Payment Processing',
        description: 'Direct Benefit Transfer (DBT) initiation to bank account',
        time: 'Pending',
        state: TimelineStepStatus.pending,
        icon: Icons.account_balance_outlined,
      ),
      const TimelineStepData(
        title: 'Payment Completed',
        description: 'Amount credited via PFMS / Aadhaar enabled payment',
        time: 'Pending',
        state: TimelineStepStatus.pending,
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
                      child: const Row(
                        mainAxisSize: MainAxisSize.min,
                        children: [
                          Icon(Icons.sync, size: 14, color: AppColors.warning),
                          SizedBox(width: 4),
                          Text(
                            '🟡 Step 4 of 7',
                            style: TextStyle(
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
                actualWeightText: 'Pending (Weighing)',
                ratePerKg: booking.ratePerKg,
                totalAmount: booking.totalAmount,
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
