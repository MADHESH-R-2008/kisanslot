class TimeSlot {
  final int id;
  final String timeRange;
  final bool isAvailable;
  final int capacity;
  final int bookedCount;

  const TimeSlot({
    required this.id,
    required this.timeRange,
    required this.isAvailable,
    this.capacity = 25,
    this.bookedCount = 10,
  });

  static int _parseInt(dynamic val, int fallback) {
    if (val == null) return fallback;
    if (val is int) return val;
    if (val is num) return val.toInt();
    if (val is String) return int.tryParse(val) ?? fallback;
    return fallback;
  }

  factory TimeSlot.fromJson(Map<String, dynamic> json) {
    final cap = _parseInt(json['capacity'], 25);
    final booked = _parseInt(json['booked_count'], 0);
    final available = json['available'] != null 
        ? _parseInt(json['available'], cap - booked)
        : (cap - booked);

    final startTime = json['start_time'] ?? '09:00';
    final endTime = json['end_time'] ?? '10:00';

    String formatTime(dynamic t) {
      if (t == null) return '09:00 AM';
      final str = t.toString().trim();
      if (str.isEmpty) return '09:00 AM';
      try {
        final parts = str.split(':');
        final hour = int.tryParse(parts[0]) ?? 9;
        final minute = parts.length > 1 ? parts[1] : '00';
        final period = hour >= 12 ? 'PM' : 'AM';
        final displayHour = hour == 0 ? 12 : (hour > 12 ? hour - 12 : hour);
        return '${displayHour.toString().padLeft(2, '0')}:${minute.padLeft(2, '0')} $period';
      } catch (_) {
        return str;
      }
    }

    return TimeSlot(
      id: _parseInt(json['id'], 0),
      timeRange: '${formatTime(startTime)} – ${formatTime(endTime)}',
      isAvailable: (json['is_active'] == true || json['is_active'] == 1 || json['is_active'] == null) && available > 0,
      capacity: cap,
      bookedCount: booked,
    );
  }

  int get availableCount => capacity - bookedCount;

  static List<TimeSlot> getMockSlots() {
    return const [
      TimeSlot(
        id: 1,
        timeRange: '09:00 AM – 10:00 AM',
        isAvailable: true,
        capacity: 25,
        bookedCount: 14,
      ),
      TimeSlot(
        id: 2,
        timeRange: '10:00 AM – 11:00 AM',
        isAvailable: true,
        capacity: 25,
        bookedCount: 8,
      ),
      TimeSlot(
        id: 3,
        timeRange: '11:00 AM – 12:00 PM',
        isAvailable: true,
        capacity: 25,
        bookedCount: 18,
      ),
      TimeSlot(
        id: 4,
        timeRange: '12:00 PM – 01:00 PM',
        isAvailable: false,
        capacity: 25,
        bookedCount: 25,
      ),
      TimeSlot(
        id: 5,
        timeRange: '02:00 PM – 03:00 PM',
        isAvailable: true,
        capacity: 25,
        bookedCount: 11,
      ),
      TimeSlot(
        id: 6,
        timeRange: '03:00 PM – 04:00 PM',
        isAvailable: true,
        capacity: 25,
        bookedCount: 9,
      ),
    ];
  }
}
