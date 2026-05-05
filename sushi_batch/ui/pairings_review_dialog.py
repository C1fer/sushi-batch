from typing import Any, Callable, Sequence

from prompt_toolkit import Application
from prompt_toolkit.application import get_app
from prompt_toolkit.formatted_text.base import StyleAndTextTuples
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.key_binding.key_processor import KeyPressEvent
from prompt_toolkit.keys import Keys
from prompt_toolkit.layout import HSplit, Window
from prompt_toolkit.layout.controls import FormattedTextControl
from prompt_toolkit.layout.layout import Layout
from prompt_toolkit.mouse_events import MouseEvent, MouseEventType, MouseModifier
from prompt_toolkit.styles import BaseStyle, Style, merge_styles
from prompt_toolkit.widgets import Button, Dialog, HorizontalLine, Label, RadioList

from ..utils.constants import CustomColor

DEFAULT_TOOLBAR = "  Up/Down / Click: Select | Left/Right / Ctrl+Up/Down / Ctrl+Wheel: Reorder | Tab: Change Focus | Enter: Confirm  \n\n"

DEFAULT_STYLE: Style = Style.from_dict({
    "dialog": f"bg:{CustomColor.BG_DARK}",
    "dialog frame.label": f"fg:{CustomColor.ACCENT} bold",
    "dialog frame.border": f"fg:{CustomColor.MUTED}",
    "dialog.body": f"fg:{CustomColor.TEXT} bg:{CustomColor.BG_DARK}",
    "horizontal-line": f"fg:{CustomColor.MUTED}",
    "vertical-line": f"fg:{CustomColor.MUTED}",
    "button": f"fg:{CustomColor.ACCENT} bold",
    "button.focused": f"bg:{CustomColor.BG_DARKER} bold",
    "radio-list": f"fg:{CustomColor.MUTED}",
    "radio": "",
    "radio-checked": f"fg:{CustomColor.ACCENT}",
    "radio-selected": "bold",
    "radio-checked-selected": f"fg:{CustomColor.ACCENT}",
    "selected": "bold",
    "message": f"fg:{CustomColor.TEXT}",
    "instructions": f"fg:{CustomColor.MUTED} bg:{CustomColor.BG_DARKER} bold",
})

DEFAULT_TEXT: StyleAndTextTuples = [
    ("class:instructions", DEFAULT_TOOLBAR),
    ("class:message", ""),
]


_reordered_radios: tuple[RadioList[Any], RadioList[Any], RadioList[Any] | None] | None = None

def _move_item(radio: RadioList[Any], app: Application[Any], delta: int) -> None:
    """Swap the selected row with its neighbor; keep focus on the same item."""
    raw: Sequence[Any] = radio.values
    if not isinstance(raw, list) or len(raw) < 2:
        return
    values: list[Any] = raw
    curr_pos: int = radio._selected_index
    new_pos: int = curr_pos + delta
    if new_pos < 0 or new_pos >= len(values):
        return
    values[curr_pos], values[new_pos] = values[new_pos], values[curr_pos]
    radio._selected_index = new_pos
    app.invalidate()


def _attach_ctrl_wheel_reorder(radio: RadioList[Any]) -> None:
    """Ctrl+scroll over a column reorders rows in that column (same as keyboard)."""
    control: FormattedTextControl = radio.control
    prev_mouse = control.mouse_handler

    def mouse_handler(mouse_event: MouseEvent) ->object:
        if (
            mouse_event.event_type
            in (MouseEventType.SCROLL_UP, MouseEventType.SCROLL_DOWN)
            and MouseModifier.CONTROL in mouse_event.modifiers
        ):
            app: Application[Any] = get_app()
            delta: int = (
                -1
                if mouse_event.event_type == MouseEventType.SCROLL_UP
                else 1
            )
            _move_item(radio, app, delta)
            return None
        return prev_mouse(mouse_event)

    control.mouse_handler: Callable[[MouseEvent], object] = mouse_handler


kb = KeyBindings()

@kb.add(Keys.Left)
@kb.add(Keys.ControlUp)
@kb.add(Keys.Right)
@kb.add(Keys.ControlDown)
def _handle_move_trigger(event: KeyPressEvent) -> None:
    if _reordered_radios is None:
        return

    delta: int = -1 if event.key_sequence[0].key in (Keys.Left, Keys.ControlUp) else 1
    radio_src, radio_dst, radio_sub = _reordered_radios
    w: Window = event.app.layout.current_window
    if w is radio_src.window:
        _move_item(radio_src, event.app, delta)
    elif w is radio_dst.window:
        _move_item(radio_dst, event.app, delta)
    elif radio_sub and w is radio_sub.window:
        _move_item(radio_sub, event.app, delta)

def _get_section(description: str, radio: RadioList[Any]) -> HSplit:
    return HSplit(
        children=[
            Label(text=description),
            radio,
        ],
        padding=1,
    )

def _create_radio_section(filepaths: list[str]) -> RadioList[Any]:
    return  RadioList(
        values= [(str(i), filepath) for i, filepath in enumerate(filepaths)], 
        open_character="", 
        select_character="*", 
        close_character="",
        select_on_focus=True,
        show_numbers=True,
    )

def _get_filepaths() -> tuple[list[str], list[str], list[str]]:
    if _reordered_radios is None:
        return ([], [], [])
    radio_src, radio_dst, radio_sub = _reordered_radios

    src_filepaths: list[str] = [str(filepath) for _, filepath in radio_src.values]
    dst_filepaths: list[str] = [str(filepath) for _, filepath in radio_dst.values]
    sub_filepaths: list[str] = [str(filepath) for _, filepath in radio_sub.values] if radio_sub else []
    return src_filepaths, dst_filepaths, sub_filepaths

def _get_dialog(src_files: list[str], dst_files: list[str], sub_files: list[str]) -> Application[Any]:
    """Display the file pairings review dialog and handle user interactions."""
    global _reordered_radios

    def exit_handler() -> None:
        _reordered_radios = None
        get_app().exit(result=None)

    def ok_handler() -> None:
        result: tuple[list[str], list[str], list[str]] = _get_filepaths()
        _reordered_radios = None
        get_app().exit(result=result)

    radio_src: RadioList[Any] = _create_radio_section(src_files)
    radio_dst: RadioList[Any] = _create_radio_section(dst_files)
    radio_sub: RadioList[Any] | None = _create_radio_section(sub_files) if sub_files else None
    _reordered_radios = (radio_src, radio_dst, radio_sub)

    _attach_ctrl_wheel_reorder(radio_src)
    _attach_ctrl_wheel_reorder(radio_dst)
    if radio_sub:
        _attach_ctrl_wheel_reorder(radio_sub)

    _style: BaseStyle = merge_styles([DEFAULT_STYLE])

    item_container = HSplit(
        children=[
            _get_section("Source Files", radio_src),
            HorizontalLine(),
            _get_section("Target Files", radio_dst),
            *([HorizontalLine(), _get_section("Subtitle Files", radio_sub)] if radio_sub else []),
        ],
    )

    help_window = Window(content=FormattedTextControl(text=DEFAULT_TEXT), height=2)

    dialog = Dialog(
        title="Review File Pairings",
        body=HSplit(
            children=[help_window, item_container], 
            padding=1,
        ),
        buttons=[
            Button(text="OK", handler=ok_handler),
            Button(text="Exit", handler=exit_handler),
        ],
        with_background=True,
    )

    return Application(
        layout=Layout(dialog),
        full_screen=True,
        key_bindings=kb,
        style=_style,
        mouse_support=True,
    )

def show_file_pairings_review_dialog(src_files: list[str], dst_files: list[str], sub_files: list[str]) -> tuple[list[str], list[str], list[str]] | None:
    return _get_dialog(src_files, dst_files, sub_files).run()