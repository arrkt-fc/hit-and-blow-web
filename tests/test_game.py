"""元コードを実行して得た判定・状態と関数版を比較する。"""
import ast
import contextlib
import io
import itertools
from pathlib import Path
import random
import runpy
import unittest
from unittest.mock import patch

from game import ALLOW_DUPLICATES, NO_DUPLICATES, Game, generate_answer, judge, validate_guess

ORIGINAL = Path(__file__).resolve().parents[1] / "original_game.py"


def run_original(answer, guesses, mode="1"):
    output = io.StringIO()
    with patch("builtins.input", side_effect=[mode, *guesses]), patch("random.sample", return_value=answer.copy()), patch("random.choices", return_value=answer.copy()), contextlib.redirect_stdout(output):
        state = runpy.run_path(str(ORIGINAL))
    return state, output.getvalue()


def original_judge():
    # 正本のASTから判定ブロックをそのまま抽出。参照処理を別の算法で再実装しない。
    tree = ast.parse(ORIGINAL.read_text())
    loop = tree.body[-1]
    start = next(i for i, node in enumerate(loop.body) if isinstance(node, ast.Assign) and isinstance(node.targets[0], ast.Name) and node.targets[0].id == "remaining_answer")
    stop = next(i for i in range(start, len(loop.body)) if isinstance(loop.body[i], ast.If) and isinstance(loop.body[i].test, ast.Compare) and ast.unparse(loop.body[i].test) == "hit == 4")
    return compile(ast.Module(body=loop.body[start:stop], type_ignores=[]), str(ORIGINAL), "exec")


class JudgeTests(unittest.TestCase):
    def test_known_cases(self):
        for answer, guess, expected in [([1,2,3,4],[1,2,3,4],(4,0)), ([1,2,3,4],[4,3,2,1],(0,4)), ([1,2,3,4],[5,6,7,8],(0,0)), ([1,1,2,2],[1,2,1,1],(1,2)), ([1,2,3,4],[2,2,2,2],(1,0)), ([1,1,1,2],[2,2,2,1],(0,2)), ([1,1,2,2],[2,2,1,1],(0,4))]:
            with self.subTest(answer=answer, guess=guess):
                self.assertEqual(judge(answer, guess), expected)

    def test_exact_original_algorithm_exhaustive(self):
        code = original_judge()
        # 1〜3の全4桁の組み合わせ、6,561組。重複とHIT位置の組み合わせを網羅。
        for a, g in itertools.product(itertools.product(range(1,4), repeat=4), repeat=2):
            answer, guess = list(a), list(g)
            namespace = dict(answer=answer, guess=guess, hit=0, blow=0, hit_positions=[])
            exec(code, namespace)
            self.assertEqual(judge(answer, guess), (namespace["hit"], namespace["blow"]))
            self.assertEqual(answer, list(a))
            self.assertEqual(guess, list(g))

    def test_exact_original_algorithm_random(self):
        code = original_judge()
        rng = random.Random(42)
        for _ in range(3000):
            a = [rng.randrange(1,10)] + rng.choices(range(10), k=3)
            g = [rng.randrange(1,10)] + rng.choices(range(10), k=3)
            namespace = dict(answer=a, guess=g, hit=0, blow=0, hit_positions=[])
            exec(code, namespace)
            self.assertEqual(judge(a, g), (namespace["hit"], namespace["blow"]))


class GameTests(unittest.TestCase):
    def test_generation_redraw_uses_original_calls(self):
        for mode, method, kwargs in [(NO_DUPLICATES,"sample",{}), (ALLOW_DUPLICATES,"choices",{"k":4})]:
            with self.subTest(mode=mode), patch("game.random." + method, side_effect=[[0,1,2,3], [0,4,5,6], [1,2,3,4]]) as draw:
                self.assertEqual(generate_answer(mode), [1,2,3,4])
                self.assertEqual(draw.call_count, 3)
                for call in draw.call_args_list:
                    if mode == NO_DUPLICATES:
                        self.assertEqual(call.args, (range(10),4))
                    else:
                        self.assertEqual(call.args, (range(10),))
                        self.assertEqual(call.kwargs, kwargs)

    def test_generation_modes(self):
        for mode in (NO_DUPLICATES, ALLOW_DUPLICATES):
            for _ in range(100):
                answer = generate_answer(mode)
                self.assertEqual(len(answer), 4)
                self.assertNotEqual(answer[0], 0)
                if mode == NO_DUPLICATES:
                    self.assertEqual(len(set(answer)), 4)
        with patch("game.random.choices", return_value=[1,1,1,1]):
            self.assertEqual(generate_answer(ALLOW_DUPLICATES), [1,1,1,1])

    def test_invalid_input_does_not_consume_attempt(self):
        game = Game(NO_DUPLICATES, [1,2,3,4])
        for value in ("", "123", "12345", "abcd", "1a23", " 123", "0123", "０１２３", "-123", "²²²²"):
            with self.subTest(value=value), self.assertRaises(ValueError):
                game.submit(value)
            self.assertEqual(game.remaining, 7)
            self.assertEqual(game.history, [])

    def test_duplicates_input_and_unicode_match_original(self):
        for mode in (NO_DUPLICATES, ALLOW_DUPLICATES):
            game = Game(mode, [1,2,3,4])
            self.assertEqual(game.submit("1111").hit, 1)
            self.assertEqual(game.submit("１２３４").hit, 4)
        self.assertEqual(validate_guess("١٢٣٤"), [1,2,3,4])

    def test_full_games_match_original(self):
        for mode, original_mode in [(NO_DUPLICATES,"1"),(ALLOW_DUPLICATES,"2")]:
            for guesses, expected in [(["1234"],"clear"), (["5678"]*6+["1234"],"clear"), (["5678"]*7,"over"), (["abc", "0123", "123", "1111", "１２３４"],"clear")]:
                with self.subTest(mode=mode, guesses=guesses):
                    old, output = run_original([1,2,3,4], guesses, original_mode)
                    game = Game(mode, [1,2,3,4])
                    for guess in guesses:
                        try:
                            game.submit(guess)
                        except ValueError:
                            pass
                    self.assertEqual(game.status, expected)
                    self.assertEqual(len(game.history), old["attempts"])
                    self.assertEqual((game.history[-1].hit,game.history[-1].blow), (old["hit"],old["blow"]))
                    self.assertIn("GAME CLEAR!" if expected == "clear" else "GAME OVER!", output)

    def test_duplicate_answer_full_game_matches_original(self):
        guesses = ["1211", "2222", "1122"]
        old, output = run_original([1,1,2,2], guesses, "2")
        game = Game(ALLOW_DUPLICATES, [1,1,2,2])
        for value in guesses:
            game.submit(value)
        self.assertEqual(game.status, "clear")
        self.assertEqual(len(game.history), old["attempts"])
        self.assertEqual([(a.hit, a.blow) for a in game.history], [(1,2),(2,0),(4,0)])
        for attempt in game.history:
            self.assertIn(f"HIT: {attempt.hit}\nBLOW: {attempt.blow}", output)

    def test_finished_game_rejects_more_attempts(self):
        game = Game(NO_DUPLICATES, [1,2,3,4])
        game.submit("1234")
        with self.assertRaises(ValueError):
            game.submit("5678")
        self.assertEqual(len(game.history), 1)


if __name__ == "__main__":
    unittest.main()
