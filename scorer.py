import re

from rapidfuzz import fuzz


def judge(question, expects, answer, results) -> bool:
    """
    q: 'give', expect: 'give'
    the expect should closely match part of the answer
    """
    expected_words = re.findall(r"\w+", expects.lower())
    response_words = re.findall(r"\w+", answer.lower())
    if not expected_words or not response_words:
        return False

    expected = " ".join(expected_words)
    expected_numbers = {word for word in expected_words if word.isdigit()}
    window_size = len(expected_words)
    windows = []
    for index in range(len(response_words) - window_size + 1):
        window_words = response_words[index : index + window_size]
        if expected_numbers and not expected_numbers.issubset(window_words):
            continue
        windows.append(" ".join(window_words))

    return max((fuzz.ratio(expected, window) for window in windows), default=0) >= 80

