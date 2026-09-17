import 'package:flutter/material.dart';
import '../models/booking.dart';
import '../utils/app_colors.dart';
import '../utils/routes.dart';
import '../widgets/custom_button.dart';

class BookingConfirmationScreen extends StatelessWidget {
  final BookingModel? booking;

  const BookingConfirmationScreen({
    super.key,
    this.booking,
  });

  @override
  Widget build(BuildContext context) {
    final activeBooking = booking ?? BookingModel.mockBooking();


    return Scaffold(
      backgroundColor: AppColors.background,
      body: SafeArea(
        child: SingleChildScrollView(
          padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 20),
          child: Column(
            children: [
              const SizedBox(height: 10),

              // Success Icon Animation / Container
              Container(
                width: 72,
                height: 72,
                decoration: BoxDecoration(
                  color: AppColors.successContainer,
                  shape: BoxShape.circle,
                  border: Border.all(color: AppColors.success.withOpacity(0.3), width: 2),
                ),
                child: const Icon(
                  Icons.check_circle_rounded,
                  color: AppColors.success,
                  size: 46,
                ),
              ),
              const SizedBox(height: 12),

              const Text(
                'Booking Confirmed!',
                style: TextStyle(
                  fontSize: 24,
                  fontWeight: FontWeight.w900,
                  color: AppColors.textPrimary,
                ),
              ),
              const SizedBox(height: 4),

              const Text(
                'Your procurement slot has been successfully scheduled',
                style: TextStyle(
                  fontSize: 13,
                  color: AppColors.textSecondary,
                ),
                textAlign: TextAlign.center,
              ),
              const SizedBox(height: 24),

              // Digital Token Ticket Card
              Container(
                decoration: BoxDecoration(
                  color: Colors.white,
                  borderRadius: BorderRadius.circular(20),
                  border: Border.all(color: AppColors.cardBorder),
                  boxShadow: [
                    BoxShadow(
                      color: AppColors.primary.withOpacity(0.08),
                      blurRadius: 16,
                      offset: const Offset(0, 6),
                    ),
                  ],
                ),
                child: Column(
                  children: [
                    // Token Banner
                    Container(
                      padding: const EdgeInsets.symmetric(vertical: 18, horizontal: 20),
                      decoration: const BoxDecoration(
                        gradient: AppColors.primaryGradient,
                        borderRadius: BorderRadius.only(
                          topLeft: Radius.circular(20),
                          topRight: Radius.circular(20),
                        ),
                      ),
                      child: Row(
                        mainAxisAlignment: MainAxisAlignment.spaceBetween,
                        children: [
                          Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              const Text(
                                'TOKEN NUMBER',
                                style: TextStyle(
                                  fontSize: 11,
                                  fontWeight: FontWeight.bold,
                                  color: Colors.white70,
                                  letterSpacing: 1,
                                ),
                              ),
                              const SizedBox(height: 2),
                              Text(
                                activeBooking.tokenDisplay.isNotEmpty
                                    ? activeBooking.tokenDisplay
                                    : '#${activeBooking.tokenNumber}',
                                style: const TextStyle(
                                  fontSize: 28,
                                  fontWeight: FontWeight.w900,
                                  color: Colors.white,
                                ),
                              ),
                            ],
                          ),
                          Container(
                            padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
                            decoration: BoxDecoration(
                              color: Colors.white.withOpacity(0.2),
                              borderRadius: BorderRadius.circular(12),
                            ),
                            child: Column(
                              children: [
                                const Text(
                                  'BOOKING ID',
                                  style: TextStyle(
                                    fontSize: 10,
                                    fontWeight: FontWeight.w600,
                                    color: Colors.white70,
                                  ),
                                ),
                                Text(
                                  activeBooking.bookingId,
                                  style: const TextStyle(
                                    fontSize: 14,
                                    fontWeight: FontWeight.bold,
                                    color: Colors.white,
                                  ),
                                ),
                              ],
                            ),
                          ),
                        ],
                      ),
                    ),

                    // Ticket Notch Divider
                    _buildTicketDivider(),

                    // Booking Details Grid
                    Padding(
                      padding: const EdgeInsets.all(20),
                      child: Column(
                        children: [
                          _buildDetailRow('Centre', activeBooking.centreName, Icons.storefront_rounded),
                          const Divider(height: 20, color: AppColors.cardBorder),
                          _buildDetailRow('Date', activeBooking.date, Icons.calendar_month_rounded),
                          const Divider(height: 20, color: AppColors.cardBorder),
                          _buildDetailRow('Time', activeBooking.timeRange, Icons.access_time_rounded),
                          const Divider(height: 20, color: AppColors.cardBorder),
                          _buildDetailRow('Produce', activeBooking.crop, Icons.grass_rounded),
                          const Divider(height: 20, color: AppColors.cardBorder),
                          _buildDetailRow('Quantity', '${activeBooking.quantityKg.toStringAsFixed(0)} kg', Icons.scale_rounded),
                          const Divider(height: 20, color: AppColors.cardBorder),
                          _buildDetailRow('Estimated Wait', '${activeBooking.waitTimeMinutes > 0 ? activeBooking.waitTimeMinutes : 12} minutes', Icons.timelapse_rounded),
                        ],
                      ),
                    ),

                    // Helpful Hint Footer
                    Container(
                      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
                      decoration: const BoxDecoration(
                        color: AppColors.secondaryContainer,
                        borderRadius: BorderRadius.only(
                          bottomLeft: Radius.circular(20),
                          bottomRight: Radius.circular(20),
                        ),
                      ),
                      child: const Row(
                        children: [
                          Icon(Icons.info_outline, size: 18, color: AppColors.secondaryDark),
                          SizedBox(width: 8),
                          Expanded(
                            child: Text(
                              'Please reach the centre 15 minutes before your slot time.',
                              style: TextStyle(
                                fontSize: 12,
                                fontWeight: FontWeight.w500,
                                color: AppColors.secondaryDark,
                              ),
                            ),
                          ),
                        ],
                      ),
                    ),
                  ],
                ),
              ),
              const SizedBox(height: 28),

              // Action Buttons
              CustomButton(
                text: 'VIEW LIVE QUEUE',
                icon: Icons.groups_rounded,
                variant: ButtonVariant.primary,
                onPressed: () {
                  Navigator.pushReplacementNamed(context, AppRoutes.queue);
                },
              ),
              const SizedBox(height: 12),

              CustomButton(
                text: 'BACK TO HOME',
                icon: Icons.home_rounded,
                variant: ButtonVariant.outlined,
                onPressed: () {
                  Navigator.pushNamedAndRemoveUntil(context, AppRoutes.home, (route) => false);
                },
              ),
              const SizedBox(height: 16),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildDetailRow(String label, String value, IconData icon) {
    return Row(
      children: [
        Icon(icon, size: 18, color: AppColors.textSecondary),
        const SizedBox(width: 10),
        Text(
          label,
          style: const TextStyle(fontSize: 14, color: AppColors.textSecondary),
        ),
        const Spacer(),
        Flexible(
          child: Text(
            value,
            style: const TextStyle(
              fontSize: 14,
              fontWeight: FontWeight.bold,
              color: AppColors.textPrimary,
            ),
            textAlign: TextAlign.end,
            maxLines: 1,
            overflow: TextOverflow.ellipsis,
          ),
        ),
      ],
    );
  }

  Widget _buildTicketDivider() {
    return const SizedBox(
      height: 2,
      width: double.infinity,
      child: CustomPaint(
        painter: _DashedLinePainter(color: AppColors.cardBorder),
      ),
    );
  }
}

class _DashedLinePainter extends CustomPainter {
  final Color color;
  const _DashedLinePainter({required this.color});

  @override
  void paint(Canvas canvas, Size size) {
    const double dashWidth = 6;
    const double dashSpace = 4;
    double startX = 0;
    final paint = Paint()
      ..color = color
      ..strokeWidth = 1.5;
    while (startX < size.width) {
      canvas.drawLine(Offset(startX, 0), Offset(startX + dashWidth, 0), paint);
      startX += dashWidth + dashSpace;
    }
  }

  @override
  bool shouldRepaint(covariant CustomPainter oldDelegate) => false;
}
