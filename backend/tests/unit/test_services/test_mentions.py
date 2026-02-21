from app.utils.mention_parser import extract_usernames


def test_extract_mentions():

    content = "Hello @john and @alice"

    result = extract_usernames(content)

    assert "john" in result
    assert "alice" in result
