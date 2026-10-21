from pathlib import Path
import tempfile
import unittest

from publish_custom_release import collect_assets, release_artifact


class PublishCustomReleaseTests(unittest.TestCase):
    def test_only_final_artifacts_are_selected(self):
        for name in ("custom-windows-flutter-x86_64-exe", "custom-ios-unsigned-xcarchive", "rustdesk-unsigned-macos-aarch64", "rustdesk-1.5.1-universal.apk"):
            self.assertTrue(release_artifact(name))
        for name in ("bridge-artifact", "librustdesk.so.aarch64-linux-android", "rustdesk-unsigned-windows-x86_64", "rustdesk-unsigned-msi-template-aarch64"):
            self.assertFalse(release_artifact(name))

    def test_collects_installers_and_rejects_conflicting_names(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            source = root / "downloads"
            (source / "one").mkdir(parents=True)
            (source / "two").mkdir()
            (source / "one/client.exe").write_bytes(b"installer")
            (source / "two/client.exe").write_bytes(b"installer")
            (source / "one/library.so").write_bytes(b"intermediate")
            collect_assets(source, root / "assets")
            self.assertEqual({p.name for p in (root / "assets").iterdir()}, {"client.exe", "SHA256SUMS"})
            (source / "two/client.exe").write_bytes(b"different")
            with self.assertRaises(ValueError):
                collect_assets(source, root / "conflict")


if __name__ == "__main__":
    unittest.main()
