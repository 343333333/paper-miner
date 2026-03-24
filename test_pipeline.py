"""
Integration tests for Phases 2–4 using mock Anthropic and SMTP clients.
Run with: python3 test_pipeline.py
"""

import json
import os
import smtplib
import sys
import types
import unittest
from unittest.mock import MagicMock, patch

sys.path.insert(0, ".")

# ---------------------------------------------------------------------------
# Sample papers fixture
# ---------------------------------------------------------------------------

SAMPLE_PAPERS = [
    {
        "id": "arxiv:2503.00001",
        "title": "Phase-field model of biomolecular condensate formation coupled to DNA",
        "abstract": (
            "We develop a Cahn-Hilliard model for liquid-liquid phase separation of "
            "disordered proteins coupled to a moving DNA binding site. Using Model B "
            "dynamics and Flory-Huggins free energy we predict coarsening exponents."
        ),
        "authors": ["A. Author"],
        "published": "2026-03-24",
        "source": "arXiv",
        "url": "https://arxiv.org/abs/2503.00001",
        "_norm_title": "phase-field model of biomolecular condensate formation coupled to dna",
    },
    {
        "id": "arxiv:2503.00002",
        "title": "Turing instability in ER-mitochondria contact sites",
        "abstract": (
            "Reaction-diffusion model for calcium oscillations at MAM contacts. "
            "Activator-inhibitor dynamics near the contact site membrane."
        ),
        "authors": ["B. Author"],
        "published": "2026-03-24",
        "source": "arXiv",
        "url": "https://arxiv.org/abs/2503.00002",
        "_norm_title": "turing instability in ermitochondria contact sites",
    },
]


# ---------------------------------------------------------------------------
# Phase 2 — Scoring
# ---------------------------------------------------------------------------

class TestScoring(unittest.TestCase):
    def _make_mock_client(self, score_data: dict):
        """Return a mock Anthropic client that returns the given JSON."""
        mock_content = MagicMock()
        mock_content.text = json.dumps(score_data)
        mock_message = MagicMock()
        mock_message.content = [mock_content]
        mock_client = MagicMock()
        mock_client.messages.create.return_value = mock_message
        return mock_client

    def test_score_above_threshold_included(self):
        from digest.score import _score_paper

        score_data = {
            "score": 8,
            "topics": ["Cahn-Hilliard", "condensate"],
            "reason": "Directly relevant phase-field work on condensates.",
            "dynamic_boundary": True,
        }
        client = self._make_mock_client(score_data)
        result = _score_paper(client, SAMPLE_PAPERS[0])
        # base 8 + dynamic_boundary +2 + 2 topics +2 = min(10,12) = 10
        self.assertEqual(result["score"], 10)
        self.assertTrue(result["dynamic_boundary"])
        self.assertIn("Cahn-Hilliard", result["topics"])

    def test_score_below_threshold_filtered(self):
        from digest.score import _score_paper, SCORE_THRESHOLD

        score_data = {
            "score": 3,
            "topics": [],
            "reason": "Not relevant.",
            "dynamic_boundary": False,
        }
        client = self._make_mock_client(score_data)
        result = _score_paper(client, SAMPLE_PAPERS[1])
        self.assertLess(result["score"], SCORE_THRESHOLD)

    def test_score_papers_filters_low_scorers(self):
        from digest import score as score_module

        responses = [
            {"score": 9, "topics": ["condensate", "Cahn-Hilliard"], "reason": "Great.", "dynamic_boundary": False},
            {"score": 2, "topics": [], "reason": "Not relevant.", "dynamic_boundary": False},
        ]
        call_count = 0

        def fake_score_paper(client, paper):
            nonlocal call_count
            data = responses[call_count % len(responses)]
            call_count += 1
            base = int(data["score"])
            topics = data["topics"]
            dyn = data["dynamic_boundary"]
            bonus = (2 if dyn else 0) + (2 if len(topics) >= 2 else 0)
            return {
                **paper,
                "score": min(10, base + bonus),
                "base_score": base,
                "topics": topics,
                "reason": data["reason"],
                "dynamic_boundary": dyn,
            }

        with patch.object(score_module, "_score_paper", side_effect=fake_score_paper), \
             patch.dict(os.environ, {"ANTHROPIC_API_KEY": "sk-test"}):
            scored = score_module.score_papers(SAMPLE_PAPERS)

        self.assertEqual(len(scored), 1)
        self.assertEqual(scored[0]["id"], "arxiv:2503.00001")

    def test_score_bonus_capped_at_10(self):
        from digest.score import _score_paper

        score_data = {
            "score": 9,
            "topics": ["condensate", "Cahn-Hilliard"],
            "reason": "Very relevant.",
            "dynamic_boundary": True,
        }
        mock_content = MagicMock()
        mock_content.text = json.dumps(score_data)
        mock_message = MagicMock()
        mock_message.content = [mock_content]
        mock_client = MagicMock()
        mock_client.messages.create.return_value = mock_message

        result = _score_paper(mock_client, SAMPLE_PAPERS[0])
        self.assertEqual(result["score"], 10)


# ---------------------------------------------------------------------------
# Phase 3 — Summarize
# ---------------------------------------------------------------------------

class TestSummarize(unittest.TestCase):
    def test_generate_digest_returns_html(self):
        from digest.summarize import generate_digest

        dummy_html = (
            "<h2>Today's Biophysics Digest — March 24, 2026</h2>"
            "<h3><a href='...'>Paper 1</a></h3><p>Summary.</p>"
        )
        mock_content = MagicMock()
        mock_content.text = dummy_html
        mock_message = MagicMock()
        mock_message.content = [mock_content]
        mock_client = MagicMock()
        mock_client.messages.create.return_value = mock_message

        scored_papers = [
            {**SAMPLE_PAPERS[0], "score": 10, "topics": ["condensate"], "reason": "Great."},
        ]

        with patch("digest.summarize.anthropic.Anthropic", return_value=mock_client), \
             patch.dict(os.environ, {"ANTHROPIC_API_KEY": "sk-test"}):
            html = generate_digest(scored_papers)

        self.assertIn("<h2>", html)
        self.assertIn("Digest", html)


# ---------------------------------------------------------------------------
# Phase 4 — Email
# ---------------------------------------------------------------------------

class TestEmailSender(unittest.TestCase):
    def _env(self):
        return {
            "GMAIL_ADDRESS": "sender@gmail.com",
            "GMAIL_APP_PASSWORD": "testpassword",
            "RECIPIENT_EMAIL": "recipient@example.com",
        }

    def test_send_digest_calls_smtp(self):
        from digest.email_sender import send_digest

        with patch("digest.email_sender.smtplib.SMTP_SSL") as mock_ssl_cls, \
             patch.dict(os.environ, self._env()):
            mock_server = MagicMock()
            mock_ssl_cls.return_value.__enter__.return_value = mock_server
            send_digest("<h2>Test</h2>", n_papers=1)

        mock_server.login.assert_called_once_with("sender@gmail.com", "testpassword")
        mock_server.sendmail.assert_called_once()
        args = mock_server.sendmail.call_args[0]
        self.assertEqual(args[0], "sender@gmail.com")
        self.assertEqual(args[1], "recipient@example.com")

    def test_send_digest_subject_contains_count(self):
        import email
        from email.header import decode_header
        from digest.email_sender import send_digest

        with patch("digest.email_sender.smtplib.SMTP_SSL") as mock_ssl_cls, \
             patch.dict(os.environ, self._env()):
            mock_server = MagicMock()
            mock_ssl_cls.return_value.__enter__.return_value = mock_server
            send_digest("<p>body</p>", n_papers=5)

        msg_str = mock_server.sendmail.call_args[0][2]
        msg = email.message_from_string(msg_str)
        subject_parts = decode_header(msg["Subject"])
        subject = "".join(
            part.decode(enc or "utf-8") if isinstance(part, bytes) else part
            for part, enc in subject_parts
        )
        self.assertIn("5 papers", subject)

    def test_send_no_papers_email(self):
        from digest.email_sender import send_no_papers_email

        with patch("digest.email_sender.smtplib.SMTP_SSL") as mock_ssl_cls, \
             patch.dict(os.environ, self._env()):
            mock_server = MagicMock()
            mock_ssl_cls.return_value.__enter__.return_value = mock_server
            send_no_papers_email()

        mock_server.sendmail.assert_called_once()

    def test_missing_env_raises(self):
        from digest.email_sender import send_digest

        clean_env = {k: v for k, v in os.environ.items()
                     if k not in ("GMAIL_ADDRESS", "GMAIL_APP_PASSWORD", "RECIPIENT_EMAIL")}
        with patch.dict(os.environ, clean_env, clear=True):
            with self.assertRaises(ValueError):
                send_digest("<p>test</p>", n_papers=1)


# ---------------------------------------------------------------------------

if __name__ == "__main__":
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    suite.addTests(loader.loadTestsFromTestCase(TestScoring))
    suite.addTests(loader.loadTestsFromTestCase(TestSummarize))
    suite.addTests(loader.loadTestsFromTestCase(TestEmailSender))

    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    sys.exit(0 if result.wasSuccessful() else 1)
