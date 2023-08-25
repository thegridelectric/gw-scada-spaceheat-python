import argparse
import os
import subprocess
from pathlib import Path
import rich

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
        usage="""python getkeys.py <certbot-key-name> <mqtt_name> <dest-rclone-name> <dest-cert-dir>
        
    Generate and copy TLS keys for gw-scada-spaceheat-python. 
    
    getkeys.py does the following: 
    1. Use ssh generate keys on certbot. 
    2. Use rclone to copy those keys to the desired location.
    
    getkeys.py requires: 
    1. The presence of the ssh key used by ssh and rclone. 
    2. Configured rclone remotes.
    
    See https://rclone.org/ for information about rclone. It can be on a Mac installed with: 
         
         brew install rclone
         
    Examples
    -------- 
         
    To generate and copy keys for the scada 'almond', ensure you have the ssh key for certbot in $HOME/.ssh and rclone
    remotes configured for 'certbot' and 'almond' and run:  
    
        python gw_spaceheat/getkeys.py almond gridworks_mqtt almond /home/pi/.config/gridworks/scada/certs
    
    To generate and copy keys for the test ATN running on the 'cloudatn' machine used by the scada 'almond', ensure you
    have remotes configured for 'certbot' and 'cloudatn' and run: 
    
        python gw_spaceheat/getkeys.py almond-atn scada_mqtt cloudatn /home/ubuntu/almond-atn/.config/gridworks/atn/certs

    """,
    )
    parser.add_argument(
        "--certbot-host",
        default="ec2-34-201-77-193.compute-1.amazonaws.com",
        help="Hostname used by ssh to reach certbot.",
    )
    parser.add_argument(
        "--certbot-ssh-user",
        default="ubuntu",
        help="Username used by ssh to reach certbot.",
    )
    parser.add_argument(
        "--certbot-ssh-key",
        default=f"{Path.home()}/.ssh/gridworks-hybrid.pem",
        help="SSH key used by ssh to reach certbot",
    )
    parser.add_argument(
        "--certbot-ca-certificate-path",
        default="/home/ubuntu/.local/share/gridworks/ca/ca.crt",
        help="Path to CA certificate on certbot.",
    )
    parser.add_argument(
        "--certbot-ca-private-key-path",
        default="/home/ubuntu/.local/share/gridworks/ca/private/ca_key.pem",
        help="Path to CA private key on certbot.",
    )
    parser.add_argument(
        "--certbot-certs-dir",
        default="/home/ubuntu/.local/share/gridworks/ca/certs",
        help="Base directory for storing certs on certbot.",
    )
    parser.add_argument(
        "--certbot-rclone-name",
        default="certbot",
        help="Name of the rclone remote used for certbot.",
    )
    parser.add_argument(
        "--force", action="store_true", help="Force regeneration of keys."
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print commands that would be executed but do not execute them.",
    )

    parser.add_argument(
        "certbot_key_name",
        help="Human friendly name used to identify these keys on certbot.",
    )
    parser.add_argument(
        "mqtt_name",
        help=(
            "Name of the MQTTConfig used in ProactorSettings-derived class to refer to the connection these "
            "keys enable. For example, For a scada use 'gridworks_mqtt', the name of the MQTTConfig used to communicate "
            "with the ATN in ScadaSettings. For the test ATN use 'scada_mqtt', the name of the MQTTConfig used to "
            "communicate with the scada in AtnSettings."
        ),
    )
    parser.add_argument(
        "dest_rclone_name",
        help=(
            "rclone remote to which files will be transferred. Use an explicit \"\" to transfer files to local "
            "machine."
        ),
    )
    parser.add_argument(
        "dest_certs_dir",
        help=(
            "Absolute path to destination directory on target machine. A scada with default config uses "
            "/home/pi/.config/gridworks/scada/certs."
        ),
    )
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
        f"{args.mqtt_name}"
    )
    certbot_src_dir = f"{certbot_certs_dir}/{args.mqtt_name}"
    certbot_src_private_dir = f"{certbot_src_dir}/private"
    rclone_dest_name = f"{args.dest_rclone_name}:" if args.dest_rclone_name else ""
    rclone_dest_dir = f"{args.dest_certs_dir}/{args.mqtt_name}"
    rclone_dest_private_dir = f"{rclone_dest_dir}/private"
    commands = dict(
        ssh_command=[
            "ssh",
            "-A",
            f"{args.certbot_ssh_user}@{args.certbot_host}",
            "-i",
            args.certbot_ssh_key,
            f"bash -l -c '{generate_key_command_str}'",
        ],
        mkdir_certs_command=[
            "rclone",
            "mkdir",
            f"{rclone_dest_name}{rclone_dest_dir}",
        ],
        mkdir_private_command=[
            f"rclone",
            "mkdir",
            f"{rclone_dest_name}{rclone_dest_private_dir}",
        ],
        copy_ca_command=[
            "rclone",
            "copyto",
            f"{args.certbot_rclone_name}:{args.certbot_ca_certificate_path}",
            f"{rclone_dest_name}{rclone_dest_dir}/ca.crt",
        ],
        copy_crt_command=[
            "rclone",
            "copyto",
            f"{args.certbot_rclone_name}:{certbot_src_dir}/{args.mqtt_name}.crt",
            f"{rclone_dest_name}{rclone_dest_dir}/{args.mqtt_name}.crt",
        ],
        copy_key_command=[
            "rclone",
            "copyto",
            f"{args.certbot_rclone_name}:{certbot_src_private_dir}/{args.mqtt_name}.pem",
            f"{rclone_dest_name}{rclone_dest_private_dir}/{args.mqtt_name}.pem",
        ],
        ls_command=[
            "rclone",
            "ls",
            f"{rclone_dest_name}{rclone_dest_dir}",
        ],
    )
    if args.dry_run:
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
                rich.print(result.stdout.decode("utf-8"))
                rich.print("")
