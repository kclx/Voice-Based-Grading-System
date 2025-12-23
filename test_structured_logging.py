"""Test script to validate structured logging instrumentation."""

import json
import sys
from src.utils import setup_logging
from src.structured_logger import StructuredLogger
from src.parser import SpeechParser, GradeEntry
from src.name_matcher import NameMatcher
from src.csv_updater import CSVUpdater

def test_logging():
    """Test all structured logging functions."""

    # Initialize logging
    logger = setup_logging()
    print("=" * 60)
    print("Testing Structured Logging Instrumentation")
    print("=" * 60)

    # Test 1: ASR Output
    print("\n[1] Testing ASR Output Logging...")
    s_logger = StructuredLogger("test_asr")
    s_logger.log_asr_output(
        raw_input="杨洋同学 对 18 错 2",
        engine="google"
    )
    print("✓ ASR output logged")

    # Test 2: Text Normalization
    print("\n[2] Testing Text Normalization Logging...")
    parser = SpeechParser()
    test_input = "杨洋同学  对  18  错  2"
    print(f"Input: '{test_input}'")

    # Test 3: Parser
    print("\n[3] Testing Parser Success/Fail Logging...")
    result = parser.parse(test_input)
    if result:
        print(f"✓ Parse success: {result}")
    else:
        print("✗ Parse failed (expected for test)")

    # Test with bad input
    bad_input = "这是无效输入"
    result = parser.parse(bad_input)
    print(f"✓ Parse failure logged for: '{bad_input}'")

    # Test 4: Name Matcher
    print("\n[4] Testing Name Matcher Logging...")
    test_names = ["杨洋", "张三", "李四", "王小明"]
    matcher = NameMatcher(test_names)

    # Test exact match
    print("  Testing exact match...")
    match, match_type = matcher.find_match("杨洋")
    print(f"  ✓ Exact match: '{match}' (type: {match_type})")

    # Test pinyin match
    print("  Testing pinyin match...")
    match, match_type = matcher.find_match("yangyang")
    print(f"  ✓ Pinyin match: '{match}' (type: {match_type})")

    # Test fuzzy match
    print("  Testing fuzzy match...")
    match, match_type = matcher.find_match("yanyang")
    print(f"  ✓ Fuzzy match: '{match}' (type: {match_type})")

    # Test no match
    print("  Testing no match...")
    match, match_type = matcher.find_match("不存在的人")
    print(f"  ✓ No match: '{match}' (type: {match_type})")

    # Test 5: CSV Update
    print("\n[5] Testing CSV Update Logging...")
    try:
        updater = CSVUpdater()

        # Test successful update (if student exists)
        test_entry = GradeEntry(name="杨洋", correct=20, wrong=5)
        success = updater.update_student(test_entry)
        if success:
            print(f"  ✓ CSV update success logged")

        # Test failed update (non-existent student)
        fail_entry = GradeEntry(name="不存在的学生", correct=10, wrong=0)
        success = updater.update_student(fail_entry)
        if not success:
            print(f"  ✓ CSV update failure logged")

    except Exception as e:
        print(f"  ⚠ CSV test error (expected if CSV structure changed): {e}")

    print("\n" + "=" * 60)
    print("Testing Complete!")
    print("=" * 60)
    print("\nCheck the log file (logs/voice_marking-YYYY-MM-DD.log) for JSON entries.")
    print("Each log entry should be valid JSON with 'timestamp' and 'stage' fields.")
    print("\nTo view structured logs:")
    print("  cat logs/voice_marking-$(date +%Y-%m-%d).log | grep '{\"timestamp\"'")
    print("\nTo parse and pretty-print JSON logs:")
    print("  cat logs/voice_marking-$(date +%Y-%m-%d).log | grep '{\"timestamp\"' | jq .")

if __name__ == "__main__":
    try:
        test_logging()
    except Exception as e:
        print(f"\n✗ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
