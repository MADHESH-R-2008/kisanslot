import 'package:flutter/material.dart';
import '../models/centre.dart';
import '../services/mock_data_service.dart';
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
  final MockDataService _dataService = MockDataService();
  String _selectedFilter = 'All';
  String? _selectedCentreId;

  @override
  Widget build(BuildContext context) {
    final centres = _dataService.centres;

    List<ProcurementCentre> filteredCentres = centres;
    if (_selectedFilter == 'Nearest') {
      filteredCentres = [...centres]..sort((a, b) => a.distanceKm.compareTo(b.distanceKm));
    } else if (_selectedFilter == 'Shortest Queue') {
      filteredCentres = [...centres]..sort((a, b) => a.queueCount.compareTo(b.queueCount));
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
      body: SafeArea(
        child: SingleChildScrollView(
          padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 12),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              // Top Map Placeholder
              MapPlaceholderWidget(
                centres: centres,
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
