#!/usr/bin/env python3
"""Manage per-project JVM build-tool devcontainers.

This is a Python 3 translation of ``bin/devcontainer``.  The original bash
script is intentionally kept as-is.
"""

import argparse
import os
import shlex
import shutil
import stat
import subprocess
import sys


DEFAULT_IMAGE = "ghcr.io/alexandru/jdk-build-tools-devcontainer:latest"
DEFAULT_AGENT_PORT = "10012"
CONTAINER_PREFIX = "jdk-build-tools-dev-"
CONTAINER_LABEL = "com.alexandru.docker-images.devcontainer=true"
OPENCODE_CONFIG_CONTAINER_DIR = "/opt/opencode-config"

IMAGE = os.environ.get("DEVCONTAINER_IMAGE") or DEFAULT_IMAGE
HOME_VOLUME_PREFIX = os.environ.get("DEVCONTAINER_HOME_VOLUME_PREFIX") or (
    f"{os.environ.get('DEVCONTAINER_HOME_VOLUME') or 'jdk-build-tools-devcontainer-home'}-"
)

CRC_POLYNOMIAL = 0x04C11DB7


def make_crc_table():
    table = []
    for value in range(256):
        crc = value << 24
        for _ in range(8):
            if crc & 0x80000000:
                crc = ((crc << 1) ^ CRC_POLYNOMIAL) & 0xFFFFFFFF
            else:
                crc = (crc << 1) & 0xFFFFFFFF
        table.append(crc)
    return table


CRC_TABLE = make_crc_table()


def posix_cksum(data):
    """Return the POSIX cksum checksum for *data*.

    POSIX cksum uses a non-reflected CRC-32 with polynomial 0x04C11DB7,
    appends the input length low byte first, then returns the bitwise
    complement.  For empty input this returns 4294967295.
    """

    crc = 0
    for byte in data:
        crc = ((crc << 8) ^ CRC_TABLE[((crc >> 24) ^ byte) & 0xFF]) & 0xFFFFFFFF

    length = len(data)
    while length:
        crc = ((crc << 8) ^ CRC_TABLE[((crc >> 24) ^ length) & 0xFF]) & 0xFFFFFFFF
        length >>= 8

    return (~crc) & 0xFFFFFFFF


def canonical_dir(path, description):
    if not os.path.isdir(path):
        print(f"{description} directory does not exist: {path}", file=sys.stderr)
        raise SystemExit(1)
    return os.path.realpath(path)


def project_path(path):
    return canonical_dir(path, "Project")


def opencode_config_path(path):
    return canonical_dir(path, "OpenCode config")


def slugify_basename(name):
    allowed = set(b"abcdefghijklmnopqrstuvwxyz0123456789_.-")
    slug = bytes(byte if byte in allowed else ord("-") for byte in os.fsencode(name).lower())
    return slug.decode("ascii") or "project"


def project_token(project_dir):
    base = os.path.basename(project_dir)
    slug = slugify_basename(base)
    checksum = posix_cksum(os.fsencode(project_dir))
    return f"{slug}-{checksum}"


def container_name(project_dir):
    return f"{CONTAINER_PREFIX}{project_token(project_dir)}"


def home_volume(project_dir):
    return f"{HOME_VOLUME_PREFIX}{project_token(project_dir)}"


def yaml_quote(value):
    escaped = value.replace("\\", "\\\\").replace('"', '\\"')
    return f'"{escaped}"'


def has_ssh_auth_sock():
    path = os.environ.get("SSH_AUTH_SOCK", "")
    if not path:
        return False
    try:
        return stat.S_ISSOCK(os.stat(path).st_mode)
    except OSError:
        return False


def find_container_cli():
    configured = os.environ.get("CONTAINER_CLI")
    if configured:
        return configured

    for cli in ("wslc.exe", "wslc", "docker", "podman"):
        path = shutil.which(cli)
        if path:
            return path

    return None


def ordered_add(values, value):
    if value and value not in values:
        values.append(value)


class DevContainer:
    def __init__(self, command, project_dir="", command_args=None, container_cli=None):
        self.command = command
        self.project_dir = project_dir
        self.command_args = list(command_args or [])
        self.container_cli = container_cli or ""
        self.container_name = container_name(project_dir) if project_dir else ""
        self.home_volume = home_volume(project_dir) if project_dir else ""
        self.opencode_config_host_dir = ""
        self.agent_port = ""
        self.container_env_args = []

    def run_cli(self, args, *, stdout=None, stderr=None, capture=False, check=False):
        command = [self.container_cli, *args]
        if capture:
            result = subprocess.run(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.DEVNULL if stderr is None else stderr,
                text=True,
                check=False,
            )
        else:
            result = subprocess.run(command, stdout=stdout, stderr=stderr, check=False)

        if check and result.returncode != 0:
            raise SystemExit(result.returncode)
        return result

    def configure_opencode_config_mount(self):
        config_dir = os.environ.get("DEVCONTAINER_OPENCODE_CONFIG_DIR")
        if config_dir:
            self.opencode_config_host_dir = opencode_config_path(config_dir)

    def configure_container_env_args(self):
        self.container_env_args = []

        api_key = os.environ.get("DEVCONTAINER_OPENCODE_GO_API_KEY")
        if api_key:
            self.container_env_args.extend(["-e", f"OPENCODE_API_KEY={api_key}"])

        if self.opencode_config_host_dir:
            self.container_env_args.extend(["-e", f"OPENCODE_CONFIG_DIR={OPENCODE_CONFIG_CONTAINER_DIR}"])

    def configure_agent_port(self):
        self.agent_port = os.environ.get("DEVCONTAINER_AGENT_PORT", "")
        if self.command == "agent-serve" and not self.agent_port:
            self.agent_port = DEFAULT_AGENT_PORT

    def container_exists(self):
        return (
            self.run_cli(
                ["inspect", self.container_name],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            ).returncode
            == 0
        )

    def container_opencode_config_source(self):
        fmt = (
            "{{range .Mounts}}{{if eq .Destination \""
            f"{OPENCODE_CONFIG_CONTAINER_DIR}"
            "\"}}{{println .Source}}{{end}}{{end}}"
        )
        return self.run_cli(["inspect", "--format", fmt, self.container_name], capture=True).stdout.strip()

    def container_agent_ports(self):
        fmt = "{{range $port, $bindings := .HostConfig.PortBindings}}{{if eq $port \"10012/tcp\"}}{{range $bindings}}{{println .HostPort}}{{end}}{{end}}{{end}}"
        output = self.run_cli(["inspect", "--format", fmt, self.container_name], capture=True).stdout
        return output.splitlines()

    def ensure_opencode_config_mount(self):
        if not self.opencode_config_host_dir:
            return

        source = self.container_opencode_config_source()
        if source != self.opencode_config_host_dir:
            print(
                "Container already exists without the requested OpenCode config mount.",
                file=sys.stderr,
            )
            print(
                f"Run `{sys.argv[0]} purge {shlex.quote(self.project_dir)}` and start it again to apply DEVCONTAINER_OPENCODE_CONFIG_DIR.",
                file=sys.stderr,
            )
            raise SystemExit(1)

    def ensure_agent_port(self):
        if not self.agent_port:
            return

        if self.agent_port in self.container_agent_ports():
            return

        print(
            f"Container already exists without host port {self.agent_port} mapped to container port 10012.",
            file=sys.stderr,
        )
        print("Remove and recreate the container to apply DEVCONTAINER_AGENT_PORT.", file=sys.stderr)
        raise SystemExit(1)

    def start_container(self, *, announce=True):
        if self.container_exists():
            self.ensure_opencode_config_mount()
            self.ensure_agent_port()
            self.run_cli(
                ["start", self.container_name],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
        else:
            self.run_cli(
                [
                    "volume",
                    "create",
                    "--label",
                    CONTAINER_LABEL,
                    "--label",
                    f"com.alexandru.docker-images.devcontainer.project={self.project_dir}",
                    self.home_volume,
                ],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )

            ssh_args = []
            if has_ssh_auth_sock():
                ssh_auth_sock = os.environ["SSH_AUTH_SOCK"]
                ssh_args = ["-v", f"{ssh_auth_sock}:{ssh_auth_sock}", "-e", f"SSH_AUTH_SOCK={ssh_auth_sock}"]

            opencode_config_args = []
            if self.opencode_config_host_dir:
                opencode_config_args = [
                    "-v",
                    f"{self.opencode_config_host_dir}:{OPENCODE_CONFIG_CONTAINER_DIR}:ro",
                ]

            agent_port_args = []
            if self.agent_port:
                agent_port_args = ["-p", f"{self.agent_port}:10012"]

            self.run_cli(
                [
                    "run",
                    "-d",
                    "--name",
                    self.container_name,
                    "--label",
                    CONTAINER_LABEL,
                    "--label",
                    f"com.alexandru.docker-images.devcontainer.project={self.project_dir}",
                    "--label",
                    f"com.alexandru.docker-images.devcontainer.home-volume={self.home_volume}",
                    "-v",
                    f"{self.project_dir}:/workspace",
                    "-v",
                    f"{self.home_volume}:/home/dev",
                    *ssh_args,
                    *self.container_env_args,
                    *opencode_config_args,
                    *agent_port_args,
                    "-w",
                    "/workspace",
                    IMAGE,
                    "sleep",
                    "infinity",
                ],
                stdout=subprocess.DEVNULL,
                check=True,
            )

        if announce:
            print(f"Container: {self.container_name}")
            print(f"Project:   {self.project_dir} -> /workspace")
            print(f"Home:      {self.home_volume} -> /home/dev")
            print(
                "Shell:     "
                f"{shlex.quote(self.container_cli)} exec -it {shlex.quote(self.container_name)} bash"
            )

    def exec_container(self, args):
        command = [
            self.container_cli,
            "exec",
            "-it",
            *self.container_env_args,
            self.container_name,
            "/usr/local/bin/devcontainer-entrypoint",
            *args,
        ]
        os.execvp(self.container_cli, command)

    def stop_container(self):
        if self.container_exists():
            self.run_cli(
                ["stop", self.container_name],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            print(f"Stopped: {self.container_name}")
        else:
            print(f"Container does not exist: {self.container_name}")

    def shell_container(self):
        self.run_in_container(["bash"])

    def exec_command(self):
        self.run_in_container(self.command_args)

    def agent(self):
        self.run_in_container(["opencode", *self.command_args])

    def agent_serve(self):
        self.run_in_container(["opencode", "serve", "--port", "10012", "--hostname", "0.0.0.0"])

    def run_in_container(self, args):
        self.start_container(announce=False)
        self.exec_container(args)

    def compose_file(self):
        self.compose_service()
        self.compose_home_volume()

    def compose_service(self):
        print("services:")
        print("  devcontainer:")
        print(f'    image: "${{DEVCONTAINER_IMAGE:-{DEFAULT_IMAGE}}}"')
        print(f"    container_name: {yaml_quote(self.container_name)}")
        print("    working_dir: /workspace")
        print("    command:")
        print("      - sleep")
        print("      - infinity")

        if self.agent_port:
            print("    ports:")
            print('      - "${DEVCONTAINER_AGENT_PORT}:10012"')

        print("    labels:")
        print('      com.alexandru.docker-images.devcontainer: "true"')
        print(
            "      com.alexandru.docker-images.devcontainer.project: "
            f"{yaml_quote(self.project_dir)}"
        )
        print(
            "      com.alexandru.docker-images.devcontainer.home-volume: "
            f"{yaml_quote(self.home_volume)}"
        )

        self.compose_environment()
        self.compose_mounts()

    def compose_has_environment(self):
        return bool(
            os.environ.get("DEVCONTAINER_OPENCODE_GO_API_KEY")
            or self.opencode_config_host_dir
            or has_ssh_auth_sock()
        )

    def compose_environment(self):
        if not self.compose_has_environment():
            return

        print("    environment:")

        if os.environ.get("DEVCONTAINER_OPENCODE_GO_API_KEY"):
            print('      OPENCODE_API_KEY: "${DEVCONTAINER_OPENCODE_GO_API_KEY}"')

        if self.opencode_config_host_dir:
            print(f"      OPENCODE_CONFIG_DIR: {yaml_quote(OPENCODE_CONFIG_CONTAINER_DIR)}")

        if has_ssh_auth_sock():
            print('      SSH_AUTH_SOCK: "${SSH_AUTH_SOCK}"')

    def compose_mounts(self):
        print("    volumes:")
        print("      - type: bind")
        print(f"        source: {yaml_quote(self.project_dir)}")
        print("        target: /workspace")
        print("      - type: volume")
        print("        source: home")
        print("        target: /home/dev")

        if self.opencode_config_host_dir:
            print("      - type: bind")
            print('        source: "${DEVCONTAINER_OPENCODE_CONFIG_DIR}"')
            print(f"        target: {yaml_quote(OPENCODE_CONFIG_CONTAINER_DIR)}")
            print("        read_only: true")

        if has_ssh_auth_sock():
            print("      - type: bind")
            print('        source: "${SSH_AUTH_SOCK}"')
            print('        target: "${SSH_AUTH_SOCK}"')

    def compose_home_volume(self):
        print()
        print("volumes:")
        print("  home:")
        print(f"    name: {yaml_quote(self.home_volume)}")
        print("    labels:")
        print('      com.alexandru.docker-images.devcontainer: "true"')
        print(
            "      com.alexandru.docker-images.devcontainer.project: "
            f"{yaml_quote(self.project_dir)}"
        )

    def purge_container(self):
        if self.container_exists():
            self.run_cli(
                ["rm", "-f", self.container_name],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            print(f"Deleted container: {self.container_name}")
        else:
            print(f"Container does not exist: {self.container_name}")

        self.purge_volume(self.home_volume)

    def collect_container_ids(self, container_ids, filter_arg):
        result = self.run_cli(
            ["ps", "-aq", "--filter", filter_arg],
            capture=True,
        )
        for container_id in result.stdout.splitlines():
            ordered_add(container_ids, container_id)

    def collect_volume_names(self, volume_names, filter_arg):
        result = self.run_cli(
            ["volume", "ls", "-q", "--filter", filter_arg],
            capture=True,
        )
        for volume_name in result.stdout.splitlines():
            ordered_add(volume_names, volume_name)

    def collect_container_home_volumes(self, volume_names, container_id):
        fmt = '{{range .Mounts}}{{if eq .Destination "/home/dev"}}{{println .Name}}{{end}}{{end}}'
        result = self.run_cli(["inspect", "--format", fmt, container_id], capture=True)
        for volume_name in result.stdout.splitlines():
            ordered_add(volume_names, volume_name)

    def purge_volume(self, volume_name):
        if (
            self.run_cli(
                ["volume", "inspect", volume_name],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            ).returncode
            == 0
        ):
            if (
                self.run_cli(
                    ["volume", "rm", "-f", volume_name],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                ).returncode
                == 0
            ):
                print(f"Deleted volume: {volume_name}")
            else:
                print(f"Failed to delete volume: {volume_name}", file=sys.stderr)
        else:
            print(f"Volume does not exist: {volume_name}")

    def purge_volumes(self, volume_names):
        if not volume_names:
            print("No devcontainer volumes found.")
            return

        for volume_name in volume_names:
            self.purge_volume(volume_name)

    def purge_all(self):
        container_ids = []
        volume_names = []

        self.collect_container_ids(container_ids, f"ancestor={IMAGE}")
        self.collect_container_ids(container_ids, f"label={CONTAINER_LABEL}")

        for container_id in container_ids:
            self.collect_container_home_volumes(volume_names, container_id)

        self.collect_volume_names(volume_names, f"label={CONTAINER_LABEL}")
        self.collect_volume_names(volume_names, f"name={HOME_VOLUME_PREFIX}")

        if container_ids:
            self.run_cli(
                ["rm", "-f", *container_ids],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            print(f"Deleted devcontainer containers: {len(container_ids)}")
        else:
            print("No devcontainer containers found.")

        self.purge_volumes(volume_names)


ENVIRONMENT_HELP = f"""
Environment:
  CONTAINER_CLI                     Container CLI to use. Defaults to first available wslc.exe, wslc, docker, or podman.
  DEVCONTAINER_IMAGE                Image to run. Defaults to {IMAGE}.
  DEVCONTAINER_AGENT_PORT           Optional host port for container port 10012; agent-serve defaults to {DEFAULT_AGENT_PORT}.
  DEVCONTAINER_HOME_VOLUME_PREFIX   Prefix for per-workspace /home/dev volumes. Defaults to {HOME_VOLUME_PREFIX}.
  DEVCONTAINER_OPENCODE_GO_API_KEY  Optional OpenCode Go API key forwarded into the container.
  DEVCONTAINER_OPENCODE_CONFIG_DIR  Optional host config directory mounted read-only; sets OPENCODE_CONFIG_DIR={OPENCODE_CONFIG_CONTAINER_DIR} inside the container.
"""


def build_parser():
    parser = argparse.ArgumentParser(
        prog=os.path.basename(sys.argv[0]),
        description="Manage per-project JVM build-tool devcontainers.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=ENVIRONMENT_HELP,
    )
    subparsers = parser.add_subparsers(dest="command", required=True)
    command_parsers = {}

    def add_project_command(name, help_text):
        command_parser = subparsers.add_parser(name, help=help_text, description=help_text)
        command_parser.add_argument("project_directory")
        command_parsers[name] = command_parser
        return command_parser

    add_project_command("start", "Start the devcontainer for a project.")
    add_project_command("stop", "Stop the devcontainer for a project.")
    add_project_command("restart", "Stop and start the devcontainer for a project.")
    add_project_command("shell", "Open an interactive shell in the project devcontainer, starting it first if needed.")
    add_project_command("compose", "Print a docker-compose.yaml for the project devcontainer to stdout.")
    add_project_command("agent-serve", "Start the opencode server in the project devcontainer, starting the container first if needed.")
    add_project_command("purge", "Delete the project devcontainer and its /home/dev volume.")

    exec_parser = subparsers.add_parser(
        "exec",
        add_help=False,
        help="Run a command in the project devcontainer, starting it first if needed.",
        description="Run a command in the project devcontainer, starting it first if needed.",
    )
    exec_parser.add_argument("project_directory")
    exec_parser.add_argument("command_args", nargs=argparse.REMAINDER)
    command_parsers["exec"] = exec_parser

    agent_parser = subparsers.add_parser(
        "agent",
        add_help=False,
        help="Start opencode in the project devcontainer, starting the container first if needed.",
        description="Start opencode in the project devcontainer, starting the container first if needed.",
    )
    agent_parser.add_argument("project_directory")
    agent_parser.add_argument("command_args", nargs=argparse.REMAINDER)
    command_parsers["agent"] = agent_parser

    purge_all_parser = subparsers.add_parser(
        "purge-all",
        help="Delete all devcontainer containers and /home/dev volumes. The image is not deleted.",
        description="Delete all devcontainer containers and /home/dev volumes. The image is not deleted.",
    )
    command_parsers["purge-all"] = purge_all_parser

    help_parser = subparsers.add_parser("help", help="Show this help or help for a command.")
    help_parser.add_argument("help_command", nargs="?", choices=sorted(command_parsers))
    command_parsers["help"] = help_parser

    return parser, command_parsers


def create_devcontainer(namespace, container_cli):
    project_dir = ""
    if hasattr(namespace, "project_directory"):
        project_dir = project_path(namespace.project_directory)

    command_args = getattr(namespace, "command_args", [])
    return DevContainer(namespace.command, project_dir, command_args, container_cli)


def dispatch(devcontainer):
    if devcontainer.command == "start":
        devcontainer.start_container()
    elif devcontainer.command == "stop":
        devcontainer.stop_container()
    elif devcontainer.command == "restart":
        devcontainer.stop_container()
        devcontainer.start_container()
    elif devcontainer.command == "shell":
        devcontainer.shell_container()
    elif devcontainer.command == "exec":
        devcontainer.exec_command()
    elif devcontainer.command == "compose":
        devcontainer.compose_file()
    elif devcontainer.command == "agent":
        devcontainer.agent()
    elif devcontainer.command == "agent-serve":
        devcontainer.agent_serve()
    elif devcontainer.command == "purge":
        devcontainer.purge_container()
    elif devcontainer.command == "purge-all":
        devcontainer.purge_all()
    else:
        raise ValueError(f"Unhandled command: {devcontainer.command}")


def main(argv=None):
    parser, command_parsers = build_parser()
    namespace = parser.parse_args(argv)

    if namespace.command == "help":
        if namespace.help_command:
            command_parsers[namespace.help_command].print_help()
        else:
            parser.print_help()
        return 0

    if namespace.command == "exec" and not namespace.command_args:
        parser.error("exec requires <project-directory> <command> [argument ...]")

    container_cli = None
    if namespace.command != "compose":
        container_cli = find_container_cli()
        if not container_cli:
            print(
                "No container CLI found. Install wslc.exe, docker, or podman, or set CONTAINER_CLI.",
                file=sys.stderr,
            )
            return 1

    devcontainer = create_devcontainer(namespace, container_cli)

    if namespace.command in {"start", "restart", "shell", "exec", "compose", "agent", "agent-serve"}:
        devcontainer.configure_opencode_config_mount()

    devcontainer.configure_agent_port()
    devcontainer.configure_container_env_args()
    dispatch(devcontainer)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
