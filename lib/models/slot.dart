class TimeSlot {
  final String id;
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

  static List<TimeSlot> getMockSlots() {
    return const [
      TimeSlot(
        id: 'slot_1',
        timeRange: '09:00 AM – 10:00 AM',
        isAvailable: true,
        capacity: 25,
        bookedCount: 14,
      ),
      TimeSlot(
        id: 'slot_2',
        timeRange: '10:00 AM – 11:00 AM',
        isAvailable: true,
        capacity: 25,
        bookedCount: 8,
      ),
      TimeSlot(
        id: 'slot_3',
        timeRange: '11:00 AM – 12:00 PM',
        isAvailable: true,
        capacity: 25,
        bookedCount: 18,
      ),
      TimeSlot(
        id: 'slot_4',
        timeRange: '12:00 PM – 01:00 PM',
        isAvailable: false,
        capacity: 25,
        bookedCount: 25,
      ),
      TimeSlot(
        id: 'slot_5',
        timeRange: '02:00 PM – 03:00 PM',
        isAvailable: true,
        capacity: 25,
        bookedCount: 11,
      ),
      TimeSlot(
        id: 'slot_6',
        timeRange: '03:00 PM – 04:00 PM',
        isAvailable: true,
        capacity: 25,
        bookedCount: 9,
      ),
    ];
  }
}
