import unittest
from pathlib import Path
from unittest.mock import patch

from miniventory.__main__ import default_data_path, parse_args


class MainTests(unittest.TestCase):
    def test_default_data_path(self) -> None:
        path = default_data_path()
        self.assertEqual(path.name, "collection.json")
        self.assertEqual(path.parent.name, ".miniventory")

    def test_parse_args_default(self) -> None:
        with patch("sys.argv", ["miniventory"]):
            args = parse_args()
        self.assertEqual(args.data, default_data_path())

    def test_parse_args_custom_data_path(self) -> None:
        with patch("sys.argv", ["miniventory", "--data", "/tmp/test.json"]):
            args = parse_args()
        self.assertEqual(args.data, Path("/tmp/test.json"))


if __name__ == "__main__":
    unittest.main()