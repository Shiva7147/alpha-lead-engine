"""Interactive CLI Terminal for Alpha Lead Engine with Rich visual dashboards.
"""

from __future__ import annotations

import asyncio
import os
import sys
from typing import Optional

from rich.console import Console
from rich.panel import Panel
from rich.progress import BarColumn, Progress, SpinnerColumn, TextColumn
from rich.prompt import Confirm, Prompt
from rich.table import Table

from alpha_lead_engine.auditor.schemas import LeadStatus
from alpha_lead_engine.automation.gmail_oauth import GmailOAuthManager
from alpha_lead_engine.engine import AlphaLeadEngine

console = Console()


def print_banner():
    banner_text = """[bold cyan]
    █████╗ ██╗     ██████╗ ██╗  ██╗ █████╗ 
   ██╔══██╗██║     ██╔══██╗██║  ██║██╔══██╗
   ███████║██║     ██████╔╝███████║███████║
   ██╔══██║██║     ██╔═══╝ ██╔══██║██╔══██║
   ██║  ██║███████╗██║     ██║  ██║██║  ██║
   ╚═╝  ╚═╝╚══════╝╚═╝     ╚═╝  ╚═╝╚═╝  ╚═╝
         [bold white]LEAD ENGINE[/bold white] [bold green]v1.0.0[/bold green]
    [dim]Autonomous AI Lead Discovery & Factual Outreach Framework[/dim]
[/bold cyan]"""
    console.print(banner_text)


def cmd_init():
    """Initializes Google OAuth credentials."""
    print_banner()
    console.print(Panel("[bold yellow]Google OAuth 2.0 Setup[/bold yellow]", border_style="cyan"))

    oauth = GmailOAuthManager()
    if not oauth.has_credentials:
        console.print("[red]❌ 'credentials.json' not found in working directory.[/red]")
        console.print("[dim]1. Create a project in Google Cloud Console.\n2. Enable Gmail API.\n3. Create OAuth 2.0 Client ID (Desktop Application).\n4. Download as 'credentials.json' and place here.[/dim]\n")
        return

    console.print("[cyan]Found 'credentials.json'. Launching browser authorization...[/cyan]")
    success = oauth.authenticate()
    if success:
        console.print("[bold green]✔ Successfully authenticated and generated token.json![/bold green]")
    else:
        console.print("[red]❌ OAuth authentication failed or was cancelled.[/red]")


def cmd_status():
    """Displays real-time pipeline status and lead table."""
    print_banner()
    engine = AlphaLeadEngine()
    metrics = engine.get_metrics()

    stats_table = Table(title="[bold cyan]Pipeline Metrics[/bold cyan]", show_header=True, header_style="bold magenta")
    stats_table.add_column("Discovered", justify="center")
    stats_table.add_column("MX Verified", justify="center")
    stats_table.add_column("AI Audited", justify="center")
    stats_table.add_column("Sent", justify="center")
    stats_table.add_column("Follow-ups", justify="center")
    stats_table.add_column("Human Review 🚨", justify="center", style="bold yellow")
    stats_table.add_column("Replies 💰", justify="center", style="bold green")

    stats_table.add_row(
        str(metrics.total_discovered),
        str(metrics.total_mx_verified),
        str(metrics.total_audited),
        str(metrics.total_sent),
        str(metrics.total_followups_sent),
        str(metrics.total_pending_human_review),
        str(metrics.total_replies),
    )
    console.print(stats_table)
    console.print()

    # Show leads
    leads = engine.store.list_leads(limit=15)
    if leads:
        lead_table = Table(title="Recent Targets", show_header=True, header_style="bold blue")
        lead_table.add_column("Company", style="bold white")
        lead_table.add_column("Email", style="dim")
        lead_table.add_column("Score", justify="center")
        lead_table.add_column("Tier", justify="center")
        lead_table.add_column("Status", justify="center")

        for l in leads:
            score_str = str(l.audit.score) if l.audit else "N/A"
            tier_str = l.audit.fit_tier.value if l.audit else "N/A"
            status_style = "green" if l.status == LeadStatus.SENT else ("yellow" if l.status == LeadStatus.NEEDS_HUMAN_REVIEW else "white")

            lead_table.add_row(
                l.raw.business_name[:25],
                (l.raw.email or "N/A")[:28],
                score_str,
                tier_str,
                f"[{status_style}]{l.status.value}[/{status_style}]"
            )
        console.print(lead_table)


def cmd_review():
    """Interactive human review terminal for flagged leads."""
    print_banner()
    engine = AlphaLeadEngine()
    flagged = engine.store.list_leads(status=LeadStatus.NEEDS_HUMAN_REVIEW)

    if not flagged:
        console.print("[green]✔ No leads currently waiting for human review.[/green]")
        return

    console.print(f"[bold yellow]Found {len(flagged)} lead(s) requiring human escalation review.[/bold yellow]\n")

    for idx, lead in enumerate(flagged):
        console.print(Panel(
            f"[bold cyan]Company:[/bold cyan] {lead.raw.business_name}\n"
            f"[bold cyan]Website:[/bold cyan] {lead.raw.website}\n"
            f"[bold cyan]Email:[/bold cyan] {lead.raw.email} (MX Valid: {lead.mx_valid})\n"
            f"[bold cyan]Audit Score:[/bold cyan] {lead.audit.score if lead.audit else 'N/A'}/100\n"
            f"[bold cyan]Reasoning:[/bold cyan] {lead.audit.reasoning if lead.audit else 'N/A'}\n"
            f"[bold cyan]Proposed Subject:[/bold cyan] {lead.email_draft.subject if lead.email_draft else 'N/A'}\n\n"
            f"[bold white]Draft Email:[/bold white]\n{lead.email_draft.initial_email if lead.email_draft else ''}",
            title=f"Review [{idx+1}/{len(flagged)}] - {lead.raw.business_name}",
            border_style="yellow"
        ))

        action = Prompt.ask("Choose action", choices=["approve", "skip", "reject"], default="approve")
        if action == "approve":
            engine.approve_lead_for_sending(lead.id)
            console.print(f"[bold green]✔ Approved '{lead.raw.business_name}' and queued for sending![/bold green]\n")
        elif action == "reject":
            engine.store.update_status(lead.id, LeadStatus.SUPPRESSED)
            console.print(f"[red]✖ Rejected and suppressed '{lead.raw.business_name}'.[/red]\n")
        else:
            console.print("[dim]Skipped for later review.[/dim]\n")


def cmd_run():
    """Interactive discovery and auditing execution."""
    print_banner()
    console.print(Panel("[bold green]Start Autonomous Discovery & Outreach[/bold green]", border_style="cyan"))

    b_name = Prompt.ask("[bold cyan]Enter your business/product name[/bold cyan]", default="Alpha Solutions")
    b_offer = Prompt.ask("[bold cyan]Describe what you offer in 1-2 sentences[/bold cyan]", default="Autonomous B2B lead generation & custom AI pipeline development")
    keywords = Prompt.ask("[bold cyan]Enter target niche / search keywords[/bold cyan]", default="B2B marketing agencies")
    location = Prompt.ask("[bold cyan]Enter target location[/bold cyan]", default="Austin, TX")
    limit = int(Prompt.ask("[bold cyan]Target lead discovery count[/bold cyan]", default="5"))
    visible_browser = Confirm.ask("[bold yellow]Run browser visibly so you can watch it crawl?[/bold yellow]", default=False)
    dry_run = Confirm.ask("[bold yellow]Run in Safe Simulation Mode (dry-run email sending)?[/bold yellow]", default=True)

    engine = AlphaLeadEngine(
        headless=not visible_browser,
        dry_run=dry_run,
        require_human_approval_to_send=True
    )

    console.print(f"\n[cyan]Starting multi-crawler pipeline...[/cyan]")
    if visible_browser:
        console.print("[bold green]Chromium browser window launching in visible mode...[/bold green]")

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        console=console,
    ) as progress:
        task = progress.add_task("[cyan]Crawling & Auditing...", total=limit)

        def on_prog(msg: str, curr: int, tot: int):
            progress.update(task, description=f"[cyan]{msg}[/cyan]", completed=curr, total=tot)

        results = asyncio.run(engine.execute_discovery_and_audit(
            business_name=b_name,
            business_offering=b_offer,
            icp_keywords=keywords,
            location=location,
            limit=limit,
            progress_callback=on_prog,
        ))

    console.print(f"\n[bold green]✔ Discovery and line-by-line audit complete! Found {len(results)} targets.[/bold green]\n")
    cmd_status()
    console.print("\n[dim]Run 'python -m alpha_lead_engine review' to inspect or approve email drafts.[/dim]")


def main():
    args = sys.argv[1:]
    if not args or args[0] in ("run", "start"):
        cmd_run()
    elif args[0] == "init":
        cmd_init()
    elif args[0] == "status":
        cmd_status()
    elif args[0] == "review":
        cmd_review()
    elif args[0] in ("-h", "--help", "help"):
        print_banner()
        console.print("""
[bold]Usage:[/bold]
  python -m alpha_lead_engine [run]      Interactive lead discovery, line-by-line audit & setup
  python -m alpha_lead_engine status     Display pipeline metrics and recent target status
  python -m alpha_lead_engine review     Human escalation checkpoint - approve/reject drafted emails
  python -m alpha_lead_engine init       Authorize Gmail API OAuth 2.0 flow
""")
    else:
        cmd_run()


if __name__ == "__main__":
    main()
