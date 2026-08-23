import 'package:flutter/material.dart';
import '../services/mock_data_service.dart';
import '../utils/app_colors.dart';
import '../utils/routes.dart';
import '../widgets/booking_card.dart';

class HomeScreen extends StatefulWidget {
  const HomeScreen({super.key});

  @override
  State<HomeScreen> createState() => _HomeScreenState();
}

class _HomeScreenState extends State<HomeScreen> {
  int _currentIndex = 0;
  final MockDataService _dataService = MockDataService();

  @override
  void initState() {
    super.initState();
    _dataService.addListener(_onStateChange);
  }

  @override
  void dispose() {
    _dataService.removeListener(_onStateChange);
    super.dispose();
  }

  void _onStateChange() {
    if (mounted) setState(() {});
  }

  void _onBottomNavTapped(int index) {
    if (index == _currentIndex) return;
    setState(() => _currentIndex = index);

    switch (index) {
      case 0:
        break;
      case 1:
        Navigator.pushNamed(context, AppRoutes.centre).then((_) {
          if (mounted) setState(() => _currentIndex = 0);
        });
        break;
      case 2:
        Navigator.pushNamed(context, AppRoutes.queue).then((_) {
          if (mounted) setState(() => _currentIndex = 0);
        });
        break;
      case 3:
        Navigator.pushNamed(context, AppRoutes.profile).then((_) {
          if (mounted) setState(() => _currentIndex = 0);
        });
        break;
    }
  }

  @override
  Widget build(BuildContext context) {
    final farmer = _dataService.currentFarmer;
    final booking = _dataService.activeBooking;

    return Scaffold(
      backgroundColor: AppColors.background,
      body: SafeArea(
        child: SingleChildScrollView(
          padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 16),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              // Top Header Bar
              Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(
                          'Hello, ${farmer.name.split(" ").first} 👨‍🌾',
                          style: const TextStyle(
                            fontSize: 22,
                            fontWeight: FontWeight.bold,
                            color: AppColors.textPrimary,
                          ),
                          maxLines: 1,
                          overflow: TextOverflow.ellipsis,
                        ),
                        const SizedBox(height: 2),
                        const Text(
                          'Welcome to KisanSlot',
                          style: TextStyle(
                            fontSize: 14,
                            color: AppColors.textSecondary,
                            fontWeight: FontWeight.w500,
                          ),
                          maxLines: 1,
                          overflow: TextOverflow.ellipsis,
                        ),
                      ],
                    ),
                  ),
                  const SizedBox(width: 12),
                  GestureDetector(
                    onTap: () => Navigator.pushNamed(context, AppRoutes.profile),
                    child: Container(
                      padding: const EdgeInsets.all(3),
                      decoration: BoxDecoration(
                        shape: BoxShape.circle,
                        border: Border.all(color: AppColors.primary, width: 2),
                      ),
                      child: const CircleAvatar(
                        radius: 20,
                        backgroundColor: AppColors.primaryContainer,
                        child: Text(
                          '👨‍🌾',
                          style: TextStyle(fontSize: 20),
                        ),
                      ),
                    ),
                  ),
                ],
              ),
              const SizedBox(height: 20),

              // Quick Statistics Banner
              Container(
                padding: const EdgeInsets.all(18),
                decoration: BoxDecoration(
                  gradient: AppColors.primaryGradient,
                  borderRadius: BorderRadius.circular(18),
                  boxShadow: [
                    BoxShadow(
                      color: AppColors.primary.withValues(alpha: 0.25),
                      blurRadius: 14,
                      offset: const Offset(0, 6),
                    ),
                  ],
                ),
                child: Column(
                  children: [
                    Row(
                      children: [
                        Container(
                          padding: const EdgeInsets.all(6),
                          decoration: BoxDecoration(
                            color: Colors.white.withValues(alpha: 0.2),
                            borderRadius: BorderRadius.circular(8),
                          ),
                          child: const Icon(Icons.flash_on_rounded, color: AppColors.secondaryLight, size: 18),
                        ),
                        const SizedBox(width: 8),
                        const Text(
                          'LIVE PROCUREMENT SNAPSHOT',
                          style: TextStyle(
                            color: Colors.white,
                            fontSize: 12,
                            fontWeight: FontWeight.bold,
                            letterSpacing: 0.8,
                          ),
                        ),
                      ],
                    ),
                    const SizedBox(height: 16),
                    Row(
                      children: [
                        // Upcoming Slot
                        Expanded(
                          child: _buildQuickStatItem(
                            title: 'Upcoming Slot',
                            value: booking != null ? '25 Aug' : 'No Slot',
                            subValue: booking?.timeRange.split('–').first.trim() ?? '--',
                          ),
                        ),
                        Container(width: 1, height: 38, color: Colors.white24),

                        // Queue Position
                        Expanded(
                          child: _buildQuickStatItem(
                            title: 'Queue Position',
                            value: booking != null ? '#${booking.queuePosition}' : '--',
                            subValue: booking != null ? '${booking.farmersAhead} ahead' : '--',
                            isHighlighted: true,
                          ),
                        ),
                        Container(width: 1, height: 38, color: Colors.white24),

                        // Waiting Time
                        Expanded(
                          child: _buildQuickStatItem(
                            title: 'Waiting Time',
                            value: booking != null ? '${booking.waitTimeMinutes} min' : '--',
                            subValue: 'Est. duration',
                          ),
                        ),
                      ],
                    ),
                  ],
                ),
              ),
              const SizedBox(height: 24),

              // Active Ticket Card
              if (booking != null) ...[
                const Text(
                  'Active Booking Ticket',
                  style: TextStyle(
                    fontSize: 18,
                    fontWeight: FontWeight.bold,
                    color: AppColors.textPrimary,
                  ),
                ),
                const SizedBox(height: 12),
                BookingCard(
                  booking: booking,
                  onTapQueue: () => Navigator.pushNamed(context, AppRoutes.queue),
                  onTapDetails: () => Navigator.pushNamed(context, AppRoutes.procurement),
                ),
                const SizedBox(height: 24),
              ],

              // Major Action Feature Cards
              const Text(
                'Services & Operations',
                style: TextStyle(
                  fontSize: 18,
                  fontWeight: FontWeight.bold,
                  color: AppColors.textPrimary,
                ),
              ),
              const SizedBox(height: 14),

              // 1. Book Procurement Slot
              _buildFeatureCard(
                context,
                title: 'Book Procurement Slot',
                subtitle: 'Choose centre and time',
                emoji: '📅',
                accentColor: AppColors.primary,
                onTap: () => Navigator.pushNamed(context, AppRoutes.centre),
              ),
              const SizedBox(height: 12),

              // 2. My Booking
              _buildFeatureCard(
                context,
                title: 'My Booking',
                subtitle: 'View booking details & token',
                emoji: '🎫',
                accentColor: const Color(0xFF0284C7),
                onTap: () {
                  if (booking != null) {
                    Navigator.pushNamed(context, AppRoutes.confirmation, arguments: booking);
                  } else {
                    Navigator.pushNamed(context, AppRoutes.centre);
                  }
                },
              ),
              const SizedBox(height: 12),

              // 3. Live Queue
              _buildFeatureCard(
                context,
                title: 'Live Queue',
                subtitle: 'Track your position & counter',
                emoji: '👥',
                badgeText: booking != null ? 'Position #${booking.queuePosition}' : null,
                accentColor: AppColors.secondary,
                onTap: () => Navigator.pushNamed(context, AppRoutes.queue),
              ),
              const SizedBox(height: 12),

              // 4. Procurement Status
              _buildFeatureCard(
                context,
                title: 'Procurement Status',
                subtitle: 'Track your produce & weighing',
                emoji: '🌾',
                accentColor: const Color(0xFF059669),
                onTap: () => Navigator.pushNamed(context, AppRoutes.procurement),
              ),
              const SizedBox(height: 12),

              // 5. Payment Status
              _buildFeatureCard(
                context,
                title: 'Payment Status',
                subtitle: 'Track your payment & bank transfer',
                emoji: '💰',
                badgeText: '₹18,275',
                accentColor: const Color(0xFF7C3AED),
                onTap: () => Navigator.pushNamed(context, AppRoutes.payment),
              ),
              const SizedBox(height: 20),
            ],
          ),
        ),
      ),
      bottomNavigationBar: BottomNavigationBar(
        currentIndex: _currentIndex,
        onTap: _onBottomNavTapped,
        type: BottomNavigationBarType.fixed,
        selectedItemColor: AppColors.primary,
        unselectedItemColor: AppColors.textSecondary,
        selectedLabelStyle: const TextStyle(fontWeight: FontWeight.bold, fontSize: 12),
        unselectedLabelStyle: const TextStyle(fontWeight: FontWeight.w500, fontSize: 12),
        backgroundColor: Colors.white,
        elevation: 8,
        items: const [
          BottomNavigationBarItem(
            icon: Icon(Icons.home_outlined),
            activeIcon: Icon(Icons.home_rounded),
            label: 'Home',
          ),
          BottomNavigationBarItem(
            icon: Icon(Icons.calendar_month_outlined),
            activeIcon: Icon(Icons.calendar_month_rounded),
            label: 'Booking',
          ),
          BottomNavigationBarItem(
            icon: Icon(Icons.groups_outlined),
            activeIcon: Icon(Icons.groups_rounded),
            label: 'Queue',
          ),
          BottomNavigationBarItem(
            icon: Icon(Icons.person_outline_rounded),
            activeIcon: Icon(Icons.person_rounded),
            label: 'Profile',
          ),
        ],
      ),
    );
  }

  Widget _buildQuickStatItem({
    required String title,
    required String value,
    required String subValue,
    bool isHighlighted = false,
  }) {
    return Column(
      children: [
        Text(
          title,
          style: TextStyle(
            color: Colors.white.withValues(alpha: 0.8),
            fontSize: 11,
          ),
          textAlign: TextAlign.center,
        ),
        const SizedBox(height: 4),
        Text(
          value,
          style: TextStyle(
            color: isHighlighted ? AppColors.secondaryLight : Colors.white,
            fontSize: 16,
            fontWeight: FontWeight.w900,
          ),
        ),
        const SizedBox(height: 2),
        Text(
          subValue,
          style: TextStyle(
            color: Colors.white.withValues(alpha: 0.7),
            fontSize: 10,
          ),
        ),
      ],
    );
  }

  Widget _buildFeatureCard(
    BuildContext context, {
    required String title,
    required String subtitle,
    required String emoji,
    required Color accentColor,
    String? badgeText,
    required VoidCallback onTap,
  }) {
    return InkWell(
      onTap: onTap,
      borderRadius: BorderRadius.circular(16),
      child: Container(
        padding: const EdgeInsets.symmetric(horizontal: 18, vertical: 16),
        decoration: BoxDecoration(
          color: Colors.white,
          borderRadius: BorderRadius.circular(16),
          border: Border.all(color: AppColors.cardBorder),
          boxShadow: [
            BoxShadow(
              color: Colors.black.withValues(alpha: 0.03),
              blurRadius: 8,
              offset: const Offset(0, 2),
            ),
          ],
        ),
        child: Row(
          children: [
            Container(
              width: 52,
              height: 52,
              decoration: BoxDecoration(
                color: accentColor.withValues(alpha: 0.1),
                borderRadius: BorderRadius.circular(14),
              ),
              child: Center(
                child: Text(
                  emoji,
                  style: const TextStyle(fontSize: 26),
                ),
              ),
            ),
            const SizedBox(width: 16),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Row(
                    children: [
                      Flexible(
                        child: Text(
                          title,
                          style: const TextStyle(
                            fontSize: 16,
                            fontWeight: FontWeight.bold,
                            color: AppColors.textPrimary,
                          ),
                        ),
                      ),
                      if (badgeText != null) ...[
                        const SizedBox(width: 8),
                        Container(
                          padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 2),
                          decoration: BoxDecoration(
                            color: accentColor.withValues(alpha: 0.15),
                            borderRadius: BorderRadius.circular(12),
                          ),
                          child: Text(
                            badgeText,
                            style: TextStyle(
                              fontSize: 11,
                              fontWeight: FontWeight.bold,
                              color: accentColor,
                            ),
                          ),
                        ),
                      ],
                    ],
                  ),
                  const SizedBox(height: 3),
                  Text(
                    subtitle,
                    style: const TextStyle(
                      fontSize: 13,
                      color: AppColors.textSecondary,
                    ),
                  ),
                ],
              ),
            ),
            const Icon(
              Icons.arrow_forward_ios_rounded,
              size: 16,
              color: AppColors.textMuted,
            ),
          ],
        ),
      ),
    );
  }
}
