import 'package:flutter/material.dart';
import '../utils/app_colors.dart';
import '../models/centre.dart';

class MapPlaceholderWidget extends StatelessWidget {
  final List<ProcurementCentre> centres;
  final String? selectedCentreId;
  final Function(ProcurementCentre)? onSelectCentre;

  const MapPlaceholderWidget({
    super.key,
    required this.centres,
    this.selectedCentreId,
    this.onSelectCentre,
  });

  @override
  Widget build(BuildContext context) {
    return Container(
      height: 180,
      width: double.infinity,
      decoration: BoxDecoration(
        color: const Color(0xFFE8ECE5),
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: AppColors.cardBorder),
        boxShadow: [
          BoxShadow(
            color: Colors.black.withValues(alpha: 0.04),
            blurRadius: 10,
            offset: const Offset(0, 4),
          ),
        ],
      ),
      child: ClipRRect(
        borderRadius: BorderRadius.circular(16),
        child: Stack(
          children: [
            // Stylized Map Grid & Roads
            CustomPaint(
              size: const Size(double.infinity, 180),
              painter: _MapGridPainter(),
            ),

            // Farmer GPS Pin
            Positioned(
              left: 40,
              top: 75,
              child: Column(
                children: [
                  Container(
                    padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                    decoration: BoxDecoration(
                      color: AppColors.primaryDark,
                      borderRadius: BorderRadius.circular(8),
                    ),
                    child: const Row(
                      mainAxisSize: MainAxisSize.min,
                      children: [
                        Icon(Icons.person_pin_circle, color: Colors.white, size: 14),
                        SizedBox(width: 4),
                        Text(
                          'You (Ravi)',
                          style: TextStyle(color: Colors.white, fontSize: 10, fontWeight: FontWeight.bold),
                        ),
                      ],
                    ),
                  ),
                  const Icon(Icons.location_on, color: AppColors.primaryDark, size: 26),
                ],
              ),
            ),

            // Centre Pins
            if (centres.isNotEmpty) ...[
              // Centre A Pin
              Positioned(
                left: 140,
                top: 40,
                child: _buildCentrePin(
                  context,
                  centres[0],
                  isSelected: selectedCentreId == centres[0].id,
                ),
              ),

              // Centre B Pin (Recommended)
              if (centres.length > 1)
                Positioned(
                  right: 50,
                  top: 55,
                  child: _buildCentrePin(
                    context,
                    centres[1],
                    isSelected: selectedCentreId == centres[1].id,
                  ),
                ),

              // Centre C Pin
              if (centres.length > 2)
                Positioned(
                  right: 130,
                  bottom: 25,
                  child: _buildCentrePin(
                    context,
                    centres[2],
                    isSelected: selectedCentreId == centres[2].id,
                  ),
                ),
            ],

            // Top-right Map Controls badge
            Positioned(
              top: 10,
              right: 10,
              child: Container(
                padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 5),
                decoration: BoxDecoration(
                  color: Colors.white.withValues(alpha: 0.92),
                  borderRadius: BorderRadius.circular(20),
                  boxShadow: [
                    BoxShadow(color: Colors.black.withValues(alpha: 0.08), blurRadius: 4),
                  ],
                ),
                child: const Row(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    Icon(Icons.layers_outlined, size: 14, color: AppColors.primary),
                    SizedBox(width: 4),
                    Text(
                      'APMC Radar',
                      style: TextStyle(
                        fontSize: 11,
                        fontWeight: FontWeight.w600,
                        color: AppColors.textPrimary,
                      ),
                    ),
                  ],
                ),
              ),
            ),

            // Bottom distance scale
            Positioned(
              left: 12,
              bottom: 8,
              child: Container(
                padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
                decoration: BoxDecoration(
                  color: Colors.white.withValues(alpha: 0.85),
                  borderRadius: BorderRadius.circular(6),
                ),
                child: const Text(
                  'Radius: 10 km',
                  style: TextStyle(fontSize: 10, fontWeight: FontWeight.w600, color: AppColors.textSecondary),
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildCentrePin(BuildContext context, ProcurementCentre centre, {required bool isSelected}) {
    final isRec = centre.isRecommended;

    return GestureDetector(
      onTap: () => onSelectCentre?.call(centre),
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 3),
            decoration: BoxDecoration(
              color: isRec ? AppColors.secondary : (isSelected ? AppColors.primary : Colors.white),
              borderRadius: BorderRadius.circular(6),
              border: Border.all(
                color: isRec ? AppColors.secondaryDark : AppColors.primary,
                width: 1.2,
              ),
              boxShadow: [
                BoxShadow(
                  color: Colors.black.withValues(alpha: 0.12),
                  blurRadius: 4,
                  offset: const Offset(0, 2),
                ),
              ],
            ),
            child: Text(
              isRec ? '⭐ ${centre.name}' : centre.name,
              style: TextStyle(
                fontSize: 10,
                fontWeight: FontWeight.bold,
                color: (isRec || isSelected) ? Colors.white : AppColors.textPrimary,
              ),
            ),
          ),
          Icon(
            Icons.location_on,
            color: isRec ? AppColors.secondary : (isSelected ? AppColors.primary : AppColors.primaryLight),
            size: 24,
          ),
        ],
      ),
    );
  }
}

class _MapGridPainter extends CustomPainter {
  @override
  void paint(Canvas canvas, Size size) {
    final roadPaint = Paint()
      ..color = const Color(0xFFD3DCD0)
      ..strokeWidth = 3
      ..style = PaintingStyle.stroke;

    final highwayPaint = Paint()
      ..color = const Color(0xFFFED7AA).withValues(alpha: 0.7)
      ..strokeWidth = 5
      ..style = PaintingStyle.stroke;

    final path1 = Path()
      ..moveTo(0, size.height * 0.45)
      ..cubicTo(size.width * 0.3, size.height * 0.4, size.width * 0.6, size.height * 0.8, size.width, size.height * 0.6);

    final path2 = Path()
      ..moveTo(size.width * 0.25, 0)
      ..cubicTo(size.width * 0.35, size.height * 0.5, size.width * 0.7, size.height * 0.5, size.width * 0.85, size.height);

    canvas.drawPath(path1, highwayPaint);
    canvas.drawPath(path2, roadPaint);

    final greenZone = Paint()
      ..color = const Color(0xFFC8E6C9).withValues(alpha: 0.35)
      ..style = PaintingStyle.fill;

    canvas.drawCircle(Offset(size.width * 0.75, size.height * 0.3), 35, greenZone);
    canvas.drawCircle(Offset(size.width * 0.2, size.height * 0.75), 45, greenZone);
  }

  @override
  bool shouldRepaint(covariant CustomPainter oldDelegate) => false;
}
