import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:intl/intl.dart';
import '../../providers/session_provider.dart';
import '../../models/session_model.dart';
import '../../ui/theme/app_colors.dart';
import 'performance_screen.dart';

class SessionHistoryScreen extends ConsumerWidget {
  const SessionHistoryScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final sessionState = ref.watch(sessionProvider);

    return Scaffold(
      backgroundColor: AppColors.background,
      appBar: AppBar(
        title: const Text('SESSION HISTORY'),
        actions: [
          if (sessionState.sessions.isNotEmpty)
            IconButton(
              icon: const Icon(Icons.delete_sweep_outlined, color: AppColors.error),
              tooltip: 'Clear all',
              onPressed: () => _confirmClearAll(context, ref),
            ),
        ],
      ),
      body: _buildBody(context, ref, sessionState),
    );
  }

  Widget _buildBody(BuildContext context, WidgetRef ref, SessionState state) {
    if (state.isLoading) {
      return const Center(child: CircularProgressIndicator(color: AppColors.accent));
    }

    if (state.errorMessage != null) {
      return Center(
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            const Icon(Icons.error_outline, color: AppColors.error, size: 56),
            const SizedBox(height: 16),
            Text(state.errorMessage!, style: const TextStyle(color: AppColors.textSecondary)),
            const SizedBox(height: 16),
            ElevatedButton(
              onPressed: () => ref.read(sessionProvider.notifier).loadSessions(),
              child: const Text('RETRY'),
            ),
          ],
        ),
      );
    }

    if (state.sessions.isEmpty) {
      return Center(
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Icon(Icons.history_toggle_off, size: 80, color: AppColors.textMuted),
            const SizedBox(height: 24),
            Text(
              'No sessions yet',
              style: TextStyle(
                fontSize: 20,
                fontWeight: FontWeight.bold,
                color: AppColors.textSecondary,
                fontFamily: 'Rajdhani',
              ),
            ),
            const SizedBox(height: 8),
            const Text(
              'Complete a real-time analysis session\nto see your history here.',
              textAlign: TextAlign.center,
              style: TextStyle(color: AppColors.textMuted, fontSize: 14),
            ),
          ],
        ),
      );
    }

    return RefreshIndicator(
      color: AppColors.accent,
      backgroundColor: AppColors.surface,
      onRefresh: () => ref.read(sessionProvider.notifier).loadSessions(),
      child: ListView.builder(
        padding: const EdgeInsets.all(16),
        itemCount: state.sessions.length,
        itemBuilder: (context, index) =>
            _SessionCard(session: state.sessions[index], ref: ref),
      ),
    );
  }

  Future<void> _confirmClearAll(BuildContext context, WidgetRef ref) async {
    final confirmed = await showDialog<bool>(
      context: context,
      builder: (_) => AlertDialog(
        backgroundColor: AppColors.surface,
        title: const Text('Clear All Sessions', style: TextStyle(color: AppColors.textPrimary)),
        content: const Text('This will permanently delete all sessions.',
            style: TextStyle(color: AppColors.textSecondary)),
        actions: [
          TextButton(
              onPressed: () => Navigator.pop(context, false),
              child: const Text('CANCEL', style: TextStyle(color: AppColors.textSecondary))),
          TextButton(
              onPressed: () => Navigator.pop(context, true),
              child: const Text('DELETE ALL', style: TextStyle(color: AppColors.error))),
        ],
      ),
    );
    if (confirmed == true) {
      final sessions = ref.read(sessionProvider).sessions;
      for (final s in sessions) {
        await ref.read(sessionProvider.notifier).deleteSession(s.id);
      }
    }
  }
}

class _SessionCard extends StatelessWidget {
  final SessionModel session;
  final WidgetRef ref;
  const _SessionCard({required this.session, required this.ref});

  @override
  Widget build(BuildContext context) {
    final scoreColor = session.averageScore >= 70
        ? AppColors.success
        : session.averageScore >= 40
            ? AppColors.warning
            : AppColors.error;

    return Dismissible(
      key: Key(session.id),
      direction: DismissDirection.endToStart,
      background: Container(
        alignment: Alignment.centerRight,
        padding: const EdgeInsets.only(right: 20),
        decoration: BoxDecoration(
          color: AppColors.error.withOpacity(0.2),
          borderRadius: BorderRadius.circular(16),
        ),
        child: const Icon(Icons.delete_outline, color: AppColors.error),
      ),
      onDismissed: (_) => ref.read(sessionProvider.notifier).deleteSession(session.id),
      child: GestureDetector(
        onTap: () => Navigator.push(
          context,
          MaterialPageRoute(builder: (_) => PerformanceScreen(session: session)),
        ),
        child: Container(
          margin: const EdgeInsets.only(bottom: 12),
          padding: const EdgeInsets.all(16),
          decoration: BoxDecoration(
            color: AppColors.surface,
            borderRadius: BorderRadius.circular(16),
            border: Border.all(color: scoreColor.withOpacity(0.3)),
          ),
          child: Row(
            children: [
              // Score Circle
              Container(
                width: 56,
                height: 56,
                decoration: BoxDecoration(
                  shape: BoxShape.circle,
                  border: Border.all(color: scoreColor, width: 2),
                  color: scoreColor.withOpacity(0.1),
                ),
                child: Center(
                  child: Text(
                    session.averageScore.toInt().toString(),
                    style: TextStyle(
                      color: scoreColor,
                      fontWeight: FontWeight.bold,
                      fontSize: 18,
                      fontFamily: 'Rajdhani',
                    ),
                  ),
                ),
              ),
              const SizedBox(width: 16),
              // Info
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      session.sportType.toUpperCase(),
                      style: const TextStyle(
                        color: AppColors.accent,
                        fontWeight: FontWeight.bold,
                        fontSize: 12,
                        letterSpacing: 1.2,
                        fontFamily: 'Rajdhani',
                      ),
                    ),
                    const SizedBox(height: 2),
                    Text(
                      DateFormat('MMM dd, yyyy • HH:mm').format(session.date),
                      style: const TextStyle(color: AppColors.textPrimary, fontSize: 14),
                    ),
                    const SizedBox(height: 2),
                    Text(
                      'Duration: ${session.durationSeconds}s',
                      style: const TextStyle(color: AppColors.textSecondary, fontSize: 12),
                    ),
                  ],
                ),
              ),
              const Icon(Icons.chevron_right, color: AppColors.textMuted),
            ],
          ),
        ),
      ),
    );
  }
}
