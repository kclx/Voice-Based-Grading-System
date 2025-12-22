"""Main application entry point for voice-based grading system."""

import sys
import signal
import time
import logging
from src.speech import ContinuousSpeechRecognizer
from src.parser import SpeechParser
from src.name_matcher import NameMatcher
from src.csv_updater import CSVUpdater
from src.utils import setup_logging


class VoiceGradingSystem:
    """Main orchestrator for the voice grading system."""

    def __init__(self):
        """Initialize all components."""
        self.logger = setup_logging()
        self.logger.info("=" * 60)
        self.logger.info("Voice Grading System Starting...")
        self.logger.info("=" * 60)

        try:
            # Initialize components
            self.csv_updater = CSVUpdater()
            self.parser = SpeechParser()
            self.name_matcher = NameMatcher(self.csv_updater.get_student_names())
            self.speech_recognizer = ContinuousSpeechRecognizer()

            # State
            self.running = False
            self.total_processed = 0
            self.successful_updates = 0
            self.failed_matches = 0

            self.logger.info("All components initialized successfully")

        except Exception as e:
            self.logger.error(f"Failed to initialize system: {e}")
            raise

    def process_speech(self, text: str):
        """
        Process recognized speech text.

        Args:
            text: Recognized speech text
        """
        self.total_processed += 1
        self.logger.info(f"\n[{self.total_processed}] Processing: '{text}'")

        # Parse the text
        entry = self.parser.parse(text)
        if entry is None:
            self.logger.warning("Failed to parse speech - format not recognized")
            print(f"⚠️  无法识别格式: {text}")
            print("    期望格式: 姓名 + 对/正确 + 数字 + 错/错误 + 数字")
            return

        # Match the name
        matched_name, match_type = self.name_matcher.find_match(entry.name)

        if matched_name is None:
            self.failed_matches += 1
            if match_type == 'ambiguous':
                # Multiple matches - ask teacher to be more specific
                similar = self.name_matcher.find_all_similar(entry.name)
                names = [n for n, _ in similar[:3]]
                self.logger.warning(f"Ambiguous name match: {names}")
                print(f"⚠️  姓名不明确: '{entry.name}'")
                print(f"    可能是: {', '.join(names)}")
                print("    请说完整姓名")
            else:
                # No match found
                self.logger.warning(f"Name not found: '{entry.name}'")
                print(f"⚠️  未找到学生: '{entry.name}'")
                print(f"    请确认姓名后重试")
            return

        # Update entry with matched name
        entry.name = matched_name

        # Update CSV
        success = self.csv_updater.update_student(entry)
        if success:
            self.successful_updates += 1
            print(f"✓ {matched_name}: 对 {entry.correct}, 错 {entry.wrong}")
            if match_type != 'exact':
                print(f"  (匹配方式: {match_type})")
        else:
            self.logger.error(f"Failed to update CSV for: '{matched_name}'")
            print(f"✗ 更新失败: {matched_name}")

    def start(self):
        """Start the voice grading system."""
        self.running = True

        # Create backup of CSV before starting
        self.csv_updater.create_backup()

        # Display startup information
        stats = self.csv_updater.get_statistics()
        print("\n" + "=" * 60)
        print("语音评分系统已启动")
        print("=" * 60)
        print(f"学生总数: {stats['total_students']}")
        print(f"当前统计 - 对: {stats['total_correct']}, 错: {stats['total_wrong']}")
        print("\n说话格式: 姓名 + 对/正确 + 数字 + 错/错误 + 数字")
        print("例如: 杨洋 对 18 错 2")
        print("\n按 Ctrl+C 停止")
        print("=" * 60 + "\n")

        # Start speech recognition
        self.speech_recognizer.start_listening(self.process_speech)

        # Setup signal handler for graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)

        # Keep main thread alive
        try:
            while self.running:
                time.sleep(1)
        except KeyboardInterrupt:
            self._shutdown()

    def _signal_handler(self, signum, frame):
        """Handle Ctrl+C gracefully."""
        print("\n\n正在停止...")
        self._shutdown()

    def _shutdown(self):
        """Shutdown the system gracefully."""
        if not self.running:
            return

        self.running = False

        # Stop speech recognition
        self.speech_recognizer.stop()

        # Display final statistics
        stats = self.csv_updater.get_statistics()
        print("\n" + "=" * 60)
        print("系统已停止")
        print("=" * 60)
        print(f"处理总数: {self.total_processed}")
        print(f"成功更新: {self.successful_updates}")
        print(f"匹配失败: {self.failed_matches}")
        print(f"\n最终统计 - 对: {stats['total_correct']}, 错: {stats['total_wrong']}")
        print("=" * 60)

        self.logger.info("Voice Grading System Stopped")
        sys.exit(0)


def main():
    """Main entry point."""
    try:
        system = VoiceGradingSystem()
        system.start()
    except Exception as e:
        logging.error(f"Fatal error: {e}", exc_info=True)
        print(f"\n✗ 系统错误: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
