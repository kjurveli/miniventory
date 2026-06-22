import io
import unittest
from unittest.mock import patch

from rich.console import Console

from miniventory import ui


class UiHelperTests(unittest.TestCase):
    def setUp(self) -> None:
        self.output = io.StringIO()
        self.test_console = Console(
            file=self.output, force_terminal=True, width=80, legacy_windows=False
        )
        self._original_console = ui.console
        ui.console = self.test_console

    def tearDown(self) -> None:
        ui.console = self._original_console

    def test_print_tags_with_values(self) -> None:
        result = ui.print_tags(["loyalist", "troops"])
        self.assertIn("loyalist", result)
        self.assertIn("cyan", result)

    def test_print_tags_empty(self) -> None:
        self.assertEqual(ui.print_tags([]), "[dim](none)[/]")

    def test_print_success_renders_checkmark(self) -> None:
        ui.print_success("Saved")
        self.assertIn("Saved", self.output.getvalue())

    def test_print_warning_renders_cross(self) -> None:
        ui.print_warning("Failed")
        self.assertIn("Failed", self.output.getvalue())

    def test_print_filter_banner_skips_when_no_tags(self) -> None:
        ui.print_filter_banner([])
        self.assertEqual(self.output.getvalue(), "")

    def test_print_filter_banner_renders_tags(self) -> None:
        ui.print_filter_banner(["loyalist"])
        self.assertIn("loyalist", self.output.getvalue())

    def test_print_numbered_list(self) -> None:
        ui.print_numbered_list(["One", "Two"], show_back=True)
        rendered = self.output.getvalue()
        self.assertIn("One", rendered)
        self.assertIn("Two", rendered)
        self.assertIn("Back", rendered)


class UiPromptTests(unittest.TestCase):
    def setUp(self) -> None:
        self._original_console = ui.console

    def tearDown(self) -> None:
        ui.console = self._original_console

    @patch.object(Console, "input", return_value="Ultramarines")
    def test_prompt_text_returns_entered_value(self, _mock_input) -> None:
        ui.console = Console()
        self.assertEqual(ui.prompt_text("Name"), "Ultramarines")

    @patch.object(Console, "input", return_value="")
    def test_prompt_text_uses_default_when_blank(self, _mock_input) -> None:
        ui.console = Console()
        self.assertEqual(ui.prompt_text("Name", "Default"), "Default")

    @patch.object(Console, "input", return_value="y")
    def test_prompt_yes_no_accepts_yes(self, _mock_input) -> None:
        ui.console = Console()
        self.assertTrue(ui.prompt_yes_no("Continue?"))

    @patch.object(Console, "input", return_value="n")
    def test_prompt_yes_no_accepts_no(self, _mock_input) -> None:
        ui.console = Console()
        self.assertFalse(ui.prompt_yes_no("Continue?"))

    @patch.object(Console, "input", return_value="")
    def test_prompt_tags_keeps_current_when_blank(self, _mock_input) -> None:
        ui.console = Console(file=io.StringIO(), force_terminal=True)
        self.assertEqual(ui.prompt_tags(current=["existing"]), ["existing"])

    @patch.object(Console, "input", return_value="alpha, Beta ")
    def test_prompt_tags_parses_comma_separated(self, _mock_input) -> None:
        ui.console = Console(file=io.StringIO(), force_terminal=True)
        self.assertEqual(ui.prompt_tags(), ["alpha", "Beta"])

    @patch.object(Console, "input", return_value="2")
    def test_prompt_choice_selects_by_number(self, _mock_input) -> None:
        ui.console = Console(file=io.StringIO(), force_terminal=True)
        result = ui.prompt_choice("Pick", ["one", "two", "three"])
        self.assertEqual(result, "two")

    @patch.object(Console, "input", side_effect=["", "2"])
    def test_select_from_list_retries_on_invalid_then_succeeds(
        self, mock_input
    ) -> None:
        ui.console = Console(file=io.StringIO(), force_terminal=True, width=80)
        items = ["Alpha", "Beta"]
        result = ui.select_from_list("Pick one", items, lambda item: item)
        self.assertEqual(result, "Beta")
        self.assertEqual(mock_input.call_count, 2)

    @patch.object(Console, "input", return_value="0")
    def test_select_from_list_cancel_returns_none(self, _mock_input) -> None:
        ui.console = Console(file=io.StringIO(), force_terminal=True, width=80)
        result = ui.select_from_list("Pick one", ["Alpha"], lambda item: item)
        self.assertIsNone(result)

    def test_select_from_list_empty_returns_none(self) -> None:
        ui.console = Console(file=io.StringIO(), force_terminal=True, width=80)
        result = ui.select_from_list("Pick one", [], lambda item: item)
        self.assertIsNone(result)


if __name__ == "__main__":
    unittest.main()