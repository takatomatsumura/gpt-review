from dotenv import load_dotenv
from gpt_review.gpt_review import review


def main():
    load_dotenv()

    review()


if __name__ == "__main__":
    main()
