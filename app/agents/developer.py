"""
Execution utilities for AI agents.
"""
from typing import List, Dict
import json
import asyncio
import ollama
from ollama import ChatResponse
from rich.console import Console
from ..tools import ToolRegistry
from .utility import get_summary, estimate_token_count, handle_tool_call
from .prompts.developer import DEVELOPER_SYSTEM_PROMPT

console = Console()



async def developer(
    backlog: List[List[Dict]],
    conversation: dict,
    max_retries: int = 3,
) -> List[str]:

    """
    Execute a step with retry logic if no tools are used.
    
    Args:
        backlog_json: List of steps to complete
        conversation: Conversation history
        max_retries: Maximum number of retry attempts (default 3)
        

    Returns:
        List[str]: Tool results

    """
    client = ollama.AsyncClient()    
    
    # Separate conversation for development
    development_conversation = conversation.copy()

    # Add the system prompt to the conversation
    development_conversation.append({'role': 'system', 'content': DEVELOPER_SYSTEM_PROMPT})


    for i, step in enumerate(backlog, 1):
        console.print(f"[bold cyan]Executing Step {i}/{len(backlog)}:[/bold cyan] {step}")

        development_conversation.append({
            'role': 'user', 
            'content': f"Complete this task: {json.dumps(step)}"
        })

        # Print an estimated token count from the conversation
        estimated_tokens = estimate_token_count(development_conversation)
        console.print(f"[orange]Estimated token count: {estimated_tokens} tokens[/orange]")

        attempt = 0

        try:
            while attempt < max_retries:
                try:
                    response: ChatResponse = await asyncio.wait_for(
                        client.chat(
                            model="qwen2.5-coder:14b",
                            messages=development_conversation,
                            tools=ToolRegistry.get_all_tools(),
                            options={
                                'temperature': 0 + (attempt * 0.1),  # Gradually increase temperature
                                'top_p': 0.1,
                            }
                        ),
                        timeout=60  # Optional: timeout to avoid hanging indefinitely
                    )
                except asyncio.TimeoutError:
                    console.print("[red]Timeout reached waiting for model response. Retrying...[/red]")
                    attempt += 1
                    development_conversation.append({
                        'role': 'system',
                        'content': 'Timeout occurred. Please try again with a shorter context.'
                    })
                    continue

                console.print(f"[dim]Response: {response.message.content}[/dim]")
                console.print(f"[dim]Tool Calls: {response.message.tool_calls}[/dim]")

                
                # Add the response to the conversation
                if response.message.content:
                    development_conversation.append(response.message)
                    

                # Handle tool calls if any
                if response.message.tool_calls:

                    development_conversation = await handle_tool_call(response, development_conversation)

                    # Only break the retry loop if there are tool calls and none of them is a 'read_file' call.
                    if response.message.tool_calls and not any(tool.function.name == "read_file" for tool in response.message.tool_calls):
                        break
                
                # No successful tool calls, prepare for retry
                attempt += 1
                if attempt < max_retries:
                    if response.message.tool_calls:
                        development_conversation.append({
                            'role': 'user',
                            'content': f'File contents have been included in the context. Use what you learned to complete the step or read another file. Step: {step["task_description"]}'
                        })
                    else:
                        development_conversation.append({
                            'role': 'user',
                            'content': f'The previous step requires file operations to complete. You must use tools to complete this step. Try to write or read files to complete the step. Step: {step["task_description"]}'
                        })
                    console.print(f"[yellow]Attempt {attempt}/{max_retries}: No successful tool usage. Retrying...[/yellow]")
                else:
                    console.print("[red]Error: Maximum retries reached without successful tool usage[/red]")
                    console.print("[red]Failed to complete step: No tools were used after maximum retries[/red]")
                    raise Exception("Maximum retries reached without successful tool usage")

        except Exception as e:
            console.print(f"[red]Error: {str(e)}[/red]")            

    



    return conversation, development_conversation