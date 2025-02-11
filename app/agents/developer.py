"""
Execution utilities for AI agents.
"""
from typing import List, Dict
import json
import asyncio
import ollama
from ollama import ChatResponse
from rich.console import Console
from ..tools import ToolRegistry, list_directory
from .utility import estimate_token_count, handle_tool_call
from .prompts.developer import DEVELOPER_SYSTEM_PROMPT
from .qa_agent import qa_agent
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
    
    # Initialize the development conversation
    development_conversation = []
    development_conversation.append({'role': 'system', 'content': 'Conversation history: ' + json.dumps(conversation)})
    development_conversation.append({'role': 'system', 'content': DEVELOPER_SYSTEM_PROMPT})

    # Begin the backlogdevelopment loop
    for i, step in enumerate(backlog, 1):
        console.print(f"[bold cyan]\nImplementing Backlog Step {i}/{len(backlog)}:[/bold cyan] {step}")


        development_conversation.append({'role': 'system', 'content': f"This is the working directory listing currently:\n {list_directory('./')}"})
        development_conversation.append({'role': 'user','content': f"Complete this task: {json.dumps(step)}"})

        # Print an estimated token count from the conversation
        estimated_tokens = estimate_token_count(development_conversation)
        console.print(f"[bold]Estimated token count: {estimated_tokens} tokens[/bold]")

        # Initialize the retry counter  
        attempt = 0

        # Begin the task development retry loop
        try:
            while attempt < max_retries:
                try:
                    # Use tools to complete the step
                    dev1_response: ChatResponse = await asyncio.wait_for(
                        client.chat(
                            model="qwen2.5-coder:14b-instruct-q4_K_M",
                            messages=development_conversation,
                            tools=ToolRegistry.get_all_tools(),
                            options={
                                'temperature': 0 + (attempt * 0.1),  # Gradually increase temperature
                                'top_p': 0.1,
                                'num_ctx': 16384,
                                'num_threads': 16,
                            }
                        ),
                        timeout=240  # Optional: timeout to avoid hanging indefinitely
                    )
                except asyncio.TimeoutError:
                    console.print("[red]Timeout reached waiting for model response. Retrying...[/red]")
                    attempt += 1
                    development_conversation.append({
                        'role': 'system',
                        'content': 'Timeout occurred. Please try again with a shorter context.'
                    })
                    continue

                # Print the response and tool calls
                console.print(f"[dim]Response: {dev1_response.message.content}[/dim]")
                console.print(f"[dim]Tool Calls: {dev1_response.message.tool_calls}[/dim]")
                
                # Add the response to the conversation if there is one
                if dev1_response.message.content:
                    development_conversation.append(dev1_response.message)                    

                # Check if there are tool calls
                if dev1_response.message.tool_calls:
                    # Handle the tool calls and update the conversation
                    development_conversation = await handle_tool_call(dev1_response, development_conversation)



                try:
                    # Send the response to the model
                    dev2_response: ChatResponse = await asyncio.wait_for(
                        client.chat(
                            model="qwen2.5-coder:14b-instruct-q4_K_M",
                            messages=development_conversation,
                            tools=ToolRegistry.get_all_tools(),
                            options={
                                'temperature': 0 + (attempt * 0.1),  # Gradually increase temperature
                                'top_p': 0.1 + (attempt * 0.1),
                                'top_k': 30 + (attempt * 5),
                                'num_ctx': 16384,
                                'num_threads': 16,
                            }
                        ),
                        timeout=240
                    )
                except asyncio.TimeoutError:
                    console.print("[red]Timeout reached waiting for model response. Retrying...[/red]")
                    attempt += 1
                    development_conversation.append({
                        'role': 'system',
                        'content': 'Timeout occurred. Please try again with a shorter context.'
                    })
                    continue

                # Print the response and tool calls
                console.print(f"[dim]Response: {dev2_response.message.content}[/dim]")
                console.print(f"[dim]Tool Calls: {dev2_response.message.tool_calls}[/dim]")

                # Add the response to the conversation if there is one
                if dev2_response.message.content:
                    development_conversation.append(dev2_response.message)  

                # Check if there are tool calls
                if dev2_response.message.tool_calls:
                    # Handle the tool calls and update the conversation
                    development_conversation = await handle_tool_call(dev2_response, development_conversation)


                # Send the response to the QA agent
                development_conversation, qa_response = await qa_agent(development_conversation, step["task_description"])
                console.print(f"[dim]QA Response: {qa_response.message.content}[/dim]")


                # Only break the retry loop if the QA response is "pass"
                if qa_response["pass_qa"]:
                    # Reset the attempt counter
                    attempt = 0
                    break

                # No successful tool calls, prepare for retry
                attempt += 1
                if attempt < max_retries:
 
                    console.print(f"[yellow]Attempt {attempt}/{max_retries}: QA failed. Retrying...[/yellow]")
                else:
                    console.print("[red]Error: Maximum retries reached without passing QA[/red]")
                    development_conversation.append({'role': 'assistant', 'content': f"Unable to complete task: {step['task_description']} failed to pass QA and exceeded the maximum number of retries. This step may require manual completion."})
                    raise Exception("Maximum retries reached without passing QA")

        except Exception as e:
            console.print(f"[red]Error: {str(e)}[/red]")            

    



    return conversation, development_conversation