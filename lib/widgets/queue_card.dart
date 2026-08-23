import 'package:flutter/material.dart';
import '../models/booking.dart';
import '../utils/app_colors.dart';

class QueueCard extends StatelessWidget {
  final BookingModel booking;
  final VoidCallback onRefresh;

  const QueueCard({
    super.key,
    required this.booking,
    required this.onRefresh,
  });

  @override
  Widget build(BuildContext context) {
    final int currentPos = booking.queuePosition;
    final bool isYourTurn = currentPos <= 1;

    // Queue milestones for visual step progress
    final milestones = [17, 12, 8, 5, 2, 1];

    return Container(
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(20),
        border: Border.all(color: AppColors.cardBorder),
        boxShadow: [
          BoxShadow(
            color: AppColors.primary.withValues(alpha: 0.08),
            blurRadius: 16,
            offset: const Offset(0, 6),
          ),
        ],
      ),
      child: Column(
        children: [
          // Hero Token Header
          Container(
            padding: const EdgeInsets.all(20),
            decoration: BoxDecoration(
              gradient: isYourTurn ? AppColors.harvestGradient : AppColors.primaryGradient,
              borderRadius: const BorderRadius.only(
                topLeft: Radius.circular(20),
                topRight: Radius.circular(20),
              ),
            ),
            child: Column(
              children: [
                Row(
                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                  children: [
                    Flexible(
                      child: Container(
                        padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
                        decoration: BoxDecoration(
                          color: Colors.white.withValues(alpha: 0.2),
                          borderRadius: BorderRadius.circular(20),
                        ),
                        child: Text(
                          'Booking: ${booking.bookingId}',
                          style: const TextStyle(
                            color: Colors.white,
                            fontSize: 12,
                            fontWeight: FontWeight.w600,
                          ),
                          maxLines: 1,
                          overflow: TextOverflow.ellipsis,
                        ),
                      ),
                    ),
                    const SizedBox(width: 8),
                    Container(
                      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
                      decoration: BoxDecoration(
                        color: Colors.white.withValues(alpha: 0.2),
                        borderRadius: BorderRadius.circular(20),
                      ),
                      child: Row(
                        mainAxisSize: MainAxisSize.min,
                        children: [
                          Container(
                            width: 8,
                            height: 8,
                            decoration: const BoxDecoration(
                              color: AppColors.success,
                              shape: BoxShape.circle,
                            ),
                          ),
                          const SizedBox(width: 6),
                          const Text(
                            'Live',
                            style: TextStyle(
                              color: AppColors.primaryDark,
                              fontSize: 12,
                              fontWeight: FontWeight.bold,
                            ),
                          ),
                        ],
                      ),
                    ),
                  ],
                ),
                const SizedBox(height: 16),
                const Text(
                  'YOUR QUEUE POSITION',
                  style: TextStyle(
                    color: Colors.white70,
                    fontSize: 13,
                    fontWeight: FontWeight.w600,
                    letterSpacing: 1.2,
                  ),
                ),
                const SizedBox(height: 6),
                Text(
                  isYourTurn ? 'YOUR TURN 🎉' : '#$currentPos',
                  style: TextStyle(
                    color: Colors.white,
                    fontSize: isYourTurn ? 34 : 48,
                    fontWeight: FontWeight.w900,
                    letterSpacing: -0.5,
                  ),
                ),
                const SizedBox(height: 6),
                Text(
                  isYourTurn
                      ? 'Please proceed directly to Counter ${booking.counterNumber}'
                      : 'Token #${booking.tokenNumber} • ${booking.centreName}',
                  style: const TextStyle(
                    color: Colors.white,
                    fontSize: 14,
                    fontWeight: FontWeight.w500,
                  ),
                  textAlign: TextAlign.center,
                  maxLines: 2,
                  overflow: TextOverflow.ellipsis,
                ),
              ],
            ),
          ),

          Padding(
            padding: const EdgeInsets.all(20),
            child: Column(
              children: [
                // Metrics Row (Farmers Ahead, Wait Time, Counter)
                Row(
                  children: [
                    Expanded(
                      child: _buildQueueStatBox(
                        title: 'Farmers Ahead',
                        value: '${booking.farmersAhead}',
                        icon: Icons.groups_outlined,
                        color: AppColors.primary,
                      ),
                    ),
                    const SizedBox(width: 10),
                    Expanded(
                      child: _buildQueueStatBox(
                        title: 'Est. Wait Time',
                        value: '${booking.waitTimeMinutes} min',
                        icon: Icons.timelapse_outlined,
                        color: AppColors.secondary,
                      ),
                    ),
                    const SizedBox(width: 10),
                    Expanded(
                      child: _buildQueueStatBox(
                        title: 'Counter',
                        value: '#${booking.counterNumber}',
                        icon: Icons.desktop_windows_outlined,
                        color: AppColors.info,
                      ),
                    ),
                  ],
                ),

                const SizedBox(height: 24),

                // Visual Step Progression Tracker
                const Align(
                  alignment: Alignment.centerLeft,
                  child: Text(
                    'Queue Step Progression',
                    style: TextStyle(
                      fontSize: 14,
                      fontWeight: FontWeight.bold,
                      color: AppColors.textPrimary,
                    ),
                  ),
                ),
                const SizedBox(height: 14),

                Container(
                  padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 16),
                  decoration: BoxDecoration(
                    color: AppColors.surfaceVariant,
                    borderRadius: BorderRadius.circular(14),
                  ),
                  child: Column(
                    children: [
                      for (int i = 0; i < milestones.length; i++) ...[
                        _buildStepItem(
                          stepNumber: milestones[i],
                          isLast: i == milestones.length - 1,
                          isReached: currentPos <= milestones[i],
                          isCurrent: (i == milestones.length - 1 && currentPos <= 1) ||
                              (currentPos <= milestones[i] && (i == milestones.length - 1 || currentPos > milestones[i + 1])),
                        ),
                        if (i < milestones.length - 1)
                          Padding(
                            padding: const EdgeInsets.symmetric(vertical: 4),
                            child: Icon(
                              Icons.arrow_downward_rounded,
                              size: 18,
                              color: currentPos <= milestones[i + 1]
                                  ? AppColors.primary
                                  : AppColors.textMuted.withValues(alpha: 0.5),
                            ),
                          ),
                      ],
                    ],
                  ),
                ),

                const SizedBox(height: 20),

                // Centre Status Strip
                Container(
                  padding: const EdgeInsets.all(12),
                  decoration: BoxDecoration(
                    color: AppColors.successContainer.withValues(alpha: 0.5),
                    borderRadius: BorderRadius.circular(12),
                    border: Border.all(color: AppColors.success.withValues(alpha: 0.2)),
                  ),
                  child: const Row(
                    mainAxisAlignment: MainAxisAlignment.spaceAround,
                    children: [
                      Row(
                        children: [
                          Icon(Icons.check_circle, size: 16, color: AppColors.success),
                          SizedBox(width: 6),
                          Text(
                            'Centre Open',
                            style: TextStyle(
                              fontSize: 12,
                              fontWeight: FontWeight.bold,
                              color: AppColors.success,
                            ),
                          ),
                        ],
                      ),
                      Row(
                        children: [
                          Icon(Icons.speed, size: 16, color: AppColors.warning),
                          SizedBox(width: 6),
                          Text(
                            'Moderate Waiting',
                            style: TextStyle(
                              fontSize: 12,
                              fontWeight: FontWeight.bold,
                              color: AppColors.warning,
                            ),
                          ),
                        ],
                      ),
                    ],
                  ),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildQueueStatBox({
    required String title,
    required String value,
    required IconData icon,
    required Color color,
  }) {
    return Container(
      padding: const EdgeInsets.symmetric(vertical: 12, horizontal: 8),
      decoration: BoxDecoration(
        color: color.withValues(alpha: 0.08),
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: color.withValues(alpha: 0.2)),
      ),
      child: Column(
        children: [
          Icon(icon, size: 20, color: color),
          const SizedBox(height: 6),
          Text(
            title,
            style: const TextStyle(fontSize: 11, color: AppColors.textSecondary),
            textAlign: TextAlign.center,
          ),
          const SizedBox(height: 4),
          Text(
            value,
            style: TextStyle(
              fontSize: 15,
              fontWeight: FontWeight.bold,
              color: color,
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildStepItem({
    required int stepNumber,
    required bool isLast,
    required bool isReached,
    required bool isCurrent,
  }) {
    final String label = isLast ? 'YOUR TURN' : 'Position #$stepNumber';
    final Color bgColor = isCurrent
        ? AppColors.primary
        : (isReached ? AppColors.primaryContainer : Colors.white);
    final Color textColor = isCurrent
        ? Colors.white
        : (isReached ? AppColors.primaryDark : AppColors.textMuted);

    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
      decoration: BoxDecoration(
        color: bgColor,
        borderRadius: BorderRadius.circular(10),
        border: Border.all(
          color: isCurrent
              ? AppColors.primaryDark
              : (isReached ? AppColors.primaryLight : AppColors.cardBorder),
          width: isCurrent ? 2 : 1,
        ),
      ),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        children: [
          Row(
            children: [
              Icon(
                isLast
                    ? Icons.celebration
                    : (isReached ? Icons.check_circle : Icons.radio_button_unchecked),
                size: 18,
                color: textColor,
              ),
              const SizedBox(width: 10),
              Text(
                label,
                style: TextStyle(
                  fontSize: 13,
                  fontWeight: isCurrent ? FontWeight.bold : FontWeight.w600,
                  color: textColor,
                ),
              ),
            ],
          ),
          if (isCurrent)
            Container(
              padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 2),
              decoration: BoxDecoration(
                color: Colors.white.withValues(alpha: 0.25),
                borderRadius: BorderRadius.circular(6),
              ),
              child: const Text(
                'CURRENT',
                style: TextStyle(
                  fontSize: 10,
                  fontWeight: FontWeight.bold,
                  color: Colors.white,
                ),
              ),
            ),
        ],
      ),
    );
  }
}
