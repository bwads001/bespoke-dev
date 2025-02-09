import ollama
from pydantic import BaseModel
from .prompts.qa_prompt import QA_SYSTEM_PROMPT
from rich.console import Console

console = Console()

GREY = "\033[90m"
RESET = "\033[0m"


class QA_Response(BaseModel):
    response: str

    pass_qa: bool

# QA agent
async def qa_agent(development_conversation: list, task: str):



    client = ollama.AsyncClient()

    qa_conversation = development_conversation.copy()
    qa_conversation.append({'role': 'system', 'content': QA_SYSTEM_PROMPT})
    qa_conversation.append({'role': 'user', 'content': f"Was this task completed?: {task}"})
    development_conversation.append({'role': 'user', 'content': f"Was this task completed?: {task}"})

    console.print("[yellow]Sending task to QA agent...[/yellow]")

    # Send the task to the QA agent
    qa_response = ""
    async for chunk in client.chat(
        model="qwen2.5-coder:14b",
        messages=qa_conversation,
        format=QA_Response.model_json_schema(),
        options={'temperature': 0.3, 'num_ctx': 16384}
    ):
        qa_response += chunk.message.content
        print(f"{GREY}{chunk.message.content}{RESET}", end="", flush=True)


    

    development_conversation.append({'role': 'assistant', 'content': qa_response})

    return development_conversation, qa_response

        