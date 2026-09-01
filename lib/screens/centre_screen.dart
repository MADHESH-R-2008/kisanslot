import 'package:flutter/material.dart';
import '../models/centre.dart';
import '../services/api_service.dart';
import '../utils/app_colors.dart';
import '../utils/routes.dart';
import '../widgets/centre_card.dart';
import '../widgets/map_placeholder.dart';

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
    _loadCentres();
  }

  Future<void> _loadCentres() async {
    setState(() {
      _isLoading = true;
      _error = null;
    });

    try {
      final data = await ApiService.getCentres();
      _centres = data.map((json) => ProcurementCentre.fromJson(json)).toList();
      if (mounted) setState(() => _isLoading = false);
    } on ApiException catch (e) {
      if (mounted) setState(() { _isLoading = false; _error = e.message; });
    } catch (e) {
      if (mounted) setState(() { _isLoading = false; _error = 'Unable to load centres. Check your connection.'; });
    }
  }

  @override
  Widget build(BuildContext context) {
    List<ProcurementCentre> filteredCentres = _centres;
    if (_selectedFilter == 'Nearest') {
      filteredCentres = [..._centres]..sort((a, b) => a.distanceKm.compareTo(b.distanceKm));
    } else if (_selectedFilter == 'Shortest Queue') {
      filteredCentres = [..._centres]..sort((a, b) => a.queueCount.compareTo(b.queueCount));
    }

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
                  Text('Loading centres...', style: TextStyle(color: AppColors.textSecondary)),
                ],
              ),
            )
          : _error != null
              ? Center(
                  child: Padding(
                    padding: const EdgeInsets.all(32),
                    child: Column(
                      mainAxisAlignment: MainAxisAlignment.center,
                      children: [
                        const Icon(Icons.cloud_off_rounded, size: 64, color: AppColors.textMuted),
                        const SizedBox(height: 16),
                        Text(_error!, textAlign: TextAlign.center, style: const TextStyle(color: AppColors.textSecondary)),
                        const SizedBox(height: 24),
                        ElevatedButton.icon(
                          onPressed: _loadCentres,
                          icon: const Icon(Icons.refresh),
                          label: const Text('TRY AGAIN'),
                        ),
                      ],
                    ),
                  ),
                )
              : SafeArea(
                  child: SingleChildScrollView(
                    padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 12),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        // Top Map Placeholder
                        MapPlaceholderWidget(
                          centres: _centres,
                          selectedCentreId: _selectedCentreId,
                          onSelectCentre: (centre) {
                            setState(() => _selectedCentreId = centre.id);
                          },
                        ),
                        const SizedBox(height: 16),

                        // Filter Chips
                        SingleChildScrollView(
                          scrollDirection: Axis.horizontal,
                          child: Row(
                            children: [
                              _buildFilterChip('All'),
                              const SizedBox(width: 8),
                              _buildFilterChip('Nearest'),
                              const SizedBox(width: 8),
                              _buildFilterChip('Shortest Queue'),
                            ],
                          ),
                        ),
                        const SizedBox(height: 16),

                        // Subtitle
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
                            const SizedBox(width: 8),
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

                        // Centre Cards List
                        if (filteredCentres.isEmpty)
                          const Padding(
                            padding: EdgeInsets.all(32),
                            child: Center(
                              child: Text('No centres available.', style: TextStyle(color: AppColors.textSecondary)),
                            ),
                          )
                        else
                          ListView.builder(
                            shrinkWrap: true,
                            physics: const NeverScrollableScrollPhysics(),
                            itemCount: filteredCentres.length,
                            itemBuilder: (context, index) {
                              final centre = filteredCentres[index];
                              return CentreCard(
                                centre: centre,
                                isSelected: _selectedCentreId == centre.id,
                                onViewSlots: () {
                                  Navigator.pushNamed(
                                    context,
                                    AppRoutes.slotBooking,
                                    arguments: centre,
                                  );
                                },
                              );
                            },
                          ),
                        const SizedBox(height: 16),
                      ],
                    ),
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
