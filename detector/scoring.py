from dataclasses import dataclass
from detector.rules import detect_text


@dataclass
class ScoreResult:
    suspicious: bool
    score: int
    reasons: list[str]


def score_text(text: str, keywords: list[str]) -> ScoreResult:
    result = detect_text(text, keywords)
    score = 0
    for reason in result.reasons:
        if reason.startswith('keyword:'):
            score += 30
        elif reason == 'url':
            score += 35
        elif reason == 'phone':
            score += 35
        elif reason == 'wechat_id_hint':
            score += 25
        else:
            score += 10
    return ScoreResult(suspicious=score >= 30, score=score, reasons=result.reasons)
