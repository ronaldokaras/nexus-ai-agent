import pytest
from core.sentiment import SentimentAnalyzer

class TestSentimentAnalyzer:
    def setup_method(self):
        self.analyzer = SentimentAnalyzer(threshold=0.45)

    def test_positive_sentiment(self):
        result = self.analyzer.analyze("Isso é incrível, estou muito feliz!")
        assert result.emotion == "positivo"
        assert result.needs_care is False

    def test_negative_sentiment(self):
        result = self.analyzer.analyze("Estou muito frustrado e triste.")
        assert result.emotion in ["negativo", "estressado"]
        assert result.needs_care is True

    def test_neutral_short_text(self):
        result = self.analyzer.analyze("ok")
        assert result.emotion == "neutro"

    def test_confidence_threshold(self):
        result = self.analyzer.analyze("código python django framework")
        assert result.emotion == "neutro"
        assert result.confidence > 0.8  # alta confiança para neutro forçado

    def test_tone_adjust(self):
        result = self.analyzer.analyze("estou muito estressado")
        assert result.tone_adjust == "suporte"