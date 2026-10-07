from app import text as bn
from app.dreams import Retriever


def test_normalize_keeps_bengali_vowel_signs_and_conjuncts():
    assert bn.normalize("স্বপ্নে, সাপ!") == "স্বপ্নে সাপ"


def test_normalize_drops_zero_width_and_unifies_composed_letters():
    assert bn.normalize("সা‍প") == "সাপ"
    assert bn.normalize("য়") == bn.normalize("য়")  # য় both ways


def test_stopwords_removed():
    assert bn.tokens("আমি স্বপ্নে সাপ দেখলাম") == ["সাপ"]


def test_inflected_forms_share_ngrams():
    assert len(set(bn.char_ngrams("সাপ")) & set(bn.char_ngrams("সাপে"))) >= 2


def test_inflected_query_ranks_right_entry_first(entries):
    hits = Retriever(entries).search("স্বপ্নে দেখলাম সাপে আমাকে কামড়াচ্ছে", k=5, min_score=0.1)
    assert hits[0][0].id == "sample-1"


def test_keywords_are_searchable(entries):
    hits = Retriever(entries).search("আমি জলে ডুবে যাচ্ছিলাম", k=5, min_score=0.1)
    assert hits and hits[0][0].id == "sample-2"


def test_unrelated_text_returns_nothing(entries):
    assert Retriever(entries).search("মোবাইলে চার্জ নেই কম্পিউটার", k=5, min_score=0.1) == []
