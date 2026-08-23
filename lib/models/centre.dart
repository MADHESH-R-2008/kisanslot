class ProcurementCentre {
  final String id;
  final String name;
  final double distanceKm;
  final int queueCount;
  final int waitMin;
  final bool isRecommended;
  final String address;
  final bool isOpen;
  final int activeCounters;
  final double rating;

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
  });

  static List<ProcurementCentre> getMockCentres() {
    return const [
      ProcurementCentre(
        id: 'centre_a',
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
        id: 'centre_b',
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
        id: 'centre_c',
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
