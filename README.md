# 🎵 Evolution of Music

## 概要
本作は、1400年代のクラシック音楽から現代のポップスに至るまでの音楽ジャンルの系譜と歴史的マイルストーン（名盤・重要曲）を、ストリームグラフ（Sankey風）として可視化するプロジェクトです。
データに基づく正確な歴史の繋がりを保ちつつ、鑑賞に堪えうるポスターアートとしての美しさを両立するように設計されています。

初期のPythonスクリプトによる静的画像出力から進化し、現在は**StreamlitによるGUIデータエディター**と、**ブラウザで閲覧可能なインタラクティブな静的HTML（SVG）**を出力するシステム構成となっています。

## 📁 ディレクトリ構成

保守性と拡張性を高めるため、フロントエンド（編集画面）、バックエンド（描画）、データソースが完全に分離されています。

```text
evolution_of_music/
│
├─ editor.py          # 📝 [フロントエンド] データ編集・ビルド実行用のStreamlitアプリ
├─ build.py           # 🚀 [ビルド用] データを読み込み、最終的なHTML/SVGを生成するスクリプト
├─ index.html         # ✨ [成果物] ビルド後に生成される静的Webページ（ブラウザで閲覧）
│
├─ data/              # 💾 [データソース]
│  ├─ genres.csv      # ジャンルの定義（誕生年、親子関係、テーマカラーなど）
│  └─ milestones.csv  # 記念碑的な名盤・重要曲のデータ
│
└─ src/               # ⚙️ [バックエンド]
   ├─ data.py         # CSVデータの読み込み・パース処理
   ├─ layout.py       # NetworkXを用いたY座標の計算や時間軸の非線形変換
   └─ render.py       # Matplotlibを用いたSVG描画・テキストの衝突回避（物理演算）エンジン

```

## 🛠 環境構築

動作にはPython 3.10以上を推奨します。依存パッケージは `requirements.txt` からインストールしてください。

```bash
# 依存ライブラリのインストール
pip install -r requirements.txt

```

**【💡 インストール時の注意（トラブルシューティング）】**
もし `matplotlib` や `numpy` の特定バージョンが見つからないというエラー（`No matching distribution found`）が出た場合は、バージョン指定を外して手動で最新版をインストールしてください。

```bash
pip install streamlit pandas matplotlib networkx

```

## 📦 依存パッケージの管理・更新

開発を進める中で新しいPythonライブラリを追加した場合は、`pipreqs` を使用して `requirements.txt` を最新の状態に更新してください。

```bash
# 1. pipreqsのインストール（未インストールの場合）
pip install pipreqs

# 2. requirements.txtの自動生成・上書き（文字化け防止のためutf8を指定）
pipreqs . --encoding=utf8 --force

# 3. 更新されたパッケージの適用
pip install -r requirements.txt

```

## 🚀 実行方法・ワークフロー

データファイルの直接編集は非推奨です。必ず用意されたGUIエディターを使用してください。

### 1. エディターの起動

以下のコマンドをターミナルで実行し、データエディター（Streamlit）を起動します。

```bash
streamlit run editor.py

```

起動すると、ブラウザで自動的に `http://localhost:8501` が開きます。

### 2. データの編集

* **Genres (ジャンル)**: 左側のテーブルでデータを直接編集できます。右側のパネルでは、Mermaidによる系統樹のプレビュー確認や、親ジャンルの複数選択、カラーピッカーを使ったテーマカラーの変更が可能です。
* **Milestones (マイルストーン)**: ジャンルの帯を膨張させる起点となる名盤や重要曲を登録します。

### 3. ビルド＆プレビュー

1. エディターのサイドバーから「ビルド＆プレビュー」を選択します。
2. **「✨ build.py を実行して全体画像を更新」** ボタンをクリックします。
3. バックグラウンドで `build.py` が実行され、成功すると自動的にブラウザの別タブで最新の `index.html` が開きます。

## 🌐 Webでの一般公開（GitHub Pages）

このプロジェクトの成果物（`index.html`、出力されたSVG画像、座標データ等の関連ファイル）はすべて静的ファイルとして構成されているため、**GitHub Pages** を使って無料で簡単に一般公開することができます。

### 公開手順

1. **変更をGitHubにプッシュする**:
ローカルでの編集とビルドが完了したら、最新の状態をGitHubリポジトリ（`main` ブランチ）にプッシュします。
```bash
git add .
git commit -m "Update music evolution data and build output"
git push origin main

```


2. **GitHub Pagesの設定を有効化する**:
* GitHubのリポジトリページ（例: `https://github.com/KI1128/evolution_of_music`）を開きます。
* 上部の **「Settings」** タブをクリックし、左側メニューの **「Pages」** を選択します。
* **Build and deployment** の **Source** を「Deploy from a branch」に設定します。
* **Branch** のドロップダウンから `main` を選択し、フォルダは `/ (root)` のまま **「Save」** をクリックします。


3. **公開完了**:
数分待つとデプロイが完了し、`https://<あなたのユーザー名>.github.io/evolution_of_music/` のURLで、世界中からアクセス可能なインタラクティブな系譜グラフが公開されます！

## ⚠️ 開発者向け・既知の仕様と注意点

* **Streamlitの警告について**:
エディター起動中、ターミナルに `Please replace use_container_width with width.` という警告が連続して出力される場合があります。これは将来のバージョンに向けた仕様変更の予告であり、現在の動作に悪影響はありません。
* **文字コードエラー**:
Windows環境で `build.py` 実行時に `UnicodeEncodeError` が発生するのを防ぐため、エディターからのビルド実行時は内部的に `python -X utf8 build.py` として呼び出しています。手動でビルドする場合は文字コードにご注意ください。
* **CSVの保存形式**:
エディターからCSVを保存する際、Excel等での文字化けを防ぐため `utf-8-sig` (BOM付きUTF-8) 形式を採用しています。
* **数値の型変換**:
CSVからデータを読み込む際、Pandasの仕様により年数が小数点付き（例: `1950.0`）として扱われることがあります。`src/data.py` 内で `int(float(value))` のように安全に型変換する処理を入れています。
