from pathlib import Path
import unittest
from unittest.mock import patch
from streamlit.testing.v1 import AppTest

APP = Path(__file__).resolve().parents[1] / "app.py"


class AppTests(unittest.TestCase):
    def start(self, mode="重複なし", answer=None):
        app = AppTest.from_file(str(APP)).run()
        app.radio(key="mode_select").set_value(mode).run()
        with patch("game.generate_answer", return_value=answer or [1,2,3,4]):
            app.button[0].click().run()
        self.assertEqual(len(app.exception), 0)
        return app

    def test_keypad_delete_validation_and_answer_persistence(self):
        app = self.start()
        with patch("game.generate_answer", side_effect=AssertionError("unexpected redraw")):
            for n in "112":
                app.button(key="digit_"+n).click().run()
            app.button(key="delete").click().run()
            self.assertEqual(app.text_input[0].value, "11")
            app.button(key="submit").click().run()
            self.assertEqual(app.session_state.game.remaining, 7)
            self.assertEqual(len(app.error), 1)
            app.text_input[0].input("abcd").run()
            self.assertEqual(app.text_input[0].value, "11")
            app.text_input[0].input("0123").run()
            self.assertEqual(app.session_state.game.remaining, 7)
            app.text_input[0].input("2222").run()
            app.button(key="submit").click().run()
            self.assertEqual(app.session_state.game.remaining, 6)
            self.assertEqual(app.session_state.game.answer, [1,2,3,4])
            app.run()
            self.assertEqual(app.session_state.game.answer, [1,2,3,4])
            self.assertEqual(len(app.exception), 0)

    def test_both_modes_clear_seventh_and_retry(self):
        for mode in ("重複なし", "重複あり"):
            with self.subTest(mode=mode):
                app = self.start(mode)
                for _ in range(6):
                    app.text_input[0].input("5678").run()
                    app.button(key="submit").click().run()
                app.text_input[0].input("１２３４").run()
                app.button(key="submit").click().run()
                self.assertEqual(app.session_state.game.status, "clear")
                self.assertTrue(any("GAME CLEAR!" in x.value for x in app.markdown))
                self.assertEqual(len(app.text_input), 0)
                app.button[0].click().run()
                self.assertEqual(app.session_state.screen, "title")
                self.assertIsNone(app.session_state.game)
                with patch("game.generate_answer", return_value=[9,8,7,6]):
                    app.button[0].click().run()
                self.assertEqual(app.session_state.game.answer, [9,8,7,6])
                self.assertEqual(app.session_state.game.remaining, 7)
                self.assertEqual(app.session_state.guess_input, "")
                self.assertEqual(len(app.exception), 0)

    def test_over_on_seventh_and_newest_first(self):
        app = self.start("重複あり", [1,1,2,2])
        for guess in ["1211", "2222", "5678", "5678", "5678", "5678", "5678"]:
            app.text_input[0].input(guess).run()
            app.button(key="submit").click().run()
        self.assertEqual(app.session_state.game.status, "over")
        self.assertEqual(app.session_state.game.remaining, 0)
        self.assertEqual((app.session_state.game.history[0].hit, app.session_state.game.history[0].blow), (1,2))
        self.assertTrue(any("GAME OVER!" in x.value for x in app.markdown))
        table = next(x.value for x in app.markdown if 'aria-label="挑戦履歴"' in x.value)
        self.assertLess(table.index('<td>07</td>'), table.index('<td>01</td>'))
        self.assertEqual(len(app.exception), 0)


if __name__ == "__main__":
    unittest.main()
