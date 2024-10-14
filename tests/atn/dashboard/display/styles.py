from rich.style import Style
from rich.text import Text

cold_style = Style(bold=True, color="#008000")
hot_style = Style(bold=True, color="dark_orange")
none_text = Text("NA", style="cyan")
# hot_ansii = r"\033[31m"  # This red
# hot_ansii = r"\033[36m"  # temporary for Paul's purpose screen
# cold_ansii = r"\033[34m"
# cold_ansii = r"\033[36m"  # temporary for Paul's purpose screen
hot_ansii = f"[{hot_style}]"
cold_ansii = f"[{cold_style}]"