from mcp.server.fastmcp import FastMCP
from configurations import robots
from mcp.server.fastmcp.exceptions import ToolError
import yaml
from pathlib import Path

inst = """
    You help users getting started on a robot in Monash Robotics Lab. 
    
    Ultimately,you will give them 2 docker-compose.yaml one for running sim 
    and one for running on real robot. Of course, at the end, you will also 
    provide steps to make this work.

    Always follow this workflow IN ORDER. Never skip or reorder steps:
    1. Ask the user what experiment they have in mind. Please do not show what robot is available at this step.
    2. Call get_available_robots() and recommend relevant robots for this experiment. Then let the user choose which robot they want. Please PROMPT MULTIPLE CHOICE.
    3. Once they choose, call get_robot_services() and describe how each service might be useful for their experiment. Then let the user choose which service they want.
    4. Once they choose, call get_robot_hardware() and recommend relevant hardwares for this experiment. Then let the user choose which hardware they want to add.
    5. Finally, once you have all the necessary information, call generate_setup() to produce two docker-compose.yaml files and guide setup
    
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
mcp = FastMCP("Roboco", instructions = inst)

def merge_yaml_strings(base_yaml: str, add_yaml: str) -> str:
    """Merges two docker-compose YAML strings securely."""
    if not base_yaml.strip(): return add_yaml
    if not add_yaml.strip(): return base_yaml
    
    base_dict = yaml.safe_load(base_yaml) or {}
    add_dict = yaml.safe_load(add_yaml) or {}

    for key in ['services', 'networks', 'volumes']:
        if key in add_dict:
            if key not in base_dict:
                base_dict[key] = {}
            base_dict[key].update(add_dict[key])
            
    return yaml.dump(base_dict, default_flow_style=False, sort_keys=False)

def read_file(path: Path) -> str:
    """Reads a file if it exists, otherwise returns an empty string."""
    return path.read_text() if path.exists() else ""

@mcp.prompt()
async def test_prompt(name: str) -> str:
    """"Just a function to test MCP prompt"""
    return f"Hi there {name}!"

@mcp.tool()
async def start_session() -> dict:
    """
    ALWAYS call this tool first when the user wants to start or greet Roboco.
    Returns the opening question to ask the user. Please do not show the user the instructions
    """
    return {
        "message": "Welcome to the Monash Robotics Lab! What experiment do you have in mind? Please describe what you're trying to do, and I'll help you find the right robot and configuration.",
        "instructions": inst 
    }

@mcp.tool()
async def get_available_robots() -> dict:
    """Return a list of all available robots."""
    return {
        "robots": [{"key": r.key, "name": r.name} for r in robots.values()],
        "instructions": "If you haven't called start_session tool in this chat session, please do that first."
    }

@mcp.tool()
async def get_robot_hardware(robot_key: str) -> dict:
    """Return the hardware options available for a specific robot."""
    if robot_key not in robots:
        raise ToolError(f"Robot '{robot_key}' not found.")
    
    robot = robots[robot_key]
    return {
        "hardware": [
            {"key": hw.key, "name": hw.name, "distros": hw.compatible_ros_distros} 
            for hw in robot.compatible_hardware
        ]
    }

@mcp.tool()
async def get_robot_services(robot_key: str) -> dict:
    """Return the software services available for a specific robot."""
    if robot_key not in robots:
        raise ToolError(f"Robot '{robot_key}' not found.")
    
    robot = robots[robot_key]
    return {
        "services": [
            {"key": s.key, "use_case": s.name, "distros": s.compatible_ros_distros} 
            for s in robot.available_service
        ]
    }

@mcp.tool()
async def generate_setup(robot_key: str, service_key: str, hardware_keys: list[str]) -> dict:
    if robot_key not in robots:
        raise ToolError(f"Robot '{robot_key}' not found.")

    robot = robots[robot_key]

    if service_key not in [s.key for s in robot.available_service]:
        raise ToolError(f"{robot_key} does not have service {service_key}")
    
    for hw_key in hardware_keys:
        if hw_key not in [h.key for h in robot.compatible_hardware]:
            raise ToolError(f"{robot_key} does not support hardware {hw_key}")

    base_dir = Path.cwd()
    robot_dir = base_dir / "services" / robot_key / service_key
    sim_compose_files = [robot_dir / "docker-compose.yaml"]
    sim_env_files = [robot_dir / ".env"]
    real_compose_files = [robot_dir / "docker-compose-real.yaml"]
    real_env_files = [robot_dir / ".env-real"]

    for hw_key in hardware_keys:
        hw_dir = base_dir / "services" / hw_key
        
        sim_compose_files.append(hw_dir / "docker-compose.yaml")
        sim_env_files.append(hw_dir / ".env")
        
        real_compose_files.append(hw_dir / "docker-compose-real.yaml")
        real_env_files.append(hw_dir / ".env-real")

    sim_yaml_merged = ""
    for path in sim_compose_files:
        sim_yaml_merged = merge_yaml_strings(sim_yaml_merged, read_file(path))
        
    sim_env_merged = "\n".join(read_file(path) for path in sim_env_files if path.exists())

    # 3. Process REAL configuration
    real_yaml_merged = ""
    for path in real_compose_files:
        real_yaml_merged = merge_yaml_strings(real_yaml_merged, read_file(path))
        
    real_env_merged = "\n".join(read_file(path) for path in real_env_files if path.exists())

    return {
        "status": "success",
        "configuration_targets": {
            "robot": robot_key,
            "service": service_key,
            "hardware": hardware_keys
        },
        "simulation": {
            "docker_compose": sim_yaml_merged.strip() or None,
            "env": sim_env_merged.strip() or None
        },
        "real_hardware": {
            "docker_compose": real_yaml_merged.strip() or None,
            "env": real_env_merged.strip() or None
        }
    }

def main():
    mcp.run(transport="stdio")

if __name__ == "__main__":
    main()