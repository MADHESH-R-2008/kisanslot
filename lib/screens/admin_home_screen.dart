import 'package:flutter/material.dart';
import '../services/api_service.dart';
import '../utils/app_colors.dart';
import '../utils/routes.dart';

class AdminHomeScreen extends StatefulWidget {
  const AdminHomeScreen({super.key});

  @override
  State<AdminHomeScreen> createState() => _AdminHomeScreenState();
}

class _AdminHomeScreenState extends State<AdminHomeScreen> {
  List<dynamic> _queue = [];
  bool _isLoading = true;

  @override
  void initState() {
    super.initState();
    _fetchQueue();
  }

  Future<void> _fetchQueue() async {
    setState(() => _isLoading = true);
    try {
      final queue = await ApiService.getAdminQueue();
      if (mounted) {
        setState(() {
          _queue = queue;
          _isLoading = false;
        });
      }
    } catch (e) {
      if (mounted) {
        setState(() => _isLoading = false);
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Error: $e'), backgroundColor: AppColors.error),
        );
      }
    }
  }

  Future<void> _updateStatus(String bookingId, String newStatus) async {
    try {
      await ApiService.updateBookingStatus(bookingId, newStatus);
      _fetchQueue(); // Refresh list
    } catch (e) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('Error: $e'), backgroundColor: AppColors.error),
      );
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppColors.background,
      appBar: AppBar(
        title: const Text('Admin Dashboard', style: TextStyle(fontWeight: FontWeight.bold)),
        actions: [
          IconButton(
            icon: const Icon(Icons.refresh),
            onPressed: _fetchQueue,
          ),
          IconButton(
            icon: const Icon(Icons.logout),
            onPressed: () async {
              await ApiService.logout();
              if (context.mounted) Navigator.pushReplacementNamed(context, AppRoutes.login);
            },
          ),
        ],
      ),
      body: _isLoading
          ? const Center(child: CircularProgressIndicator())
          : _queue.isEmpty
              ? const Center(child: Text('No active bookings in queue today.'))
              : ListView.builder(
                  padding: const EdgeInsets.all(16),
                  itemCount: _queue.length,
                  itemBuilder: (context, index) {
                    final item = _queue[index];
                    return _buildQueueCard(item);
                  },
                ),
    );
  }

  Widget _buildQueueCard(Map<String, dynamic> item) {
    final status = item['status'] as String;
    return Card(
      margin: const EdgeInsets.only(bottom: 16),
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
      child: Padding(
        padding: const EdgeInsets.all(16.0),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                Text(
                  'Token: #${item['token_number']}',
                  style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 18),
                ),
                Chip(
                  label: Text(status),
                  backgroundColor: _getStatusColor(status).withValues(alpha: 0.1),
                  labelStyle: TextStyle(color: _getStatusColor(status), fontWeight: FontWeight.bold),
                )
              ],
            ),
            const SizedBox(height: 8),
            Text('Booking ID: ${item['booking_id']}'),
            Text('Crop: ${item['crop']} (${item['quantity']} kg)'),
            Text('Vehicle: ${item['vehicle_number']}'),
            const SizedBox(height: 16),
            const Divider(),
            Row(
              mainAxisAlignment: MainAxisAlignment.end,
              children: _buildActionButtons(item['booking_id'], status),
            )
          ],
        ),
      ),
    );
  }

  List<Widget> _buildActionButtons(String bookingId, String status) {
    if (status == 'CONFIRMED') {
      return [
        ElevatedButton(
          onPressed: () => _updateStatus(bookingId, 'ARRIVED'),
          child: const Text('Mark Arrived'),
        ),
      ];
    } else if (status == 'ARRIVED') {
      return [
        ElevatedButton(
          onPressed: () => _updateStatus(bookingId, 'PROCESSING'),
          child: const Text('Start Processing'),
        ),
      ];
    } else if (status == 'PROCESSING') {
      return [
        ElevatedButton(
          style: ElevatedButton.styleFrom(backgroundColor: AppColors.primary),
          onPressed: () {
            Navigator.pushNamed(context, AppRoutes.adminProcurement, arguments: bookingId)
                .then((_) => _fetchQueue());
          },
          child: const Text('Log Procurement', style: TextStyle(color: Colors.white)),
        ),
      ];
    }
    return [];
  }

  Color _getStatusColor(String status) {
    switch (status) {
      case 'CONFIRMED': return Colors.blue;
      case 'ARRIVED': return Colors.orange;
      case 'PROCESSING': return Colors.deepPurple;
      case 'COMPLETED': return Colors.green;
      default: return Colors.grey;
    }
  }
}
