import 'package:flutter/material.dart';
import '../models/booking.dart';
import '../services/mock_data_service.dart';
import '../utils/app_colors.dart';
import '../widgets/custom_button.dart';
import '../widgets/queue_card.dart';

class QueueScreen extends StatefulWidget {
  const QueueScreen({super.key});

  @override
  State<QueueScreen> createState() => _QueueScreenState();
}

class _QueueScreenState extends State<QueueScreen> {
  final MockDataService _dataService = MockDataService();
  bool _isRefreshing = false;

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

  void _handleRefreshQueue() {
    setState(() => _isRefreshing = true);

    Future.delayed(const Duration(milliseconds: 500), () {
      if (!mounted) return;
      _dataService.refreshQueue();
      setState(() => _isRefreshing = false);

      final booking = _dataService.activeBooking;
      final pos = booking?.queuePosition ?? 17;
      final isTurn = pos <= 1;

      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text(
            isTurn
                ? '🎉 It is YOUR TURN! Please proceed to Counter #${booking?.counterNumber ?? 3}'
                : 'Queue updated: Position #$pos (${booking?.farmersAhead ?? 0} farmers ahead)',
          ),
          backgroundColor: isTurn ? AppColors.success : AppColors.primary,
          duration: const Duration(seconds: 2),
        ),
      );
    });
  }

  @override
  Widget build(BuildContext context) {
    final booking = _dataService.activeBooking ?? BookingModel.mockBooking();

    return Scaffold(
      backgroundColor: AppColors.background,
      appBar: AppBar(
        title: const Text('Live Queue'),
        leading: IconButton(
          icon: const Icon(Icons.arrow_back_ios_new_rounded),
          onPressed: () => Navigator.pop(context),
        ),
        actions: [
          IconButton(
            icon: _isRefreshing
                ? const SizedBox(
                    width: 18,
                    height: 18,
                    child: CircularProgressIndicator(strokeWidth: 2, color: AppColors.primary),
                  )
                : const Icon(Icons.refresh_rounded, color: AppColors.primary),
            tooltip: 'Refresh Queue',
            onPressed: _isRefreshing ? null : _handleRefreshQueue,
          ),
        ],
      ),
      body: SafeArea(
        child: SingleChildScrollView(
          padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 12),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              // Queue Status Announcement Strip
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 10),
                decoration: BoxDecoration(
                  color: AppColors.primaryContainer,
                  borderRadius: BorderRadius.circular(12),
                  border: Border.all(color: AppColors.primary.withValues(alpha: 0.2)),
                ),
                child: const Row(
                  children: [
                    Icon(Icons.sensors_rounded, color: AppColors.primary, size: 20),
                    SizedBox(width: 10),
                    Expanded(
                      child: Text(
                        'Live Token Stream is active. Tap Refresh to simulate queue updates.',
                        style: TextStyle(
                          fontSize: 12,
                          fontWeight: FontWeight.w600,
                          color: AppColors.primaryDark,
                        ),
                      ),
                    ),
                  ],
                ),
              ),
              const SizedBox(height: 16),

              // Main Queue Visualizer Card
              QueueCard(
                booking: booking,
                onRefresh: _handleRefreshQueue,
              ),
              const SizedBox(height: 20),

              // Refresh CTA Button
              CustomButton(
                text: 'REFRESH QUEUE',
                icon: Icons.refresh_rounded,
                isLoading: _isRefreshing,
                variant: ButtonVariant.primary,
                onPressed: _handleRefreshQueue,
              ),
              const SizedBox(height: 12),

              // Direct Counter Guidance Card
              Container(
                padding: const EdgeInsets.all(16),
                decoration: BoxDecoration(
                  color: Colors.white,
                  borderRadius: BorderRadius.circular(16),
                  border: Border.all(color: AppColors.cardBorder),
                ),
                child: Row(
                  children: [
                    Container(
                      padding: const EdgeInsets.all(10),
                      decoration: BoxDecoration(
                        color: AppColors.infoContainer,
                        borderRadius: BorderRadius.circular(12),
                      ),
                      child: const Icon(Icons.support_agent_rounded, color: AppColors.info, size: 24),
                    ),
                    const SizedBox(width: 14),
                    const Expanded(
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text(
                            'Queue Assistance',
                            style: TextStyle(
                              fontSize: 14,
                              fontWeight: FontWeight.bold,
                              color: AppColors.textPrimary,
                            ),
                          ),
                          SizedBox(height: 2),
                          Text(
                            'Need help or missed your turn? Speak to the Centre Desk Helper.',
                            style: TextStyle(fontSize: 12, color: AppColors.textSecondary),
                          ),
                        ],
                      ),
                    ),
                  ],
                ),
              ),
              const SizedBox(height: 24),
            ],
          ),
        ),
      ),
    );
  }
}
