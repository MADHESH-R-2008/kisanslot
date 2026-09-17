class ProcurementCentre {
  final int id;
  final String name;
  final double distanceKm;
  final int queueCount;
  final int waitMin;
  final bool isRecommended;
  final String address;
  final bool isOpen;
  final int activeCounters;
  final double rating;
  final String? googleMapUrl;
  final double? latitude;
  final double? longitude;

  const ProcurementCentre({
    required this.id,
    required this.name,
    required this.distanceKm,
    required this.queueCount,
    required this.waitMin,
    this.isRecommended = false,
    required this.address,
    this.isOpen = true,
    this.activeCounters = 3,
    this.rating = 4.8,
    this.googleMapUrl,
    this.latitude,
    this.longitude,
  });

  factory ProcurementCentre.fromJson(Map<String, dynamic> json) {
    final qCount = json['queue_count'] ?? 0;
    return ProcurementCentre(
      id: json['id'],
      name: json['name'] ?? '',
      distanceKm: (json['distance_km'] ?? json['distance'] ?? 0).toDouble(),
      queueCount: qCount,
      waitMin: json['estimated_wait_minutes'] ?? 0,
      isRecommended: qCount <= 10,  // Auto-recommend if queue is short
      address: json['address'] ?? '',
      isOpen: json['is_active'] ?? true,
      activeCounters: json['active_counters'] ?? 3,
      rating: (json['rating'] ?? 4.5).toDouble(),
      googleMapUrl: json['google_map_url'],
      latitude: (json['latitude'] != null) ? (json['latitude'] as num).toDouble() : null,
      longitude: (json['longitude'] != null) ? (json['longitude'] as num).toDouble() : null,
    );
  }

  static List<ProcurementCentre> getMockCentres() {
    return const [
      ProcurementCentre(
        id: 1,
        name: 'Centre A',
        distanceKm: 4.0,
        queueCount: 28,
        waitMin: 85,
        isRecommended: false,
        address: 'APMC Market Yard, North Block, Main Road',
        isOpen: true,
        activeCounters: 4,
        rating: 4.2,
      ),
      ProcurementCentre(
        id: 2,
        name: 'Centre B',
        distanceKm: 7.0,
        queueCount: 8,
        waitMin: 20,
        isRecommended: true,
        address: 'Taluk Regulated Agricultural Market, Highway Junction',
        isOpen: true,
        activeCounters: 3,
        rating: 4.9,
      ),
      ProcurementCentre(
        id: 3,
        name: 'Centre C',
        distanceKm: 10.0,
        queueCount: 15,
        waitMin: 43,
        isRecommended: false,
        address: 'District Farmers Co-operative Hub, Sector 4',
        isOpen: true,
        activeCounters: 2,
        rating: 4.5,
      ),
    ];
  }
}
