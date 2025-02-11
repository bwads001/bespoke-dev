"""
Analysis utilities for AI agents.
"""
from typing import List, Dict, Tuple
import ollama
from ollama import ChatResponse
from pydantic import BaseModel, Field, RootModel
from rich.console import Console
from .prompts.backlog import BACKLOG_SYSTEM_PROMPT
from .prompts.analyst import ANALYST_SYSTEM_PROMPT



console = Console()

GREY = "\033[90m"
RESET = "\033[0m"
# Define the Task model
class Task(BaseModel):
    """Development backlog task with dependencies"""
    task_id: str = Field(..., description="Unique task identifier (e.g., SC-01, FE-01)")
    task_type: str = Field(..., enum=["scaffolding", "feature_implementation", "configuration", "documentation"])
    task_description: str = Field(..., description="Technical implementation details")
    task_notes: str = Field(..., description="Any additional notes about the task that are not covered by the task_description.")
    acceptance_criteria: List[str] = Field(..., description="Specific criteria for task completion")
    task_dependencies: List[str] = Field([], description="Task IDs this depends on")

# Define the Backlog model
class Backlog(RootModel):
    """Ordered list of development tasks"""
    root: List[Task] = Field(..., min_items=1)


# Define the Workflow model
async def analyze_task(task: str, workflow_conversation: List[Dict]) -> Tuple[List[Dict], Backlog]:
    """Use R1 to analyze and plan the task.
    
    Returns:
        Tuple[List[Dict], Backlog]: (Updated workflow conversation, Backlog of tasks)
    """
    # Create a client for the Analysis task    
    client = ollama.AsyncClient()

    console.print("\n[yellow]Creating analysis client...[/yellow]")

    # Add the user prompt to the workflow conversation
    workflow_conversation.append({'role':'user', 'content':f"Break down this coding task into logical implementation steps: {task}"})
    

    try:
        console.print("[yellow]Sending task to R1 for analysis...[/yellow]")

        # Generate application build plan
        analyst_response = ""
        async for chunk in await client.chat(
            model="phi4",
            messages=[
                {'role': 'system','content': ANALYST_SYSTEM_PROMPT},
                {'role':'user', 'content':f"Break down this coding task into logical implementation steps: {task}"}
            ],
            stream=True,
            options={'temperature': 0.3}
        ):
            analyst_response += chunk.message.content
            print(f"{GREY}{chunk.message.content}{RESET}", end="", flush=True)


        # Add the assistant response to the workflow conversation
        workflow_conversation.append({'role':'assistant', 'content':analyst_response})
        console.print("\n[green]Analysis complete![/green]")

        # Generate backlog
        console.print("\n[yellow]Generating task backlog...[/yellow]")
        backlog_response = await client.chat(
            model="qwen2.5-coder:14b-instruct-q4_K_M",
            messages=[
                {'role': 'system', 'content': BACKLOG_SYSTEM_PROMPT},
                {'role': 'user', 'content': f'''
                    Use this application build plan to generate all of the development tasks needed to build the application:
                    {analyst_response}
                    
                    Respond with JSON matching this schema: {Backlog.model_json_schema()}
                    Use exact field names and validate against dependencies
                '''}
            ],
            format=Backlog.model_json_schema(),
            options={'temperature': 0.3, 'top_k': 40, 'top_p': 0.2}
        )
        print(f"{GREY}{backlog_response.message.content}{RESET}", end="", flush=True)

        validated_backlog = Backlog.model_validate_json(backlog_response.message.content)
        console.print(f"\n[green]Received {len(validated_backlog.root)} tasks[/green]")

        return workflow_conversation, validated_backlog

    except Exception as e:
        console.print(f"\n[red]Error during processing: {str(e)}[/red]")
        if 'backlog_response' in locals():
            console.print(f"[dim]Partial response: {backlog_response}[/dim]")
        raise 