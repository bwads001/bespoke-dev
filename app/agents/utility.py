"""
Utility functions for AI agents.
"""
from typing import List
import ollama
from ollama import ChatResponse
import json
from rich.console import Console
from ..tools import ToolRegistry

console = Console()






async def get_summary(messages: List[dict]) -> str:
    """Get a summary of changes made"""
    messages.append({
        'role': 'user',
        'content': 'Review the conversation history and summarize what tasks have been completed and any that failed or need additional work. Be brief and specific.'
    })

    client = ollama.AsyncClient()

    summary_response = await client.chat(
        model="qwen2.5",
        messages=messages,
        options={
            'temperature': 0.6,
            'top_p': 0.8,
            'num_ctx': 16384,
        }
    )


    return summary_response.message.content 



def estimate_token_count(messages: List[dict], char_per_token: int = 4) -> int:
    """
    Estimate the total token count for the given conversation messages.
    
    Args:
        messages (List[dict]): List of conversation messages.
        char_per_token (int): Approximate number of characters per token (default is 4).
    
    Returns:
        int: Estimated token count.
    """
    total_chars = sum(len(message.get('content', '')) for message in messages)


    return total_chars // char_per_token


async def handle_tool_call(response: ChatResponse, development_conversation: List[dict]) -> List[dict]:
    """
    Handle a tool call by executing the tool and adding the result to the conversation.
    """
    for tool in response.message.tool_calls:
        if function_to_call := ToolRegistry.get_tool(tool.function.name):
            console.print(f"[cyan]Calling function: {tool.function.name}[/cyan]")
            args = (tool.function.arguments if isinstance(tool.function.arguments, dict)
                else json.loads(tool.function.arguments))
            try:
                result = function_to_call(**args)

                console.print(f"[green]Function result: {result}[/green]")
                
                # Add tool result to conversation
                development_conversation.append({'role': 'tool', 'content': str(result), 'name': tool.function.name})

            except Exception as e:
                error_msg = f'Error executing {tool.function.name}: {str(e)}'
                console.print(f"[red]{error_msg}[/red]")

                # Add error message to conversation
                development_conversation.append({'role': 'system', 'content': f'The previous tool call failed: {error_msg}. Please try a different approach.'})

    return development_conversation
