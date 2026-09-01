class FarmerModel {
  final int? id;
  final String name;
  final String farmerId;
  final String mobile;
  final String village;
  final String district;
  final String state;
  final String crop;
  final double expectedQuantity;

  const FarmerModel({
    this.id,
    required this.name,
    required this.farmerId,
    required this.mobile,
    required this.village,
    required this.district,
    required this.state,
    required this.crop,
    required this.expectedQuantity,
  });

  factory FarmerModel.fromJson(Map<String, dynamic> json) {
    return FarmerModel(
      id: json['id'],
      name: json['name'] ?? '',
      farmerId: json['farmer_id'] ?? '',
      mobile: json['mobile'] ?? '',
      village: json['village'] ?? '',
      district: json['district'] ?? '',
      state: json['state'] ?? '',
      crop: json['crop'] ?? '',
      expectedQuantity: (json['expected_quantity'] ?? 0).toDouble(),
    );
  }

  Map<String, dynamic> toJson() => {
    if (id != null) 'id': id,
    'name': name,
    'farmer_id': farmerId,
    'mobile': mobile,
    'village': village,
    'district': district,
    'state': state,
    'crop': crop,
    'expected_quantity': expectedQuantity,
  };

  FarmerModel copyWith({
    int? id,
    String? name,
    String? farmerId,
    String? mobile,
    String? village,
    String? district,
    String? state,
    String? crop,
    double? expectedQuantity,
  }) {
    return FarmerModel(
      id: id ?? this.id,
      name: name ?? this.name,
      farmerId: farmerId ?? this.farmerId,
      mobile: mobile ?? this.mobile,
      village: village ?? this.village,
      district: district ?? this.district,
      state: state ?? this.state,
      crop: crop ?? this.crop,
      expectedQuantity: expectedQuantity ?? this.expectedQuantity,
    );
  }

  static FarmerModel mockFarmer() {
    return const FarmerModel(
      name: 'Ravi Kumar',
      farmerId: 'FR10245',
      mobile: '9876543210',
      village: 'Example Village',
      district: 'Example District',
      state: 'Tamil Nadu',
      crop: 'Paddy',
      expectedQuantity: 850.0,
    );
  }
}
