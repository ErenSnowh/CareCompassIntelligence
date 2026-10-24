"""
Unit tests for TextPreprocessor and Language Normalization.
Validates English, Hindi, and Hinglish text cleaning and keyword extraction.
"""

from app.data.preprocessor import TextPreprocessor


def test_language_detection():
    tp = TextPreprocessor()

    assert tp.detect_language("Patient has high fever and chest pain") == "English"
    assert tp.detect_language("मरीज को बहुत तेज बुखार है और सीने में दर्द है") == "Hindi"
    assert tp.detect_language("papa ko do din se bukhar hai aur khansi bhi") == "Hinglish"


def test_text_normalization():
    tp = TextPreprocessor()

    raw_text = "  Patient  has    fever  and COUGH!!  "
    normalized = tp.normalize(raw_text)
    assert "patient has fever and cough" in normalized


def test_keyword_extraction():
    tp = TextPreprocessor()

    text = "papa ko tez bukhar aur seene mein dard ho raha hai"
    keywords = tp.extract_keywords(text)
    assert len(keywords) > 0
    assert any("fever" in k or "bukhar" in k or "chest" in k or "dard" in k for k in keywords)
