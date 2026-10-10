
import os
import json
import re

from dotenv import load_dotenv
from langchain_nvidia_ai_endpoints import ChatNVIDIA
from langchain_core.prompts import ChatPromptTemplate


# Load API key
load_dotenv()

API_KEY = os.getenv("NVIDIA_API_KEY")

if not API_KEY:
    raise ValueError(
        "NVIDIA_API_KEY not found. Check your .env file."
    )


# Initialize NVIDIA Nemotron
llm = ChatNVIDIA(
    model="nvidia/nemotron-3.5-lightning-30b-a3b",
    nvidia_api_key=API_KEY,
    temperature=0,
    max_completion_tokens=1000,
)


prompt = ChatPromptTemplate.from_messages([
    (
        "system",
        """
You interpret navigation commands for a robot simulator.

Grid:
- Rows: 0 to 14
- Columns: 0 to 19
- Default goal: row 12, column 18

Convert the user's instruction into exactly one JSON object.

For a valid navigation command, use:
{{
  "valid": true,
  "action": "navigate",
  "goal_row": 8,
  "goal_col": 4,
  "message": "Navigation command understood."
}}

Replace the example coordinates with the requested destination.

If the user says "go to the goal", use row 12, column 18.

For unclear or unsupported commands, use:
{{
  "valid": false,
  "action": "none",
  "goal_row": null,
  "goal_col": null,
  "message": "Please provide a valid navigation destination."
}}

Never invent coordinates.
Reject coordinates outside the grid.
Return JSON only. Do not use Markdown fences.
"""
    ),
    ("human", "{user_command}"),
])

chain = prompt | llm



def parse_json_response(content):
    """Extract the JSON object from a Nemotron response."""

    if isinstance(content, list):
        parts = []

        for block in content:
            if isinstance(block, str):
                parts.append(block)
            elif isinstance(block, dict) and block.get("text"):
                parts.append(block["text"])

        content = "\n".join(parts)

    if not isinstance(content, str) or not content.strip():
        raise ValueError("The model returned empty content.")

    content = content.strip()

    # Remove optional Markdown code fences.
    content = re.sub(
        r"```(?:json)?\s*",
        "",
        content,
        flags=re.IGNORECASE
    )
    content = content.replace("```", "")

    # Find the first JSON object and handle nested braces.
    start = content.find("{")

    if start == -1:
        raise ValueError(
            f"No JSON object found: {content[:300]!r}"
        )

    decoder = json.JSONDecoder()

    try:
        result, _ = decoder.raw_decode(content[start:])
    except json.JSONDecodeError as error:
        raise ValueError(
            f"Could not parse JSON: {content[start:start + 300]!r}"
        ) from error

    if not isinstance(result, dict):
        raise ValueError("Expected a JSON object.")

    return result


def interpret_command(user_command):
    """Interpret and validate a natural-language command."""

    if not isinstance(user_command, str) or not user_command.strip():
        return {
            "valid": False,
            "action": "none",
            "goal_row": None,
            "goal_col": None,
            "message": "Please enter a command."
        }

    try:
        response = chain.invoke({
            "user_command": user_command.strip()
        })

        # Helpful diagnostic output
        print("\nRaw Nemotron response:")
        print(repr(response.content))

        result = parse_json_response(response.content)

        if not isinstance(result, dict):
            raise ValueError("Response must be a JSON object.")

        if result.get("valid") is not True:
            return {
                "valid": False,
                "action": "none",
                "goal_row": None,
                "goal_col": None,
                "message": str(result.get(
                    "message",
                    "Invalid navigation command."
                ))
            }

        if result.get("action") != "navigate":
            raise ValueError("Unsupported action.")

        row = result.get("goal_row")
        col = result.get("goal_col")

        # Reject booleans as well as non-integer coordinates.
        if (
            isinstance(row, bool)
            or not isinstance(row, int)
            or isinstance(col, bool)
            or not isinstance(col, int)
        ):
            raise ValueError("Coordinates must be integers.")

        if not (0 <= row < 15 and 0 <= col < 20):
            raise ValueError("Destination is outside the grid.")

        return {
            "valid": True,
            "action": "navigate",
            "goal_row": row,
            "goal_col": col,
            "message": str(result.get(
                "message",
                "Navigation command understood."
            ))
        }

    except Exception as error:
        print("Command interpretation error:", error)

        return {
            "valid": False,
            "action": "none",
            "goal_row": None,
            "goal_col": None,
            "message": "Could not interpret the command. Check terminal."
        }


if __name__ == "__main__":
    print("Robot Navigation Command Interpreter")
    print("Type 'quit' to exit.\n")

    while True:
        command = input("Robot command: ")

        if command.strip().lower() == "quit":
            break

        result = interpret_command(command)
        print(json.dumps(result, indent=4))
