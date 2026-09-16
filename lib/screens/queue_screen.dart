import 'package:flutter/material.dart';
import 'package:web_socket_channel/web_socket_channel.dart';
import 'dart:convert';
import '../models/booking.dart';
import '../services/api_service.dart';
import '../utils/app_colors.dart';
import '../widgets/custom_button.dart';
import '../widgets/queue_card.dart';

class QueueScreen extends StatefulWidget {
  const QueueScreen({super.key});

  @override
  State<QueueScreen> createState() => _QueueScreenState();
}

class _QueueScreenState extends State<QueueScreen> {
  bool _isRefreshing = false;
  bool _isLoading = true;
  BookingModel? _booking;
  String? _error;
  WebSocketChannel? _channel;

  @override
  void initState() {
    super.initState();
    _loadQueueData();
  }
  
  @override
  void dispose() {
    _channel?.sink.close();
    super.dispose();
  }
  
  void _setupWebSocket(int centreId) {
    if (_channel != null) return; // already connected
    
    // Determine WS url based on API base url
    final wsBase = ApiService.baseUrl.replaceFirst('http', 'ws');
    final wsUrl = Uri.parse('$wsBase/ws/queue/$centreId');
    
    _channel = WebSocketChannel.connect(wsUrl);
    _channel!.stream.listen((message) {
      try {
        final data = jsonDecode(message);
        if (data['event'] == 'QUEUE_UPDATED' || data['event'] == 'ACK') {
          _handleRefreshQueue();
        }
      } catch (e) {
        debugPrint('WebSocket parse error: $e');
      }
    }, onError: (error) {
      debugPrint('WebSocket error: $error');
    }, onDone: () {
      debugPrint('WebSocket disconnected');
      _channel = null;
    });
  }

  Future<void> _loadQueueData() async {
    setState(() {
      _isLoading = true;
      _error = null;
    });

    try {
      final bookingId = await ApiService.getActiveBookingId();
      if (bookingId == null || bookingId.isEmpty) {
        if (mounted) setState(() { _isLoading = false; _error = 'No active booking found.'; });
        return;
      }

      final bookingData = await ApiService.getBooking(bookingId);
      _booking = BookingModel.fromJson(bookingData);

      // Load queue position data
      final queueData = await ApiService.getQueue(bookingId);
      _booking = _booking!.copyWith(
        queuePosition: queueData['queue_position'] ?? 0,
        farmersAhead: queueData['farmers_ahead'] ?? 0,
        waitTimeMinutes: queueData['estimated_wait_minutes'] ?? 0,
        counterNumber: queueData['active_counters'] ?? 3,
        status: _parseStatus(queueData['status']),
        assignedCounterName: queueData['counter_name'],
        tokenDisplay: queueData['token_display'] ?? '',
      );
      
      _setupWebSocket(_booking!.centreId);

      if (mounted) setState(() => _isLoading = false);
    } on ApiException catch (e) {
      if (mounted) setState(() { _isLoading = false; _error = e.message; });
    } catch (e) {
      if (mounted) setState(() { _isLoading = false; _error = 'Unable to load queue data.'; });
    }
  }

  Future<void> _handleRefreshQueue() async {
    setState(() => _isRefreshing = true);

    try {
      final bookingId = await ApiService.getActiveBookingId();
      if (bookingId == null) {
        setState(() => _isRefreshing = false);
        return;
      }

      final queueData = await ApiService.getQueue(bookingId);
      final pos = queueData['queue_position'] ?? 0;
      final ahead = queueData['farmers_ahead'] ?? 0;

      _booking = _booking?.copyWith(
        queuePosition: pos,
        farmersAhead: ahead,
        waitTimeMinutes: queueData['estimated_wait_minutes'] ?? 0,
        counterNumber: queueData['active_counters'] ?? 3,
        status: _parseStatus(queueData['status']),
        assignedCounterName: queueData['counter_name'],
        tokenDisplay: queueData['token_display'] ?? '',
      );

      if (mounted) {
        setState(() => _isRefreshing = false);

        final bool isTurn = _booking!.status == BookingStatus.called || _booking!.status == BookingStatus.serving || pos <= 1;
        String message;
        Color bgColor = AppColors.primary;
        
        if (_booking!.status == BookingStatus.called) {
          message = '🔊 YOUR TOKEN IS CALLED! Proceed to ${_booking!.assignedCounterName ?? "the counter"}.';
          bgColor = const Color(0xFF8B5CF6);
        } else if (_booking!.status == BookingStatus.serving) {
          message = '🟢 Currently Serving at ${_booking!.assignedCounterName ?? "the counter"}.';
          bgColor = const Color(0xFF10B981);
        } else if (isTurn) {
          message = '🎉 It is almost YOUR TURN!';
          bgColor = AppColors.success;
        } else {
          message = 'Queue updated: Position #$pos ($ahead farmers ahead)';
        }

        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text(message),
            backgroundColor: bgColor,
            duration: const Duration(seconds: 4),
          ),
        );
      }
    } catch (e) {
      if (mounted) {
        setState(() => _isRefreshing = false);
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text('Failed to refresh: $e'),
            backgroundColor: AppColors.error,
          ),
        );
      }
    }
  }

  BookingStatus _parseStatus(dynamic statusStr) {
    if (statusStr == null) return BookingStatus.inQueue;
    final s = statusStr.toString().toUpperCase();
    switch (s) {
      case 'CONFIRMED': return BookingStatus.confirmed;
      case 'ARRIVED':
      case 'VERIFIED':
      case 'WAITING': return BookingStatus.inQueue;
      case 'CALLED': return BookingStatus.called;
      case 'SERVING': return BookingStatus.serving;
      case 'PROCESSING': return BookingStatus.procuring;
      case 'COMPLETED': return BookingStatus.completed;
      case 'CANCELLED': return BookingStatus.cancelled;
      case 'NO_SHOW': return BookingStatus.noShow;
      case 'SKIPPED': return BookingStatus.skipped;
      default: return BookingStatus.inQueue;
    }
  }

  @override
  Widget build(BuildContext context) {
    if (_isLoading) {
      return Scaffold(
        backgroundColor: AppColors.background,
        appBar: AppBar(title: const Text('Live Queue')),
        body: const Center(
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              CircularProgressIndicator(color: AppColors.primary),
              SizedBox(height: 16),
              Text('Loading queue...', style: TextStyle(color: AppColors.textSecondary)),
            ],
          ),
        ),
      );
    }

    if (_error != null || _booking == null) {
      return Scaffold(
        backgroundColor: AppColors.background,
        appBar: AppBar(
          title: const Text('Live Queue'),
          leading: IconButton(
            icon: const Icon(Icons.arrow_back_ios_new_rounded),
            onPressed: () => Navigator.pop(context),
          ),
        ),
        body: Center(
          child: Padding(
            padding: const EdgeInsets.all(32),
            child: Column(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                const Icon(Icons.groups_outlined, size: 64, color: AppColors.textMuted),
                const SizedBox(height: 16),
                Text(_error ?? 'No active booking.', textAlign: TextAlign.center, style: const TextStyle(color: AppColors.textSecondary, fontSize: 16)),
                const SizedBox(height: 24),
                ElevatedButton.icon(
                  onPressed: _loadQueueData,
                  icon: const Icon(Icons.refresh),
                  label: const Text('TRY AGAIN'),
                ),
              ],
            ),
          ),
        ),
      );
    }

    final booking = _booking!;

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
                        'Live Token Stream is active. Tap Refresh to get latest queue data.',
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
