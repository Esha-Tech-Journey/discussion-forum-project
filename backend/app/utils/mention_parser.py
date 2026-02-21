import re


# Match @username mentions where @ is not part of a word/email.
# Examples matched: "@priya", "hi @priya"
# Examples ignored: "test@example.com", "foo@bar"
MENTION_PATTERN = r"(?<!\w)@(\w+)"


def extract_usernames(content: str) -> list[str]:
    """
    Extract usernames from content.
    """

    return re.findall(MENTION_PATTERN, content or "")
