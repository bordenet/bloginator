"""Tests for AI slop detector."""

from bloginator.quality.slop_detector import SlopDetector


def test_slop_detector_initialization():
    """Test SlopDetector initializes and loads patterns."""
    detector = SlopDetector()
    assert detector.patterns is not None
    assert "em_dashes" in detector.patterns


def test_detect_em_dashes():
    """Test detection of em-dashes."""
    detector = SlopDetector()
    text = "This is a test—with an em-dash—in it."

    violations = detector.detect(text)

    # Should find em-dash violations
    em_dash_violations = [v for v in violations if v.pattern_name == "em_dashes"]
    assert len(em_dash_violations) > 0
    assert all(v.severity == "critical" for v in em_dash_violations)
    assert all(v.matched_text == "—" for v in em_dash_violations)


def test_detect_flowery_phrases():
    """Test detection of flowery corporate jargon."""
    detector = SlopDetector()
    text = "Let's dive deep into this topic and leverage our synergy."

    violations = detector.detect(text)

    # Should find flowery phrase violations
    flowery_violations = [v for v in violations if v.pattern_name == "flowery_phrases"]
    assert len(flowery_violations) >= 2  # "dive deep" and "leverage"
    assert all(v.severity == "high" for v in flowery_violations)


def test_detect_hedging_words():
    """Test detection of hedging words."""
    detector = SlopDetector()
    text = "Perhaps we might want to consider this approach, maybe."

    violations = detector.detect(text)

    # Should find hedging word violations
    hedging_violations = [v for v in violations if v.pattern_name == "hedging_words"]
    assert len(hedging_violations) >= 2  # "perhaps" and "maybe"
    assert all(v.severity == "medium" for v in hedging_violations)


def test_detect_vague_language():
    """Test detection of vague language."""
    detector = SlopDetector()
    text = "There are various approaches and several options to consider."

    violations = detector.detect(text)

    # Should find vague language violations
    vague_violations = [v for v in violations if v.pattern_name == "vague_language"]
    assert len(vague_violations) >= 2  # "various" and "several"
    assert all(v.severity == "low" for v in vague_violations)


def test_detect_clean_text():
    """Test that clean text has no violations."""
    detector = SlopDetector()
    text = "This is clean, direct text. It uses commas and periods. No AI slop here."

    violations = detector.detect(text)

    # Should have no violations
    assert len(violations) == 0


def test_detect_multiple_violations():
    """Test detection of multiple violation types."""
    detector = SlopDetector()
    text = """
    Let's dive deep into this topic—it's a game changer.
    Perhaps we should leverage our synergy to move the needle.
    There are various approaches and several options.
    """

    violations = detector.detect(text)

    # Should find multiple types
    assert len(violations) > 0
    pattern_names = {v.pattern_name for v in violations}
    assert "em_dashes" in pattern_names
    assert "flowery_phrases" in pattern_names


def test_has_critical_violations_true():
    """Test has_critical_violations returns True for em-dashes."""
    detector = SlopDetector()
    text = "This has an em-dash—right here."

    assert detector.has_critical_violations(text) is True


def test_has_critical_violations_false():
    """Test has_critical_violations returns False for non-critical."""
    detector = SlopDetector()
    text = "Perhaps we should consider this approach."  # Only medium severity

    assert detector.has_critical_violations(text) is False


def test_violation_line_numbers():
    """Test that violations include line numbers."""
    detector = SlopDetector()
    text = """Line 1 is clean.
Line 2 has an em-dash—here.
Line 3 is clean.
Line 4 has another em-dash—there."""

    violations = detector.detect(text)

    em_dash_violations = [v for v in violations if v.pattern_name == "em_dashes"]
    assert len(em_dash_violations) == 2
    line_numbers = {v.line_number for v in em_dash_violations}
    assert 2 in line_numbers
    assert 4 in line_numbers


def test_case_insensitive_detection():
    """Test that detection is case-insensitive."""
    detector = SlopDetector()
    text = "Let's DIVE DEEP and Leverage our synergy."

    violations = detector.detect(text)

    flowery_violations = [v for v in violations if v.pattern_name == "flowery_phrases"]
    assert len(flowery_violations) >= 2


def test_word_boundary_detection():
    """Test that detection respects word boundaries."""
    detector = SlopDetector()
    # "perhaps" should match, but "perhaps" in "haps" should not
    text = "Perhaps this is good. The mishaps were unfortunate."

    violations = detector.detect(text)

    hedging_violations = [v for v in violations if v.pattern_name == "hedging_words"]
    # Should only find "Perhaps", not "haps" in "mishaps"
    assert len(hedging_violations) == 1

