from pathlib import Path
from typing import Optional
import yaml
from configurations import robots, hardwares

def merge_yaml_strings(base_yaml: str, add_yaml: str) -> str:
    """Merge two docker-compose YAML strings."""
    if not base_yaml.strip():
        return add_yaml
    if not add_yaml.strip():
        return base_yaml

    base_dict = yaml.safe_load(base_yaml) or {}
    add_dict = yaml.safe_load(add_yaml) or {}

    for key in ("services", "networks", "volumes"):
        if key in add_dict:
            base_dict.setdefault(key, {}).update(add_dict[key])

    return yaml.dump(base_dict, default_flow_style=False, sort_keys=False)


def read_file(path: Path) -> str:
    """Read a file if it exists, otherwise return an empty string."""
    return path.read_text() if path.exists() else ""

def get_available_hardwares() -> list[dict]:
    """Return a list of all available hardwares (independent of any robot)."""
    return [{"key": hw.key, "name": hw.name} for hw in hardwares.values()]

def get_hardware(hardware_key: str):
    """Return a hardware by key, or raise KeyError."""
    if hardware_key not in hardwares:
        raise KeyError(f"Hardware '{hardware_key}' not found.")
    return hardwares[hardware_key]

def get_available_robots() -> list[dict]:
    """Return a list of all available robots."""
    return [{"key": r.key, "name": r.name} for r in robots.values()]

def get_robot(robot_key: str):
    """Return a robot by key, or raise KeyError."""
    if robot_key not in robots:
        raise KeyError(f"Robot '{robot_key}' not found.")
    return robots[robot_key]

def get_robot_services(robot_key: str) -> list[dict]:
    """Return the software services available for a specific robot."""
    robot = get_robot(robot_key)
    return [
        {"key": s.key, "name": s.name, "distros": s.compatible_ros_distros}
        for s in robot.available_service
    ]

def get_robot_hardware(robot_key: str) -> list[dict]:
    """Return the hardware options available for a specific robot."""
    robot = get_robot(robot_key)
    return [
        {"key": hw.key, "name": hw.name, "distros": hw.compatible_ros_distros}
        for hw in robot.compatible_hardware
    ]

def generate_setup(
    robot_key: Optional[str],
    service_key: Optional[str],
    hardware_keys: list[str],
    services_dir: Optional[Path] = None,
) -> dict:
    
    if services_dir is None:
        services_dir = Path.cwd() / "services"

    sim_compose_files = []
    sim_env_files = []
    real_compose_files = []
    real_env_files = []

    if robot_key is not None:
        robot = get_robot(robot_key)

        valid_services = {s.key for s in robot.available_service}
        if service_key not in valid_services:
            raise ValueError(f"{robot_key} does not have service '{service_key}'")

        valid_hw = {h.key for h in robot.compatible_hardware}
        for hw_key in hardware_keys:
            if hw_key not in valid_hw:
                raise ValueError(f"{robot_key} does not support hardware '{hw_key}'")

        robot_dir = services_dir / robot_key / service_key
        sim_compose_files.append(robot_dir / "docker-compose-sim.yaml")
        sim_env_files.append(robot_dir / ".env-sim")
        real_compose_files.append(robot_dir / "docker-compose.yaml")
        real_env_files.append(robot_dir / ".env")

    for hw_key in hardware_keys:
        hw_dir = services_dir / hw_key
        sim_compose_files.append(hw_dir / "docker-compose-sim.yaml")
        sim_env_files.append(hw_dir / ".env-sim")
        real_compose_files.append(hw_dir / "docker-compose.yaml")
        real_env_files.append(hw_dir / ".env")

    print(sim_compose_files)
    print(real_compose_files)
    sim_yaml = ""
    for path in sim_compose_files:
        sim_yaml = merge_yaml_strings(sim_yaml, read_file(path))
    sim_env = "\n".join(read_file(p) for p in sim_env_files if p.exists())

    real_yaml = ""
    for path in real_compose_files:
        real_yaml = merge_yaml_strings(real_yaml, read_file(path))
    real_env = "\n".join(read_file(p) for p in real_env_files if p.exists())

    return {
        "sim_compose": sim_yaml.strip() or None,
        "sim_env": sim_env.strip() or None,
        "real_compose": real_yaml.strip() or None,
        "real_env": real_env.strip() or None,
    }