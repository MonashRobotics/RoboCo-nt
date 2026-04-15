#!/usr/bin/env python3


from pathlib import Path
import questionary
import roboco_core

def main() -> None:
    print()
    print("╔══════════════════════════════════════════════╗")
    print("║       🤖  Roboco CLI — Project Setup         ║")
    print("║       Monash Robotics Lab                    ║")
    print("╚══════════════════════════════════════════════╝")
    print()

    project_name = questionary.text(
        "What is your project name?",
        validate=lambda v: True if v.strip() else "Project name cannot be empty.",
    ).ask()
    if project_name is None:
        return

    project_name = project_name.strip()
    no_selection = "__none__"

    available_robots = roboco_core.get_available_robots()
    robot_choices = [
         questionary.Choice(title="No robot", value=no_selection),
    ] + [
        questionary.Choice(title=r["name"], value=r["key"])
        for r in available_robots
    ]

    robot_key = questionary.select(
        "Which robot would you like to use?",
        choices=robot_choices,
    ).ask()
    if robot_key is None:
        return

    robot = None
    service_key = None
    hardware_keys = []

    if robot_key != no_selection:
        robot = roboco_core.get_robot(robot_key)

        # ── 3. Choose service ─────────────────────────────────────────────
        available_services = roboco_core.get_robot_services(robot_key)
        service_choices = [
            questionary.Choice(title=s["name"], value=s["key"])
            for s in available_services
        ]
        service_key = questionary.select(
            "Which service do you want to run?",
            choices=service_choices,
        ).ask()
        if service_key is None:
            return

        # ── 4. Choose hardware (robot-specific) ──────────────────────────
        available_hw = roboco_core.get_robot_hardware(robot_key)
        if available_hw:
            hw_choices = [
                questionary.Choice(title="No additional hardware", value=no_selection),
            ] + [
                questionary.Choice(title=hw["name"], value=hw["key"])
                for hw in available_hw
            ]
            selected = questionary.checkbox(
                "Select hardware to include (Space to toggle, Enter to confirm):",
                choices=hw_choices,
            ).ask()
            if selected is None:
                return
            hardware_keys = [k for k in selected if k != no_selection]
    else:
        robot_key = None
        available_hw = roboco_core.get_available_hardwares()
        if available_hw:
            hw_choices = [
                questionary.Choice(title="No hardware", value=no_selection),
            ] + [
                questionary.Choice(title=hw["name"], value=hw["key"])
                for hw in available_hw
            ]
            selected = questionary.checkbox(
                "Select hardware to include (Space to toggle, Enter to confirm):",
                choices=hw_choices,
            ).ask()
            if selected is None:
                return
            hardware_keys = [k for k in selected if k != no_selection]
            
    print()
    print("── Summary ──────────────────────────────────────")
    print(f"  Project   : {project_name}")
    print(f"  Robot     : {robot.name + ' (' + robot_key + ')' if robot else '(none)'}")
    print(f"  Service   : {service_key if service_key else '(none)'}")
    print(f"  Hardware  : {', '.join(hardware_keys) if hardware_keys else '(none)'}")
    print("─────────────────────────────────────────────────")
    print()

    if robot is None and not hardware_keys:
        print("⚠️  Nothing to generate — no robot or hardware was selected.")
        return

    proceed = questionary.confirm("Generate project files?", default=True).ask()
    if not proceed:
        print("Aborted.")
        return

    result = roboco_core.generate_setup(robot_key, service_key, hardware_keys)

    project_dir = Path("/app/projects") / project_name
    project_dir.mkdir(parents=True, exist_ok=True)

    file_map = {
        "docker-compose-sim.yaml": result["sim_compose"],
        ".env-sim": result["sim_env"],
        "docker-compose.yaml": result["real_compose"],
        ".env": result["real_env"],
    }

    files_written = []
    for filename, content in file_map.items():
        if content:
            p = project_dir / filename
            p.write_text(content)
            files_written.append(p)

    print()
    if files_written:
        print(f"✅ Project '{project_name}' created at: {project_dir.resolve()}")

if __name__ == "__main__":
    main()