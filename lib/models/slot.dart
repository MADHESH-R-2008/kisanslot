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

  factory TimeSlot.fromJson(Map<String, dynamic> json) {
    final available = json['available'] ?? (json['capacity'] ?? 25) - (json['booked_count'] ?? 0);
    final startTime = json['start_time'] ?? '09:00';
    final endTime = json['end_time'] ?? '10:00';

    // Convert 24h times to display format
    String formatTime(String t) {
      final parts = t.split(':');
      final hour = int.parse(parts[0]);
      final minute = parts[1];
      final period = hour >= 12 ? 'PM' : 'AM';
      final displayHour = hour == 0 ? 12 : (hour > 12 ? hour - 12 : hour);
      return '${displayHour.toString().padLeft(2, '0')}:$minute $period';
    }

    return TimeSlot(
      id: json['id'],
      timeRange: '${formatTime(startTime)} – ${formatTime(endTime)}',
      isAvailable: (json['is_active'] ?? true) && available > 0,
      capacity: json['capacity'] ?? 25,
      bookedCount: json['booked_count'] ?? 0,
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
