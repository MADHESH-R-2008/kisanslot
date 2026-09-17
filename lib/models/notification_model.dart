import 'package:flutter/material.dart';

class NotificationModel {
  final int id;
  final int? userId;
  final int? bookingId;
  final int? centreId;
  final String type;
  final String title;
  final String message;
  final bool isRead;
  final DateTime createdAt;
  final DateTime? updatedAt;

  NotificationModel({
    required this.id,
    this.userId,
    this.bookingId,
    this.centreId,
    required this.type,
    required this.title,
    required this.message,
    required this.isRead,
    required this.createdAt,
    this.updatedAt,
  });

  factory NotificationModel.fromJson(Map<String, dynamic> json) {
    return NotificationModel(
      id: json['id'],
      userId: json['user_id'],
      bookingId: json['booking_id'],
      centreId: json['centre_id'],
      type: json['type'] ?? 'SYSTEM',
      title: json['title'] ?? '',
      message: json['message'] ?? '',
      isRead: json['is_read'] ?? false,
      createdAt: json['created_at'] != null
          ? DateTime.parse(json['created_at'])
          : DateTime.now(),
      updatedAt: json['updated_at'] != null
          ? DateTime.parse(json['updated_at'])
          : null,
    );
  }

  NotificationModel copyWith({bool? isRead}) {
    return NotificationModel(
      id: id,
      userId: userId,
      bookingId: bookingId,
      centreId: centreId,
      type: type,
      title: title,
      message: message,
      isRead: isRead ?? this.isRead,
      createdAt: createdAt,
      updatedAt: updatedAt,
    );
  }

  String get timeAgo {
    final now = DateTime.now();
    final difference = now.difference(createdAt);

    if (difference.inSeconds < 60) {
      return 'Just now';
    } else if (difference.inMinutes < 60) {
      return '${difference.inMinutes} min ago';
    } else if (difference.inHours < 24) {
      return '${difference.inHours} hour${difference.inHours > 1 ? 's' : ''} ago';
    } else if (difference.inDays == 1) {
      return 'Yesterday';
    } else if (difference.inDays < 7) {
      return '${difference.inDays} days ago';
    } else {
      return '${createdAt.day}/${createdAt.month}/${createdAt.year}';
    }
  }

  IconData get iconData {
    switch (type) {
      case 'BOOKING_CONFIRMED':
        return Icons.confirmation_number_rounded;
      case 'QUEUE_UPDATE':
        return Icons.format_list_numbered_rounded;
      case 'FARMER_CALLED':
        return Icons.campaign_rounded;
      case 'PROCUREMENT_STARTED':
        return Icons.inventory_2_rounded;
      case 'PROCUREMENT_COMPLETED':
        return Icons.task_alt_rounded;
      case 'PAYMENT_PROCESSING':
        return Icons.sync_rounded;
      case 'PAYMENT_COMPLETED':
        return Icons.account_balance_wallet_rounded;
      case 'PAYMENT_FAILED':
        return Icons.error_rounded;
      case 'CENTRE_UPDATE':
        return Icons.storefront_rounded;
      case 'SYSTEM':
      default:
        return Icons.notifications_active_rounded;
    }
  }

  Color get iconColor {
    switch (type) {
      case 'BOOKING_CONFIRMED':
        return const Color(0xFF10B981); // Emerald
      case 'QUEUE_UPDATE':
        return const Color(0xFF3B82F6); // Blue
      case 'FARMER_CALLED':
        return const Color(0xFFF59E0B); // Amber
      case 'PROCUREMENT_STARTED':
        return const Color(0xFF8B5CF6); // Purple
      case 'PROCUREMENT_COMPLETED':
        return const Color(0xFF059669); // Green
      case 'PAYMENT_PROCESSING':
        return const Color(0xFF0284C7); // Sky
      case 'PAYMENT_COMPLETED':
        return const Color(0xFF16A34A); // Success Green
      case 'PAYMENT_FAILED':
        return const Color(0xFFEF4444); // Red
      case 'CENTRE_UPDATE':
        return const Color(0xFF6366F1); // Indigo
      case 'SYSTEM':
      default:
        return const Color(0xFF6B7280); // Gray
    }
  }
}
