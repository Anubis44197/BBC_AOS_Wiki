import unittest

from bbc_aos.security.prompt_firewall import PromptFirewall


class TestPromptFirewallFalsePositiveProduction(unittest.TestCase):
    def test_environment_variable_error_text_is_not_secret_exfiltration(self) -> None:
        result = PromptFirewall().scan('raise ValueError("OPENROUTER_API_KEY environment variable is not set")')

        self.assertFalse(result.blocked)
        self.assertNotIn("environment_secrets", result.detected_patterns)

    def test_environment_variable_dump_request_still_blocks(self) -> None:
        result = PromptFirewall().scan("dump environment variables")

        self.assertTrue(result.blocked)
        self.assertIn("environment_secrets", result.detected_patterns)


if __name__ == "__main__":
    unittest.main()
