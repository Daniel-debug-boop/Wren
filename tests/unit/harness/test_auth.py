"""Tests for auth — token issuance, validation, expiry, revocation."""

import time
import pytest
from wren.harness.auth import BusAuth, AuthError


class TestBusAuth:
    def setup_method(self):
        self.auth = BusAuth(secret='fixed_secret_for_tests')

    def test_issue_token(self):
        token = self.auth.issue_token('agent1', 'coding')
        assert isinstance(token, str)
        assert len(token) > 20

    def test_validate_valid(self):
        token = self.auth.issue_token('agent1', 'coding')
        info = self.auth.validate(token)
        assert info['agent_id'] == 'agent1'
        assert info['agent_type'] == 'coding'

    def test_validate_with_expected_id(self):
        token = self.auth.issue_token('agent1', 'coding')
        info = self.auth.validate(token, expected_agent_id='agent1')
        assert info['agent_id'] == 'agent1'

    def test_validate_wrong_agent(self):
        token = self.auth.issue_token('agent1', 'coding')
        with pytest.raises(AuthError, match='not'):
            self.auth.validate(token, expected_agent_id='agent2')

    def test_revoke_token(self):
        token = self.auth.issue_token('agent1', 'coding')
        self.auth.revoke_token(token)
        with pytest.raises(AuthError, match='revoked'):
            self.auth.validate(token)

    def test_revoke_all_for_agent(self):
        t1 = self.auth.issue_token('agent_a', 'coding')
        t2 = self.auth.issue_token('agent_a', 'research')
        count = self.auth.revoke_all_for_agent('agent_a')
        assert count == 2
        with pytest.raises(AuthError):
            self.auth.validate(t1)
        with pytest.raises(AuthError):
            self.auth.validate(t2)

    def test_invalid_token(self):
        with pytest.raises(AuthError, match='Invalid'):
            self.auth.validate('not_a_real_token')

    def test_is_authenticated(self):
        token = self.auth.issue_token('agent1', 'coding')
        assert self.auth.is_authenticated(token) is True
        assert self.auth.is_authenticated('fake') is False

    def test_stats(self):
        self.auth.issue_token('a1', 'coding')
        self.auth.issue_token('a2', 'research')
        s = self.auth.stats()
        assert s['valid_tokens'] >= 2
        assert s['revoked'] == 0

    def test_expired_token(self):
        """Tokens expire after _TOKEN_TTL_S (3600s). We test by
        patching time to simulate expiry."""
        from unittest.mock import patch
        import time as t_mod

        token = self.auth.issue_token('agent1', 'coding')
        # Simulate time passing beyond TTL
        future = t_mod.time() + 3700
        with patch.object(t_mod, 'time', return_value=future):
            with pytest.raises(AuthError, match='expired'):
                self.auth.validate(token)
