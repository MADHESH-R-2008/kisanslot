import 'package:flutter/material.dart';
import '../models/centre.dart';
import '../utils/app_colors.dart';
import '../utils/map_launcher.dart';
import 'custom_button.dart';

class CentreCard extends StatelessWidget {
  final ProcurementCentre centre;
  final VoidCallback onViewSlots;
  final bool isSelected;

  const CentreCard({
    super.key,
    required this.centre,
    required this.onViewSlots,
    this.isSelected = false,
  });

  @override
  Widget build(BuildContext context) {
    final isRec = centre.isRecommended;

    return Container(
      margin: const EdgeInsets.only(bottom: 16),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(18),
        border: Border.all(
          color: isRec
              ? AppColors.secondary
              : (isSelected ? AppColors.primary : AppColors.cardBorder),
          width: isRec || isSelected ? 2 : 1,
        ),
        boxShadow: [
          BoxShadow(
            color: isRec
                ? AppColors.secondary.withOpacity(0.12)
                : Colors.black.withOpacity(0.04),
            blurRadius: 10,
            offset: const Offset(0, 4),
          ),
        ],
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // Header with Recommended Tag if applicable
          if (isRec)
            Container(
              width: double.infinity,
              padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 6),
              decoration: const BoxDecoration(
                color: AppColors.secondaryContainer,
                borderRadius: BorderRadius.only(
                  topLeft: Radius.circular(16),
                  topRight: Radius.circular(16),
                ),
              ),
              child: const Row(
                children: [
                  Icon(Icons.star, size: 16, color: AppColors.secondaryDark),
                  SizedBox(width: 6),
                  Text(
                    '⭐ Recommended (Shortest Queue)',
                    style: TextStyle(
                      fontSize: 12,
                      fontWeight: FontWeight.bold,
                      color: AppColors.secondaryDark,
                    ),
                  ),
                ],
              ),
            ),

          Padding(
            padding: const EdgeInsets.all(18),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                // Title and Status
                Row(
                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                  children: [
                    Expanded(
                      child: Text(
                        centre.name,
                        style: const TextStyle(
                          fontSize: 20,
                          fontWeight: FontWeight.bold,
                          color: AppColors.textPrimary,
                        ),
                      ),
                    ),
                    Container(
                      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
                      decoration: BoxDecoration(
                        color: centre.isOpen
                            ? AppColors.successContainer
                            : AppColors.errorContainer,
                        borderRadius: BorderRadius.circular(20),
                      ),
                      child: Row(
                        mainAxisSize: MainAxisSize.min,
                        children: [
                          Container(
                            width: 8,
                            height: 8,
                            decoration: BoxDecoration(
                              color: centre.isOpen
                                  ? AppColors.success
                                  : AppColors.error,
                              shape: BoxShape.circle,
                            ),
                          ),
                          const SizedBox(width: 6),
                          Text(
                            centre.isOpen ? 'Open' : 'Closed',
                            style: TextStyle(
                              fontSize: 12,
                              fontWeight: FontWeight.bold,
                              color: centre.isOpen
                                  ? AppColors.success
                                  : AppColors.error,
                            ),
                          ),
                        ],
                      ),
                    ),
                  ],
                ),

                const SizedBox(height: 6),
                InkWell(
                  onTap: () {
                    MapLauncher.openGoogleMaps(
                      mapUrl: centre.googleMapUrl,
                      latitude: centre.latitude,
                      longitude: centre.longitude,
                      name: centre.name,
                      address: centre.address,
                      context: context,
                    );
                  },
                  borderRadius: BorderRadius.circular(8),
                  child: Padding(
                    padding: const EdgeInsets.symmetric(vertical: 2),
                    child: Row(
                      children: [
                        const Icon(Icons.location_on_rounded, size: 16, color: AppColors.primary),
                        const SizedBox(width: 4),
                        Expanded(
                          child: Text(
                            centre.address,
                            style: const TextStyle(
                              fontSize: 13,
                              color: AppColors.primary,
                              fontWeight: FontWeight.w500,
                              decoration: TextDecoration.underline,
                            ),
                            maxLines: 1,
                            overflow: TextOverflow.ellipsis,
                          ),
                        ),
                        const SizedBox(width: 4),
                        Container(
                          padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
                          decoration: BoxDecoration(
                            color: AppColors.infoContainer,
                            borderRadius: BorderRadius.circular(6),
                          ),
                          child: const Row(
                            children: [
                              Icon(Icons.directions_outlined, size: 12, color: AppColors.info),
                              SizedBox(width: 2),
                              Text(
                                'Maps ↗',
                                style: TextStyle(
                                  fontSize: 10,
                                  fontWeight: FontWeight.bold,
                                  color: AppColors.info,
                                ),
                              ),
                            ],
                          ),
                        ),
                      ],
                    ),
                  ),
                ),

                const SizedBox(height: 16),

                // Metrics Grid (Distance, Queue, Estimated Wait)
                Container(
                  padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 12),
                  decoration: BoxDecoration(
                    color: AppColors.surfaceVariant,
                    borderRadius: BorderRadius.circular(12),
                  ),
                  child: Row(
                    children: [
                      // Distance
                      Expanded(
                        child: _buildMetricItem(
                          icon: Icons.near_me_outlined,
                          label: 'Distance',
                          value: centre.distanceKm <= 0
                              ? 'Nearby'
                              : (centre.distanceKm < 1.0
                                  ? '${(centre.distanceKm * 1000).toStringAsFixed(0)} m'
                                  : '${centre.distanceKm.toStringAsFixed(1)} km'),
                          color: AppColors.primary,
                        ),
                      ),
                      Container(width: 1, height: 32, color: AppColors.cardBorder),

                      // Queue
                      Expanded(
                        child: _buildMetricItem(
                          icon: Icons.people_outline,
                          label: 'Queue',
                          value: '${centre.queueCount} farmers',
                          color: centre.queueCount < 10
                              ? AppColors.success
                              : (centre.queueCount < 20 ? AppColors.warning : AppColors.error),
                        ),
                      ),
                      Container(width: 1, height: 32, color: AppColors.cardBorder),

                      // Estimated Wait
                      Expanded(
                        child: _buildMetricItem(
                          icon: Icons.timer_outlined,
                          label: 'Est. Wait',
                          value: '${centre.waitMin} min',
                          color: centre.waitMin <= 25 ? AppColors.success : AppColors.warning,
                        ),
                      ),
                    ],
                  ),
                ),

                const SizedBox(height: 16),

                // Action Buttons Row
                Row(
                  children: [
                    OutlinedButton.icon(
                      onPressed: () {
                        MapLauncher.openGoogleMaps(
                          mapUrl: centre.googleMapUrl,
                          latitude: centre.latitude,
                          longitude: centre.longitude,
                          name: centre.name,
                          address: centre.address,
                          context: context,
                        );
                      },
                      icon: const Icon(Icons.map_rounded, size: 16, color: AppColors.primary),
                      label: const Text(
                        'Directions',
                        style: TextStyle(color: AppColors.primary, fontSize: 13, fontWeight: FontWeight.bold),
                      ),
                      style: OutlinedButton.styleFrom(
                        side: const BorderSide(color: AppColors.primary),
                        padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 12),
                        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
                      ),
                    ),
                    const SizedBox(width: 10),
                    Expanded(
                      child: CustomButton(
                        text: 'View Slots',
                        icon: Icons.calendar_month_outlined,
                        variant: isRec ? ButtonVariant.secondary : ButtonVariant.primary,
                        onPressed: onViewSlots,
                      ),
                    ),
                  ],
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildMetricItem({
    required IconData icon,
    required String label,
    required String value,
    required Color color,
  }) {
    return Column(
      children: [
        Icon(icon, size: 18, color: color),
        const SizedBox(height: 4),
        Text(
          label,
          style: const TextStyle(
            fontSize: 11,
            color: AppColors.textSecondary,
          ),
        ),
        const SizedBox(height: 2),
        Text(
          value,
          style: TextStyle(
            fontSize: 13,
            fontWeight: FontWeight.bold,
            color: color,
          ),
        ),
      ],
    );
  }
}
