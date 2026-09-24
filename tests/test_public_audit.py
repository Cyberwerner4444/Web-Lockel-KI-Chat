import contextlib
import importlib.util
import io
import tempfile
import unittest
from pathlib import Path


AUDIT_PATH = Path(__file__).resolve().parents[1] / "tools" / "public_audit.py"
SPEC = importlib.util.spec_from_file_location("public_audit", AUDIT_PATH)
public_audit = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(public_audit)


class PublicAuditTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory(prefix="helmut-public-audit-test-")
        self.old_root = public_audit.ROOT
        public_audit.ROOT = Path(self.temp_dir.name)

    def tearDown(self):
        public_audit.ROOT = self.old_root
        self.temp_dir.cleanup()

    def run_audit(self):
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            status = public_audit.main()
        return status, output.getvalue()

    def test_private_environment_file_is_rejected(self):
        (public_audit.ROOT / ".env").write_text("SECRET=placeholder\n", encoding="utf-8")
        status, output = self.run_audit()
        self.assertEqual(status, 1)
        self.assertIn("private environment file", output)

    def test_environment_template_contents_are_scanned(self):
        (public_audit.ROOT / ".env.example").write_text(
            "SERVER=198.51.100." + "42\n", encoding="utf-8"
        )
        status, output = self.run_audit()
        self.assertEqual(status, 1)
        self.assertIn("private/production pattern", output)

    def test_out_of_scope_pages_and_logos_are_rejected(self):
        (public_audit.ROOT / "live-mining.html").write_text("", encoding="utf-8")
        logo = public_audit.ROOT / "assets" / "helmut-logo.jpg"
        logo.parent.mkdir()
        logo.write_bytes(b"test")
        status, output = self.run_audit()
        self.assertEqual(status, 1)
        self.assertIn("out-of-scope legacy page/feature", output)
        self.assertIn("out-of-scope upload/logo asset", output)

    def test_sanitized_environment_template_and_caddy_placeholder_pass(self):
        (public_audit.ROOT / ".env.example").write_text(
            "HOST=127.0.0.1\nKEY=replace-this-locally\n", encoding="utf-8"
        )
        (public_audit.ROOT / "Caddyfile").write_text(
            "example.com { reverse_proxy 127.0.0.1:8080 }\n", encoding="utf-8"
        )
        status, output = self.run_audit()
        self.assertEqual(status, 0, output)


if __name__ == "__main__":
    unittest.main()
