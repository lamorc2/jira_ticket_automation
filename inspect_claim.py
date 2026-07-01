import sys

from ClaimTicketStore import ClaimTicketStore


def main() -> None:
    if len(sys.argv) != 2:
        print("Usage: python3 inspect_claim.py CST-123")
        return

    issue_key = sys.argv[1]
    store = ClaimTicketStore()
    claim = store.get_claim(issue_key)

    if claim is None:
        print(f"No claim found for {issue_key}")
        return

    print(claim)


if __name__ == "__main__":
    main()