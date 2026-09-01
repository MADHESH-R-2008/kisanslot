import 'package:flutter/material.dart';
import '../services/api_service.dart';
import '../utils/app_colors.dart';

class AdminProcurementScreen extends StatefulWidget {
  final String bookingId;

  const AdminProcurementScreen({super.key, required this.bookingId});

  @override
  State<AdminProcurementScreen> createState() => _AdminProcurementScreenState();
}

class _AdminProcurementScreenState extends State<AdminProcurementScreen> {
  bool _isLoading = true;
  Map<String, dynamic>? _procurementData;

  final _weightController = TextEditingController();
  final _rateController = TextEditingController();
  String _qualityStatus = 'PENDING';

  @override
  void initState() {
    super.initState();
    _fetchProcurement();
  }

  Future<void> _fetchProcurement() async {
    try {
      final data = await ApiService.getProcurement(widget.bookingId);
      if (mounted) {
        setState(() {
          _procurementData = data;
          _rateController.text = data['rate'].toString();
          if (data['actual_weight'] != null) {
            _weightController.text = data['actual_weight'].toString();
          }
          _qualityStatus = data['quality_status'] == 'PENDING' ? 'GOOD' : data['quality_status'];
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

  Future<void> _submitProcurement() async {
    if (_weightController.text.isEmpty) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Please enter actual weight'), backgroundColor: AppColors.error),
      );
      return;
    }

    setState(() => _isLoading = true);

    try {
      final actualWeight = double.parse(_weightController.text);
      final rate = double.parse(_rateController.text);

      await ApiService.updateProcurement(widget.bookingId, {
        'actual_weight': actualWeight,
        'rate': rate,
        'quality_status': _qualityStatus,
        'status': 'COMPLETED'
      });
      
      // Update booking status to completed too
      await ApiService.updateBookingStatus(widget.bookingId, 'COMPLETED');

      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('Procurement logged successfully!'), backgroundColor: AppColors.success),
        );
        Navigator.pop(context);
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

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppColors.background,
      appBar: AppBar(
        title: const Text('Log Procurement', style: TextStyle(fontWeight: FontWeight.bold)),
      ),
      body: _isLoading
          ? const Center(child: CircularProgressIndicator())
          : _procurementData == null
              ? const Center(child: Text('Failed to load procurement details.'))
              : SingleChildScrollView(
                  padding: const EdgeInsets.all(16.0),
                  child: Card(
                    shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
                    child: Padding(
                      padding: const EdgeInsets.all(16.0),
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.stretch,
                        children: [
                          Text('Booking: ${widget.bookingId}', style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 18)),
                          const SizedBox(height: 8),
                          Text('Crop: ${_procurementData!['crop']}'),
                          Text('Expected Quantity: ${_procurementData!['expected_quantity']} kg'),
                          const Divider(height: 32),
                          const Text('Actual Weight (kg)', style: TextStyle(fontWeight: FontWeight.bold)),
                          const SizedBox(height: 8),
                          TextField(
                            controller: _weightController,
                            keyboardType: TextInputType.number,
                            decoration: const InputDecoration(
                              border: OutlineInputBorder(),
                              hintText: 'Enter measured weight',
                            ),
                          ),
                          const SizedBox(height: 16),
                          const Text('Quality Assessment', style: TextStyle(fontWeight: FontWeight.bold)),
                          const SizedBox(height: 8),
                          DropdownButtonFormField<String>(
                            value: _qualityStatus,
                            decoration: const InputDecoration(border: OutlineInputBorder()),
                            items: const [
                              DropdownMenuItem(value: 'EXCELLENT', child: Text('Excellent (Grade A)')),
                              DropdownMenuItem(value: 'GOOD', child: Text('Good (Grade B)')),
                              DropdownMenuItem(value: 'FAIR', child: Text('Fair (Grade C)')),
                              DropdownMenuItem(value: 'REJECTED', child: Text('Rejected')),
                            ],
                            onChanged: (value) {
                              if (value != null) setState(() => _qualityStatus = value);
                            },
                          ),
                          const SizedBox(height: 16),
                          const Text('Rate per kg (₹)', style: TextStyle(fontWeight: FontWeight.bold)),
                          const SizedBox(height: 8),
                          TextField(
                            controller: _rateController,
                            keyboardType: TextInputType.number,
                            decoration: const InputDecoration(
                              border: OutlineInputBorder(),
                            ),
                          ),
                          const SizedBox(height: 32),
                          ElevatedButton(
                            style: ElevatedButton.styleFrom(
                              backgroundColor: AppColors.primary,
                              padding: const EdgeInsets.symmetric(vertical: 16),
                            ),
                            onPressed: _submitProcurement,
                            child: const Text('SUBMIT & GENERATE BILL', style: TextStyle(color: Colors.white, fontSize: 16, fontWeight: FontWeight.bold)),
                          ),
                        ],
                      ),
                    ),
                  ),
                ),
    );
  }
}
