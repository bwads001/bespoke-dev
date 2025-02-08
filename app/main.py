"""
Main CLI interface for the Bespoke Dev AI agent.
"""
import asyncio
import typer
from rich.console import Console
from .workflow import process_workflow
from .tools import ToolRegistry

app = typer.Typer()
console = Console()

@app.command()
def process(user_prompt: str):
    """Process a development task using the AI agent."""
    try:
        console.print(f"\n[bold blue]Starting Bespoke Dev AI[/bold blue]")
        console.print(f"[blue]User Prompt:[/blue] {user_prompt}")
        # console.print(f"[orange]{ToolRegistry.get_all_tools()}[/orange]")
        console.print("\n[blue]Initializing workflow...[/blue]")
        
        results, summary = asyncio.run(process_workflow(user_prompt))
        
        console.print("\n[dim green]Conversation:[/dim green]")
        for result in results:
            console.print(f"\n[bold cyan]Role:[/bold cyan] {result['role']}\n[bold green]Content:[/bold green] [dim]{result['content']}[/dim]")            


        console.print("\n[bold green]Summary:[/bold green]")
        console.print(f"\n[dim]{summary}[/dim]")



        return results
    except Exception as e:
        console.print(f"\n[bold red]Error occurred:[/bold red]")
        console.print(f"[red]{str(e)}[/red]")
        import traceback
        console.print(f"[dim red]{traceback.format_exc()}[/dim red]")
        raise typer.Exit(1)

def main():
    app()

if __name__ == '__main__':
    main() 