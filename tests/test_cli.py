import unittest
from pathlib import Path

from worksheet_agents.__main__ import EXAMPLES_DIR, load_request, parse_args


class CliTests(unittest.TestCase):
    def test_input_name_selects_json_and_matching_output(self):
        args = parse_args(["--input", "linear_functions"])
        self.assertEqual(args.input, EXAMPLES_DIR / "inputs" / "linear_functions.json")
        self.assertEqual(args.output, EXAMPLES_DIR / "worksheets" / "linear_functions.md")
        self.assertEqual(load_request(args).topic, "Linear Functions")

    def test_explicit_path_and_output_remain_available(self):
        input_path = EXAMPLES_DIR / "inputs" / "ecosystems.json"
        args = parse_args(["--input", str(input_path), "--output", "custom/ecosystems.md"])
        self.assertEqual(args.input, input_path)
        self.assertEqual(args.output, Path("custom/ecosystems.md"))

    def test_direct_fields_derive_output_from_topic(self):
        args = parse_args([
            "--subject", "Science", "--topic", "Food Chains", "--grade", "5",
            "--objective", "Explain how energy moves through a food chain",
        ])
        self.assertEqual(args.output, EXAMPLES_DIR / "worksheets" / "food_chains.md")
        self.assertEqual(load_request(args).topic, "Food Chains")


if __name__ == "__main__":
    unittest.main()
