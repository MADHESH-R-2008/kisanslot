import 'dart:async';
import 'package:flutter/material.dart';
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

  @override
  void initState() {
    super.initState();
    _loadCentres(showLoading: true);
  }

  Future<void> _loadCentres({bool showLoading = true}) async {
    if (showLoading && mounted) {
      setState(() {
        _isLoading = true;
        _error = null;
      });
    } else if (showLoading) {
      _isLoading = true;
      _error = null;
    }

    try {
      final data = await ApiService.getCentres();
      final loaded = data.whereType<Map>().map((json) {
        return ProcurementCentre.fromJson(Map<String, dynamic>.from(json));
      }).toList();

      if (!mounted) return;
      setState(() {
        _centres = loaded;
        _isLoading = false;
      });
    } catch (_) {
      if (!mounted) return;
      setState(() {
        _centres = [];
        _isLoading = false;
        _error = 'Unable to load procurement centres. Please try again.';
      });
    }

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
            : _error != null
            ? _buildErrorState()
          : RefreshIndicator(
              onRefresh: _loadCentres,
              color: AppColors.primary,
              child: ListView(
                padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 12),
                children: [
                  // ── Location banner ─────────────────────────────────────
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

  Widget _buildErrorState() {
    final error = _error;
    if (error == null) return const SizedBox.shrink();

    return Center(
      child: Padding(
        padding: const EdgeInsets.all(24),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            const Icon(Icons.cloud_off_rounded, size: 52, color: AppColors.textMuted),
            const SizedBox(height: 12),
            Text(
              error,
              textAlign: TextAlign.center,
              style: const TextStyle(color: AppColors.textSecondary),
            ),
            const SizedBox(height: 16),
            ElevatedButton.icon(
              onPressed: _loadCentres,
              icon: const Icon(Icons.refresh_rounded),
              label: const Text('TRY AGAIN'),
            ),
          ],
        ),
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
