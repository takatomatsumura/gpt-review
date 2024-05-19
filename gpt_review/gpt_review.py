import os
import json
from openai import AzureOpenAI


def review():
    AZURE_OPENAI_API_KEY = os.getenv("AZURE_OPENAI_API_KEY")
    AZURE_API_BASE = os.getenv("AZURE_API_BASE")
    AZURE_API_VERSION = os.getenv("AZURE_API_VERSION")
    AZURE_DEPLOY_MODEL = os.getenv("AZURE_DEPLOY_MODEL")
    DIFF_FILE = os.getenv("DIFF_FILE", "diff.txt")

    client = AzureOpenAI(
        api_key=AZURE_OPENAI_API_KEY,
        api_version=AZURE_API_VERSION,
        azure_endpoint=AZURE_API_BASE,
        azure_deployment=AZURE_DEPLOY_MODEL,
        timeout=120,
    )

    with open(DIFF_FILE, "rb") as f:
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
                                    "description": "pointed out file path",
                                },
                                "line_number": {
                                    "type": "number",
                                    "description": "pointed out line number",
                                },
                                "perspective": {
                                    "type": "string",
                                    "description": "Select the perspective from which the code had an issue: 'パフォーマンス', 'セキュリティ', or '保守性'. Must be Japanese.",
                                },
                                "level": {
                                    "type": "string",
                                    "description": "Evaluate how critical the issue is on a scale. Please choose from the following six options: Critical, High, Medium, Low, Warning, Info. Note that the level decreases from Critical to Info. Must be English.",
                                },
                                "comment": {
                                    "type": "string",
                                    "description": "pointed out content",
                                },
                                "suggestion": {
                                    "type": "string",
                                    "description": "Only write the corrected code. Do not write review comments or points of issue here.",
                                },
                            },
                            "required": [
                                "file_path",
                                "line_number",
                                "perspective",
                                "level",
                                "comment",
                                "suggestion",
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
        comment_body = f"*{review['perspective']}* 観点の *{review['level']}* レベルの指摘\n {review['comment']}\n\n```suggestion\n{review['suggestion']}\n```"
        comment = {
            "path": review["file_path"],
            "position": review["line_number"],
            "body": comment_body,
        }
        request_body["comments"].append(comment)
    with open("tmp.txt", "w") as f:
        f.writelines(json.dumps(request_body, ensure_ascii=False))
