import pytest
from utils import send_email, is_placeholder_email


@pytest.mark.parametrize('address', [
    'compliance@example.com', 'admin@example.com', 'demo@example.com',
    'Admin <admin@EXAMPLE.COM>', 'user@sub.example.org', 'user@invalid',
])
def test_placeholder_never_connects_to_smtp(address, monkeypatch):
    monkeypatch.setenv('SMTP_EMAIL', 'configured-sender@mail.test')
    monkeypatch.setenv('SMTP_PASSWORD', 'test-only')
    # The shared test fixture raises if any real SMTP connection is attempted.
    assert is_placeholder_email(address)
    assert send_email(address, 'Code', 'Test') is False


def test_real_domain_not_treated_as_placeholder():
    assert not is_placeholder_email('person@gmail.com')
    assert not is_placeholder_email('person@myexample.com')
