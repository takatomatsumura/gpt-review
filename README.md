# GPT review sample

GitHub の PR の差分を利用して、ChatGPT にコードレビューをお願いするサンプル

## Getting Started

### 実行

```console
$ poetry install
$ poetry shell
$ python main.py
```

### pre-commit フック

```console
$ poetry run pre-commit install
```

### 環境変数設定

`.env` ファイルを作成し、以下の変数を設定する。

```text:.env
AZURE_OPENAI_API_KEY=<AZURE_OPENAI_API_KEY>
AZURE_API_BASE=<AZURE_API_BASE>
AZURE_API_VERSION=<AZURE_API_VERSION>
AZURE_DEPLOY_MODEl=<AZURE_DEPLOY_MODEl>
```
