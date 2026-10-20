# HIT & BLOW — 公開用

Python + Streamlit。提供された元コードの判定手順を維持しています。

## Streamlit Community Cloudへの公開

1. このフォルダの内容をGitHubの専用リポジトリに保存します。`.streamlit` フォルダも含めてください。
2. https://share.streamlit.io/ にログインし「Create app」を選択します。
3. 作成したリポジトリとブランチ、エントリーポイント `app.py` を指定します。
4. Advanced settingsでPython 3.12を選択します。
5. Deployを押し、起動後にSharingで公開範囲がPublicになっていることを確認します。
6. 発行された `https://…streamlit.app` を共有します。

閲覧者はPythonのインストール不要で、公開アプリはログインせずに遊べます。
公開URL: https://hit-blow-codebreaker.streamlit.app/

公開ソース: https://github.com/arrkt-fc/hit-and-blow-web

2026-10-20に公開しました。公開版はPython 3.12 / Streamlit 1.66.0で動作確認済みです。

公式手順: https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/deploy

## ローカルで実行・検証

Python 3.12の仮想環境で、次を実行してください。

```sh
python -m pip install -r requirements.txt
python -m unittest discover -s tests -v
python -m streamlit run app.py --server.address 127.0.0.1
```

公開版ではローカル専用の接続アドレス指定だけを外しています。
ゲームロジック・入力条件・勝敗条件・UIはローカル版と同一です。
各接続のゲーム状態はsession_stateで分離し、DBやユーザー情報は保存しません。
