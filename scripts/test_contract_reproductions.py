"""Independent synthetic reproductions; these are not model-behavior eval results."""
from decimal import Decimal
from hashlib import sha256
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest


def verified_input(path, digest):
    payload = path.read_bytes()
    if sha256(payload).hexdigest() != digest:
        raise ValueError("input digest mismatch")
    return payload


class Renderer:
    def render(self):
        return "ready"


def construct(renderer):
    return renderer.render()


def numeric_result():
    return Decimal("12.50")


class ContractReproductions(unittest.TestCase):
    def test_file_fixture_contract(self):
        with TemporaryDirectory() as tmp:
            path = Path(tmp) / "input.txt"
            payload = b"synthetic input"
            digest = sha256(payload).hexdigest()
            with self.assertRaises(FileNotFoundError):
                verified_input(path, digest)
            path.write_bytes(payload)
            self.assertEqual(verified_input(path, digest), payload)
            with self.assertRaises(ValueError):
                verified_input(path, "invalid")

    def test_runtime_fixture_interface(self):
        with self.assertRaises(AttributeError):
            construct(object())
        self.assertEqual(construct(Renderer()), "ready")

    def test_result_type_contract(self):
        value = numeric_result()
        self.assertIsInstance(value, Decimal)
        self.assertNotEqual(value, "12.50")
        self.assertEqual(value, Decimal("12.50"))
        self.assertEqual(format(value, "f"), "12.50")


if __name__ == "__main__":
    unittest.main(verbosity=2)
