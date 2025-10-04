import asyncio
import base64
import os
import shlex
import pyautogui
from enum import StrEnum
from pathlib import Path
from typing import Literal, TypedDict
from uuid import uuid4

from anthropic.types.beta import BetaToolComputerUse20250124Param

from .base import BaseAnthropicTool, ToolError, ToolResult
from .run import run

OUTPUT_DIR = "/tmp/outputs"

TYPING_DELAY_MS = 12
TYPING_GROUP_SIZE = 50

Action = Literal[
    "key",
    "type",
    "mouse_move",
    "left_click",
    "left_click_drag",
    "right_click",
    "middle_click",
    "double_click",
    "triple_click",
    "screenshot",
    "cursor_position",
    "scroll",
    "left_mouse_down",
    "left_mouse_up",
    "hold_key",
    "wait",
]


class Resolution(TypedDict):
    width: int
    height: int


# sizes above XGA/WXGA are not recommended (see README.md)
# scale down to one of these targets if ComputerTool._scaling_enabled is set
MAX_SCALING_TARGETS: dict[str, Resolution] = {
    "XGA": Resolution(width=1024, height=768),  # 4:3
    "WXGA": Resolution(width=1280, height=800),  # 16:10
    "FWXGA": Resolution(width=1366, height=768),  # ~16:9
}
SCALE_DESTINATION = MAX_SCALING_TARGETS["FWXGA"]


class ScalingSource(StrEnum):
    COMPUTER = "computer"
    API = "api"


class ComputerToolOptions(TypedDict):
    display_height_px: int
    display_width_px: int
    display_number: int | None


def chunks(s: str, chunk_size: int) -> list[str]:
    return [s[i : i + chunk_size] for i in range(0, len(s), chunk_size)]


class ComputerTool(BaseAnthropicTool):
    """
    A tool that allows the agent to interact with the screen, keyboard, and mouse of the current macOS computer.
    The tool parameters are defined by Anthropic and are not editable.
    Requires cliclick to be installed: brew install cliclick
    """

    name: Literal["computer"] = "computer"
    api_type: Literal["computer_20250124"] = "computer_20250124"
    width: int
    height: int
    display_num: int | None

    _screenshot_delay = 1.0  # macOS is generally faster than X11
    _scaling_enabled = True

    @property
    def options(self) -> ComputerToolOptions:
        return {
            "display_width_px": self.width,
            "display_height_px": self.height,
            "display_number": self.display_num,
        }

    def to_params(self) -> BetaToolComputerUse20250124Param:
        return {"name": self.name, "type": self.api_type, **self.options}

    def __init__(self):
        super().__init__()

        self.width, self.height = pyautogui.size()
        assert self.width and self.height, "WIDTH, HEIGHT must be set"
        self.display_num = None  # macOS doesn't use X11 display numbers

    async def __call__(
        self,
        *,
        action: Action,
        text: str | None = None,
        coordinate: tuple[int, int] | None = None,
        **kwargs,
    ):
        print("Action: ", action, text, coordinate)
        if action in ("mouse_move", "left_click_drag"):
            if coordinate is None:
                raise ToolError(f"coordinate is required for {action}")
            if text is not None:
                raise ToolError(f"text is not accepted for {action}")
            if not isinstance(coordinate, list) or len(coordinate) != 2:
                raise ToolError(f"{coordinate} must be a tuple of length 2")
            if not all(isinstance(i, int) and i >= 0 for i in coordinate):
                raise ToolError(f"{coordinate} must be a tuple of non-negative ints")

            x, y = self.scale_coordinates(ScalingSource.API, coordinate[0], coordinate[1])

            if action == "mouse_move":
                return await self.shell(f"cliclick m:{x},{y}", take_screenshot=True)
            elif action == "left_click_drag":
                return await self.shell(f"cliclick dd:{x},{y}", take_screenshot=True)

        if action in ("key", "type"):
            if text is None:
                raise ToolError(f"text is required for {action}")
            if coordinate is not None:
                raise ToolError(f"coordinate is not accepted for {action}")
            if not isinstance(text, str):
                raise ToolError(output=f"{text} must be a string")

            if action == "key":
                # Map special keys to cliclick key codes
                special_keys_map = {
                    "Return": "return",
                    "return": "return",
                    "enter": "return",
                    "space": "space",
                    "Tab": "tab",
                    "tab": "tab",
                    "Left": "arrow-left",
                    "left": "arrow-left",
                    "Right": "arrow-right",
                    "right": "arrow-right",
                    "Up": "arrow-up",
                    "up": "arrow-up",
                    "Down": "arrow-down",
                    "down": "arrow-down",
                    "Escape": "esc",
                    "escape": "esc",
                    "esc": "esc",
                    "delete": "delete",
                    "backspace": "delete",
                    "home": "home",
                    "end": "end",
                    "pageup": "page-up",
                    "pagedown": "page-down",
                    "f1": "f1", "f2": "f2", "f3": "f3", "f4": "f4",
                    "f5": "f5", "f6": "f6", "f7": "f7", "f8": "f8",
                    "f9": "f9", "f10": "f10", "f11": "f11", "f12": "f12",
                }

                try:
                    # Use cliclick for all key operations
                    if "+" in text:
                        keys = text.split("+")
                        modifiers = [k.strip() for k in keys[:-1]]
                        target_key = keys[-1].strip()

                        # Convert modifiers to cliclick format
                        cliclick_modifiers = []
                        for mod in modifiers:
                            if mod in ["cmd", "command"]:
                                cliclick_modifiers.append("cmd")
                            elif mod == "ctrl":
                                cliclick_modifiers.append("ctrl")
                            elif mod == "alt":
                                cliclick_modifiers.append("alt")
                            elif mod == "shift":
                                cliclick_modifiers.append("shift")

                        # Check if target key is a special key
                        if target_key.lower() in special_keys_map:
                            key_code = special_keys_map[target_key.lower()]
                            key_action = f"kp:{key_code}"
                        else:
                            # Regular letter/number key - use type
                            key_action = f"t:{target_key}"

                        if cliclick_modifiers:
                            cmd_parts = [f"kd:{','.join(cliclick_modifiers)}", key_action, f"ku:{','.join(cliclick_modifiers)}"]
                            cmd = "cliclick " + " ".join(cmd_parts)
                        else:
                            cmd = f"cliclick {key_action}"
                    else:
                        # Single key press
                        if text.lower() in special_keys_map:
                            # Special key - use key press
                            key_code = special_keys_map[text.lower()]
                            cmd = f"cliclick kp:{key_code}"
                        else:
                            # Regular letter/number/symbol - use type
                            cmd = f"cliclick t:{text}"

                    return await self.shell(cmd, take_screenshot=True)

                except Exception as e:
                    return ToolResult(output=None, error=str(e), base64_image=None)
            elif action == "type":
                results: list[ToolResult] = []
                for chunk in chunks(text, TYPING_GROUP_SIZE):
                    cmd = f"cliclick w:{TYPING_DELAY_MS} t:{shlex.quote(chunk)}"
                    results.append(await self.shell(cmd, take_screenshot=False))
                screenshot_base64 = (await self.screenshot()).base64_image
                return ToolResult(
                    output="".join(result.output or "" for result in results),
                    error="".join(result.error or "" for result in results),
                    base64_image=screenshot_base64,
                )

        if action in (
            "left_click",
            "right_click",
            "double_click",
            "triple_click",
            "middle_click",
            "left_mouse_down",
            "left_mouse_up",
            "screenshot",
            "cursor_position",
        ):
            if text is not None:
                raise ToolError(f"text is not accepted for {action}")
            if coordinate is not None:
                raise ToolError(f"coordinate is not accepted for {action}")

            if action == "screenshot":
                return await self.screenshot()
            elif action == "cursor_position":
                result = await self.shell(
                    "cliclick p",
                    take_screenshot=False,
                )
                if result.output:
                    x, y = map(int, result.output.strip().split(","))
                    x, y = self.scale_coordinates(ScalingSource.COMPUTER, x, y)
                    return result.replace(output=f"X={x},Y={y}")
                return result
            else:
                click_cmd = {
                    "left_click": "c:.",
                    "right_click": "rc:.",
                    "middle_click": "mc:.",
                    "double_click": "dc:.",
                    "triple_click": "tc:.",
                    "left_mouse_down": "md:.",
                    "left_mouse_up": "mu:.",
                }[action]
                return await self.shell(f"cliclick {click_cmd}", take_screenshot=True)

        if action == "scroll":
            if coordinate is None:
                raise ToolError("coordinate is required for scroll action")
            if not isinstance(coordinate, list) or len(coordinate) != 2:
                raise ToolError(f"{coordinate} must be a tuple of length 2")
            if not all(isinstance(i, int) and i >= 0 for i in coordinate):
                raise ToolError(f"{coordinate} must be a tuple of non-negative ints")

            x, y = self.scale_coordinates(ScalingSource.API, coordinate[0], coordinate[1])

            # Get scroll parameters from kwargs
            scroll_direction = kwargs.get("scroll_direction", "down")
            scroll_amount = kwargs.get("scroll_amount", 5)

            # Map direction to scroll amount with sign
            direction_multiplier = {
                "down": -1,
                "up": 1,
                "left": 1,
                "right": -1,
            }.get(scroll_direction, -1)

            # cliclick scroll format: w:x,y (scroll with amount at position)
            # Positive values scroll up/left, negative values scroll down/right
            scroll_value = scroll_amount * direction_multiplier

            if scroll_direction in ["up", "down"]:
                cmd = f"cliclick m:{x},{y} w:{scroll_value}"
            else:
                # For horizontal scrolling, use shift+scroll
                cmd = f"cliclick m:{x},{y} kd:shift w:{scroll_value} ku:shift"

            return await self.shell(cmd, take_screenshot=True)

        if action == "hold_key":
            if text is None:
                raise ToolError("text is required for hold_key action")

            # Map key names to cliclick format
            key_map = {
                "command": "cmd",
                "cmd": "cmd",
                "ctrl": "ctrl",
                "alt": "alt",
                "shift": "shift",
            }

            key = key_map.get(text.lower(), text.lower())

            # Hold key down (note: this will remain held until key up)
            cmd = f"cliclick kd:{key}"
            return await self.shell(cmd, take_screenshot=True)

        if action == "wait":
            # Get duration from kwargs, default to 1 second
            duration = kwargs.get("duration", 1.0)
            if not isinstance(duration, (int, float)) or duration < 0:
                raise ToolError("duration must be a non-negative number")

            await asyncio.sleep(duration)

            # Take screenshot after waiting
            screenshot_result = await self.screenshot()
            return ToolResult(
                output=f"Waited for {duration} seconds",
                error=None,
                base64_image=screenshot_result.base64_image
            )

        raise ToolError(f"Invalid action: {action}")

    async def screenshot(self):
        """Take a screenshot of the current screen and return the base64 encoded image."""
        output_dir = Path(OUTPUT_DIR)
        output_dir.mkdir(parents=True, exist_ok=True)
        path = output_dir / f"screenshot_{uuid4().hex}.png"

        # Use macOS native screencapture
        screenshot_cmd = f"screencapture -x {path}"
        result = await self.shell(screenshot_cmd, take_screenshot=False)

        if self._scaling_enabled:
            x, y = SCALE_DESTINATION['width'], SCALE_DESTINATION['height']
            await self.shell(
                f"sips -z {y} {x} {path}",  # sips is macOS native image processor
                take_screenshot=False
            )

        if path.exists():
            return result.replace(
                base64_image=base64.b64encode(path.read_bytes()).decode()
            )
        raise ToolError(f"Failed to take screenshot: {result.error}")

    async def shell(self, command: str, take_screenshot=False) -> ToolResult:
        """Run a shell command and return the output, error, and optionally a screenshot."""
        _, stdout, stderr = await run(command)
        base64_image = None

        if take_screenshot:
            # delay to let things settle before taking a screenshot
            await asyncio.sleep(self._screenshot_delay)
            base64_image = (await self.screenshot()).base64_image

        return ToolResult(output=stdout, error=stderr, base64_image=base64_image)

    def scale_coordinates(self, source: ScalingSource, x: int, y: int) -> tuple[int, int]:
        """
        Scale coordinates between original resolution and target resolution (SCALE_DESTINATION).

        Args:
            source: ScalingSource.API for scaling up from SCALE_DESTINATION to original resolution
                   or ScalingSource.COMPUTER for scaling down from original to SCALE_DESTINATION
            x, y: Coordinates to scale

        Returns:
            Tuple of scaled (x, y) coordinates
        """
        if not self._scaling_enabled:
            return x, y

        # Calculate scaling factors
        x_scaling_factor = SCALE_DESTINATION['width'] / self.width
        y_scaling_factor = SCALE_DESTINATION['height'] / self.height

        if source == ScalingSource.API:
            # Scale up from SCALE_DESTINATION to original resolution
            if x > SCALE_DESTINATION['width'] or y > SCALE_DESTINATION['height']:
                raise ToolError(f"Coordinates {x}, {y} are out of bounds for {SCALE_DESTINATION['width']}x{SCALE_DESTINATION['height']}")
            return round(x / x_scaling_factor), round(y / y_scaling_factor)
        else:
            # Scale down from original resolution to SCALE_DESTINATION
            return round(x * x_scaling_factor), round(y * y_scaling_factor)
