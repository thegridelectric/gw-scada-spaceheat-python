import dotenv
import pendulum
from gwproto.data_classes.hardware_layout import HardwareLayout

from actors.config import ScadaSettings
from gwproto.enums import KindOfParam
from gwproto.types import KeyparamChangeLog

settings = ScadaSettings(_env_file=dotenv.find_dotenv())

layout = HardwareLayout.load(settings.paths.hardware_layout)
scada_alias = layout.layout["MyScadaGNode"]["Alias"]

author = input("Your name:\n")

key_param_name = input("Name of the key param: \n")

print("What kind of param is this?")
for val in KindOfParam.values():
    print(f"    {val}")

kind = input("Select one of the above\n")

before = input("Before\n")

after = input("After\n")

description = input("Description\n")


d = {
    "AboutNodeAlias": f"{scada_alias}",
    "ChangeTimeUtc": pendulum.now().format("YYYY-MM-DDTHH:mm:ss.SSS"),
    "Author": f"{author}",
    "ParamName": f"{key_param_name}",
    "Description": f"{description}",
    "KindGtEnumSymbol": f"{KindOfParam.value_to_symbol(kind)}",
    "Before": before,
    "After": after,
    "TypeName": "keyparam.change.log",
    "Version": "000",
}

print(d)
msg = KeyparamChangeLog.model_validate(d).model_dump(exclude_none=True)

print(msg)

s = input("Press any key to continue ...")

topic = f"gw/{scada_alias}/{c.TypeName}".replace(".", "-")

mqtt_command = (
    f"mosquitto_pub -h '{settings.gridworks_mqtt.host}' -p {settings.gridworks_mqtt.tls.port} \ \n"
    f"--cafile {settings.gridworks_mqtt.tls.paths.ca_cert_path} \ \n"
    f"--cert {settings.gridworks_mqtt.tls.paths.cert_path} \ \n"
    f"--key {settings.gridworks_mqtt.tls.paths.private_key_path} \ \n"
    f"-u '{settings.gridworks_mqtt.username}' -P '{settings.gridworks_mqtt.password.get_secret_value()}' \ \n"
    f"-t '{topic}' -m {msg}"
)


print("TRY SENDING THIS:\n")

print(mqtt_command)
