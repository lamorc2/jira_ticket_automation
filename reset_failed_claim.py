import sys

from ClaimTicketStore import ClaimTicketStore


def main() -> None:
    if len(sys.argv) != 2:
        print("Usage: python3 reset_failed_claim.py CST-123")
        return

    issue_key = sys.argv[1]
    store = ClaimTicketStore()

    if store.reset_failed_claim(issue_key):
        print(f"Reset failed claim for {issue_key}")
    else:
        print(f"No failed claim to reset for {issue_key}")


if __name__ == "__main__":
    main()