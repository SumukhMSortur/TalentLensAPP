import 'package:flutter_riverpod/flutter_riverpod.dart';

enum SportType { squat, pushup, pullup }

class SettingsState {
  final SportType selectedSport;
  final bool isGpuEnabled;
  final bool isCloudSyncEnabled;

  SettingsState({
    this.selectedSport = SportType.squat,
    this.isGpuEnabled = true,
    this.isCloudSyncEnabled = false,
  });

  SettingsState copyWith({
    SportType? selectedSport,
    bool? isGpuEnabled,
    bool? isCloudSyncEnabled,
  }) {
    return SettingsState(
      selectedSport: selectedSport ?? this.selectedSport,
      isGpuEnabled: isGpuEnabled ?? this.isGpuEnabled,
      isCloudSyncEnabled: isCloudSyncEnabled ?? this.isCloudSyncEnabled,
    );
  }
}

class SettingsNotifier extends StateNotifier<SettingsState> {
  SettingsNotifier() : super(SettingsState());

  void setSport(SportType sport) => state = state.copyWith(selectedSport: sport);
  void toggleGpu(bool value) => state = state.copyWith(isGpuEnabled: value);
  void toggleCloudSync(bool value) => state = state.copyWith(isCloudSyncEnabled: value);
}

final settingsProvider = StateNotifierProvider<SettingsNotifier, SettingsState>((ref) {
  return SettingsNotifier();
});
