"""ゲームロジック。提供された original_game.py の処理を関数化。"""
import random
from dataclasses import dataclass, field
from typing import List, Tuple

MAX_ATTEMPTS = 7
NO_DUPLICATES = "重複なし"
ALLOW_DUPLICATES = "重複あり"
MODES = (NO_DUPLICATES, ALLOW_DUPLICATES)


def generate_answer(mode: str) -> List[int]:
    if mode not in MODES:
        raise ValueError("不明なモードです。")
    while True:
        if mode == NO_DUPLICATES:
            answer = random.sample(range(10), 4)
        else:
            answer = random.choices(range(10), k=4)
        if answer[0] != 0:
            return answer


def validate_guess(value: str) -> List[int]:
    # 元コードどおり、モードによる重複入力の制限は設けない。
    if len(value) != 4:
        raise ValueError("4桁で入力してください。")
    if value.isdigit() == False:
        raise ValueError("入力できるのは数字のみです。")
    if int(value[0]) == 0:
        raise ValueError("先頭の数字は1〜9から選んでください。")
    return [int(c) for c in value]


def judge(answer: List[int], guess: List[int]) -> Tuple[int, int]:
    """HITの位置を両方から削除した後、BLOWを1つずつ消費する。"""
    hit = 0
    blow = 0
    hit_positions = []
    remaining_answer = answer.copy()
    remaining_guess = guess.copy()
    for num in range(0, 4):
        if answer[num] == guess[num]:
            hit += 1
            hit_positions.append(num)
    for pos in reversed(hit_positions):
        remaining_answer.pop(pos)
        remaining_guess.pop(pos)
    for x in remaining_answer:
        if x in remaining_guess:
            blow += 1
            remaining_guess.remove(x)
    return hit, blow


@dataclass(frozen=True)
class Attempt:
    number: int
    guess: str
    hit: int
    blow: int


@dataclass
class Game:
    mode: str
    answer: List[int]
    history: List[Attempt] = field(default_factory=list)
    status: str = "playing"

    @classmethod
    def new(cls, mode: str) -> "Game":
        return cls(mode=mode, answer=generate_answer(mode))

    @property
    def remaining(self) -> int:
        return MAX_ATTEMPTS - len(self.history)

    def submit(self, value: str) -> Attempt:
        if self.status != "playing":
            raise ValueError("ゲームは終了しています。RETRYで再開してください。")
        guess = validate_guess(value)
        hit, blow = judge(self.answer, guess)
        attempt = Attempt(len(self.history) + 1, value, hit, blow)
        self.history.append(attempt)
        # 最終回でも、勝利を先に判定する。
        if hit == 4:
            self.status = "clear"
        elif self.remaining == 0:
            self.status = "over"
        return attempt
