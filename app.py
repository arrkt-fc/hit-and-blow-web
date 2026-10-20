"""Streamlit UI。実行: python -m streamlit run app.py"""
from html import escape
from pathlib import Path

import streamlit as st

from game import Game, MODES, NO_DUPLICATES

st.set_page_config(page_title="HIT & BLOW", page_icon="🔷", layout="centered")
st.markdown(f"<style>{Path(__file__).with_name('style.css').read_text()}</style>", unsafe_allow_html=True)

for key, value in {"game": None, "screen": "title", "guess_input": "", "accepted_input": "", "error": "", "input_revision": 0, "animate_input": False, "animate_result": False}.items():
    if key not in st.session_state:
        st.session_state[key] = value


def start():
    st.session_state.game = Game.new(st.session_state.mode_select)
    st.session_state.screen = "game"
    reset_input()


def reset_input():
    st.session_state.guess_input = ""
    st.session_state.accepted_input = ""
    st.session_state.error = ""
    st.session_state.animate_input = False
    st.session_state.animate_result = False


def retry():
    st.session_state.game = None
    st.session_state.screen = "title"
    reset_input()


def input_changed():
    value = st.session_state.guess_input
    # 不正な貼り付けは削除・変換せず、直前の有効な入力に戻す。
    if (value and not value.isdigit()) or len(value) > 4:
        st.session_state.guess_input = st.session_state.accepted_input
        st.session_state.error = "数字を4桁まで入力できます。"
        return
    try:
        converted = [int(c) for c in value]
    except ValueError:
        st.session_state.guess_input = st.session_state.accepted_input
        st.session_state.error = "0〜9の数字を入力してください。"
        return
    if converted and converted[0] == 0:
        st.session_state.guess_input = st.session_state.accepted_input
        st.session_state.error = "先頭に0は使えません。"
        return
    st.session_state.accepted_input = value
    st.session_state.error = ""
    st.session_state.input_revision += 1
    st.session_state.animate_input = True
    st.session_state.animate_result = False


def digit(value):
    current = st.session_state.guess_input
    if len(current) == 4:
        return
    st.session_state.guess_input = current + value
    input_changed()


def delete():
    st.session_state.guess_input = st.session_state.guess_input[:-1]
    input_changed()


def submit():
    try:
        st.session_state.game.submit(st.session_state.guess_input)
    except ValueError as error:
        st.session_state.error = str(error)
        return
    reset_input()
    st.session_state.animate_result = True


def history(game):
    st.markdown('<div class="section-label">ATTEMPT LOG <span>挑戦履歴 · 新しい順</span></div>', unsafe_allow_html=True)
    rows = ""
    for index, attempt in enumerate(reversed(game.history)):
        animation = " latest" if index == 0 and st.session_state.animate_result else ""
        rows += f'<tr class="{animation}"><td>{attempt.number:02}</td><td class="guess">{escape(attempt.guess)}</td><td class="hit">{attempt.hit}</td><td class="blow">{attempt.blow}</td></tr>'
    if not rows:
        rows = '<tr><td colspan="4" class="empty-log">まだ挑戦はありません。最初の4桁を入力しましょう。</td></tr>'
    st.markdown('<div class="log-wrap"><table aria-label="挑戦履歴"><thead><tr><th scope="col">挑戦番号</th><th scope="col">入力数字</th><th scope="col">HIT</th><th scope="col">BLOW</th></tr></thead><tbody>' + rows + '</tbody></table></div>', unsafe_allow_html=True)


st.markdown('<div class="brand-line"><span class="signal"></span> CODEBREAKER SYSTEM <span class="version">01 / 07</span></div>', unsafe_allow_html=True)

if st.session_state.screen == "title":
    st.markdown('''<div class="hero"><div class="eyebrow">FOUR DIGITS. SEVEN CHANCES.</div>
    <h1>HIT <span class="accent">&</span><br>BLOW<span class="period">.</span></h1>
    <p>4桁の暗号を、解き明かせ。</p></div>
    <div class="preview-code" aria-hidden="true"><span>?</span><span>?</span><span>?</span><span>?</span></div>''', unsafe_allow_html=True)
    st.markdown('<div class="section-label">SELECT MODE <span>ゲームモードを選択</span></div>', unsafe_allow_html=True)
    st.radio("ゲームモード", MODES, key="mode_select", horizontal=True, label_visibility="collapsed")
    description = "正解はすべて異なる数字。" if st.session_state.mode_select == NO_DUPLICATES else "正解に同じ数字が複数含まれることがあります。"
    st.caption(description + " どちらのモードも入力には同じ数字を使えます。")
    st.button("START GAME →", type="primary", use_container_width=True, on_click=start)
    st.markdown('<div class="rules"><div><b>HIT</b><span>数字も位置も一致</span></div><div><b>BLOW</b><span>数字が一致・位置は違う</span></div></div>', unsafe_allow_html=True)
    st.caption("数字4桁 / 先頭0は禁止 / 最大7回 / 4HITでクリア")
else:
    game = st.session_state.game
    st.markdown('<div class="game-heading"><h1>HIT <span class="accent">&</span> BLOW</h1><p>4桁の暗号を、解き明かせ。</p></div>', unsafe_allow_html=True)
    st.markdown(f'<div class="status-strip"><div><small>GAME MODE</small><strong>{game.mode}</strong></div><div><small>CHANCES LEFT</small><strong class="remaining">{game.remaining}<span> / 7</span></strong></div></div>', unsafe_allow_html=True)
    pips = ''.join('<span class="used"></span>' if i < len(game.history) else '<span></span>' for i in range(7))
    st.markdown(f'<div class="pips" aria-label="残り{game.remaining}回">{pips}</div>', unsafe_allow_html=True)
    if game.status == "playing":
        st.markdown('<div class="section-label">ENTER YOUR CODE <span>4桁の数字を入力</span></div>', unsafe_allow_html=True)
        value = st.session_state.guess_input
        cells = ''.join(f'<span class="filled">{c}</span>' if i < len(value) else '<span>·</span>' for i, c in enumerate(value.ljust(4)))
        animation = " input-pop" if st.session_state.animate_input else ""
        st.markdown(f'<div class="code-display{animation}" data-revision="{st.session_state.input_revision}" aria-hidden="true">{cells}</div>', unsafe_allow_html=True)
        st.text_input("数字入力（4桁・先頭0不可）", key="guess_input", placeholder="例: 1234", on_change=input_changed, autocomplete="off")
        if st.session_state.error:
            st.error(st.session_state.error)
        st.markdown('<div class="keypad-anchor"></div>', unsafe_allow_html=True)
        with st.container(key="keypad"):
            for group in ("123", "456", "789"):
                for col, number in zip(st.columns(3), group):
                    col.button(number, key=f"digit_{number}", use_container_width=True, on_click=digit, args=(number,), disabled=len(value) == 4)
            cols = st.columns(3)
            cols[0].button("削除 ⌫", key="delete", use_container_width=True, on_click=delete, disabled=not value)
            cols[1].button("0", key="digit_0", use_container_width=True, on_click=digit, args=("0",), disabled=len(value) == 4 or not value)
            cols[2].button("判定 →", key="submit", type="primary", use_container_width=True, on_click=submit)
        if game.history:
            last = game.history[-1]
            animation = " result-in" if st.session_state.animate_result else ""
            st.markdown(f'<div class="last-result{animation}" role="status">{last.guess} <span>→</span> <b>{last.hit} HIT</b><span>/</span><b>{last.blow} BLOW</b></div>', unsafe_allow_html=True)
        else:
            st.caption("テンキーまたはキーボードで入力し、「判定」を押してください。")
    else:
        clear = game.status == "clear"
        status = "clear" if clear else "over"
        title = "GAME CLEAR!" if clear else "GAME OVER!"
        message = f"{len(game.history)}回目で暗号を解読しました。" if clear else "7回の挑戦が終了しました。"
        st.markdown(f'<div class="end-card {status}" role="status"><div class="eyebrow">{"ACCESS GRANTED" if clear else "ACCESS DENIED"}</div><h2>{title}</h2><p>{message}</p><small>ANSWER</small><div class="answer">{"".join(map(str, game.answer))}</div></div>', unsafe_allow_html=True)
        st.button("RETRY → モード選択へ", type="primary", use_container_width=True, on_click=retry)
    history(game)
    with st.expander("遊び方・入力ルール"):
        st.write("HIT：数字と位置が一致。BLOW：数字は含まれるが位置が異なる。4HITでクリアです。")
        st.write("最大7回。7回目の正解もクリアです。入力エラーは回数に含めません。数字4桁・先頭0は禁止。どちらのモードでも同じ数字を入力できます。")

st.markdown('<div class="footer">HIT & BLOW <span>•</span> THINK. TRY. DECODE.</div>', unsafe_allow_html=True)
