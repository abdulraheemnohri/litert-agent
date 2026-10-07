"""Example: inspect pending approvals.

Usage:
    python examples/approvals_demo.py
"""

from litert_agent.security.policy import list_pending

def main() -> None:
    pending = list_pending()
    if not pending:
        print("No pending approvals.")
        return
    for request in pending:
        print(request)
        print("decide with: litert-agent security decide <id> --allow once|session")
        print("           or: litert-agent security decide <id> --deny")


if __name__ == "__main__":
    main()
