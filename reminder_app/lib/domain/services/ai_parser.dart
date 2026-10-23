import '../models/reminder.dart';

/// Port: natural language → structured reminder draft (JSON contract later).
///
/// Stage 01: [MockAiParser] with heuristic / static parse.
/// Stage 02+: HTTP call to AI API; validate JSON schema; map to [ParsedReminderDraft].
///
/// TODO(stage-02+): implement real AI parser — App owns scheduling after parse.
abstract class AiParser {
  /// Parse [text] into a draft the user can confirm/edit.
  Future<ParsedReminderDraft> parse(String text);
}
