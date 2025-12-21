import requests
import argparse

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--token", required=True, help="Authentication token")
    args = parser.parse_args()

    # To get a token, log in to the application and copy the token from the browser's local storage
    headers = {"Authorization": f"Bearer {args.token}"}

    # Create a new conversation
    response = requests.post(
        "http://localhost:8001/api/conversations",
        json={"title": "Evaluation"},
        headers=headers,
    )
    conversation_id = response.json()["id"]

    questions = [
        "What is banding?",
        "How does cascade work?",
        "What happens when I cast a spell with storm?",
        "Can I counter a spell that can't be countered?",
    ]

    for question in questions:
        response = requests.post(
            f"http://localhost:8001/api/conversations/{conversation_id}/chat",
            json={"question": question},
            headers=headers,
        )
        data = response.json()
        print(f"Question: {question}")
        print(f"Answer: {data['content']}")
        print("-" * 20)

if __name__ == "__main__":
    main()

