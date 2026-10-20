import json
import os

from dotenv import load_dotenv
from groq import Groq

from core.tools import TOOL_DECLARATIONS, execute_tool


load_dotenv()

api_key = os.getenv("GROQ_API_KEY")

if not api_key:
    raise ValueError(
        "GROQ_API_KEY was not found in the .env file."
    )


client = Groq(
    api_key=api_key
)


# =========================
# System instruction
# =========================

SYSTEM_INSTRUCTION = (
    "You are a fast desktop AI assistant. "
    "Be concise, direct, and conversational. "
    "For simple questions, answer in one short sentence. "
    "For normal questions, use 1-2 short sentences. "
    "Avoid unnecessary explanations, repetition, greetings, and filler. "
    "Only provide detailed answers when the user explicitly asks for detail. "
    "You have access to tools that can interact with the user's computer. "
    "Use tools whenever they are necessary to accurately fulfill the user's request. "
    "You may use multiple tools in sequence when necessary to complete a task. "
    "For example, if you need to find something before opening it, "
    "search for it first and then use the appropriate tool with the result."
)


# =========================
# Tool definitions
# =========================

tools = [
    {
        "type": "function",
        "function": {
            "name": tool["name"],
            "description": tool["description"],
            "parameters": tool["parameters"],
        },
    }
    for tool in TOOL_DECLARATIONS
]


# =========================
# AI response
# =========================

def get_response(history):

    messages = [
        {
            "role": "system",
            "content": SYSTEM_INSTRUCTION,
        }
    ]

    # Convert our internal history format
    # into Groq's message format.

    for message in history:

        role = message["role"]

        if role == "model":
            role = "assistant"

        text = message["parts"][0]["text"]

        messages.append({
            "role": role,
            "content": text,
        })


    # =========================
    # Tool execution loop
    # =========================

    max_tool_rounds = 5

    for _ in range(max_tool_rounds):

        response = client.chat.completions.create(
            model="openai/gpt-oss-120b",
            messages=messages,
            tools=tools,
            tool_choice="auto",
            temperature=1,
            max_completion_tokens=2048,
            top_p=1,
            reasoning_effort="medium",
        )

        assistant_message = response.choices[0].message


        # =========================
        # No more tools needed
        # =========================

        if not assistant_message.tool_calls:

            return (
                assistant_message.content
                or "I'm not sure how to respond to that."
            )


        # =========================
        # Add assistant tool request
        # =========================

        messages.append(
            assistant_message
        )


        # =========================
        # Execute requested tools
        # =========================

        for tool_call in assistant_message.tool_calls:

            tool_name = tool_call.function.name

            arguments_text = (
                tool_call.function.arguments
            )

            try:

                arguments = json.loads(
                    arguments_text
                )

            except json.JSONDecodeError:

                arguments = {}


            try:

                result = execute_tool(
                    tool_name,
                    arguments
                )

            except Exception as e:

                result = {
                    "success": False,
                    "error": str(e)
                }


            messages.append({
                "role": "tool",
                "tool_call_id": tool_call.id,
                "content": json.dumps(
                    result
                ),
            })


    # =========================
    # Safety fallback
    # =========================

    return (
        "I couldn't complete the task "
        "because it required too many steps."
    )