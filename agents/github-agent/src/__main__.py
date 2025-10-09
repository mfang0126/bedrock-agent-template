"""GitHub Agent CLI - Entry point for command-line interface."""

import sys
from pathlib import Path
from typing import Optional

import typer

# Add parent directories to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from agents.github_agent.agent import run_agent_query

from common.config.config import Config
from tools.github import issues, repos

app = typer.Typer(
    name="github-agent",
    help="GitHub Agent CLI - Manage your GitHub repositories and issues",
    add_completion=False,
)


@app.command()
def invoke(
    prompt: str = typer.Argument(..., help="Your question or request"),
    session_id: Optional[str] = typer.Option(
        None, "--session-id", "-s", help="Session ID for conversation context"
    ),
):
    """
    Invoke the GitHub agent with a natural language prompt.

    Examples:
        github-agent invoke "list my repositories"
        github-agent invoke "create a new repository called test-project"
        github-agent invoke "show issues in my project"
    """
    config = Config(environment="local")

    typer.echo(f"🤖 GitHub Agent")
    typer.echo(f"{'─' * 50}")

    if config.is_mock_mode():
        typer.echo("⚠️  Running in MOCK MODE (no real API calls)")
        typer.echo(f"{'─' * 50}\n")

    # Run the query
    try:
        result = run_agent_query(prompt, mock_mode=config.is_mock_mode())
        typer.echo(result)
    except Exception as e:
        typer.echo(f"❌ Error: {e}", err=True)
        raise typer.Exit(code=1)


@app.command()
def auth():
    """
    Test GitHub OAuth Device Flow authentication.

    This command will guide you through the OAuth flow.
    In mock mode, it shows what the flow would look like.
    """
    config = Config(environment="local")

    typer.echo("🔐 GitHub OAuth Device Flow Authentication")
    typer.echo(f"{'─' * 50}")

    if config.is_mock_mode():
        typer.echo("\n⚠️  MOCK MODE - This is a simulation\n")
        typer.echo("In real mode, you would:")
        typer.echo("1. 📱 Receive a device code (e.g., 'ABCD-1234')")
        typer.echo("2. 🌐 Visit: https://github.com/login/device")
        typer.echo("3. ⌨️  Enter the code")
        typer.echo("4. ✅ Authorize the application")
        typer.echo("5. 🎉 Receive access token")
        typer.echo("\n" + "─" * 50)
        typer.echo("\nMock authentication successful! ✅")
        typer.echo("Token: mock_github_access_token_xxxxx")
    else:
        typer.echo("\n🚧 Real OAuth flow will be implemented in Phase 3")
        typer.echo("\nTo enable real OAuth, you need to:")
        typer.echo(
            "1. Create a GitHub OAuth App at: https://github.com/settings/developers"
        )
        typer.echo("2. Enable Device Flow authorization")
        typer.echo("3. Add GITHUB_CLIENT_ID and GITHUB_CLIENT_SECRET to .env")
        typer.echo("4. Set MOCK_MODE=false in .env")


@app.command(name="tools")
def tools_command(
    action: str = typer.Argument("list", help="Action: list, describe"),
    tool_name: Optional[str] = typer.Option(
        None, "--name", "-n", help="Specific tool name"
    ),
):
    """
    List and describe available GitHub tools.

    Examples:
        github-agent tools list
        github-agent tools describe --name list_github_repos
    """
    typer.echo("🔧 GitHub Agent Tools")
    typer.echo(f"{'─' * 50}\n")

    if action == "list":
        typer.echo("Repository Tools:")
        typer.echo("  📁 list_github_repos - List user's repositories")
        typer.echo("  ➕ create_github_repo - Create a new repository")
        typer.echo("  ℹ️  get_repo_info - Get detailed repository information")
        typer.echo("\nIssue Tools:")
        typer.echo("  📋 list_github_issues - List issues in a repository")
        typer.echo("  ➕ create_github_issue - Create a new issue")
        typer.echo("  ✅ close_github_issue - Close an existing issue")

    elif action == "describe":
        if not tool_name:
            typer.echo("❌ Error: --name required for describe action", err=True)
            raise typer.Exit(code=1)

        tool_descriptions = {
            "list_github_repos": "List all repositories for the authenticated user with stats",
            "create_github_repo": "Create a new GitHub repository with name, description, and visibility",
            "get_repo_info": "Get detailed information about a specific repository",
            "list_github_issues": "List issues in a repository (open, closed, or all)",
            "create_github_issue": "Create a new issue with title, body, and labels",
            "close_github_issue": "Close an existing issue by number",
        }

        if tool_name in tool_descriptions:
            typer.echo(f"Tool: {tool_name}")
            typer.echo(f"Description: {tool_descriptions[tool_name]}")
        else:
            typer.echo(f"❌ Tool '{tool_name}' not found", err=True)
            raise typer.Exit(code=1)


@app.command(name="config")
def show_config():
    """Show current configuration."""
    config = Config(environment="local")

    typer.echo("⚙️  Configuration")
    typer.echo(f"{'─' * 50}")
    typer.echo(f"Environment: {config.environment}")
    typer.echo(f"Mock Mode: {config.is_mock_mode()}")
    typer.echo(f"AWS Region: {config.get_aws_region()}")

    if config.is_mock_mode():
        typer.echo("\n💡 To use real GitHub API:")
        typer.echo("   1. Set MOCK_MODE=false in .env")
        typer.echo("   2. Add your GitHub OAuth credentials")
        typer.echo("   3. Run: github-agent auth")


if __name__ == "__main__":
    app()
