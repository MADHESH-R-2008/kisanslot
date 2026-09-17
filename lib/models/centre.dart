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

  ProcurementCentre copyWithDistance(double newDistanceKm) {
    return ProcurementCentre(
      id: id,
      name: name,
      distanceKm: newDistanceKm,
      queueCount: queueCount,
      waitMin: waitMin,
      isRecommended: isRecommended,
      address: address,
      isOpen: isOpen,
      activeCounters: activeCounters,
      rating: rating,
      googleMapUrl: googleMapUrl,
      latitude: latitude,
      longitude: longitude,
    );
  }

  static double _parseDouble(dynamic val, double fallback) {
    if (val == null) return fallback;
    if (val is num) return val.toDouble();
    if (val is String) return double.tryParse(val) ?? fallback;
    return fallback;
  }

  static double? _parseOptionalDouble(dynamic val) {
    if (val == null) return null;
    if (val is num) return val.toDouble();
    if (val is String) return double.tryParse(val);
    return null;
  }

  static int _parseInt(dynamic val, int fallback) {
    if (val == null) return fallback;
    if (val is int) return val;
    if (val is num) return val.toInt();
    if (val is String) return int.tryParse(val) ?? fallback;
    return fallback;
  }

  factory ProcurementCentre.fromJson(Map<String, dynamic> json) {
    final qCount = _parseInt(json['queue_count'], 0);
    return ProcurementCentre(
      id: _parseInt(json['id'], 0),
      name: (json['name'] ?? '').toString(),
      distanceKm: _parseDouble(json['distance_km'] ?? json['distance'], 0.0),
      queueCount: qCount,
      waitMin: _parseInt(json['estimated_wait_minutes'], 0),
      isRecommended: qCount <= 10,  // Auto-recommend if queue is short
      address: (json['address'] ?? '').toString(),
      isOpen: json['is_active'] == true || json['is_active'] == 1 || json['is_active'] == null,
      activeCounters: _parseInt(json['active_counters'], 3),
      rating: _parseDouble(json['rating'], 4.5),
      googleMapUrl: json['google_map_url']?.toString(),
      latitude: _parseOptionalDouble(json['latitude']),
      longitude: _parseOptionalDouble(json['longitude']),
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
