import argparse
import os
import subprocess
from pathlib import Path
import rich

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    parser.add_argument(
        "--certbot-host", default="ec2-34-201-77-193.compute-1.amazonaws.com"
    )
    parser.add_argument("--certbot-ssh-user", default="ubuntu")
    parser.add_argument("--certbot-ssh-key", default=f"{Path.home()}/.ssh/gridworks-hybrid.pem")
    parser.add_argument(
        "--certbot-ca-certificate-path", default="/home/ubuntu/.local/share/gridworks/ca/ca.crt"
    )
    parser.add_argument(
        "--certbot-ca-private-key-path", default="/home/ubuntu/.local/share/gridworks/ca/private/ca_key.pem"
    )
    parser.add_argument("--certbot-certs-dir", default="/home/ubuntu/.local/share/gridworks/ca/certs")
    parser.add_argument("--certbot-rclone-name", default="certbot")
    parser.add_argument("--force", action="store_true")
    parser.add_argument("--dry-run", action="store_true")

    parser.add_argument("certbot_key_name")
    parser.add_argument("certbot_mqtt_name")
    parser.add_argument("dest_rclone_name")
    parser.add_argument("dest_rclone_certs_dir")
    args = parser.parse_args()

    commands = dict()
    certbot_certs_dir = f"{args.certbot_certs_dir}/{args.certbot_key_name}"
    force_text = "--force " if args.force else ""
    generate_key_command_str = (
        "gwcert key add "
        f"--ca-certificate-path {args.certbot_ca_certificate_path} "
        f"--ca-private-key-path {args.certbot_ca_private_key_path} "
        f"{force_text}"
        f"--certs-dir {certbot_certs_dir} "
        f"{args.certbot_mqtt_name}"
    )
    certbot_src_dir = f"{certbot_certs_dir}/{args.certbot_mqtt_name}"
    certbot_src_private_dir = f"{certbot_src_dir}/private"
    rclone_dest_name = f"{args.dest_rclone_name}:" if args.dest_rclone_name else ""
    rclone_dest_dir = f"{args.dest_rclone_certs_dir}/{args.certbot_mqtt_name}"
    rclone_dest_private_dir = f"{rclone_dest_dir}/private"
    commands = dict(
        ssh_command = [
        "ssh",
        "-A",
        f"{args.certbot_ssh_user}@{args.certbot_host}",
        "-i",
        args.certbot_ssh_key,
        f"bash -l -c '{generate_key_command_str}'"
    ],
        mkdir_certs_command = [
            "rclone",
            "mkdir",
            f"{rclone_dest_name}{rclone_dest_dir}",
        ],
        mkdir_private_command = [
            f"rclone",
            "mkdir",
            f"{rclone_dest_name}{rclone_dest_private_dir}",
        ],
        copy_ca_command = [
            "rclone",
            "copyto",
            f"{args.certbot_rclone_name}:{args.certbot_ca_certificate_path}",
            f"{rclone_dest_name}{rclone_dest_dir}/ca.crt",
        ],
        copy_crt_command = [
            "rclone",
            "copyto",
            f"{args.certbot_rclone_name}:{certbot_src_dir}/{args.certbot_mqtt_name}.crt",
            f"{rclone_dest_name}{rclone_dest_dir}/{args.certbot_mqtt_name}.crt",
        ],
        copy_key_command = [
            "rclone",
            "copyto",
            f"{args.certbot_rclone_name}:{certbot_src_private_dir}/{args.certbot_mqtt_name}.pem",
            f"{rclone_dest_name}{rclone_dest_private_dir}/{args.certbot_mqtt_name}.pem",
        ],
        ls_command = [
            "rclone",
            "ls",
            f"{rclone_dest_name}{rclone_dest_dir}",
        ]
    )
    if args.dry_run:
        print(commands)
        print("\nDry run. Showing Commands and exiting:\n")
        for cmd in commands.values():
            print(f"{' '.join(cmd)}")
        print()
    else:
        for i, cmd in enumerate(commands.values()):
            rich.print(f"Running command:\n\n\t{' '.join(cmd)}\n")
            result = subprocess.run(cmd, capture_output=True)
            if result.returncode != 0:
                rich.print(f"Command output:\n[\n{result.stderr.decode('utf-8')}\n]")
                raise RuntimeError(
                    f"ERROR. Command <{' '.join(cmd)}> failed with returncode:{result.returncode}"
                )
            if i == len(commands) - 1:
                rich.print(result.stdout.decode('utf-8'))
                rich.print("")
