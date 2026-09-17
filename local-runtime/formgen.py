#!/usr/bin/env python3
"""Formgen-like terminal forms for Mini-ROLLS.

The COBOL corpus stays ACCEPT-based. This harness draws each .LAY as a boxed
TUI: the cursor sits inside [ ], typing edits that field, Tab/Enter moves to
the next field, and values stay visible on the form until SAVE or CANCEL.
"""
from pathlib import Path
import curses
import os
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
FORMS = ROOT / "forms"
BIN = ROOT / "bin"
LIST_TARGETS = {"ROLS6005", "ROLS6013", "ROLS6023"}
MIN_WIDTH = 52
LABEL_WIDTH = 14
CUS_REC = 46
PRD_REC = 52
LOOKUP_WIDTH = 32

# OpenVMS-style logical names. Production ROLLS uses HP COBOL ASSIGN TO
# logicals on the SIROL cluster. Local GnuCOBOL -std=cobol85 maps the same
# implementor-names to environment variables (no HP COBOL / OpenVMS license).
LOGICALS = {
    "ORDERS": str(ROOT / "data" / "orders.dat"),
    "CUSTOMERS": str(ROOT / "data" / "customers.dat"),
    "PRODUCTS": str(ROOT / "data" / "products.dat"),
    "HISTORY": str(ROOT / "data" / "order_history.dat"),
}


def apply_logicals(env=None):
    target = os.environ if env is None else env
    for name, path in LOGICALS.items():
        target.setdefault(name, path)
    return target


apply_logicals()


def _chunks(path, size):
    if not path.exists():
        return []
    data = path.read_bytes()
    n = len(data) - (len(data) % size)
    return [data[i : i + size] for i in range(0, n, size)]


def load_customers():
    items = []
    for rec in _chunks(Path(os.environ.get("CUSTOMERS", LOGICALS["CUSTOMERS"])), CUS_REC):
        items.append(
            {
                "id": rec[0:6].decode("ascii"),
                "label": rec[6:36].decode("ascii").rstrip(),
                "detail": rec[36:46].decode("ascii").rstrip(),
            }
        )
    return items


def load_products():
    items = []
    for rec in _chunks(Path(os.environ.get("PRODUCTS", LOGICALS["PRODUCTS"])), PRD_REC):
        cents = int(rec[36:45].decode("ascii") or "0")
        items.append(
            {
                "id": rec[0:6].decode("ascii"),
                "label": rec[6:36].decode("ascii").rstrip(),
                "detail": f"{cents / 100:.2f}",
            }
        )
    return items


def load_lookup(kind):
    if kind == "CUSTOMER":
        items = [row for row in load_customers() if row["detail"] == "ACTIVE"]
        return items or load_customers()
    if kind == "PRODUCT":
        return load_products()
    return []


def lookup_title(kind):
    if kind == "CUSTOMER":
        return "SELECT CUSTOMER"
    if kind == "PRODUCT":
        return "SELECT PRODUCT"
    return "SELECT"


def parse(name):
    path = FORMS / f"{name}.LAY"
    if not path.exists():
        raise SystemExit(f"Missing form: {path}")
    d = {"fields": [], "menus": [], "actions": [], "title": name}
    for line in path.read_text().splitlines():
        if not line.strip():
            continue
        k, *rest = line.split(" ", 1)
        val = rest[0] if rest else ""
        if k == "TITLE":
            d["title"] = val
        elif k == "FIELD":
            d["fields"].append(val.split("|"))
        elif k == "MENU":
            d["menus"].append(val.split("|"))
        elif k == "ACTION":
            d["actions"].append(val.split("|"))
    return d


def validate():
    errors = []
    for path in FORMS.glob("*.LAY"):
        for row in parse(path.stem)["menus"]:
            target = row[2]
            if target in ("BACK", "EXIT"):
                continue
            if not (FORMS / f"{target}.LAY").exists():
                errors.append(f"{path.name}: missing {target}.LAY")
    if errors:
        raise SystemExit("Form configuration errors:\n- " + "\n- ".join(errors))


class Field:
    def __init__(self, name, label, typ, extra):
        self.name = name
        self.label = label
        self.typ = typ
        self.lookup = extra if typ == "LOOKUP" else None
        self.length = LOOKUP_WIDTH if typ == "LOOKUP" else int(extra)
        self.text = ""
        self.choice_label = ""
        self.cursor = 0

    def display(self):
        if self.typ == "LOOKUP":
            shown = self.choice_label if self.choice_label else "(choose with Enter)"
            return (shown + " " * self.length)[: self.length]
        if self.typ == "NUMERIC":
            return self.text.zfill(self.length)[: self.length]
        return (self.text + " " * self.length)[: self.length]

    def submit_value(self):
        if self.typ == "LOOKUP":
            return self.text.zfill(6)
        if self.typ == "NUMERIC":
            return self.display()
        return self.text.rstrip()

    def set_choice(self, cid, label):
        self.text = cid
        self.choice_label = f"{cid} {label}".strip()

    def clear_choice(self):
        self.text = ""
        self.choice_label = ""

    def cursor_in_display(self):
        if self.typ == "LOOKUP":
            return 0
        if self.typ == "NUMERIC":
            return max(len(self.display()) - 1, 0)
        return min(self.cursor, max(self.length - 1, 0))

    def type_char(self, ch):
        if self.typ == "LOOKUP":
            return False, "Press Enter to choose from the list."
        if self.typ == "NUMERIC":
            if not ch.isdigit():
                return False, f"Enter up to {self.length} digits."
            if len(self.text) >= self.length:
                return False, f"Enter up to {self.length} digits."
            self.text += ch
            return True, ""
        if not ch.isprintable() or ch == "\t":
            return False, ""
        if len(self.text) >= self.length:
            return False, f"Enter up to {self.length} characters."
        self.text = self.text[: self.cursor] + ch + self.text[self.cursor :]
        self.text = self.text[: self.length]
        self.cursor = min(self.cursor + 1, self.length)
        return True, ""

    def backspace(self):
        if self.typ == "LOOKUP":
            self.clear_choice()
            return
        if self.typ == "NUMERIC":
            self.text = self.text[:-1]
            return
        if self.cursor <= 0:
            return
        self.text = self.text[: self.cursor - 1] + self.text[self.cursor :]
        self.cursor -= 1

    def move_left(self):
        if self.typ != "NUMERIC":
            self.cursor = max(0, self.cursor - 1)

    def move_right(self):
        if self.typ != "NUMERIC":
            self.cursor = min(self.cursor + 1, len(self.text), self.length)


class FormSession:
    def __init__(self, spec):
        self.title = spec.get("title", "")
        self.fields = [
            Field(name, label, typ, length)
            for name, label, typ, length in spec["fields"]
        ]
        self.actions = []
        for key, label, _target in spec["actions"]:
            if key == "LIST":
                continue
            self.actions.append({"key": key, "label": label.upper()})
        if self.fields and not any(a["key"] == "CANCEL" for a in self.actions):
            dismiss = (
                "BACK"
                if any("CANCEL" in a["label"] for a in self.actions)
                else "CANCEL"
            )
            self.actions.append({"key": "CANCEL", "label": dismiss})
        if not self.actions:
            self.actions.append({"key": "CANCEL", "label": "BACK"})
        self.focus = 0
        self.message = ""

    @property
    def widget_count(self):
        return len(self.fields) + len(self.actions)

    def focused_field(self):
        if self.focus < len(self.fields):
            return self.fields[self.focus]
        return None

    def focused_action(self):
        if self.focus >= len(self.fields):
            return self.actions[self.focus - len(self.fields)]
        return None

    def next_widget(self):
        if self.widget_count:
            self.focus = (self.focus + 1) % self.widget_count

    def prev_widget(self):
        if self.widget_count:
            self.focus = (self.focus - 1) % self.widget_count

    def validate_fields(self):
        for i, field in enumerate(self.fields):
            if field.typ == "LOOKUP":
                if not field.text.isdigit() or int(field.text) == 0:
                    self.focus = i
                    kind = "customer" if field.lookup == "CUSTOMER" else "product"
                    self.message = f"Choose a {kind} with Enter."
                    return False
            elif field.typ == "NUMERIC":
                if not field.text.isdigit() or len(field.text) > field.length:
                    self.focus = i
                    self.message = f"Enter up to {field.length} digits."
                    return False
            elif len(field.text) > field.length:
                self.focus = i
                self.message = f"Enter up to {field.length} characters."
                return False
        return True

    def handle(self, token):
        """Apply a logical key. Returns submit/cancel/lookup or None."""
        self.message = ""
        if token == "esc":
            return "cancel"
        if token in ("tab", "down"):
            self.next_widget()
            return None
        if token in ("btab", "up"):
            self.prev_widget()
            return None
        action = self.focused_action()
        if action:
            if token in ("enter", " "):
                if action["key"] == "CANCEL":
                    return "cancel"
                if not self.validate_fields():
                    return None
                return "submit"
            return None
        field = self.focused_field()
        if not field:
            return None
        if field.typ == "LOOKUP" and token in ("enter", " "):
            return "lookup"
        if token == "enter":
            self.next_widget()
            return None
        if token == "backspace":
            field.backspace()
            return None
        if token == "left":
            field.move_left()
            return None
        if token == "right":
            field.move_right()
            return None
        if token.startswith("char:"):
            ok, self.message = field.type_char(token[5:])
            if ok:
                self.message = ""
            return None
        return None

    def values(self):
        return [field.submit_value() for field in self.fields]


def _box(title, body_rows, width=None):
    width = max(
        [MIN_WIDTH, len(title) + 4] + [len(row) + 4 for row in body_rows] + ([width] if width else [])
    )
    inner = width - 4
    lines = [
        "+" + "-" * (width - 2) + "+",
        "| " + title.ljust(inner) + " |",
        "+" + "-" * (width - 2) + "+",
    ]
    for row in body_rows:
        lines.append("| " + row.ljust(inner) + " |")
    lines.append("+" + "-" * (width - 2) + "+")
    return lines, width


def layout_form(session):
    """Build boxed form lines and the terminal cursor position inside [ ]."""
    label_w = max([LABEL_WIDTH] + [len(f.label) for f in session.fields] or [LABEL_WIDTH])
    body = [""]
    field_meta = []
    for field in session.fields:
        prefix = f"{field.label:<{label_w}} : [ "
        row = f"{prefix}{field.display()} ]"
        field_meta.append((len(body), len(prefix), field))
        body.append(row)
    body.append("")
    btn_labels = [f"[ {a['label']} ]" for a in session.actions]
    btn_line = "   ".join(btn_labels)
    body.append(btn_line)
    lines, width = _box(session.title, body)
    inner = width - 4
    btn_index = len(lines) - 2
    lines[btn_index] = "| " + btn_line.center(inner) + " |"
    cursor = None
    lookup_span = None
    focused = session.focused_field()
    if focused is not None:
        row_in_body, prefix_len, field = field_meta[session.focus]
        y = 3 + row_in_body
        value = field.display()
        x0 = 2 + prefix_len - 2
        x1 = x0 + 2 + len(value) + 2
        if field.typ == "LOOKUP":
            lookup_span = (y, x0, x1)
        else:
            cursor = (y, 2 + prefix_len + field.cursor_in_display())
    button_spans = []
    btn_x = 2 + lines[btn_index].index(btn_line) if btn_line else 2
    pos = 0
    for i, label in enumerate(btn_labels):
        start = btn_x + pos
        button_spans.append((btn_index, start, start + len(label), i))
        pos += len(label) + (3 if i < len(btn_labels) - 1 else 0)
    if focused is not None and focused.typ == "LOOKUP":
        kind = "customer" if focused.lookup == "CUSTOMER" else "product"
        hint = f"Enter opens {kind} list    Tab next    Esc cancel"
    else:
        hint = "Tab/Enter next field    Esc cancel"
    return {
        "lines": lines,
        "width": width,
        "cursor": cursor,
        "button_spans": button_spans,
        "lookup_span": lookup_span,
        "hint": hint,
        "message": session.message,
    }


def layout_picker(title, items, selected):
    body = [""]
    for i, item in enumerate(items):
        marker = ">" if i == selected else " "
        extra = f"  {item['detail']}" if item.get("detail") else ""
        body.append(f"{marker} {item['id']}  {item['label']}{extra}")
    body.append("")
    lines, width = _box(title, body)
    hint = "Arrows move    Enter selects    Esc cancel"
    return {"lines": lines, "width": width, "hint": hint, "cursor": None}


def layout_menu(title, items, selected):
    body = [""]
    for i, (_key, label, _target) in enumerate(items):
        marker = ">" if i == selected else " "
        body.append(f"{marker} {_key}. {label}")
    body.append("")
    lines, width = _box(title, body)
    hint = "Arrows/Tab move    Enter selects    number jumps"
    return {"lines": lines, "width": width, "hint": hint, "cursor": None}


def layout_pager(title, text_lines, offset, view_h):
    view = text_lines[offset : offset + view_h]
    if not view:
        view = [""]
    while len(view) < min(view_h, 8):
        view.append("")
    body = [""] + view + ["", "[ OK ]"]
    lines, width = _box(title, body)
    return {"lines": lines, "width": width, "hint": "Enter/Esc back    Up/Down scroll", "cursor": None}


def execute(name, values=None):
    exe = BIN / f"ui-{name}"
    if not exe.exists():
        raise SystemExit(f"Missing executable: {exe}")
    data = "" if values is None else "\n".join(values) + "\n"
    env = apply_logicals(os.environ.copy())
    result = subprocess.run(
        [str(exe)], input=data, text=True, cwd=ROOT, capture_output=True, env=env
    )
    return result


def _token_from_key(key):
    if key in (9,):
        return "tab"
    if key == curses.KEY_BTAB:
        return "btab"
    if key in (curses.KEY_ENTER, 10, 13):
        return "enter"
    if key in (curses.KEY_BACKSPACE, 127, 8):
        return "backspace"
    if key == curses.KEY_LEFT:
        return "left"
    if key == curses.KEY_RIGHT:
        return "right"
    if key == curses.KEY_UP:
        return "up"
    if key == curses.KEY_DOWN:
        return "down"
    if key == 27:
        return "esc"
    if 32 <= key <= 126:
        return f"char:{chr(key)}"
    return None


def _draw(stdscr, layout, focus_button=None):
    stdscr.erase()
    max_y, max_x = stdscr.getmaxyx()
    lines = layout["lines"]
    if max_y < len(lines) + 3 or max_x < layout["width"]:
        msg = f"Terminal too small ({max_x}x{max_y}). Resize and retry."
        stdscr.addstr(0, 0, msg[: max(0, max_x - 1)])
        stdscr.refresh()
        return
    origin_y = max(0, (max_y - (len(lines) + 2)) // 2)
    origin_x = max(0, (max_x - layout["width"]) // 2)
    for i, line in enumerate(lines):
        attr = curses.A_BOLD if i == 1 else curses.A_NORMAL
        try:
            stdscr.addstr(origin_y + i, origin_x, line, attr)
        except curses.error:
            pass
    if focus_button is not None:
        for row, x0, x1, idx in layout.get("button_spans", []):
            if idx == focus_button:
                try:
                    stdscr.addstr(
                        origin_y + row,
                        origin_x + x0,
                        lines[row][x0:x1],
                        curses.A_REVERSE,
                    )
                except curses.error:
                    pass
    if layout.get("lookup_span"):
        row, x0, x1 = layout["lookup_span"]
        try:
            stdscr.addstr(
                origin_y + row,
                origin_x + x0,
                lines[row][x0:x1],
                curses.A_REVERSE,
            )
        except curses.error:
            pass
    footer_y = origin_y + len(lines)
    if layout.get("message"):
        try:
            stdscr.addstr(footer_y, origin_x, layout["message"][: layout["width"]], curses.A_BOLD)
        except curses.error:
            pass
        footer_y += 1
    if layout.get("hint"):
        try:
            stdscr.addstr(footer_y, origin_x, layout["hint"][: layout["width"]], curses.A_DIM)
        except curses.error:
            pass
    cursor = layout.get("cursor")
    if cursor is None:
        curses.curs_set(0)
    else:
        curses.curs_set(1)
        stdscr.move(origin_y + cursor[0], origin_x + cursor[1])
    stdscr.refresh()


def _wait_key(stdscr):
    while True:
        key = stdscr.getch()
        if key == curses.KEY_RESIZE:
            return "resize"
        return key


def run_pager(stdscr, title, text):
    lines = (text or "").splitlines() or ["(no output)"]
    offset = 0
    while True:
        max_y, _max_x = stdscr.getmaxyx()
        view_h = max(8, max_y - 10)
        layout = layout_pager(title, lines, offset, view_h)
        _draw(stdscr, layout, focus_button=0)
        key = _wait_key(stdscr)
        if key == "resize":
            continue
        token = _token_from_key(key) if key != "resize" else None
        if token in ("enter", "esc", " ") or (token == "char:" + "q"):
            return
        if token == "down":
            offset = min(max(0, len(lines) - 1), offset + 1)
        elif token == "up":
            offset = max(0, offset - 1)


def run_picker(stdscr, kind):
    items = load_lookup(kind)
    title = lookup_title(kind)
    if not items:
        run_pager(stdscr, title, f"No {kind.lower()}s found. Create one first.")
        return None
    selected = 0
    while True:
        layout = layout_picker(title, items, selected)
        _draw(stdscr, layout)
        key = _wait_key(stdscr)
        if key == "resize":
            continue
        token = _token_from_key(key)
        if token is None:
            continue
        if token in ("down", "tab"):
            selected = (selected + 1) % len(items)
            continue
        if token in ("up", "btab"):
            selected = (selected - 1) % len(items)
            continue
        if token == "esc":
            return None
        if token in ("enter", " "):
            return items[selected]


def run_form(stdscr, name):
    spec = parse(name)
    if name in LIST_TARGETS or (not spec["fields"] and spec["actions"]):
        result = execute(name)
        output = (result.stdout or "") + (result.stderr or "")
        if result.returncode:
            output = (output + f"\n{name} failed: {result.returncode}").strip()
        run_pager(stdscr, spec.get("title", name), output)
        return
    session = FormSession(spec)
    while True:
        layout = layout_form(session)
        action = session.focused_action()
        focus_button = None if action is None else session.focus - len(session.fields)
        _draw(stdscr, layout, focus_button=focus_button)
        key = _wait_key(stdscr)
        if key == "resize":
            continue
        token = _token_from_key(key)
        if token is None:
            continue
        outcome = session.handle(token)
        if outcome == "cancel":
            return
        if outcome == "lookup":
            field = session.focused_field()
            choice = run_picker(stdscr, field.lookup)
            if choice:
                field.set_choice(choice["id"], choice["label"])
            continue
        if outcome == "submit":
            result = execute(name, session.values())
            output = (result.stdout or "").strip()
            if result.stderr.strip():
                output = (output + "\n" + result.stderr.strip()).strip()
            if result.returncode:
                output = (output + f"\n{name} failed: {result.returncode}").strip()
            run_pager(stdscr, spec.get("title", name), output or "(no output)")
            return


def run_menu(stdscr, name):
    selected = 0
    while True:
        spec = parse(name)
        items = spec["menus"]
        selected = min(selected, max(len(items) - 1, 0))
        layout = layout_menu(spec.get("title", name), items, selected)
        _draw(stdscr, layout)
        key = _wait_key(stdscr)
        if key == "resize":
            continue
        token = _token_from_key(key)
        if token is None:
            continue
        if token in ("down", "tab"):
            selected = (selected + 1) % len(items)
            continue
        if token in ("up", "btab"):
            selected = (selected - 1) % len(items)
            continue
        if token == "esc":
            return "BACK" if name != "ROLS0001" else "EXIT"
        choice = None
        if token == "enter":
            choice = items[selected]
        elif token and token.startswith("char:"):
            ch = token[5:].upper()
            choice = next((row for row in items if row[0].upper() == ch), None)
            if choice:
                selected = items.index(choice)
        if not choice:
            continue
        target = choice[2]
        if target in ("BACK", "EXIT"):
            return target
        if target in LIST_TARGETS:
            run_form(stdscr, target)
            continue
        child = parse(target)
        if child["menus"]:
            if run_menu(stdscr, target) == "EXIT" and name == "ROLS0001":
                continue
            continue
        run_form(stdscr, target)


def main(stdscr):
    validate()
    curses.curs_set(1)
    curses.noecho()
    curses.cbreak()
    stdscr.keypad(True)
    try:
        curses.start_color()
        curses.use_default_colors()
    except curses.error:
        pass
    while True:
        if run_menu(stdscr, "ROLS0001") == "EXIT":
            break


if __name__ == "__main__":
    if not sys.stdin.isatty() or not sys.stdout.isatty():
        raise SystemExit("Mini-ROLLS forms need an interactive terminal. Run ./run.sh in a terminal.")
    curses.wrapper(main)
