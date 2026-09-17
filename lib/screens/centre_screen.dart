import 'dart:async';
import 'package:flutter/material.dart';
import 'package:geolocator/geolocator.dart';
import '../models/centre.dart';
import '../services/api_service.dart';
import '../utils/app_colors.dart';
import '../utils/routes.dart';
import '../widgets/centre_card.dart';

class CentreScreen extends StatefulWidget {
  const CentreScreen({super.key});

  @override
  State<CentreScreen> createState() => _CentreScreenState();
}

class _CentreScreenState extends State<CentreScreen> {
  String _selectedFilter = 'All';
  int? _selectedCentreId;

  List<ProcurementCentre> _centres = [];
  bool _isLoading = true;
  String? _error;
  Position? _currentPosition;
  String? _locationStatus;
  bool _gpsLoading = false;

  @override
  void initState() {
    super.initState();
    _loadCentres();
  }

  // ─── GPS: runs FULLY async, never calls setState mid-frame ───────────────
  Future<void> _updateLocationAndDistances() async {
    if (!mounted || _gpsLoading) return;

    // Use microtask to push off any possible in-frame execution
    await Future.microtask(() => null);
    if (!mounted) return;

    _gpsLoading = true;

    try {
      bool serviceEnabled = await Geolocator.isLocationServiceEnabled();
      if (!serviceEnabled) {
        _scheduleSetState(() => _locationStatus = 'Location services disabled.');
        return;
      }

      LocationPermission permission = await Geolocator.checkPermission();
      if (permission == LocationPermission.denied) {
        // requestPermission() shows the SYSTEM dialog — the app loses focus,
        // then regains it. We add a short delay AFTER the await so any
        // in-progress frame caused by the app-resume has completed.
        permission = await Geolocator.requestPermission();
        await Future.delayed(const Duration(milliseconds: 100));
        if (!mounted) return;

        if (permission == LocationPermission.denied) {
          _scheduleSetState(() => _locationStatus = 'Location permission denied.');
          return;
        }
      }

      if (permission == LocationPermission.deniedForever) {
        _scheduleSetState(() => _locationStatus = 'Location permission permanently denied.');
        return;
      }

      Position position;
      try {
        position = await Geolocator.getCurrentPosition(
          locationSettings: const LocationSettings(
            accuracy: LocationAccuracy.medium,
            timeLimit: Duration(seconds: 5),
          ),
        );
      } catch (_) {
        _scheduleSetState(() => _locationStatus = 'GPS unavailable — using default distances.');
        return;
      }

      if (!mounted) return;

      _currentPosition = position;
      final List<ProcurementCentre> updated = _centres.map((centre) {
        if (centre.latitude != null &&
            centre.longitude != null &&
            centre.latitude != 0.0 &&
            centre.longitude != 0.0) {
          try {
            double meters = Geolocator.distanceBetween(
              position.latitude,
              position.longitude,
              centre.latitude!,
              centre.longitude!,
            );
            if (meters.isNaN || meters.isInfinite) return centre;
            double distKm = meters / 1000.0;
            if (distKm.isNaN || distKm.isInfinite) return centre;
            distKm = double.tryParse(distKm.toStringAsFixed(1)) ?? centre.distanceKm;
            return centre.copyWithDistance(distKm);
          } catch (_) {
            return centre;
          }
        }
        return centre;
      }).toList();

      _scheduleSetState(() {
        _centres = updated;
        _locationStatus =
            'GPS: ${position.latitude.toStringAsFixed(3)}, ${position.longitude.toStringAsFixed(3)}';
      });
    } catch (_) {
      _scheduleSetState(() => _locationStatus = 'GPS error — using default distances.');
    } finally {
      _gpsLoading = false;
    }
  }

  /// Safely schedule a setState so it always runs AFTER the current frame.
  void _scheduleSetState(VoidCallback fn) {
    WidgetsBinding.instance.addPostFrameCallback((_) {
      if (mounted) setState(fn);
    });
  }

  Future<void> _loadCentres() async {
    setState(() {
      _isLoading = true;
      _error = null;
      _locationStatus = null;
      _gpsLoading = false;
    });

    try {
      final data = await ApiService.getCentres();
      List<ProcurementCentre> loaded =
          data.map((json) => ProcurementCentre.fromJson(json)).toList();

      if (loaded.isEmpty) loaded = ProcurementCentre.getMockCentres();

      if (!mounted) return;
      setState(() {
        _centres = loaded;
        _isLoading = false;
      });
    } catch (_) {
      if (!mounted) return;
      setState(() {
        _centres = ProcurementCentre.getMockCentres();
        _isLoading = false;
      });
    }

    // Start GPS AFTER the frame that shows the centres completes
    WidgetsBinding.instance.addPostFrameCallback((_) {
      if (mounted) _updateLocationAndDistances();
    });
  }

  List<ProcurementCentre> get _filteredCentres {
    final list = List<ProcurementCentre>.from(_centres);
    try {
      if (_selectedFilter == 'Nearest') {
        list.sort((a, b) {
          final ad = (a.distanceKm.isNaN || a.distanceKm.isInfinite) ? 9999.0 : a.distanceKm;
          final bd = (b.distanceKm.isNaN || b.distanceKm.isInfinite) ? 9999.0 : b.distanceKm;
          return ad.compareTo(bd);
        });
      } else if (_selectedFilter == 'Shortest Queue') {
        list.sort((a, b) => a.queueCount.compareTo(b.queueCount));
      }
    } catch (_) {}
    return list;
  }

  @override
  Widget build(BuildContext context) {
    final filteredCentres = _filteredCentres;

    return Scaffold(
      backgroundColor: AppColors.background,
      appBar: AppBar(
        title: const Text('Select Procurement Centre'),
        leading: IconButton(
          icon: const Icon(Icons.arrow_back_ios_new_rounded),
          onPressed: () => Navigator.pop(context),
        ),
      ),
      body: _isLoading
          ? const Center(
              child: Column(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  CircularProgressIndicator(color: AppColors.primary),
                  SizedBox(height: 16),
                  Text(
                    'Loading centres...',
                    style: TextStyle(color: AppColors.textSecondary),
                  ),
                ],
              ),
            )
          : RefreshIndicator(
              onRefresh: _loadCentres,
              color: AppColors.primary,
              child: ListView(
                padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 12),
                children: [
                  // ── Location banner ─────────────────────────────────────
                  _buildLocationBanner(),
                  const SizedBox(height: 8),

                  // ── Filter chips ─────────────────────────────────────────
                  Wrap(
                    spacing: 8,
                    runSpacing: 8,
                    children: [
                      _buildFilterChip('All'),
                      _buildFilterChip('Nearest'),
                      _buildFilterChip('Shortest Queue'),
                    ],
                  ),
                  const SizedBox(height: 12),

                  // ── Count header ─────────────────────────────────────────
                  Row(
                    mainAxisAlignment: MainAxisAlignment.spaceBetween,
                    children: [
                      Flexible(
                        child: Text(
                          'Available Centres (${filteredCentres.length})',
                          style: const TextStyle(
                            fontSize: 16,
                            fontWeight: FontWeight.bold,
                            color: AppColors.textPrimary,
                          ),
                          maxLines: 1,
                          overflow: TextOverflow.ellipsis,
                        ),
                      ),
                      if (_gpsLoading)
                        const SizedBox(
                          width: 14,
                          height: 14,
                          child: CircularProgressIndicator(
                            strokeWidth: 2,
                            color: AppColors.primary,
                          ),
                        )
                      else
                        const Text(
                          'Real-time Queue',
                          style: TextStyle(
                            fontSize: 12,
                            fontWeight: FontWeight.w600,
                            color: AppColors.primary,
                          ),
                        ),
                    ],
                  ),
                  const SizedBox(height: 12),

                  // ── Centres list ─────────────────────────────────────────
                  if (filteredCentres.isEmpty)
                    const Padding(
                      padding: EdgeInsets.all(32),
                      child: Center(
                        child: Text(
                          'No centres available.',
                          style: TextStyle(color: AppColors.textSecondary),
                        ),
                      ),
                    )
                  else
                    ...filteredCentres.map(
                      (centre) => CentreCard(
                        key: ValueKey(centre.id),
                        centre: centre,
                        isSelected: _selectedCentreId == centre.id,
                        onViewSlots: () {
                          Navigator.pushNamed(
                            context,
                            AppRoutes.slotBooking,
                            arguments: centre,
                          );
                        },
                      ),
                    ),

                  const SizedBox(height: 20),
                ],
              ),
            ),
    );
  }

  Widget _buildLocationBanner() {
    if (_locationStatus == null && !_gpsLoading) return const SizedBox.shrink();

    final bool hasGps = _currentPosition != null;
    final Color bgColor = hasGps ? Colors.green.shade50 : Colors.amber.shade50;
    final Color borderColor = hasGps ? Colors.green.shade200 : Colors.amber.shade200;
    final Color iconColor = hasGps ? Colors.green.shade700 : Colors.amber.shade800;
    final Color textColor = hasGps ? Colors.green.shade900 : Colors.amber.shade900;
    final IconData iconData =
        hasGps ? Icons.my_location_rounded : Icons.location_searching_rounded;

    return Container(
      margin: const EdgeInsets.only(bottom: 4),
      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
      decoration: BoxDecoration(
        color: bgColor,
        borderRadius: BorderRadius.circular(8),
        border: Border.all(color: borderColor),
      ),
      child: Row(
        children: [
          if (_gpsLoading && _locationStatus == null)
            SizedBox(
              width: 14,
              height: 14,
              child: CircularProgressIndicator(strokeWidth: 2, color: iconColor),
            )
          else
            Icon(iconData, size: 14, color: iconColor),
          const SizedBox(width: 8),
          Expanded(
            child: Text(
              _locationStatus ?? 'Getting GPS location...',
              style: TextStyle(fontSize: 11, color: textColor, fontWeight: FontWeight.w500),
            ),
          ),
          GestureDetector(
            onTap: _loadCentres,
            child: Icon(Icons.refresh_rounded, size: 14, color: iconColor),
          ),
        ],
      ),
    );
  }

  Widget _buildFilterChip(String label) {
    final bool isSelected = _selectedFilter == label;
    return ChoiceChip(
      label: Text(label),
      selected: isSelected,
      onSelected: (val) {
        if (val) setState(() => _selectedFilter = label);
      },
      selectedColor: AppColors.primaryContainer,
      backgroundColor: Colors.white,
      side: BorderSide(
        color: isSelected ? AppColors.primary : AppColors.cardBorder,
      ),
      labelStyle: TextStyle(
        fontSize: 12,
        fontWeight: isSelected ? FontWeight.bold : FontWeight.w500,
        color: isSelected ? AppColors.primaryDark : AppColors.textSecondary,
      ),
    );
  }
}
