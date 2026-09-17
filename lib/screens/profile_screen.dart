import 'package:flutter/material.dart';
import '../models/farmer.dart';
import '../models/booking.dart';
import '../services/api_service.dart';
import '../utils/app_colors.dart';
import '../utils/routes.dart';
import '../widgets/booking_card.dart';

class ProfileScreen extends StatefulWidget {
  const ProfileScreen({super.key});

  @override
  State<ProfileScreen> createState() => _ProfileScreenState();
}

class _ProfileScreenState extends State<ProfileScreen> {
  bool _isLoading = true;
  String? _error;
  FarmerModel? _farmer;
  List<BookingModel> _bookings = [];

  @override
  void initState() {
    super.initState();
    _loadData();
  }

  Future<void> _loadData() async {
    setState(() { _isLoading = true; _error = null; });

    try {
      final profileData = await ApiService.getProfile();
      _farmer = FarmerModel.fromJson(profileData);

      // Attempt to load active booking as a mock "history" since backend only returns active booking right now
      // In a real app we would call a /bookings/history endpoint
      try {
        final bookingId = await ApiService.getActiveBookingId();
        if (bookingId != null && bookingId.isNotEmpty) {
          final bookingData = await ApiService.getBooking(bookingId);
          _bookings = [BookingModel.fromJson(bookingData)];
        }
      } catch (_) {
        _bookings = [];
      }

      if (mounted) setState(() => _isLoading = false);
    } on ApiException catch (e) {
      if (mounted) setState(() { _isLoading = false; _error = e.message; });
    } catch (e) {
      if (mounted) setState(() { _isLoading = false; _error = 'Unable to load profile data.'; });
    }
  }

  void _showEditProfileDialog(FarmerModel farmer) {
    final nameCtrl = TextEditingController(text: farmer.name);
    final villageCtrl = TextEditingController(text: farmer.village);
    final districtCtrl = TextEditingController(text: farmer.district);
    final stateCtrl = TextEditingController(text: farmer.state);

    showDialog(
      context: context,
      builder: (ctx) => AlertDialog(
        title: const Text('Edit Farmer Profile'),
        content: SingleChildScrollView(
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              TextField(
                controller: nameCtrl,
                decoration: const InputDecoration(labelText: 'Full Name'),
              ),
              const SizedBox(height: 12),
              TextField(
                controller: villageCtrl,
                decoration: const InputDecoration(labelText: 'Village'),
              ),
              const SizedBox(height: 12),
              TextField(
                controller: districtCtrl,
                decoration: const InputDecoration(labelText: 'District'),
              ),
              const SizedBox(height: 12),
              TextField(
                controller: stateCtrl,
                decoration: const InputDecoration(labelText: 'State'),
              ),
            ],
          ),
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(ctx),
            child: const Text('Cancel'),
          ),
          ElevatedButton(
            onPressed: () {
              ScaffoldMessenger.of(context).showSnackBar(
                const SnackBar(
                  content: Text('Profile update API endpoint coming soon in Phase 3!'),
                  backgroundColor: AppColors.primary,
                ),
              );
              Navigator.pop(ctx);
            },
            child: const Text('Save'),
          ),
        ],
      ),
    );
  }

  void _showMyBookingsSheet() {
    showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      backgroundColor: Colors.transparent,
      builder: (ctx) => DraggableScrollableSheet(
        initialChildSize: 0.7,
        maxChildSize: 0.9,
        minChildSize: 0.4,
        builder: (_, scrollController) => Container(
          decoration: const BoxDecoration(
            color: AppColors.background,
            borderRadius: BorderRadius.only(
              topLeft: Radius.circular(24),
              topRight: Radius.circular(24),
            ),
          ),
          padding: const EdgeInsets.all(20),
          child: ListView(
            controller: scrollController,
            children: [
              Center(
                child: Container(
                  width: 40,
                  height: 4,
                  decoration: BoxDecoration(
                    color: AppColors.cardBorder,
                    borderRadius: BorderRadius.circular(2),
                  ),
                ),
              ),
              const SizedBox(height: 16),
              const Text(
                'My Bookings History',
                style: TextStyle(
                  fontSize: 20,
                  fontWeight: FontWeight.bold,
                  color: AppColors.textPrimary,
                ),
              ),
              const SizedBox(height: 14),
              if (_bookings.isEmpty)
                const Center(
                  child: Padding(
                    padding: EdgeInsets.all(32.0),
                    child: Text('No active bookings found'),
                  ),
                )
              else
                ..._bookings.map(
                  (b) => Padding(
                    padding: const EdgeInsets.only(bottom: 14),
                    child: BookingCard(
                      booking: b,
                      isCompact: true,
                    ),
                  ),
                ),
            ],
          ),
        ),
      ),
    );
  }

  void _showHelpSupportDialog() {
    showDialog(
      context: context,
      builder: (ctx) => AlertDialog(
        title: const Row(
          children: [
            Icon(Icons.support_agent_rounded, color: AppColors.primary),
            SizedBox(width: 8),
            Text('Help & Support'),
          ],
        ),
        content: const Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              'Kisan Call Centre (Toll-Free):',
              style: TextStyle(fontWeight: FontWeight.bold),
            ),
            SizedBox(height: 4),
            Text('📞 1800-180-1551', style: TextStyle(color: AppColors.primary, fontSize: 16, fontWeight: FontWeight.bold)),
            SizedBox(height: 14),
            Text(
              'Procurement Help Desk:',
              style: TextStyle(fontWeight: FontWeight.bold),
            ),
            SizedBox(height: 4),
            Text('✉️ support@kisanslot.gov.in'),
            SizedBox(height: 14),
            Text(
              'Operating Hours: 08:00 AM – 06:00 PM (Mon-Sat)',
              style: TextStyle(fontSize: 12, color: AppColors.textSecondary),
            ),
          ],
        ),
        actions: [
          ElevatedButton(
            onPressed: () => Navigator.pop(ctx),
            child: const Text('Close'),
          ),
        ],
      ),
    );
  }

  void _handleLogout() {
    showDialog(
      context: context,
      builder: (ctx) => AlertDialog(
        title: const Text('Confirm Logout'),
        content: const Text('Are you sure you want to sign out from KisanSlot?'),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(ctx),
            child: const Text('Cancel'),
          ),
          ElevatedButton(
            style: ElevatedButton.styleFrom(backgroundColor: AppColors.error),
            onPressed: () async {
              Navigator.pop(ctx); // Close dialog
              await ApiService.clearToken();
              if (mounted) {
                Navigator.pushNamedAndRemoveUntil(context, AppRoutes.login, (route) => false);
              }
            },
            child: const Text('Logout'),
          ),
        ],
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    if (_isLoading) {
      return Scaffold(
        backgroundColor: AppColors.background,
        appBar: AppBar(title: const Text('Farmer Profile')),
        body: const Center(child: CircularProgressIndicator(color: AppColors.primary)),
      );
    }

    if (_error != null || _farmer == null) {
      return Scaffold(
        backgroundColor: AppColors.background,
        appBar: AppBar(
          title: const Text('Farmer Profile'),
          leading: IconButton(icon: const Icon(Icons.arrow_back_ios_new_rounded), onPressed: () => Navigator.pop(context)),
        ),
        body: Center(
          child: Padding(
            padding: const EdgeInsets.all(32),
            child: Column(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                const Icon(Icons.person_off_outlined, size: 64, color: AppColors.textMuted),
                const SizedBox(height: 16),
                Text(_error ?? 'Profile unavailable.', textAlign: TextAlign.center, style: const TextStyle(color: AppColors.textSecondary, fontSize: 16)),
                const SizedBox(height: 24),
                ElevatedButton.icon(
                  onPressed: () async {
                    final navigator = Navigator.of(context);
                    await ApiService.clearToken();
                    navigator.pushNamedAndRemoveUntil(AppRoutes.login, (route) => false);
                  },
                  icon: const Icon(Icons.logout),
                  label: const Text('LOGOUT'),
                ),
              ],
            ),
          ),
        ),
      );
    }

    final farmer = _farmer!;

    return Scaffold(
      backgroundColor: AppColors.background,
      appBar: AppBar(
        title: const Text('Farmer Profile'),
        leading: IconButton(
          icon: const Icon(Icons.arrow_back_ios_new_rounded),
          onPressed: () => Navigator.pop(context),
        ),
      ),
      body: SafeArea(
        child: SingleChildScrollView(
          padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 12),
          child: Column(
            children: [
              // Farmer Profile Card
              Container(
                width: double.infinity,
                padding: const EdgeInsets.all(22),
                decoration: BoxDecoration(
                  color: Colors.white,
                  borderRadius: BorderRadius.circular(20),
                  border: Border.all(color: AppColors.cardBorder),
                  boxShadow: [
                    BoxShadow(
                      color: Colors.black.withOpacity(0.04),
                      blurRadius: 10,
                      offset: const Offset(0, 4),
                    ),
                  ],
                ),
                child: Column(
                  children: [
                    // Avatar & Badge
                    Stack(
                      children: [
                        Container(
                          width: 80,
                          height: 80,
                          decoration: BoxDecoration(
                            shape: BoxShape.circle,
                            color: AppColors.primaryContainer,
                            border: Border.all(color: AppColors.primary, width: 2),
                          ),
                          child: const Center(
                            child: Text(
                              '👨‍🌾',
                              style: TextStyle(fontSize: 42),
                            ),
                          ),
                        ),
                        Positioned(
                          bottom: 0,
                          right: 0,
                          child: Container(
                            padding: const EdgeInsets.all(4),
                            decoration: const BoxDecoration(
                              color: AppColors.success,
                              shape: BoxShape.circle,
                            ),
                            child: const Icon(Icons.verified, size: 16, color: Colors.white),
                          ),
                        ),
                      ],
                    ),
                    const SizedBox(height: 14),

                    Text(
                      farmer.name,
                      style: const TextStyle(
                        fontSize: 22,
                        fontWeight: FontWeight.bold,
                        color: AppColors.textPrimary,
                      ),
                    ),
                    const SizedBox(height: 4),

                    Container(
                      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 3),
                      decoration: BoxDecoration(
                        color: AppColors.primaryContainer,
                        borderRadius: BorderRadius.circular(8),
                      ),
                      child: Text(
                        'Farmer ID: ${farmer.farmerId}',
                        style: const TextStyle(
                          fontSize: 13,
                          fontWeight: FontWeight.bold,
                          color: AppColors.primaryDark,
                        ),
                      ),
                    ),
                    const SizedBox(height: 20),
                    const Divider(height: 1, color: AppColors.cardBorder),
                    const SizedBox(height: 16),

                    _buildProfileInfoRow('Mobile Number', '+91 ${farmer.mobile}', Icons.phone_android_rounded),
                    const SizedBox(height: 12),
                    _buildProfileInfoRow('Village', farmer.village, Icons.home_work_outlined),
                    const SizedBox(height: 12),
                    _buildProfileInfoRow('District', farmer.district, Icons.location_city_outlined),
                    const SizedBox(height: 12),
                    _buildProfileInfoRow('State', farmer.state, Icons.map_outlined),
                    const SizedBox(height: 12),
                    _buildProfileInfoRow('Default Crop', '${farmer.crop} (${farmer.expectedQuantity.toStringAsFixed(0)} kg)', Icons.grass_rounded),
                  ],
                ),
              ),
              const SizedBox(height: 24),

              // Action Buttons List
              _buildMenuActionTile(
                title: 'Edit Profile',
                icon: Icons.edit_outlined,
                color: AppColors.primary,
                onTap: () => _showEditProfileDialog(farmer),
              ),
              const SizedBox(height: 10),

              _buildMenuActionTile(
                title: 'My Bookings',
                icon: Icons.confirmation_number_outlined,
                color: const Color(0xFF0284C7),
                onTap: _showMyBookingsSheet,
              ),
              const SizedBox(height: 10),

              _buildMenuActionTile(
                title: 'Help & Support',
                icon: Icons.support_agent_rounded,
                color: AppColors.secondary,
                onTap: _showHelpSupportDialog,
              ),
              const SizedBox(height: 10),

              _buildMenuActionTile(
                title: 'Logout',
                icon: Icons.logout_rounded,
                color: AppColors.error,
                onTap: _handleLogout,
              ),
              const SizedBox(height: 28),

              // App Version & Ministry Badge
              const Center(
                child: Text(
                  'KisanSlot v1.0.0 (Phase 2 Backend Integration)\nMinistry of Agriculture & Farmers Welfare',
                  textAlign: TextAlign.center,
                  style: TextStyle(
                    fontSize: 11,
                    color: AppColors.textMuted,
                    height: 1.4,
                  ),
                ),
              ),
              const SizedBox(height: 20),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildProfileInfoRow(String label, String value, IconData icon) {
    return Row(
      children: [
        Icon(icon, size: 18, color: AppColors.textSecondary),
        const SizedBox(width: 10),
        Text(
          label,
          style: const TextStyle(fontSize: 14, color: AppColors.textSecondary),
        ),
        const Spacer(),
        Flexible(
          child: Text(
            value,
            style: const TextStyle(
              fontSize: 14,
              fontWeight: FontWeight.w600,
              color: AppColors.textPrimary,
            ),
            textAlign: TextAlign.end,
            maxLines: 1,
            overflow: TextOverflow.ellipsis,
          ),
        ),
      ],
    );
  }

  Widget _buildMenuActionTile({
    required String title,
    required IconData icon,
    required Color color,
    required VoidCallback onTap,
  }) {
    return InkWell(
      onTap: onTap,
      borderRadius: BorderRadius.circular(14),
      child: Container(
        padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 14),
        decoration: BoxDecoration(
          color: Colors.white,
          borderRadius: BorderRadius.circular(14),
          border: Border.all(color: AppColors.cardBorder),
        ),
        child: Row(
          children: [
            Container(
              padding: const EdgeInsets.all(8),
              decoration: BoxDecoration(
                color: color.withOpacity(0.1),
                borderRadius: BorderRadius.circular(10),
              ),
              child: Icon(icon, color: color, size: 20),
            ),
            const SizedBox(width: 14),
            Expanded(
              child: Text(
                title,
                style: TextStyle(
                  fontSize: 15,
                  fontWeight: FontWeight.w600,
                  color: color == AppColors.error ? AppColors.error : AppColors.textPrimary,
                ),
              ),
            ),
            const Icon(Icons.arrow_forward_ios_rounded, size: 14, color: AppColors.textMuted),
          ],
        ),
      ),
    );
  }
}
