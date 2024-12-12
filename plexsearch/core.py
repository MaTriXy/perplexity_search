import sys
import signal
from typing import Optional, List, Dict
from rich.console import Console
from rich.live import Live
from rich.spinner import Spinner
from plexsearch import __version__
from plexsearch.update_checker import UpdateChecker
from plexsearch.api import PerplexityAPI
from plexsearch.config import Config
from plexsearch.context import ConversationContext


console = Console()


def get_terminal_size() -> tuple[int, int]:
    """Get the dimensions of the terminal."""
    try:
        import shutil
        height, width = shutil.get_terminal_size()
        return height, width
    except Exception:
        # Fallback to default dimensions if shutil fails
        return 24, 80

def clear_new_area() -> None:
    """Clear screen while preserving scrollback buffer."""
    console.print("[cyan]Clearing screen...[/cyan]")
    # Print newlines to push content up
    height, _ = get_terminal_size()
    console.print("\n" * height)
    # Use Rich's clear which preserves scrollback
    console.clear()

def handle_no_stream_search(query: str, args, payload: dict) -> str:
    """Handle non-streaming search mode."""
    console.print("[cyan]About to clear screen in no_stream mode...[/cyan]")
    clear_new_area()
    spinner_text = "Searching..."
    buffer = []
    
    with Live(Spinner("dots", text=spinner_text), refresh_per_second=10, transient=True):
        for chunk in perform_search(query=query, api_key=args.api_key,
                                  model=args.model, stream=False,
                                  show_citations=args.citations,
                                  context=payload.get("messages")):
            buffer.append(chunk)
    
    content = "".join(buffer)
    console.print(f"Perplexity: {content}")
    return content

def handle_streaming_search(query: str, args, payload: dict) -> str:
    """Handle streaming search mode."""
    accumulated_text = ""
    with Live("", refresh_per_second=10, transient=False) as live:
        for chunk in perform_search(query=query, api_key=args.api_key,
                                  model=args.model, stream=True,
                                  show_citations=args.citations,
                                  context=payload.get("messages")):
            accumulated_text += chunk
            live.update(f"Perplexity: {accumulated_text}")
    return accumulated_text

def handle_search(query: str, args, context=None) -> str:
    """Handle a single search query execution."""
    no_stream = args.no_stream or os.environ.get("OR_APP_NAME") == "Aider"
    payload = _build_api_payload(query=query, model=args.model,
                               stream=not no_stream, show_citations=args.citations)
    if context:
        payload["messages"] = context

    if no_stream:
        return handle_no_stream_search(query, args, payload)
    else:
        return handle_streaming_search(query, args, payload)

def handle_interactive_mode(args, context=None):
    """Handle interactive mode search session."""
    if context is None:
        context = []
    console.print("[green]Entering interactive mode. Type your queries below. Type 'exit' to quit.[/green]")
    
    while True:
        user_input = console.input("\n[cyan]> [/cyan]")
        if user_input.strip() == "":
            console.print("[yellow]Please enter a query or type 'exit' to quit.[/yellow]")
            continue
        if user_input.lower() == "exit":
            console.print("[yellow]Exiting interactive mode.[/yellow]")
            break

        clear_new_area()
        context.append({"role": "user", "content": user_input})
        try:
            content = handle_search(user_input, args, context)
            context.append({"role": "assistant", "content": content})
        except Exception as e:
            console.print(f"[red]Error:[/red] {e}")
            print(f"[red]Error:[/red] {e}", file=sys.stderr)

def setup_signal_handler():
    """Set up interrupt signal handler."""
    def handle_interrupt(signum, frame):
        console.print("\n[yellow]Search interrupted by user[/yellow]")
        sys.exit(0)
    
    signal.signal(signal.SIGINT, handle_interrupt)

def main():
    """CLI entry point"""
    try:
        args = parse_arguments()
        setup_signal_handler()
    
        # Check for updates
        checker = UpdateChecker("plexsearch", __version__)
        if latest_version := checker.check_and_notify():
            console.print(f"\n[yellow]New version {latest_version} available![/yellow]\n")
            response = input("Would you like to update now? (Y/n): ").strip().lower()
            if not response or response in ['y', 'yes']:
                try:
                    if checker.update_package():
                        console.print("[green]Successfully updated to the new version! The new version will be used on next execution.[/green]")
                    else:
                        console.print("[red]Update failed. Please try updating manually with: pip install --upgrade plexsearch[/red]")
                except Exception as e:
                    console.print(f"[red]Update failed: {str(e)}[/red]")
                console.print()

        query = " ".join(args.query) if args.query else None
        
        if query is None:
            handle_interactive_mode(args)
        else:
            clear_new_area()
            handle_search(query, args)
            
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        print(f"[red]Error:[/red] {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
