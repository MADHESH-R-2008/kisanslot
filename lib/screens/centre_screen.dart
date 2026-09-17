import 'package:flutter/material.dart';
import 'package:geolocator/geolocator.dart';
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
  Position? _currentPosition;
  String? _locationStatus;

  @override
  void initState() {
    super.initState();
    _loadCentres();
  }

  Future<Position?> _determinePosition() async {
    try {
      bool serviceEnabled = await Geolocator.isLocationServiceEnabled();
      if (!serviceEnabled) {
        if (mounted) setState(() => _locationStatus = 'Location services disabled. Using default distances.');
        return null;
      }

      LocationPermission permission = await Geolocator.checkPermission();
      if (permission == LocationPermission.denied) {
        permission = await Geolocator.requestPermission();
        if (permission == LocationPermission.denied) {
          if (mounted) setState(() => _locationStatus = 'Location permission denied. Using default distances.');
          return null;
        }
      }

      if (permission == LocationPermission.deniedForever) {
        if (mounted) setState(() => _locationStatus = 'Location permission permanently denied.');
        return null;
      }

      return await Geolocator.getCurrentPosition(
        locationSettings: const LocationSettings(
          accuracy: LocationAccuracy.medium,
          timeLimit: Duration(seconds: 4),
        ),
      );
    } catch (_) {
      if (mounted) setState(() => _locationStatus = 'Could not fetch live GPS position.');
      return null;
    }
  }

  Future<void> _loadCentres() async {
    setState(() {
      _isLoading = true;
      _error = null;
      _locationStatus = null;
    });

    try {
      final data = await ApiService.getCentres();
      List<ProcurementCentre> loaded = data.map((json) => ProcurementCentre.fromJson(json)).toList();

      if (loaded.isEmpty) {
        loaded = ProcurementCentre.getMockCentres();
      }

      _centres = loaded;
      if (mounted) setState(() => _isLoading = false);

      _updateLocationAndDistances();
    } on ApiException catch (_) {
      if (mounted) {
        setState(() {
          _centres = ProcurementCentre.getMockCentres();
          _isLoading = false;
        });
        _updateLocationAndDistances();
      }
    } catch (_) {
      if (mounted) {
        setState(() {
          _centres = ProcurementCentre.getMockCentres();
          _isLoading = false;
        });
        _updateLocationAndDistances();
      }
    }
  }

  Future<void> _updateLocationAndDistances() async {
    try {
      Position? position = await _determinePosition();
      if (position == null || !mounted) return;

      _currentPosition = position;
      List<ProcurementCentre> updated = _centres.map((centre) {
        if (centre.latitude != null && centre.longitude != null) {
          double meters = Geolocator.distanceBetween(
            position.latitude,
            position.longitude,
            centre.latitude!,
            centre.longitude!,
          );
          double distKm = double.parse((meters / 1000.0).toStringAsFixed(1));
          return centre.copyWithDistance(distKm);
        }
        return centre;
      }).toList();

      if (mounted) {
        setState(() {
          _centres = updated;
          _locationStatus = 'GPS location acquired (${position.latitude.toStringAsFixed(3)}, ${position.longitude.toStringAsFixed(3)})';
        });
      }
    } catch (_) {}
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
                        // Location status banner
                        if (_locationStatus != null)
                          Container(
                            margin: const EdgeInsets.only(bottom: 12),
                            padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
                            decoration: BoxDecoration(
                              color: _currentPosition != null ? Colors.green.shade50 : Colors.amber.shade50,
                              borderRadius: BorderRadius.circular(8),
                              border: Border.all(
                                color: _currentPosition != null ? Colors.green.shade200 : Colors.amber.shade200,
                              ),
                            ),
                            child: Row(
                              children: [
                                Icon(
                                  _currentPosition != null ? Icons.my_location_rounded : Icons.location_off_rounded,
                                  size: 16,
                                  color: _currentPosition != null ? Colors.green.shade700 : Colors.amber.shade800,
                                ),
                                const SizedBox(width: 8),
                                Expanded(
                                  child: Text(
                                    _locationStatus!,
                                    style: TextStyle(
                                      fontSize: 11,
                                      color: _currentPosition != null ? Colors.green.shade900 : Colors.amber.shade900,
                                      fontWeight: FontWeight.w500,
                                    ),
                                  ),
                                ),
                                GestureDetector(
                                  onTap: _loadCentres,
                                  child: Icon(
                                    Icons.refresh_rounded,
                                    size: 16,
                                    color: _currentPosition != null ? Colors.green.shade700 : Colors.amber.shade800,
                                  ),
                                ),
                              ],
                            ),
                          ),

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
