from mcp.server.fastmcp import FastMCP
from mcp.server.fastmcp.exceptions import ToolError
import roboco_core

inst = """
    You help users getting started on a robot in Monash Robotics Lab. 
    
    Ultimately,you will give them 2 docker-compose.yaml one for running sim 
    and one for running on real robot. Of course, at the end, you will also 
    provide steps to make this work.

    Always follow this workflow IN ORDER. Never skip or reorder steps:
    1. Ask the user what experiment they have in mind. Please do not show what robot is available at this step.
    2. Call get_available_robots() and recommend relevant robots for this experiment. Then let the user choose which robot they want. Please PROMPT MULTIPLE CHOICE.
    3. Once they choose, call get_robot_services() and describe how each service might be useful for their experiment. Then let the user choose which service they want.
    4. Once they choose, call get_robot_hardware() and recommend relevant hardwares for this experiment. Then let the user choose which hardware they want to add. Always include a "No additional hardware" option — hardware is optional and the user may not need any.
    5. Finally, once you have all the necessary information, call generate_setup() to produce two docker-compose.yaml files and guide setup. If the user chose no hardware, pass an empty list for hardware_keys.
    
    Do NOT call get_available_robots() until the user has described their experiment.
    Do NOT call multiple tools in one answer, please go tool by tool depending on user's answer and questions.
    Do NOT list robots, services, or hardware from memory - always use the tools.

    INTERACTION RULES - ALWAYS FOLLOW:
    - ALWAYS present choices as clickable multiple choice options using the ask_user_input tool.
    - NEVER list options as plain text bullets or letters (A, B, C) when asking the user to choose.
    - NEVER shows the description in the multiple choice box, only the name.
    - Every time the user must make a selection (robot, service, hardware), you MUST call ask_user_input with the options before proceeding.
    """

# Initialize FastMCP server
mcp = FastMCP("Roboco", instructions=inst, host="0.0.0.0", port=8000)

@mcp.prompt()
async def test_prompt(name: str) -> str:
    """Just a function to test MCP prompt"""
    return f"Hi there {name}!"

@mcp.tool()
async def start_session() -> dict:
    """
    ALWAYS call this tool first when the user wants to start or greet Roboco.
    Returns the opening question to ask the user. Please do not show the user the instructions
    """
    return {
        "message": "Welcome to the Monash Robotics Lab! What experiment do you have in mind? Please describe what you're trying to do, and I'll help you find the right robot and configuration.",
        "instructions": inst,
    }

@mcp.tool()
async def get_available_robots() -> dict:
    """Return a list of all available robots."""
    return {
        "robots": roboco_core.get_available_robots(),
        "instructions": "If you haven't called start_session tool in this chat session, please do that first.",
    }

@mcp.tool()
async def get_robot_hardware(robot_key: str) -> dict:
    """Return the hardware options available for a specific robot."""
    try:
        return {"hardware": roboco_core.get_robot_hardware(robot_key)}
    except KeyError as exc:
        raise ToolError(str(exc))

@mcp.tool()
async def get_robot_services(robot_key: str) -> dict:
    """Return the software services available for a specific robot."""
    try:
        return {"services": roboco_core.get_robot_services(robot_key)}
    except KeyError as exc:
        raise ToolError(str(exc))

@mcp.tool()
async def generate_setup(robot_key: str, service_key: str, hardware_keys: list[str]) -> dict:
    try:
        result = roboco_core.generate_setup(robot_key, service_key, hardware_keys)
    except (KeyError, ValueError) as exc:
        raise ToolError(str(exc))

    return {
        "status": "success",
        "configuration_targets": {
            "robot": robot_key,
            "service": service_key,
            "hardware": hardware_keys,
        },
        "simulation": {
            "docker_compose": result["sim_compose"],
            "env": result["sim_env"],
        },
        "real_hardware": {
            "docker_compose": result["real_compose"],
            "env": result["real_env"],
        },
    }

def main():
    mcp.run(transport="sse")

if __name__ == "__main__":
    main()