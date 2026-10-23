import 'package:flutter/material.dart';

import '../../app_scope.dart';
import '../../domain/models/reminder.dart';
import '../../theme/app_theme.dart';
import '../../utils/date_format_zh.dart';
import '../confirm/parse_confirm_page.dart';
import '../settings/reminder_settings_page.dart';
import '../widgets/reminder_tile.dart';
import '../widgets/section_header.dart';

class HomePage extends StatefulWidget {
  const HomePage({super.key});

  @override
  State<HomePage> createState() => _HomePageState();
}

class _HomePageState extends State<HomePage> {
  final _controller = TextEditingController();
  final _focus = FocusNode();
  bool _parsing = false;

  @override
  void dispose() {
    _controller.dispose();
    _focus.dispose();
    super.dispose();
  }

  Future<void> _parseAndConfirm([String? overrideText]) async {
    final text = (overrideText ?? _controller.text).trim();
    if (text.isEmpty) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('先说一句想提醒的事吧～')),
      );
      return;
    }
    setState(() => _parsing = true);
    try {
      final scope = AppScope.read(context);
      final draft = await scope.aiParser.parse(text);
      if (!mounted) return;
      await Navigator.of(context).push<bool>(
        MaterialPageRoute(
          builder: (_) => ParseConfirmPage(draft: draft),
        ),
      );
      if (overrideText == null) {
        _controller.clear();
      }
    } finally {
      if (mounted) setState(() => _parsing = false);
    }
  }

  Future<void> _openManualCreate() async {
    final draft = ParsedReminderDraft(
      title: '',
      dueAt: DateTime.now().add(const Duration(hours: 1)),
    );
    final edited = await Navigator.of(context).push<ParsedReminderDraft>(
      MaterialPageRoute(
        builder: (_) => ReminderSettingsPage(initial: draft, title: '指定时间'),
      ),
    );
    if (edited == null || !mounted) return;
    await Navigator.of(context).push<bool>(
      MaterialPageRoute(
        builder: (_) => ParseConfirmPage(draft: edited),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    final repo = AppScope.of(context).repository;
    return ListenableBuilder(
      listenable: repo,
      builder: (context, _) {
        final today = repo.todayPending();
        final upcoming = repo.upcomingPending();
        final done = repo.completed();
        final greeting = DateFormatZh.greeting(DateTime.now());

        return CustomScrollView(
          slivers: [
            SliverToBoxAdapter(
              child: _HomeHero(
                greeting: greeting,
                controller: _controller,
                focusNode: _focus,
                parsing: _parsing,
                onSubmit: () => _parseAndConfirm(),
                onTenMinutes: () {
                  _controller.text = '10 分钟后提醒我休息一下';
                  _parseAndConfirm('10 分钟后提醒我休息一下');
                },
                onPickTime: _openManualCreate,
              ),
            ),
            SliverPadding(
              padding: const EdgeInsets.fromLTRB(20, 8, 20, 28),
              sliver: SliverList(
                delegate: SliverChildListDelegate([
                  SectionHeader(title: '今日待办', count: today.length),
                  if (today.isEmpty)
                    const _EmptyHint(text: '今天还没有待办，说一句话创建吧')
                  else
                    ...today.map(
                      (r) => Padding(
                        padding: const EdgeInsets.only(bottom: 10),
                        child: ReminderTile(reminder: r),
                      ),
                    ),
                  SectionHeader(title: '即将提醒', count: upcoming.length),
                  if (upcoming.isEmpty)
                    const _EmptyHint(text: '近期没有安排')
                  else
                    ...upcoming.take(5).map(
                      (r) => Padding(
                        padding: const EdgeInsets.only(bottom: 10),
                        child: ReminderTile(reminder: r),
                      ),
                    ),
                  SectionHeader(title: '已完成', count: done.length),
                  if (done.isEmpty)
                    const _EmptyHint(text: '完成的提醒会出现在这里')
                  else
                    ...done.take(3).map(
                      (r) => Padding(
                        padding: const EdgeInsets.only(bottom: 10),
                        child: ReminderTile(reminder: r),
                      ),
                    ),
                ]),
              ),
            ),
          ],
        );
      },
    );
  }
}

class _HomeHero extends StatelessWidget {
  const _HomeHero({
    required this.greeting,
    required this.controller,
    required this.focusNode,
    required this.parsing,
    required this.onSubmit,
    required this.onTenMinutes,
    required this.onPickTime,
  });

  final String greeting;
  final TextEditingController controller;
  final FocusNode focusNode;
  final bool parsing;
  final VoidCallback onSubmit;
  final VoidCallback onTenMinutes;
  final VoidCallback onPickTime;

  @override
  Widget build(BuildContext context) {
    return Container(
      width: double.infinity,
      decoration: const BoxDecoration(
        gradient: LinearGradient(
          begin: Alignment.topLeft,
          end: Alignment.bottomRight,
          colors: [
            Color(0xFFC8E8E4),
            Color(0xFFE8F3EF),
            Color(0xFFF3F8F7),
          ],
          stops: [0.0, 0.55, 1.0],
        ),
      ),
      child: SafeArea(
        bottom: false,
        child: Padding(
          padding: const EdgeInsets.fromLTRB(20, 12, 20, 8),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(
                'AI 个人提醒助手',
                style: Theme.of(context).textTheme.headlineSmall?.copyWith(
                      fontWeight: FontWeight.w900,
                      color: AppColors.tealDeep,
                      letterSpacing: 0.2,
                    ),
              ),
              const SizedBox(height: 6),
              Text(
                '$greeting，想提醒什么？',
                style: Theme.of(context).textTheme.titleMedium?.copyWith(
                      color: AppColors.inkMuted,
                      fontWeight: FontWeight.w500,
                    ),
              ),
              const SizedBox(height: 18),
              AnimatedContainer(
                duration: const Duration(milliseconds: 280),
                curve: Curves.easeOutCubic,
                decoration: BoxDecoration(
                  color: AppColors.surfaceElevated,
                  borderRadius: BorderRadius.circular(20),
                  boxShadow: [
                    BoxShadow(
                      color: AppColors.tealDeep.withValues(alpha: 0.12),
                      blurRadius: 24,
                      offset: const Offset(0, 10),
                    ),
                  ],
                ),
                child: Column(
                  children: [
                    TextField(
                      controller: controller,
                      focusNode: focusNode,
                      minLines: 2,
                      maxLines: 4,
                      textInputAction: TextInputAction.send,
                      onSubmitted: (_) => onSubmit(),
                      style: Theme.of(context).textTheme.titleMedium?.copyWith(
                            fontWeight: FontWeight.w600,
                          ),
                      decoration: const InputDecoration(
                        hintText: '例如：明天下午三点提醒我交作业',
                        border: InputBorder.none,
                        enabledBorder: InputBorder.none,
                        focusedBorder: InputBorder.none,
                        filled: false,
                        contentPadding: EdgeInsets.fromLTRB(18, 16, 18, 8),
                      ),
                    ),
                    Padding(
                      padding: const EdgeInsets.fromLTRB(12, 0, 12, 12),
                      child: Row(
                        children: [
                          Expanded(
                            child: FilledButton(
                              onPressed: parsing ? null : onSubmit,
                              child: parsing
                                  ? const SizedBox(
                                      height: 20,
                                      width: 20,
                                      child: CircularProgressIndicator(
                                        strokeWidth: 2.4,
                                        color: Colors.white,
                                      ),
                                    )
                                  : const Text('智能解析'),
                            ),
                          ),
                        ],
                      ),
                    ),
                  ],
                ),
              ),
              const SizedBox(height: 14),
              Row(
                children: [
                  _ShortcutChip(
                    label: '10 分钟后',
                    icon: Icons.timer_outlined,
                    onTap: parsing ? null : onTenMinutes,
                  ),
                  const SizedBox(width: 10),
                  _ShortcutChip(
                    label: '指定时间',
                    icon: Icons.event_outlined,
                    onTap: parsing ? null : onPickTime,
                  ),
                ],
              ),
              const SizedBox(height: 8),
            ],
          ),
        ),
      ),
    );
  }
}

class _ShortcutChip extends StatelessWidget {
  const _ShortcutChip({
    required this.label,
    required this.icon,
    required this.onTap,
  });

  final String label;
  final IconData icon;
  final VoidCallback? onTap;

  @override
  Widget build(BuildContext context) {
    return Material(
      color: AppColors.amberSoft,
      borderRadius: BorderRadius.circular(14),
      child: InkWell(
        onTap: onTap,
        borderRadius: BorderRadius.circular(14),
        child: Padding(
          padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 10),
          child: Row(
            mainAxisSize: MainAxisSize.min,
            children: [
              Icon(icon, size: 18, color: AppColors.amber),
              const SizedBox(width: 6),
              Text(
                label,
                style: Theme.of(context).textTheme.labelLarge?.copyWith(
                      fontWeight: FontWeight.w700,
                      color: AppColors.ink,
                    ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}

class _EmptyHint extends StatelessWidget {
  const _EmptyHint({required this.text});

  final String text;

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 16, top: 4),
      child: Text(
        text,
        style: Theme.of(context).textTheme.bodyMedium?.copyWith(
              color: AppColors.inkMuted,
            ),
      ),
    );
  }
}
