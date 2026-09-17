import 'package:flutter/material.dart';
import '../utils/app_colors.dart';

enum TimelineStepStatus { completed, current, pending }

class TimelineStepData {
  final String title;
  final String description;
  final String? time;
  final TimelineStepStatus state;
  final IconData icon;

  const TimelineStepData({
    required this.title,
    required this.description,
    this.time,
    required this.state,
    required this.icon,
  });
}

class StatusTimelineCard extends StatelessWidget {
  final String title;
  final List<TimelineStepData> steps;

  const StatusTimelineCard({
    super.key,
    required this.title,
    required this.steps,
  });

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(20),
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
          Row(
            children: [
              const Icon(Icons.timeline_rounded, color: AppColors.primary, size: 22),
              const SizedBox(width: 8),
              Text(
                title,
                style: const TextStyle(
                  fontSize: 16,
                  fontWeight: FontWeight.bold,
                  color: AppColors.textPrimary,
                ),
              ),
            ],
          ),
          const SizedBox(height: 16),
          Column(
            children: steps.asMap().entries.map((entry) {
              final index = entry.key;
              final step = entry.value;
              final isLast = index == steps.length - 1;

              return IntrinsicHeight(
                child: Row(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    // Timeline Icon and vertical line
                    Column(
                      children: [
                        _buildStepCircle(step.state, step.icon),
                        if (!isLast)
                          Expanded(
                            child: Container(
                              width: 2,
                              margin: const EdgeInsets.symmetric(vertical: 4),
                              color: step.state == TimelineStepStatus.completed
                                  ? AppColors.success
                                  : (step.state == TimelineStepStatus.current
                                      ? AppColors.warning
                                      : AppColors.cardBorder),
                            ),
                          ),
                      ],
                    ),
                    const SizedBox(width: 14),

                    // Step Info
                    Expanded(
                      child: Padding(
                        padding: EdgeInsets.only(bottom: isLast ? 0 : 20),
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Row(
                              mainAxisAlignment: MainAxisAlignment.spaceBetween,
                              children: [
                                Expanded(
                                  child: Text(
                                    step.title,
                                    style: TextStyle(
                                      fontSize: 15,
                                      fontWeight: step.state == TimelineStepStatus.current
                                          ? FontWeight.bold
                                          : FontWeight.w600,
                                      color: step.state == TimelineStepStatus.pending
                                          ? AppColors.textMuted
                                          : AppColors.textPrimary,
                                    ),
                                  ),
                                ),
                                if (step.time != null)
                                  Text(
                                    step.time!,
                                    style: const TextStyle(
                                      fontSize: 11,
                                      color: AppColors.textSecondary,
                                    ),
                                  ),
                              ],
                            ),
                            const SizedBox(height: 3),
                            Text(
                              step.description,
                              style: TextStyle(
                                fontSize: 13,
                                color: step.state == TimelineStepStatus.pending
                                    ? AppColors.textMuted
                                    : AppColors.textSecondary,
                              ),
                            ),
                          ],
                        ),
                      ),
                    ),
                  ],
                ),
              );
            }).toList(),
          ),
        ],
      ),
    );
  }

  Widget _buildStepCircle(TimelineStepStatus state, IconData icon) {
    switch (state) {
      case TimelineStepStatus.completed:
        return Container(
          width: 28,
          height: 28,
          decoration: const BoxDecoration(
            color: AppColors.success,
            shape: BoxShape.circle,
          ),
          child: const Icon(Icons.check, size: 16, color: Colors.white),
        );
      case TimelineStepStatus.current:
        return Container(
          width: 28,
          height: 28,
          decoration: BoxDecoration(
            color: AppColors.warningContainer,
            shape: BoxShape.circle,
            border: Border.all(color: AppColors.warning, width: 2),
          ),
          child: const Icon(Icons.sync, size: 16, color: AppColors.warning),
        );
      case TimelineStepStatus.pending:
        return Container(
          width: 28,
          height: 28,
          decoration: BoxDecoration(
            color: AppColors.surfaceVariant,
            shape: BoxShape.circle,
            border: Border.all(color: AppColors.cardBorder, width: 1.5),
          ),
          child: Icon(icon, size: 14, color: AppColors.textMuted),
        );
    }
  }
}

class ProduceSummaryCard extends StatelessWidget {
  final String crop;
  final double expectedQuantity;
  final String actualWeightText;
  final double ratePerKg;
  final double? totalAmount;

  const ProduceSummaryCard({
    super.key,
    required this.crop,
    required this.expectedQuantity,
    required this.actualWeightText,
    required this.ratePerKg,
    this.totalAmount,
  });

  @override
  Widget build(BuildContext context) {
    final double calculatedTotal = totalAmount ?? (expectedQuantity * ratePerKg);

    return Container(
      padding: const EdgeInsets.all(20),
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
              Icon(Icons.agriculture_rounded, color: AppColors.primary, size: 22),
              SizedBox(width: 8),
              Text(
                'Produce & Valuation Summary',
                style: TextStyle(
                  fontSize: 16,
                  fontWeight: FontWeight.bold,
                  color: AppColors.textPrimary,
                ),
              ),
            ],
          ),
          const SizedBox(height: 16),
          _buildRow('Crop', crop, icon: Icons.grass),
          const Divider(height: 20, color: AppColors.cardBorder),
          _buildRow('Expected Quantity', '${expectedQuantity.toStringAsFixed(0)} kg', icon: Icons.inventory_2_outlined),
          const Divider(height: 20, color: AppColors.cardBorder),
          _buildRow('Actual Weight', actualWeightText, icon: Icons.scale_outlined, isHighlighted: true),
          const Divider(height: 20, color: AppColors.cardBorder),
          _buildRow('Government Rate', '₹${ratePerKg.toStringAsFixed(2)} / kg', icon: Icons.sell_outlined),
          const Divider(height: 20, color: AppColors.cardBorder),
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 12),
            decoration: BoxDecoration(
              color: AppColors.primaryContainer,
              borderRadius: BorderRadius.circular(12),
            ),
            child: Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                const Text(
                  'Estimated Value',
                  style: TextStyle(
                    fontSize: 15,
                    fontWeight: FontWeight.bold,
                    color: AppColors.primaryDark,
                  ),
                ),
                Text(
                  '₹${calculatedTotal.toStringAsFixed(0).replaceAllMapped(RegExp(r'(\d{1,3})(?=(\d{3})+(?!\d))'), (Match m) => '${m[1]},')}',
                  style: const TextStyle(
                    fontSize: 18,
                    fontWeight: FontWeight.w900,
                    color: AppColors.primaryDark,
                  ),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildRow(String label, String value, {required IconData icon, bool isHighlighted = false}) {
    return Row(
      children: [
        Icon(icon, size: 18, color: AppColors.textSecondary),
        const SizedBox(width: 8),
        Text(
          label,
          style: const TextStyle(fontSize: 14, color: AppColors.textSecondary),
        ),
        const Spacer(),
        Text(
          value,
          style: TextStyle(
            fontSize: 14,
            fontWeight: FontWeight.bold,
            color: isHighlighted ? AppColors.warning : AppColors.textPrimary,
          ),
        ),
      ],
    );
  }
}
