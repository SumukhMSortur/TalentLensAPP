import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:shared_preferences/shared_preferences.dart';
import '../../ui/theme/app_colors.dart';

// ─── Settings State ──────────────────────────────────────────────────────────
class SettingsState {
  final String sportType;
  final bool useGpuDelegate;
  final bool showSkeleton;
  final bool enableHaptics;
  final double confidenceThreshold;
  final String cameraFacing; // 'back' | 'front'

  const SettingsState({
    this.sportType = 'General',
    this.useGpuDelegate = true,
    this.showSkeleton = true,
    this.enableHaptics = true,
    this.confidenceThreshold = 0.5,
    this.cameraFacing = 'back',
  });

  SettingsState copyWith({
    String? sportType,
    bool? useGpuDelegate,
    bool? showSkeleton,
    bool? enableHaptics,
    double? confidenceThreshold,
    String? cameraFacing,
  }) =>
      SettingsState(
        sportType: sportType ?? this.sportType,
        useGpuDelegate: useGpuDelegate ?? this.useGpuDelegate,
        showSkeleton: showSkeleton ?? this.showSkeleton,
        enableHaptics: enableHaptics ?? this.enableHaptics,
        confidenceThreshold: confidenceThreshold ?? this.confidenceThreshold,
        cameraFacing: cameraFacing ?? this.cameraFacing,
      );
}

// ─── Settings Notifier ───────────────────────────────────────────────────────
class SettingsNotifier extends StateNotifier<SettingsState> {
  SettingsNotifier() : super(const SettingsState()) {
    _load();
  }

  static const _keySport = 'sport_type';
  static const _keyGpu = 'use_gpu';
  static const _keySkeleton = 'show_skeleton';
  static const _keyHaptics = 'enable_haptics';
  static const _keyThreshold = 'confidence_threshold';
  static const _keyCamera = 'camera_facing';

  Future<void> _load() async {
    final prefs = await SharedPreferences.getInstance();
    state = SettingsState(
      sportType: prefs.getString(_keySport) ?? 'General',
      useGpuDelegate: prefs.getBool(_keyGpu) ?? true,
      showSkeleton: prefs.getBool(_keySkeleton) ?? true,
      enableHaptics: prefs.getBool(_keyHaptics) ?? true,
      confidenceThreshold: prefs.getDouble(_keyThreshold) ?? 0.5,
      cameraFacing: prefs.getString(_keyCamera) ?? 'back',
    );
  }

  Future<void> setSportType(String value) async {
    state = state.copyWith(sportType: value);
    (await SharedPreferences.getInstance()).setString(_keySport, value);
  }

  Future<void> setUseGpu(bool value) async {
    state = state.copyWith(useGpuDelegate: value);
    (await SharedPreferences.getInstance()).setBool(_keyGpu, value);
  }

  Future<void> setShowSkeleton(bool value) async {
    state = state.copyWith(showSkeleton: value);
    (await SharedPreferences.getInstance()).setBool(_keySkeleton, value);
  }

  Future<void> setEnableHaptics(bool value) async {
    state = state.copyWith(enableHaptics: value);
    (await SharedPreferences.getInstance()).setBool(_keyHaptics, value);
  }

  Future<void> setConfidenceThreshold(double value) async {
    state = state.copyWith(confidenceThreshold: value);
    (await SharedPreferences.getInstance()).setDouble(_keyThreshold, value);
  }

  Future<void> setCameraFacing(String value) async {
    state = state.copyWith(cameraFacing: value);
    (await SharedPreferences.getInstance()).setString(_keyCamera, value);
  }
}

final settingsProvider = StateNotifierProvider<SettingsNotifier, SettingsState>(
  (_) => SettingsNotifier(),
);

// ─── Settings Screen ──────────────────────────────────────────────────────────
class SettingsScreen extends ConsumerWidget {
  const SettingsScreen({super.key});

  static const _sports = [
    'General',
    'Running',
    'Swimming',
    'Cycling',
    'Weightlifting',
    'Gymnastics',
    'Basketball',
    'Football',
    'Tennis',
    'Badminton',
  ];

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final s = ref.watch(settingsProvider);
    final notifier = ref.read(settingsProvider.notifier);

    return Scaffold(
      backgroundColor: AppColors.background,
      appBar: AppBar(title: const Text('SETTINGS')),
      body: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          // ── Analysis Settings ──────────────────────────────────────
          _SectionHeader(label: 'ANALYSIS'),
          _SettingsTile(
            icon: Icons.sports,
            label: 'Sport Type',
            subtitle: s.sportType,
            trailing: DropdownButton<String>(
              value: s.sportType,
              dropdownColor: AppColors.surface,
              underline: const SizedBox(),
              style: const TextStyle(color: AppColors.accent, fontFamily: 'Rajdhani'),
              onChanged: (v) => notifier.setSportType(v!),
              items: _sports
                  .map((e) => DropdownMenuItem(value: e, child: Text(e)))
                  .toList(),
            ),
          ),
          _SettingsTile(
            icon: Icons.memory_outlined,
            label: 'GPU Acceleration',
            subtitle: 'Use GPU delegate for faster inference',
            trailing: Switch(
              value: s.useGpuDelegate,
              onChanged: notifier.setUseGpu,
              activeColor: AppColors.accent,
            ),
          ),

          const SizedBox(height: 16),
          // ── Display Settings ───────────────────────────────────────
          _SectionHeader(label: 'DISPLAY'),
          _SettingsTile(
            icon: Icons.accessibility_new_outlined,
            label: 'Skeleton Overlay',
            subtitle: 'Show pose keypoints on camera',
            trailing: Switch(
              value: s.showSkeleton,
              onChanged: notifier.setShowSkeleton,
              activeColor: AppColors.accent,
            ),
          ),
          _SettingsTile(
            icon: Icons.flip_camera_android_outlined,
            label: 'Camera',
            subtitle: '${s.cameraFacing == 'back' ? 'Rear' : 'Front'} camera',
            trailing: SegmentedButton<String>(
              segments: const [
                ButtonSegment(value: 'back', icon: Icon(Icons.camera_rear_outlined, size: 18)),
                ButtonSegment(value: 'front', icon: Icon(Icons.camera_front_outlined, size: 18)),
              ],
              selected: {s.cameraFacing},
              onSelectionChanged: (v) => notifier.setCameraFacing(v.first),
              style: ButtonStyle(
                backgroundColor: MaterialStateProperty.resolveWith(
                  (states) => states.contains(MaterialState.selected)
                      ? AppColors.accent.withOpacity(0.15)
                      : Colors.transparent,
                ),
              ),
            ),
          ),

          const SizedBox(height: 16),
          // ── Inference Settings ─────────────────────────────────────
          _SectionHeader(label: 'INFERENCE'),
          _SettingsTile(
            icon: Icons.tune_outlined,
            label: 'Confidence Threshold',
            subtitle: 'Min visibility to include landmark: ${(s.confidenceThreshold * 100).toInt()}%',
            trailing: null,
            footer: Slider(
              value: s.confidenceThreshold,
              min: 0.1,
              max: 0.9,
              divisions: 8,
              activeColor: AppColors.accent,
              inactiveColor: AppColors.surfaceVariant,
              label: '${(s.confidenceThreshold * 100).toInt()}%',
              onChanged: notifier.setConfidenceThreshold,
            ),
          ),

          const SizedBox(height: 16),
          // ── Feedback Settings ──────────────────────────────────────
          _SectionHeader(label: 'FEEDBACK'),
          _SettingsTile(
            icon: Icons.vibration_outlined,
            label: 'Haptic Feedback',
            subtitle: 'Vibrate on coaching alerts',
            trailing: Switch(
              value: s.enableHaptics,
              onChanged: notifier.setEnableHaptics,
              activeColor: AppColors.accent,
            ),
          ),

          const SizedBox(height: 16),
          // ── About ─────────────────────────────────────────────────
          _SectionHeader(label: 'ABOUT'),
          _SettingsTile(
            icon: Icons.info_outline,
            label: 'Talent Lens AI',
            subtitle: 'Version 1.0.0 • Built for elite athletic performance',
            trailing: null,
          ),
          _SettingsTile(
            icon: Icons.biotech_outlined,
            label: 'Model',
            subtitle: 'AQANet LSTM • Input: [1, 30, 76] • Output: [1, 1]',
            trailing: null,
          ),
          const SizedBox(height: 32),
        ],
      ),
    );
  }
}

// ─── Helper Widgets ───────────────────────────────────────────────────────────
class _SectionHeader extends StatelessWidget {
  final String label;
  const _SectionHeader({required this.label});

  @override
  Widget build(BuildContext context) => Padding(
        padding: const EdgeInsets.only(top: 8, bottom: 8, left: 4),
        child: Text(
          label,
          style: const TextStyle(
            color: AppColors.accent,
            fontSize: 11,
            fontWeight: FontWeight.bold,
            letterSpacing: 2,
            fontFamily: 'Rajdhani',
          ),
        ),
      );
}

class _SettingsTile extends StatelessWidget {
  final IconData icon;
  final String label;
  final String subtitle;
  final Widget? trailing;
  final Widget? footer;

  const _SettingsTile({
    required this.icon,
    required this.label,
    required this.subtitle,
    required this.trailing,
    this.footer,
  });

  @override
  Widget build(BuildContext context) => Container(
        margin: const EdgeInsets.only(bottom: 8),
        padding: const EdgeInsets.all(16),
        decoration: BoxDecoration(
          color: AppColors.surface,
          borderRadius: BorderRadius.circular(12),
          border: Border.all(color: AppColors.surfaceVariant.withOpacity(0.5)),
        ),
        child: Column(
          children: [
            Row(
              children: [
                Icon(icon, color: AppColors.accent, size: 22),
                const SizedBox(width: 14),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(label,
                          style: const TextStyle(
                              color: AppColors.textPrimary, fontWeight: FontWeight.w600)),
                      Text(subtitle,
                          style: const TextStyle(
                              color: AppColors.textSecondary, fontSize: 12)),
                    ],
                  ),
                ),
                if (trailing != null) trailing!,
              ],
            ),
            if (footer != null) footer!,
          ],
        ),
      );
}
