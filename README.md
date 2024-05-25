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
AZURE_DEPLOY_MODEL=<AZURE_DEPLOY_MODEL>
INPUT_MAX_TOKEN=<INPUT_MAX_TOKEN>
OUTPUT_MAX_TOKEN=<OUTPUT_MAX_TOKEN>
<!-- optional -->
DIFF_FILE=diff.txt
PROMPT_FILE=prompt.md
EXCLUDE_FILES=README\.md,prompt\.md,pyproject\.toml,poetry\.lock,\.gitignore
```
