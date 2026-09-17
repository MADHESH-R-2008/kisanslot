import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import '../services/api_service.dart';
import '../utils/app_colors.dart';
import '../utils/routes.dart';
import '../widgets/custom_button.dart';

class RegisterScreen extends StatefulWidget {
  const RegisterScreen({super.key});

  @override
  State<RegisterScreen> createState() => _RegisterScreenState();
}

class _RegisterScreenState extends State<RegisterScreen> {
  final _formKey = GlobalKey<FormState>();

  final _nameController = TextEditingController();
  final _mobileController = TextEditingController();
  final _farmerIdController = TextEditingController();
  final _villageController = TextEditingController();
  final _districtController = TextEditingController();
  final _stateController = TextEditingController();
  final _quantityController = TextEditingController(text: '850');
  final _passwordController = TextEditingController();
  final _confirmPasswordController = TextEditingController();

  final List<String> _crops = [
    'Paddy',
    'Wheat',
    'Maize',
    'Cotton',
    'Sugarcane',
    'Other',
  ];
  String _selectedCrop = 'Paddy';
  bool _isLoading = false;
  bool _obscurePassword = true;
  bool _obscureConfirm = true;

  @override
  void dispose() {
    _nameController.dispose();
    _mobileController.dispose();
    _farmerIdController.dispose();
    _villageController.dispose();
    _districtController.dispose();
    _stateController.dispose();
    _quantityController.dispose();
    _passwordController.dispose();
    _confirmPasswordController.dispose();
    super.dispose();
  }

  Future<void> _handleRegister() async {
    if (_formKey.currentState!.validate()) {
      setState(() => _isLoading = true);

      try {
        // Generate farmer ID if not provided
        String farmerId = _farmerIdController.text.trim();
        if (farmerId.isEmpty) {
          farmerId = 'FR${DateTime.now().millisecondsSinceEpoch % 90000 + 10000}';
        }

        await ApiService.register(
          name: _nameController.text.trim(),
          mobile: _mobileController.text.trim(),
          farmerId: farmerId,
          village: _villageController.text.trim(),
          district: _districtController.text.trim(),
          state: _stateController.text.trim(),
          crop: _selectedCrop,
          expectedQuantity: double.tryParse(_quantityController.text.trim()) ?? 850.0,
          password: _passwordController.text.trim(),
        );

        if (!mounted) return;
        setState(() => _isLoading = false);

        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text('Farmer account registered for ${_nameController.text.trim()}!'),
            backgroundColor: AppColors.success,
          ),
        );

        Navigator.pushNamedAndRemoveUntil(context, AppRoutes.home, (route) => false);
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
            content: Text('Connection error: $e'),
            backgroundColor: AppColors.error,
            duration: const Duration(seconds: 4),
          ),
        );
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppColors.background,
      appBar: AppBar(
        title: const Text('Create Farmer Account'),
        leading: IconButton(
          icon: const Icon(Icons.arrow_back_ios_new_rounded),
          onPressed: () => Navigator.pop(context),
        ),
      ),
      body: SafeArea(
        child: SingleChildScrollView(
          padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 16),
          child: Form(
            key: _formKey,
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                // Header Banner
                Container(
                  padding: const EdgeInsets.all(16),
                  decoration: BoxDecoration(
                    color: AppColors.primaryContainer,
                    borderRadius: BorderRadius.circular(16),
                    border: Border.all(color: AppColors.primary.withValues(alpha: 0.15)),
                  ),
                  child: const Row(
                    children: [
                      Text('👨‍🌾', style: TextStyle(fontSize: 32)),
                      SizedBox(width: 14),
                      Expanded(
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Text(
                              'Farmer Registration',
                              style: TextStyle(
                                fontSize: 16,
                                fontWeight: FontWeight.bold,
                                color: AppColors.primaryDark,
                              ),
                            ),
                            SizedBox(height: 2),
                            Text(
                              'Quick onboarding for slot booking and live queue access',
                              style: TextStyle(fontSize: 12, color: AppColors.textSecondary),
                            ),
                          ],
                        ),
                      ),
                    ],
                  ),
                ),
                const SizedBox(height: 22),

                // Full Name
                _buildFieldLabel('Full Name *'),
                TextFormField(
                  controller: _nameController,
                  textCapitalization: TextCapitalization.words,
                  decoration: const InputDecoration(
                    hintText: 'Enter farmer full name',
                    prefixIcon: Icon(Icons.person_outline_rounded),
                  ),
                  validator: (val) => val == null || val.trim().isEmpty ? 'Full name is required' : null,
                ),
                const SizedBox(height: 16),

                // Mobile Number
                _buildFieldLabel('Mobile Number *'),
                TextFormField(
                  controller: _mobileController,
                  keyboardType: TextInputType.phone,
                  inputFormatters: [
                    FilteringTextInputFormatter.digitsOnly,
                    LengthLimitingTextInputFormatter(10),
                  ],
                  decoration: const InputDecoration(
                    hintText: 'Enter 10-digit mobile',
                    prefixIcon: Icon(Icons.phone_android_rounded),
                    prefixText: '+91 ',
                  ),
                  validator: (val) {
                    if (val == null || val.trim().isEmpty) return 'Mobile number is required';
                    if (val.trim().length != 10) return 'Must be 10 digits';
                    return null;
                  },
                ),
                const SizedBox(height: 16),

                // Farmer ID
                _buildFieldLabel('Farmer ID (Optional / Auto-assigned)'),
                TextFormField(
                  controller: _farmerIdController,
                  decoration: const InputDecoration(
                    hintText: 'e.g. FR10245',
                    prefixIcon: Icon(Icons.badge_outlined),
                  ),
                ),
                const SizedBox(height: 16),

                // Village, District, State Row / Column
                _buildFieldLabel('Village *'),
                TextFormField(
                  controller: _villageController,
                  decoration: const InputDecoration(
                    hintText: 'Enter village name',
                    prefixIcon: Icon(Icons.home_work_outlined),
                  ),
                  validator: (val) => val == null || val.trim().isEmpty ? 'Village is required' : null,
                ),
                const SizedBox(height: 16),

                Row(
                  children: [
                    Expanded(
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          _buildFieldLabel('District *'),
                          TextFormField(
                            controller: _districtController,
                            decoration: const InputDecoration(
                              hintText: 'District',
                              prefixIcon: Icon(Icons.location_city_outlined),
                            ),
                            validator: (val) => val == null || val.trim().isEmpty ? 'Required' : null,
                          ),
                        ],
                      ),
                    ),
                    const SizedBox(width: 12),
                    Expanded(
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          _buildFieldLabel('State *'),
                          TextFormField(
                            controller: _stateController,
                            decoration: const InputDecoration(
                              hintText: 'State',
                              prefixIcon: Icon(Icons.map_outlined),
                            ),
                            validator: (val) => val == null || val.trim().isEmpty ? 'Required' : null,
                          ),
                        ],
                      ),
                    ),
                  ],
                ),
                const SizedBox(height: 16),

                // Crop Dropdown
                _buildFieldLabel('Primary Crop *'),
                DropdownButtonFormField<String>(
                  initialValue: _selectedCrop,
                  decoration: const InputDecoration(
                    prefixIcon: Icon(Icons.grass_rounded),
                  ),
                  items: _crops.map((crop) {
                    return DropdownMenuItem<String>(
                      value: crop,
                      child: Text(crop, style: const TextStyle(fontWeight: FontWeight.w600)),
                    );
                  }).toList(),
                  onChanged: (val) {
                    if (val != null) setState(() => _selectedCrop = val);
                  },
                ),
                const SizedBox(height: 16),

                // Expected Quantity
                _buildFieldLabel('Expected Quantity (in kg) *'),
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
                    if (val == null || val.trim().isEmpty) return 'Expected quantity is required';
                    final qty = double.tryParse(val.trim());
                    if (qty == null || qty <= 0) return 'Enter a valid quantity in kg';
                    return null;
                  },
                ),
                const SizedBox(height: 16),

                // Password
                _buildFieldLabel('Password *'),
                TextFormField(
                  controller: _passwordController,
                  obscureText: _obscurePassword,
                  decoration: InputDecoration(
                    hintText: 'Create a password',
                    prefixIcon: const Icon(Icons.lock_outline_rounded),
                    suffixIcon: IconButton(
                      icon: Icon(_obscurePassword ? Icons.visibility_off_outlined : Icons.visibility_outlined),
                      onPressed: () => setState(() => _obscurePassword = !_obscurePassword),
                    ),
                  ),
                  validator: (val) {
                    if (val == null || val.trim().isEmpty) return 'Password is required';
                    if (val.trim().length < 4) return 'Minimum 4 characters';
                    return null;
                  },
                ),
                const SizedBox(height: 16),

                // Confirm Password
                _buildFieldLabel('Confirm Password *'),
                TextFormField(
                  controller: _confirmPasswordController,
                  obscureText: _obscureConfirm,
                  decoration: InputDecoration(
                    hintText: 'Re-enter password',
                    prefixIcon: const Icon(Icons.lock_rounded),
                    suffixIcon: IconButton(
                      icon: Icon(_obscureConfirm ? Icons.visibility_off_outlined : Icons.visibility_outlined),
                      onPressed: () => setState(() => _obscureConfirm = !_obscureConfirm),
                    ),
                  ),
                  validator: (val) {
                    if (val == null || val.trim().isEmpty) return 'Please confirm password';
                    if (val.trim() != _passwordController.text.trim()) return 'Passwords do not match';
                    return null;
                  },
                ),
                const SizedBox(height: 28),

                // Register Button
                CustomButton(
                  text: 'REGISTER',
                  icon: Icons.person_add_alt_1_rounded,
                  isLoading: _isLoading,
                  onPressed: _handleRegister,
                ),
                const SizedBox(height: 20),
              ],
            ),
          ),
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
          fontSize: 14,
          fontWeight: FontWeight.w600,
          color: AppColors.textPrimary,
        ),
      ),
    );
  }
}
