#!/usr/bin/env python3
"""Setup or update the GitHub OAuth credential provider for AgentCore."""

import argparse
import sys
from pathlib import Path

# Ensure shared modules are importable
sys.path.insert(0, str(Path(__file__).parent / "src"))

from common.auth.credential_provider import CredentialProviderManager
from common.config.config import Config

DEFAULT_PROVIDER_NAME = "github-provider"

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Create or update the GitHub OAuth credential provider"
    )
    parser.add_argument(
        "--environment",
        "-e",
        default="local",
        choices=("local", "production"),
        help="Configuration environment source (default: local)",
    )
    parser.add_argument(
        "--provider-name",
        default=DEFAULT_PROVIDER_NAME,
        help=f"Credential provider name (default: {DEFAULT_PROVIDER_NAME})",
    )
    parser.add_argument(
        "--region",
        help="AWS region override (defaults to value from configuration)",
    )
    parser.add_argument(
        "--update",
        action="store_true",
        help="Delete and recreate the provider if it already exists",
    )
    parser.add_argument(
        "--force",
        "-f",
        action="store_true",
        help="Skip interactive prompts (use with --update)",
    )
    return parser.parse_args()

def prompt_confirm(message: str, assume_yes: bool) -> bool:
    """Prompt the user for confirmation unless forcing."""
    if assume_yes:
        return True

    if not sys.stdin.isatty():
        return False

    try:
        response = input(f"{message} [y/N]: ").strip().lower()
    except EOFError:
        return False

    return response in {"y", "yes"}

def pretty_print_header(title: str) -> None:
    print("=" * 70)
    print(title)
    print("=" * 70)
    print()

def main() -> int:
    args = parse_args()
    provider_name = args.provider_name or DEFAULT_PROVIDER_NAME

    pretty_print_header("🔐 GitHub OAuth Credential Provider Setup")

    config = Config(environment=args.environment)

    try:
        credentials = config.get_github_credentials()
    except ValueError as exc:
        print(f"❌ Error: {exc}")
        print()
        print("📝 Setup instructions:")
        print("   1. Create a GitHub OAuth App at https://github.com/settings/developers")
        print("   2. Add credentials to your .env (or Secrets Manager if production):")
        print("      GITHUB_CLIENT_ID=your_client_id")
        print("      GITHUB_CLIENT_SECRET=your_client_secret")
        print("   3. Rerun this script")
        return 1

    client_id = credentials["client_id"]
    client_secret = credentials["client_secret"]
    region = args.region or config.get_aws_region()

    print("✅ GitHub OAuth credentials loaded")
    print(f"   Client ID: {client_id[:10]}...")
    print(f"   Region: {region}")
    print()

    manager = CredentialProviderManager(region=region)
    existing = manager.find_provider_by_name(provider_name)

    if existing:
        arn = existing.get("arn") or existing.get("credentialProviderArn")
        print(f"ℹ️  Provider '{provider_name}' already exists")
        if arn:
            print(f"   ARN: {arn}")
        print()

        if not args.update:
            print("Use --update to delete and recreate the provider or --force --update to skip prompts.")
            return 0

        if not prompt_confirm(
            f"Replace existing provider '{provider_name}'?",
            assume_yes=args.force,
        ):
            print("🚫 Update cancelled")
            return 1

    print("📡 Creating GitHub credential provider in AgentCore...")

    try:
        response = manager.create_or_replace_github_provider(
            name=provider_name,
            client_id=client_id,
            client_secret=client_secret,
            replace_existing=existing is not None,
        )
    except Exception as exc:  # noqa: BLE001
        print()
        pretty_print_header("❌ ERROR: Failed to create credential provider")
        print(f"Error: {exc}")
        print()
        print("💡 Common issues:")
        print("   - AWS credentials not configured")
        print("   - No Bedrock AgentCore access in your region")
        print("   - Credential provider with same name already exists (use --update)")
        print()
        print("🔧 To fix:")
        print("   - Run: aws configure")
        print("   - Ensure AgentCore is available in your region")
        print("   - Delete existing provider if needed")
        print()
        return 1

    print()
    pretty_print_header("✅ SUCCESS! GitHub credential provider ready")
    print(f"Provider ARN: {response['credentialProviderArn']}")
    print()
    print("📝 Next steps:")
    print("   1. Deploy your agent:")
    print("      agentcore configure -e src/agents/github_agent/runtime.py")
    print("      agentcore launch")
    print()
    print("   2. Test your agent:")
    print("      agentcore invoke '{\"prompt\": \"list my repositories\"}'")
    print()

    return 0

if __name__ == "__main__":
    sys.exit(main())
