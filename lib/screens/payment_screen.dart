import 'package:flutter/material.dart';
import '../models/booking.dart';
import '../services/mock_data_service.dart';
import '../utils/app_colors.dart';
import '../utils/routes.dart';
import '../widgets/custom_button.dart';
import '../widgets/status_card.dart';

class PaymentScreen extends StatelessWidget {
  const PaymentScreen({super.key});

  @override
  Widget build(BuildContext context) {
    final booking = MockDataService().activeBooking ?? BookingModel.mockBooking();

    final List<TimelineStepData> paymentTimelineSteps = [
      const TimelineStepData(
        title: 'Procurement Completed',
        description: 'Mandi J-Form generated and produce safely stored',
        time: '25 Aug, 11:30 AM',
        state: TimelineStepStatus.completed,
        icon: Icons.check_circle_outline,
      ),
      const TimelineStepData(
        title: 'Payment Initiated',
        description: 'Payment voucher created by APMC procurement officer',
        time: '25 Aug, 02:15 PM',
        state: TimelineStepStatus.completed,
        icon: Icons.send_outlined,
      ),
      const TimelineStepData(
        title: 'Payment Processing',
        description: 'Direct Benefit Transfer (DBT) clearance through PFMS',
        time: 'In Progress',
        state: TimelineStepStatus.current,
        icon: Icons.sync,
      ),
      const TimelineStepData(
        title: 'Payment Completed',
        description: 'Credit notification will be sent to registered mobile',
        time: 'Exp. 27 Aug 2026',
        state: TimelineStepStatus.pending,
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
                      color: AppColors.secondary.withValues(alpha: 0.25),
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
                            color: Colors.white.withValues(alpha: 0.25),
                            borderRadius: BorderRadius.circular(20),
                          ),
                          child: const Row(
                            mainAxisSize: MainAxisSize.min,
                            children: [
                              Icon(Icons.hourglass_top_rounded, size: 14, color: Colors.white),
                              SizedBox(width: 4),
                              Text(
                                '🟡 Processing',
                                style: TextStyle(
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
                    const Text(
                      '₹18,275',
                      style: TextStyle(
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
                      color: Colors.black.withValues(alpha: 0.04),
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
                    _buildRow('Quantity', '${booking.quantityKg.toStringAsFixed(0)} kg'),
                    const Divider(height: 18, color: AppColors.cardBorder),
                    _buildRow('Rate per kg', '₹${booking.ratePerKg.toStringAsFixed(2)} / kg'),
                    const Divider(height: 18, color: AppColors.cardBorder),
                    _buildRow('Gross Payable', '₹18,275.00', isBold: true),
                    const Divider(height: 18, color: AppColors.cardBorder),
                    _buildRow('Mandi Charges / Deductions', '₹0.00 (100% Free)'),
                    const Divider(height: 18, color: AppColors.cardBorder),
                    _buildRow('Net Payable (DBT)', '₹18,275.00', isBold: true, isHighlight: true),
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
