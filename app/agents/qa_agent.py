import ollama
from pydantic import BaseModel
from .prompts.qa_prompt import QA_SYSTEM_PROMPT
from rich.console import Console
from typing import Tuple

console = Console()

GREY = "\033[90m"
RESET = "\033[0m"


class QA_Response(BaseModel):
    response: str
    pass_qa: bool

# QA agent
async def qa_agent(development_conversation: list, task: str) -> Tuple[list, QA_Response]:



    client = ollama.AsyncClient()

    qa_conversation = development_conversation.copy()
    qa_conversation.append({'role': 'system', 'content': QA_SYSTEM_PROMPT})
    qa_conversation.append({'role': 'user', 'content': f"Was this task completed?: {task}"})
    development_conversation.append({'role': 'user', 'content': f"Was this task completed?: {task}"})

    console.print("[yellow]Sending task to QA agent...[/yellow]")

    # Send the task to the QA agent
    qa_response = await client.chat(
        model="qwen2.5-coder:14b-instruct-q4_K_M",
        messages=qa_conversation,
        format=QA_Response.model_json_schema(),
        options={'temperature': 0.3, 'num_ctx': 16384}
    )
    print(f"{GREY}QA Response:{qa_response}{RESET}")
    validated_qa_response = QA_Response.model_validate_json(qa_response.message.content)
    print(f"{GREY}QA Response:{qa_response.message.content}{RESET}")


    if validated_qa_response.pass_qa:
        development_conversation.append({'role': 'assistant', 'content': f"QA PASSED"})
    else:
        development_conversation.append({'role': 'assistant', 'content': f"QA FAILED: {validated_qa_response.response}"})

    return development_conversation, validated_qa_response

        