import os
import json
from openai import AzureOpenAI


PROMPT_DIFF_FILE = "diff_with_line_number.txt"


def add_line_numbers_to_diff(diff_file: str):
    with open(diff_file, "r") as f:
        diff = f.readlines()
    result: list[str] = []
    line_number: int = 0
    for d in diff:
        if d.startswith("+++") or d.startswith("---"):
            result.append(d)
            continue
        if d.startswith("@@"):
            headers = d.split(" ")
            line_number = int(headers[2].split(",")[0].replace("+", ""))
            result.append(d)
            continue
        if d.startswith(" "):
            d = f" {line_number}" + d
            line_number += 1
        if d.startswith("+"):
            d = f" {line_number}" + d
            line_number += 1
        if d.startswith("-"):
            d = " " + d
        result.append(d)

    with open(PROMPT_DIFF_FILE, "w") as f:
        f.writelines(result)


def review():
    AZURE_OPENAI_API_KEY = os.getenv("AZURE_OPENAI_API_KEY")
    AZURE_API_BASE = os.getenv("AZURE_API_BASE")
    AZURE_API_VERSION = os.getenv("AZURE_API_VERSION")
    AZURE_DEPLOY_MODEL = os.getenv("AZURE_DEPLOY_MODEL")
    DIFF_FILE = os.getenv("DIFF_FILE", "diff.txt")

    add_line_numbers_to_diff(diff_file=DIFF_FILE)

    client = AzureOpenAI(
        api_key=AZURE_OPENAI_API_KEY,
        api_version=AZURE_API_VERSION,
        azure_endpoint=AZURE_API_BASE,
        azure_deployment=AZURE_DEPLOY_MODEL,
    )

    with open(PROMPT_DIFF_FILE, "r") as f:
        diff = f.read()

    functions = [
        {
            "name": "code_review",
            "description": "Engineer-friendly code review of GitHub diffs in application development",
            "parameters": {
                "type": "object",
                "properties": {
                    "reviews": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "file_path": {
                                    "type": "string",
                                    "description": "Read the path of the file to be pointed out from the differences.",
                                },
                                "line_number": {
                                    "type": "number",
                                    "description": "Read the line numbers listed at the left end of each line from the provided differences such as ' <line_number>+ <code>' not '<line_number> <code>'."
                                    "Always specify the line numbers of the code after the changes, not before.",
                                },
                                "perspective": {
                                    "type": "string",
                                    "description": "Select the perspective from which the code had an issue: 'パフォーマンス', 'セキュリティ', or '保守性'. Must be Japanese.",
                                },
                                "level": {
                                    "type": "string",
                                    "description": "Evaluate how critical the issue is on a scale."
                                    "Please choose from the following six options: Critical, High, Medium, Low, Warning, Info."
                                    "Note that the level decreases from Critical to Info. Must be English.",
                                },
                                "review_comment": {
                                    "type": "string",
                                    "description": "Describe the specific issues. Write the code correction proposals in 'fixed_code'. Must be Japanese.",
                                },
                                "fixed_code": {
                                    "type": "string",
                                    "description": "Only write the corrected code. Do not write review comments or points of issue here, make sure it is not influenced by Japanese or English."
                                    "Please maintain the indentation of the code below. Additionally, if there is no specific code to correct, it can be omitted.",
                                },
                            },
                            "required": [
                                "file_path",
                                "line_number",
                                "perspective",
                                "level",
                                "review_comment",
                            ],
                        },
                    },
                },
            },
        }
    ]

    chat_completion = client.chat.completions.create(
        messages=[
            {
                "role": "user",
                "content": "The differences provided are code differences that occurred on GitHub during app development.\n"
                "Please conduct a code review from the perspectives of security, performance, and maintainability, and provide suggestions for corrections.\n"
                "However, the output format should include the location of the suggestion (file path and line number), the content of the observation, and the corrected code in JSON format.\n"
                "Additionally, please include motivational and partially affirmative comments in the review comments, such as 'Almost there! Keep it up!' or 'This is good from a maintainability perspective, but it's not so good from a performance perspective.'"
                "Be careful not to offend the implementer. The review content can be in Japanese. Please use Japanese for the term 'perspective' and English for 'level'."
                "Since the suggestion involves the corrected code, make sure it is not influenced by Japanese or English."
                "Please do not include natural language content, always ensure the content is appropriate as a programming language."
                f"\n diff: {diff}",
            },
        ],
        model=AZURE_DEPLOY_MODEL,
        functions=functions,
        max_tokens=4096,
    )
    response = chat_completion.choices[0].message.function_call.arguments
    reviews = json.loads(response)["reviews"]
    github_comment(reviews=reviews)


def github_comment(reviews: list[dict]):
    request_body = {
        "body": "GPT review finish.",
        "event": "COMMENT" if reviews else "APPROVE",
        "comments": [],
    }
    if not reviews:
        request_body["body"] += "\n\n指摘事項はありませんでした。"
    for review in reviews:
        comment_body = f"**{review['perspective']}** 観点の **{review['level']}** レベルの指摘\n {review['review_comment']}"
        if fixed_code := review.get("fixed_code"):
            comment_body += f"\n\n```suggestion\n{fixed_code}\n```"
        comment = {
            "path": review["file_path"],
            "position": review["line_number"],
            "body": comment_body,
        }
        request_body["comments"].append(comment)
    with open("tmp.txt", "w") as f:
        f.writelines(json.dumps(request_body, ensure_ascii=False))
