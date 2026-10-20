import random
print("===== HIT & BLOW =====")
print()
print("ゲームモードを選択してください")
print()
print("1：重複なし")
print("2：重複あり")
print()
while True:
    mode = input("1 or 2を選択 →  ")
    #重複無し
    if mode == "1":
        answer = random.sample(range(10), 4)
        while answer[0] == 0:
            answer = random.sample(range(10), 4)
        break
    #重複あり
    elif mode == "2":
        answer = random.choices(range(10), k=4)
        while answer[0] == 0:
            answer = random.choices(range(10), k=4)
        break
    #入力値エラー
    else:
        print("数字の1か2を入力してください")
#挑戦回数
attempts = 0
while True:
    hit = 0
    blow = 0
    guess = []
    hit_positions = []
    print()
    numbers = input("4桁の数字を入力→")
    if len(numbers) != 4:
        print("4桁で入力してください")
        continue
    if numbers.isdigit() == False:
        print("入力できるのは数字のみ")
        continue
    if int(numbers[0]) == 0:
        print("先頭の数字は１〜９から選んでください")
        continue
    attempts += 1
    for i in numbers:
        i = int(i)
        guess.append(i)
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
    if hit == 4 :
        print(f"HIT: {hit}")
        print(f"BLOW: {blow}")
        print("GAME CLEAR!")
        break
    if (7-attempts) > 0:
        print(f"HIT: {hit}")
        print(f"BLOW: {blow}")
        print(f"チャレンジ回数残り： {7-attempts}")
        print()
    elif attempts == 7:
        print(f"HIT: {hit}")
        print(f"BLOW: {blow}")
        print("GAME OVER!")
        break
