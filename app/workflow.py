"""
Core workflow management.
"""

from typing import List
from rich.console import Console
from .tools import OUTPUT_DIR
from .agents import developer, analyze_task, get_summary

# Configuration
MAX_STEPS = 25  # Maximum number of steps to execute

console = Console()


# Create output directory if it doesn't exist
OUTPUT_DIR.mkdir(exist_ok=True)

async def process_workflow(task: str) -> List[str]:
    """Process a task through the complete workflow."""
    try:
        # Analysis Phase
        console.print("\n[bold blue]Analysis Phase[/bold blue]")

        # Initialize conversation
        workflow_conversation = []

        # Send task to analyst agent
        workflow_conversation, validated_backlog = await analyze_task( task, workflow_conversation)

        backlog_list = validated_backlog.root  # List[Task]
        serialized_backlog = [task.model_dump() for task in backlog_list]

        
        console.print("\n[bold green]Generated Plan:[/bold green]")
        for i, step in enumerate(backlog_list, 1):
            console.print(f"{i}. {step}\n")        


        # Execution Phase
        console.print("\n[bold blue]Execution Phase[/bold blue]")     

        # Send steps to developer agent
        workflow_conversation, development_conversation = await developer(serialized_backlog, workflow_conversation, 3)

        console.print(f"[bold green]Development conversation:[/bold green]")

        for result in development_conversation:
            console.print(f"[bold cyan]Role:[/bold cyan] {result['role']}\n[bold green]Content:[/bold green] [dim]{result['content']}[/dim]")


        # Get the summary of the development conversation
        development_summary = await get_summary(development_conversation)
        workflow_conversation.append({'role': 'assistant', 'content': development_summary})


        
        return workflow_conversation, development_summary
        
    except Exception as e:
        console.print(f"[bold red]Error in workflow:[/bold red] {str(e)}")

        raise 