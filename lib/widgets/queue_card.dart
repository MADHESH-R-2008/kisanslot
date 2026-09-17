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
    if (booking.status == BookingStatus.completed) {
      return _buildCompletedCard();
    } else if (booking.status == BookingStatus.skipped || booking.status == BookingStatus.noShow) {
      return _buildSkippedCard();
    } else if (booking.status == BookingStatus.called) {
      return _buildCalledCard();
    } else if (booking.status == BookingStatus.serving || booking.status == BookingStatus.procuring || booking.status == BookingStatus.atCounter) {
      return _buildServingCard();
    }

    return _buildWaitingCard();
  }

  Widget _buildBaseCard({required Gradient gradient, required List<Widget> children}) {
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
          Container(
            width: double.infinity,
            padding: const EdgeInsets.all(24),
            decoration: BoxDecoration(
              gradient: gradient,
              borderRadius: const BorderRadius.only(
                topLeft: Radius.circular(20),
                topRight: Radius.circular(20),
              ),
            ),
            child: Column(
              children: children,
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildTokenDisplay() {
    return Text(
      booking.tokenDisplay.isNotEmpty ? booking.tokenDisplay : '#${booking.tokenNumber}',
      style: const TextStyle(
        color: Colors.white,
        fontSize: 48,
        fontWeight: FontWeight.w900,
        letterSpacing: -0.5,
      ),
    );
  }

  Widget _buildBookingIdPill() {
    return Container(
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
      ),
    );
  }

  Widget _buildCalledCard() {
    return _buildBaseCard(
      gradient: const LinearGradient(colors: [Color(0xFF8B5CF6), Color(0xFF6D28D9)]), // Purple for called
      children: [
        _buildBookingIdPill(),
        const SizedBox(height: 16),
        const Icon(Icons.campaign_rounded, color: Colors.white, size: 48),
        const SizedBox(height: 8),
        const Text(
          'YOUR TOKEN IS CALLED!',
          style: TextStyle(color: Colors.white70, fontSize: 13, fontWeight: FontWeight.w700, letterSpacing: 1.2),
        ),
        _buildTokenDisplay(),
        const SizedBox(height: 12),
        Container(
          padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
          decoration: BoxDecoration(
            color: Colors.white,
            borderRadius: BorderRadius.circular(50),
          ),
          child: Text(
            'Proceed to ${booking.assignedCounterName ?? 'Counter'}',
            style: const TextStyle(color: Color(0xFF6D28D9), fontWeight: FontWeight.bold, fontSize: 16),
          ),
        ),
      ],
    );
  }

  Widget _buildServingCard() {
    return _buildBaseCard(
      gradient: const LinearGradient(colors: [Color(0xFF10B981), Color(0xFF047857)]), // Emerald for serving
      children: [
        _buildBookingIdPill(),
        const SizedBox(height: 16),
        const Icon(Icons.sync_rounded, color: Colors.white, size: 48),
        const SizedBox(height: 8),
        const Text(
          'CURRENTLY SERVING',
          style: TextStyle(color: Colors.white70, fontSize: 13, fontWeight: FontWeight.w700, letterSpacing: 1.2),
        ),
        _buildTokenDisplay(),
        const SizedBox(height: 12),
        Text(
          'At ${booking.assignedCounterName ?? 'Counter'}',
          style: const TextStyle(color: Colors.white, fontWeight: FontWeight.w600, fontSize: 16),
        ),
      ],
    );
  }

  Widget _buildSkippedCard() {
    return _buildBaseCard(
      gradient: const LinearGradient(colors: [Color(0xFFF97316), Color(0xFFC2410C)]), // Orange for skipped
      children: [
        _buildBookingIdPill(),
        const SizedBox(height: 16),
        const Icon(Icons.warning_rounded, color: Colors.white, size: 48),
        const SizedBox(height: 8),
        const Text(
          'TOKEN SKIPPED',
          style: TextStyle(color: Colors.white70, fontSize: 13, fontWeight: FontWeight.w700, letterSpacing: 1.2),
        ),
        _buildTokenDisplay(),
        const SizedBox(height: 12),
        const Text(
          'You missed your turn. Please contact the centre desk.',
          style: TextStyle(color: Colors.white, fontWeight: FontWeight.w500, fontSize: 14),
          textAlign: TextAlign.center,
        ),
      ],
    );
  }

  Widget _buildCompletedCard() {
    return _buildBaseCard(
      gradient: const LinearGradient(colors: [Color(0xFF3B82F6), Color(0xFF1D4ED8)]), // Blue for completed
      children: [
        _buildBookingIdPill(),
        const SizedBox(height: 16),
        const Icon(Icons.check_circle_rounded, color: Colors.white, size: 48),
        const SizedBox(height: 8),
        const Text(
          'PROCUREMENT COMPLETED',
          style: TextStyle(color: Colors.white70, fontSize: 13, fontWeight: FontWeight.w700, letterSpacing: 1.2),
        ),
        _buildTokenDisplay(),
      ],
    );
  }

  Widget _buildWaitingCard() {
    final int currentPos = booking.queuePosition;
    final bool isYourTurn = currentPos <= 1;
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
                      child: _buildBookingIdPill(),
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
                  isYourTurn ? 'NEXT 🎉' : '#$currentPos',
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
                      ? 'Please wait for your token ${booking.tokenDisplay.isNotEmpty ? booking.tokenDisplay : '#${booking.tokenNumber}'} to be called'
                      : 'Token ${booking.tokenDisplay.isNotEmpty ? booking.tokenDisplay : '#${booking.tokenNumber}'} • ${booking.centreName}',
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
                // Metrics Grid (Current Token, Farmers Ahead, Wait Time, Counter)
                Row(
                  children: [
                    Expanded(
                      child: _buildQueueStatBox(
                        title: 'Current Token',
                        value: booking.currentServingToken ?? 'None',
                        icon: Icons.campaign_outlined,
                        color: AppColors.secondaryDark,
                      ),
                    ),
                    const SizedBox(width: 8),
                    Expanded(
                      child: _buildQueueStatBox(
                        title: 'Farmers Ahead',
                        value: '${booking.farmersAhead}',
                        icon: Icons.groups_outlined,
                        color: AppColors.primary,
                      ),
                    ),
                  ],
                ),
                const SizedBox(height: 10),
                Row(
                  children: [
                    Expanded(
                      child: _buildQueueStatBox(
                        title: 'Est. Wait',
                        value: '${booking.waitTimeMinutes} min',
                        icon: Icons.timelapse_outlined,
                        color: AppColors.secondary,
                      ),
                    ),
                    const SizedBox(width: 8),
                    Expanded(
                      child: _buildQueueStatBox(
                        title: 'Active Counters',
                        value: '${booking.counterNumber}',
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
