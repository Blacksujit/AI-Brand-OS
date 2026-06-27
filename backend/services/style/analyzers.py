from __future__ import annotations

import math
import re
from typing import ClassVar

from schemas.style import StyleParams


class LexicalAnalyzer:
    def extract(self, text: str) -> dict:
        words = re.findall(r"[a-zA-Z0-9']+", text)
        if not words:
            return {
                "word_count": 0,
                "unique_word_ratio": 0.0,
                "avg_word_length": 0.0,
                "vocabulary_richness": 0.0,
            }
        word_lengths = [len(w) for w in words]
        unique = {w.lower() for w in words}
        return {
            "word_count": len(words),
            "unique_word_ratio": len(unique) / len(words),
            "avg_word_length": sum(word_lengths) / len(words),
            "vocabulary_richness": len(unique) / math.sqrt(len(words)),
        }

    def score(self, features: dict, params: StyleParams) -> float:
        richness = features.get("vocabulary_richness", 0.0)
        return min(min(richness, 10.0) / 10.0, 1.0)


class SyntacticAnalyzer:
    SENTENCE_END = re.compile(r"[.!?]+")

    def extract(self, text: str) -> dict:
        sentences = [s.strip() for s in self.SENTENCE_END.split(text) if s.strip()]
        words = re.findall(r"[a-zA-Z0-9']+", text)
        if not sentences or not words:
            return {
                "sentence_count": 0,
                "avg_sentence_length": 0.0,
                "paragraph_count": 0,
                "avg_paragraph_length": 0.0,
                "long_sentence_ratio": 0.0,
            }
        paragraphs = [p for p in text.split("\n\n") if p.strip()]
        sent_lengths = [len(s.split()) for s in sentences]
        return {
            "sentence_count": len(sentences),
            "avg_sentence_length": sum(sent_lengths) / len(sentences),
            "paragraph_count": max(len(paragraphs), 1),
            "avg_paragraph_length": len(sentences) / max(len(paragraphs), 1),
            "long_sentence_ratio": sum(1 for s in sent_lengths if s > 30) / len(sentences),
        }

    def score(self, features: dict, params: StyleParams) -> float:
        avg_sent = features.get("avg_sentence_length", 20.0)
        target = params.avg_sentence_length or 20.0
        return 1.0 - min(abs(avg_sent - target) / target, 1.0)


class TonalAnalyzer:
    FORMALITY_MARKERS: ClassVar[dict] = {
        "formal": [
            "therefore",
            "consequently",
            "nevertheless",
            "furthermore",
            "notwithstanding",
            "herein",
            "therein",
            "thus",
            "hence",
            "pursuant",
            "hereto",
            "wherein",
            "aforementioned",
            "hereby",
        ],
        "informal": [
            "gonna",
            "wanna",
            "gotta",
            "kinda",
            "sorta",
            "yeah",
            "nah",
            "cool",
            "awesome",
            "literally",
            "basically",
            "actually",
            "honestly",
            "right",
            "okay",
            "hey",
            "guys",
            "stuff",
        ],
    }
    ANALOGY_MARKERS: ClassVar[list[str]] = [
        "like",
        "as if",
        "similar to",
        "reminds me of",
        "imagine",
        "picture this",
        "think of it as",
        "in the same way",
        "just as",
        "akin to",
        "parallel to",
        "comparable to",
    ]
    HUMOR_MARKERS: ClassVar[list[str]] = [
        "😂",
        "😅",
        "🤔",
        "🙃",
        "😉",
        "jk",
        "just kidding",
        "ironically",
        "admittedly",
        "confession",
        "unpopular opinion",
        "hot take",
        "devil's advocate",
    ]

    def extract(self, text: str) -> dict:
        lower = text.lower()
        formal_count = sum(lower.count(m) for m in self.FORMALITY_MARKERS["formal"])
        informal_count = sum(lower.count(m) for m in self.FORMALITY_MARKERS["informal"])
        total = formal_count + informal_count or 1
        analogy_count = sum(lower.count(m) for m in self.ANALOGY_MARKERS)
        humor_count = sum(lower.count(m) for m in self.HUMOR_MARKERS)
        words = len(re.findall(r"[a-zA-Z0-9']+", text)) or 1
        return {
            "formality_score": formal_count / total,
            "analogy_frequency": analogy_count / words * 100,
            "humor_frequency": humor_count / words * 100,
        }

    def score(self, features: dict, params: StyleParams) -> float:
        formality = features.get("formality_score", 0.5)
        target = params.formality or 0.5
        return 1.0 - min(abs(formality - target) / (max(target, 0.1)), 1.0)


class StructuralAnalyzer:
    HOOK_PATTERNS: ClassVar[list[str]] = [
        r"^did you know",
        r"^here's why",
        r"^the truth about",
        r"^what if i told you",
        r"^i've been thinking",
        r"^after years of",
        r"^i used to think",
        r"^this is why",
        r"^you might think",
        r"^here's what",
        r"^imagine",
        r"^picture this",
        r"^let me share",
        r"^question:",
        r"^(number|#)\d+\.",
        r"^thread:",
        r"^\d+\/\d+",
        r"^\[thread\]",
    ]
    CTA_PATTERNS: ClassVar[list[str]] = [
        r"(follow|share|retweet|like|comment|subscribe)",
        r"(what do you think|agree|disagree|thoughts\?)",
        r"(let me know|drop a|tag someone|share this)",
        r"(follow me|turn on|hit that|ring the)",
        r"(repost|quote tweet|send this to)",
        r"(if you found this|was this helpful|enjoyed this)",
        r"(click the|link in bio|link in comments|caption this)",
    ]
    LIST_PATTERN = re.compile(r"^\d+[.)]|^[-*] ", re.MULTILINE)
    QUOTE_PATTERN = re.compile(r'["""""]|^> ', re.MULTILINE)

    def extract(self, text: str) -> dict:
        lines = text.strip().split("\n")
        first_line = lines[0].strip() if lines else ""
        last_line = lines[-1].strip() if lines else ""
        has_hook = any(re.search(p, first_line.lower()) for p in self.HOOK_PATTERNS)
        has_cta = any(re.search(p, last_line.lower()) for p in self.CTA_PATTERNS)
        list_lines = len(self.LIST_PATTERN.findall(text))
        quote_lines = len(self.QUOTE_PATTERN.findall(text))
        return {
            "has_hook": 1.0 if has_hook else 0.0,
            "has_cta": 1.0 if has_cta else 0.0,
            "list_density": list_lines / max(len(lines), 1),
            "quote_density": quote_lines / max(len(lines), 1),
        }

    def score(self, features: dict, params: StyleParams) -> float:
        score = 0.0
        score += features.get("has_hook", 0.0) * 0.3
        score += features.get("has_cta", 0.0) * 0.3
        score += (1.0 - features.get("list_density", 0.0)) * 0.2
        score += (1.0 - features.get("quote_density", 0.0)) * 0.2
        return score


class StyleAnalyzer:
    def __init__(self) -> None:
        self._lexical = LexicalAnalyzer()
        self._syntactic = SyntacticAnalyzer()
        self._tonal = TonalAnalyzer()
        self._structural = StructuralAnalyzer()

    def analyze(self, text: str, params: StyleParams) -> dict:
        lexical = self._lexical.extract(text)
        syntactic = self._syntactic.extract(text)
        tonal = self._tonal.extract(text)
        structural = self._structural.extract(text)
        return {
            "lexical": lexical,
            "syntactic": syntactic,
            "tonal": tonal,
            "structural": structural,
            "lexical_score": self._lexical.score(lexical, params),
            "syntactic_score": self._syntactic.score(syntactic, params),
            "tonal_score": self._tonal.score(tonal, params),
            "structural_score": self._structural.score(structural, params),
            "overall": (
                self._lexical.score(lexical, params) * 0.15
                + self._syntactic.score(syntactic, params) * 0.25
                + self._tonal.score(tonal, params) * 0.35
                + self._structural.score(structural, params) * 0.25
            ),
        }

    def extract_signal_data(self, text: str) -> dict:
        lexical = self._lexical.extract(text)
        syntactic = self._syntactic.extract(text)
        tonal = self._tonal.extract(text)
        structural = self._structural.extract(text)
        return {
            "word_count": lexical["word_count"],
            "unique_word_ratio": lexical["unique_word_ratio"],
            "avg_word_length": lexical["avg_word_length"],
            "vocabulary_richness": lexical["vocabulary_richness"],
            "avg_sentence_length": syntactic["avg_sentence_length"],
            "long_sentence_ratio": syntactic["long_sentence_ratio"],
            "formality_score": tonal["formality_score"],
            "analogy_frequency": tonal["analogy_frequency"],
            "humor_frequency": tonal["humor_frequency"],
            "has_hook": structural["has_hook"],
            "has_cta": structural["has_cta"],
        }
