import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:intl/intl.dart';
import '../models/centre.dart';
import '../models/slot.dart';
import '../models/booking.dart';
import '../services/api_service.dart';
import '../utils/app_colors.dart';
import '../utils/routes.dart';
import '../widgets/custom_button.dart';

class SlotBookingScreen extends StatefulWidget {
  final ProcurementCentre? selectedCentre;

  const SlotBookingScreen({
    super.key,
    this.selectedCentre,
  });

  @override
  State<SlotBookingScreen> createState() => _SlotBookingScreenState();
}

class _SlotBookingScreenState extends State<SlotBookingScreen> {
  final _formKey = GlobalKey<FormState>();

  late ProcurementCentre _centre;
  late DateTime _selectedDate;
  int? _selectedSlotId;
  late String _selectedCrop;
  late TextEditingController _quantityController;
  late TextEditingController _vehicleController;
  bool _isLoading = false;
  bool _isSlotsLoading = true;
  String? _slotsError;
  List<TimeSlot> _slots = [];

  final List<String> _crops = [
    'Paddy',
    'Wheat',
    'Maize',
    'Cotton',
    'Sugarcane',
    'Other',
  ];

  @override
  void initState() {
    super.initState();
    _centre = widget.selectedCentre ?? ProcurementCentre.getMockCentres()[1];
    _selectedDate = DateTime.now();
    _selectedCrop = 'Paddy';
    _quantityController = TextEditingController(text: '850');
    _vehicleController = TextEditingController(text: 'TN 01 AB 1234');

    _loadSlots();
  }

  Future<void> _loadSlots() async {
    setState(() {
      _isSlotsLoading = true;
      _slotsError = null;
    });

    try {
      final dateStr = DateFormat('yyyy-MM-dd').format(_selectedDate);
      final data = await ApiService.getSlots(_centre.id, dateStr);
      _slots = data.map((json) => TimeSlot.fromJson(json)).toList();

      // Auto-select first available slot
      _selectedSlotId = null;
      for (final slot in _slots) {
        if (slot.isAvailable) {
          _selectedSlotId = slot.id;
          break;
        }
      }

      if (mounted) setState(() => _isSlotsLoading = false);
    } on ApiException catch (e) {
      if (mounted) setState(() { _isSlotsLoading = false; _slotsError = e.message; });
    } catch (e) {
      if (mounted) setState(() { _isSlotsLoading = false; _slotsError = 'Unable to load slots.'; });
    }
  }

  @override
  void dispose() {
    _quantityController.dispose();
    _vehicleController.dispose();
    super.dispose();
  }

  Future<void> _handleConfirmBooking() async {
    if (_formKey.currentState!.validate()) {
      if (_selectedSlotId == null) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(
            content: Text('Please select a time slot.'),
            backgroundColor: AppColors.error,
          ),
        );
        return;
      }

      setState(() => _isLoading = true);

      try {
        final data = await ApiService.createBooking(
          centreId: _centre.id,
          slotId: _selectedSlotId!,
          crop: _selectedCrop,
          expectedQuantity: double.tryParse(_quantityController.text.trim()) ?? 850.0,
          vehicleNumber: _vehicleController.text.trim().toUpperCase(),
        );

        if (!mounted) return;
        setState(() => _isLoading = false);

        final newBooking = BookingModel.fromCreateResponse(data);

        Navigator.pushReplacementNamed(
          context,
          AppRoutes.confirmation,
          arguments: newBooking,
        );
      } on ApiException catch (e) {
        if (!mounted) return;
        setState(() => _isLoading = false);
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text(e.message),
            backgroundColor: AppColors.error,
            duration: const Duration(seconds: 3),
          ),
        );
      } catch (e) {
        if (!mounted) return;
        setState(() => _isLoading = false);
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text('Booking failed: $e'),
            backgroundColor: AppColors.error,
          ),
        );
      }
    }
  }

  Future<void> _pickDate() async {
    final picked = await showDatePicker(
      context: context,
      initialDate: _selectedDate,
      firstDate: DateTime(2026, 1, 1),
      lastDate: DateTime(2027, 12, 31),
      builder: (context, child) {
        return Theme(
          data: Theme.of(context).copyWith(
            colorScheme: const ColorScheme.light(
              primary: AppColors.primary,
              onPrimary: Colors.white,
              onSurface: AppColors.textPrimary,
            ),
          ),
          child: child!,
        );
      },
    );
    if (picked != null) {
      setState(() => _selectedDate = picked);
      _loadSlots(); // Reload slots for new date
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppColors.background,
      appBar: AppBar(
        title: const Text('Book Procurement Slot'),
        leading: IconButton(
          icon: const Icon(Icons.arrow_back_ios_new_rounded),
          onPressed: () => Navigator.pop(context),
        ),
      ),
      body: SafeArea(
        child: SingleChildScrollView(
          padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 12),
          child: Form(
            key: _formKey,
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                // Selected Centre Summary Box
                Container(
                  padding: const EdgeInsets.all(16),
                  decoration: BoxDecoration(
                    color: Colors.white,
                    borderRadius: BorderRadius.circular(16),
                    border: Border.all(color: AppColors.cardBorder),
                    boxShadow: [
                      BoxShadow(
                        color: Colors.black.withOpacity(0.04),
                        blurRadius: 8,
                        offset: const Offset(0, 2),
                      ),
                    ],
                  ),
                  child: Row(
                    children: [
                      Container(
                        padding: const EdgeInsets.all(12),
                        decoration: BoxDecoration(
                          color: AppColors.primaryContainer,
                          borderRadius: BorderRadius.circular(12),
                        ),
                        child: const Icon(Icons.storefront_rounded, color: AppColors.primary, size: 26),
                      ),
                      const SizedBox(width: 14),
                      Expanded(
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            const Text(
                              'Selected Centre',
                              style: TextStyle(fontSize: 12, color: AppColors.textSecondary),
                            ),
                            const SizedBox(height: 2),
                            Text(
                              _centre.name,
                              style: const TextStyle(
                                fontSize: 18,
                                fontWeight: FontWeight.bold,
                                color: AppColors.textPrimary,
                              ),
                            ),
                            const SizedBox(height: 2),
                            Text(
                              '${_centre.distanceKm} km away • ${_centre.queueCount} in queue',
                              style: const TextStyle(fontSize: 12, color: AppColors.textSecondary),
                            ),
                          ],
                        ),
                      ),
                      TextButton(
                        onPressed: () => Navigator.pop(context),
                        child: const Text('Change'),
                      ),
                    ],
                  ),
                ),
                const SizedBox(height: 20),

                // Date Selection Section
                const Text(
                  'Select Date',
                  style: TextStyle(
                    fontSize: 16,
                    fontWeight: FontWeight.bold,
                    color: AppColors.textPrimary,
                  ),
                ),
                const SizedBox(height: 8),

                InkWell(
                  onTap: _pickDate,
                  borderRadius: BorderRadius.circular(14),
                  child: Container(
                    padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 14),
                    decoration: BoxDecoration(
                      color: Colors.white,
                      borderRadius: BorderRadius.circular(14),
                      border: Border.all(color: AppColors.primary, width: 1.5),
                    ),
                    child: Row(
                      children: [
                        const Icon(Icons.calendar_today_rounded, color: AppColors.primary, size: 20),
                        const SizedBox(width: 12),
                        Expanded(
                          child: Text(
                            DateFormat('dd MMMM yyyy').format(_selectedDate),
                            style: const TextStyle(
                              fontSize: 16,
                              fontWeight: FontWeight.bold,
                              color: AppColors.textPrimary,
                            ),
                            maxLines: 1,
                            overflow: TextOverflow.ellipsis,
                          ),
                        ),
                        const SizedBox(width: 8),
                        Container(
                          padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
                          decoration: BoxDecoration(
                            color: AppColors.primaryContainer,
                            borderRadius: BorderRadius.circular(8),
                          ),
                          child: const Text(
                            'Change',
                            style: TextStyle(
                              fontSize: 12,
                              fontWeight: FontWeight.bold,
                              color: AppColors.primaryDark,
                            ),
                          ),
                        ),
                      ],
                    ),
                  ),
                ),
                const SizedBox(height: 24),

                // Available Time Slots Header & Legend
                const Text(
                  'Available Time Slots',
                  style: TextStyle(
                    fontSize: 16,
                    fontWeight: FontWeight.bold,
                    color: AppColors.textPrimary,
                  ),
                ),
                const SizedBox(height: 6),

                // Legend row
                Wrap(
                  spacing: 12,
                  runSpacing: 4,
                  children: [
                    _buildLegendItem(AppColors.primary, 'Selected'),
                    _buildLegendItem(Colors.white, 'Available', hasBorder: true),
                    _buildLegendItem(Colors.grey.shade300, 'Full'),
                  ],
                ),
                const SizedBox(height: 12),

                // Grid of Time Slots — from API
                if (_isSlotsLoading)
                  const Padding(
                    padding: EdgeInsets.all(32),
                    child: Center(
                      child: Column(
                        children: [
                          CircularProgressIndicator(color: AppColors.primary),
                          SizedBox(height: 12),
                          Text('Loading slots...', style: TextStyle(color: AppColors.textSecondary)),
                        ],
                      ),
                    ),
                  )
                else if (_slotsError != null)
                  Padding(
                    padding: const EdgeInsets.all(32),
                    child: Center(
                      child: Column(
                        children: [
                          const Icon(Icons.cloud_off_rounded, size: 48, color: AppColors.textMuted),
                          const SizedBox(height: 12),
                          Text(_slotsError!, style: const TextStyle(color: AppColors.textSecondary)),
                          const SizedBox(height: 12),
                          ElevatedButton(onPressed: _loadSlots, child: const Text('TRY AGAIN')),
                        ],
                      ),
                    ),
                  )
                else if (_slots.isEmpty)
                  const Padding(
                    padding: EdgeInsets.all(32),
                    child: Center(
                      child: Text('No available slots for this date.', style: TextStyle(color: AppColors.textSecondary)),
                    ),
                  )
                else
                  LayoutBuilder(
                    builder: (context, constraints) {
                      final itemWidth = (constraints.maxWidth - 10) / 2;
                      return Wrap(
                        spacing: 10,
                        runSpacing: 10,
                        children: _slots.map((slot) {
                          final isSelected = _selectedSlotId == slot.id;
                          return SizedBox(
                            width: itemWidth,
                            child: _buildSlotCard(slot, isSelected: isSelected),
                          );
                        }).toList(),
                      );
                    },
                  ),
                const SizedBox(height: 24),

                // Produce and Vehicle Details Form
                const Text(
                  'Produce & Vehicle Details',
                  style: TextStyle(
                    fontSize: 16,
                    fontWeight: FontWeight.bold,
                    color: AppColors.textPrimary,
                  ),
                ),
                const SizedBox(height: 12),

                // Crop Dropdown
                _buildFieldLabel('Crop'),
                DropdownButtonFormField<String>(
                  value: _selectedCrop,
                  decoration: const InputDecoration(
                    prefixIcon: Icon(Icons.grass_rounded),
                  ),
                  items: _crops.map((c) {
                    return DropdownMenuItem(
                      value: c,
                      child: Text(c, style: const TextStyle(fontWeight: FontWeight.w600)),
                    );
                  }).toList(),
                  onChanged: (val) {
                    if (val != null) setState(() => _selectedCrop = val);
                  },
                ),
                const SizedBox(height: 14),

                // Expected Quantity
                _buildFieldLabel('Expected Quantity'),
                TextFormField(
                  controller: _quantityController,
                  keyboardType: const TextInputType.numberWithOptions(decimal: true),
                  inputFormatters: [
                    FilteringTextInputFormatter.allow(RegExp(r'^\d+\.?\d{0,2}')),
                  ],
                  decoration: const InputDecoration(
                    hintText: 'e.g. 850',
                    prefixIcon: Icon(Icons.scale_outlined),
                    suffixText: 'kg',
                    suffixStyle: TextStyle(fontWeight: FontWeight.bold, color: AppColors.primary),
                  ),
                  validator: (val) {
                    if (val == null || val.trim().isEmpty) return 'Enter quantity';
                    final qty = double.tryParse(val.trim());
                    if (qty == null || qty <= 0) return 'Invalid quantity';
                    return null;
                  },
                ),
                const SizedBox(height: 14),

                // Vehicle Number
                _buildFieldLabel('Vehicle Number'),
                TextFormField(
                  controller: _vehicleController,
                  textCapitalization: TextCapitalization.characters,
                  decoration: const InputDecoration(
                    hintText: 'e.g. TN 01 AB 1234',
                    prefixIcon: Icon(Icons.local_shipping_outlined),
                  ),
                  validator: (val) {
                    if (val == null || val.trim().isEmpty) return 'Vehicle number is required';
                    return null;
                  },
                ),
                const SizedBox(height: 28),

                // Confirm Booking Button
                CustomButton(
                  text: 'CONFIRM BOOKING',
                  icon: Icons.check_circle_outline_rounded,
                  isLoading: _isLoading,
                  onPressed: _handleConfirmBooking,
                ),
                const SizedBox(height: 24),
              ],
            ),
          ),
        ),
      ),
    );
  }

  Widget _buildSlotCard(TimeSlot slot, {required bool isSelected}) {
    final bool isAvailable = slot.isAvailable;

    Color bgColor = Colors.white;
    Color textColor = AppColors.textPrimary;
    Color borderColor = AppColors.cardBorder;

    if (!isAvailable) {
      bgColor = Colors.grey.shade100;
      textColor = AppColors.textMuted;
      borderColor = Colors.grey.shade300;
    } else if (isSelected) {
      bgColor = AppColors.primary;
      textColor = Colors.white;
      borderColor = AppColors.primaryDark;
    }

    return InkWell(
      onTap: isAvailable
          ? () {
              setState(() => _selectedSlotId = slot.id);
            }
          : null,
      borderRadius: BorderRadius.circular(12),
      child: Container(
        padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 8),
        decoration: BoxDecoration(
          color: bgColor,
          borderRadius: BorderRadius.circular(12),
          border: Border.all(
            color: borderColor,
            width: isSelected ? 2 : 1,
          ),
          boxShadow: isSelected
              ? [
                  BoxShadow(
                    color: AppColors.primary.withOpacity(0.25),
                    blurRadius: 8,
                    offset: const Offset(0, 3),
                  ),
                ]
              : null,
        ),
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              slot.timeRange,
              style: TextStyle(
                fontSize: 12,
                fontWeight: FontWeight.bold,
                color: textColor,
              ),
              maxLines: 1,
              overflow: TextOverflow.ellipsis,
            ),
            const SizedBox(height: 3),
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                Flexible(
                  child: Text(
                    isAvailable ? '${slot.availableCount} left' : 'Full',
                    style: TextStyle(
                      fontSize: 11,
                      fontWeight: FontWeight.w600,
                      color: !isAvailable
                          ? AppColors.error
                          : (isSelected ? Colors.white70 : AppColors.success),
                    ),
                  ),
                ),
                if (isSelected)
                  const Icon(Icons.check_circle, size: 14, color: Colors.white)
                else if (!isAvailable)
                  const Icon(Icons.block, size: 14, color: AppColors.error),
              ],
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildFieldLabel(String label) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 6),
      child: Text(
        label,
        style: const TextStyle(
          fontSize: 13,
          fontWeight: FontWeight.w600,
          color: AppColors.textPrimary,
        ),
      ),
    );
  }

  Widget _buildLegendItem(Color color, String label, {bool hasBorder = false}) {
    return Row(
      mainAxisSize: MainAxisSize.min,
      children: [
        Container(
          width: 10,
          height: 10,
          decoration: BoxDecoration(
            color: color,
            borderRadius: BorderRadius.circular(2),
            border: hasBorder ? Border.all(color: AppColors.cardBorder) : null,
          ),
        ),
        const SizedBox(width: 4),
        Text(
          label,
          style: const TextStyle(fontSize: 11, color: AppColors.textSecondary),
        ),
      ],
    );
  }
}
