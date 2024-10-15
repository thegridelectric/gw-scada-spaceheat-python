from typing import Callable
from typing import Optional

from rich.style import Style
from rich.text import Text

misc_style = Style(bold=True, color="#008000")
cold_style = Style(bold=True, color="cyan1")
hot_style = Style(bold=True, color="dark_orange")
none_text = Text("NA", style=misc_style)

def temperature_color(
    degrees: float,
    graded_min: int = 32,
    graded_max: int = 100,
    cyan_ceiling: int = 40,
    cyan_graded_degrees: int = 8,
) -> str:
    num_graded_degrees = graded_max - graded_min
    red_graded_degrees = max(min(degrees - graded_min, num_graded_degrees), 0)
    red_fraction = red_graded_degrees / num_graded_degrees
    red = int(red_fraction * 255)
    blue = int((1 - red_fraction) * 255)
    if degrees <= cyan_ceiling:
        green_graded_degrees = min(abs(cyan_ceiling - degrees), cyan_graded_degrees)
        green_fraction =  green_graded_degrees / cyan_graded_degrees
        green = int(green_fraction * 255)
    else:
        green = 0
    return f"#{red:02X}{green:02X}{blue:02X}"

def fahrenheit_color(fahrenheit: float) -> str:
    return temperature_color(
        fahrenheit,
        graded_min=32,
        graded_max=100,
        cyan_ceiling=40,
        cyan_graded_degrees=8,
    )

def celcius_color(fahrenheit: float) -> str:
    return temperature_color(
        fahrenheit,
        graded_min=0,
        graded_max=100,
        cyan_ceiling=6,
        cyan_graded_degrees=6,
    )

def tank_color(fahrenheit: float) -> str:
    return temperature_color(
        fahrenheit,
        graded_min=32,
        graded_max=210,
        cyan_ceiling=32,
        cyan_graded_degrees=8,
    )


def markup_temperature(
    temperature: Optional[float],
    style_generator: Callable[[float | int], str] | str | Style = fahrenheit_color,
    *,
    unit_str: str = "F",
    number_format_str: str = "{temperature:5.1f}",
) -> str:
    if isinstance(style_generator, (str, Style)):
        style = style_generator
    else:
        style = style_generator(temperature)
    if temperature is None:
        degree_str = " --- "
    else:
        degree_str = number_format_str.format(temperature=temperature)
    return Text(f"{degree_str}°{unit_str}", style=style).markup

def markup_tank_temperature(
    temperature: float,
):
    return markup_temperature(temperature, style_generator=tank_color)