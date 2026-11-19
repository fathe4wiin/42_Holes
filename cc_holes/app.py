"""Dark red and black terminal UI."""

from pathlib import Path

from rich.text import Text
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical, VerticalScroll
from textual.screen import Screen
from textual.widgets import Button, DataTable, Footer, Input, ListItem, ListView, RichLog, Static

from cc_holes.catalog import CatalogError, load_catalog
from cc_holes.guide import CREDITS, GUIDE, LOGO, TAGLINE
from cc_holes.py_run import PY_MODULES
from cc_holes.runner import Done, Log, Plan, RunControl, Update, run_project

CSS = """
Screen {
    background: #070000;
    color: #f4e8e8;
}
#hero {
    padding: 1 2 0 2;
    color: #ff5555;
    text-style: bold;
}
.sub {
    color: #c9a3a3;
    padding: 0 2 1 2;
}
ListView {
    background: #140606;
    border: solid #6e1414;
}
#projects {
    margin: 0 2 1 2;
    height: 1fr;
}
ListItem {
    height: auto;
    padding: 1 1;
}
ListView > ListItem.-highlight,
ListView > ListItem.--highlight {
    background: #5a1010;
    color: #fff5f5;
}
.item {
    height: auto;
}
Input {
    background: #120303;
    color: #fff4f4;
    border: solid #8d1f1f;
    margin: 0 2 1 2;
}
Input:focus {
    border: solid #ff4d4d;
}
Button {
    background: #6d1212;
    color: #fff2f2;
    border: none;
    margin: 0 1 0 0;
}
Button:hover {
    background: #9a1c1c;
}
Button:disabled {
    background: #2a1212;
    color: #806868;
}
#actions {
    height: auto;
    padding: 0 2 1 2;
}
#table {
    height: 1fr;
    margin: 0 2;
    background: #100202;
}
#detail {
    height: 10;
    margin: 0 2 1 2;
    background: #100202;
    border: solid #6e1414;
    color: #f0d6d6;
}
Header, Footer {
    background: #2a0000;
    color: #f0d0d0;
}
DataTable > .datatable--header,
DataTable > .datatable--header-cell {
    background: #2a0808;
    color: #ffb4b4;
}
DataTable > .datatable--cursor {
    background: #4a0d0d;
}
#stage {
    align: center middle;
    width: 100%;
    height: 1fr;
}
#window {
    width: 76;
    height: 27;
    max-width: 94%;
    max-height: 90%;
    background: #120404;
    border: solid #8d1f1f;
}
#brand {
    height: 60%;
    align: center middle;
    content-align: center middle;
}
#ascii {
    width: auto;
    height: auto;
    color: #ff4444;
    text-align: center;
    text-style: bold;
}
#tagline {
    width: 100%;
    height: auto;
    margin-top: 1;
    color: #d7b4b4;
    text-align: center;
}
#menu-slot {
    height: 40%;
    align: center middle;
    padding: 0 2 1 2;
}
#dash-menu {
    width: 42;
    height: auto;
    max-height: 100%;
    background: transparent;
    border: none;
    padding: 0;
}
#dash-menu ListItem {
    height: 1;
    padding: 0 1;
    color: #f4e8e8;
}
#dash-menu ListItem.-highlight {
    background: #5a1010;
    color: #ffffff;
    text-style: bold;
}
#guide-scroll, #credits-scroll {
    height: 1fr;
    margin: 0 2 1 2;
    padding: 1 2;
    background: #120404;
    border: solid #6e1414;
}
#guide-body, #credits-body {
    height: auto;
    color: #f0d6d6;
}
"""


def normalize(text: str) -> Path:
    path = Path(text.strip()).expanduser()
    if not path.is_absolute():
        path = Path.cwd() / path
    return path


_CIRCLE_00 = ("libft",)
_CIRCLE_01 = ("get_next_line", "ft_printf", "push_swap")
_READY = set(_CIRCLE_00) | set(_CIRCLE_01) | {item.name for item in PY_MODULES}
_PLACEHOLDER = {
    "libft": "/home/you/libft",
    "ft_printf": "/home/you/ft_printf",
    "get_next_line": "/home/you/get_next_line",
    "push_swap": "/home/you/push_swap",
}
_SUBJECT_LABEL = {
    "libft": "subject v19.2",
    "ft_printf": "subject v12.1",
    "get_next_line": "subject v14.3",
    "push_swap": "subject v1.2",
}
for _module in PY_MODULES:
    _PLACEHOLDER[_module.name] = f"/home/you/{_module.name}"
    _SUBJECT_LABEL[_module.name] = f"{_module.title} · subject v{_module.version}"


def path_problem(path: Path, project: str | None = None) -> str:
    if not str(path).strip() or path == Path.cwd() / "":
        return ""
    if not path.exists():
        return "That folder does not exist."
    if not path.is_dir():
        return "That path is a file. Pass the project folder."
    if project == "get_next_line":
        if (path / "get_next_line.c").is_file() and (path / "get_next_line.h").is_file():
            return ""
        return "get_next_line.c and get_next_line.h were not found in that folder."
    if project in {item.name for item in PY_MODULES}:
        return ""
    names = ("Makefile", "makefile", "GNUmakefile")
    if not any((path / name).is_file() for name in names):
        return "No Makefile in that folder."
    return ""


class MenuList(ListView):
    """Arrow keys move. a, g, c, and q stay on the screen."""

    BINDINGS = [
        Binding("up", "cursor_up", show=False),
        Binding("down", "cursor_down", show=False),
        Binding("left", "cursor_up", show=False),
        Binding("right", "cursor_down", show=False),
        Binding("enter", "select_cursor", show=False),
    ]


class MenuItem(ListItem):
    def __init__(self, key: str, label: str, action: str) -> None:
        super().__init__(Static(f"{key}   {label}"))
        self.menu_action = action


class HomeScreen(Screen):
    BINDINGS = [
        Binding("a", "tests", "Available tests", priority=True),
        Binding("g", "guide", "Use guide", priority=True),
        Binding("c", "credits", "Credits", priority=True),
        Binding("q", "quit", "Quit", priority=True),
    ]

    def compose(self) -> ComposeResult:
        with Vertical(id="stage"):
            with Vertical(id="window"):
                with Vertical(id="brand"):
                    yield Static(LOGO, id="ascii")
                    yield Static(TAGLINE, id="tagline")
                with Vertical(id="menu-slot"):
                    yield MenuList(
                        MenuItem("a", "Available tests", "tests"),
                        MenuItem("g", "Use guide", "guide"),
                        MenuItem("c", "Credits", "credits"),
                        MenuItem("q", "Quit", "quit"),
                        id="dash-menu",
                    )
        yield Footer()

    def on_mount(self) -> None:
        menu = self.query_one("#dash-menu", MenuList)
        menu.index = 0
        menu.focus()

    def on_list_view_selected(self, event: ListView.Selected) -> None:
        item = event.item
        if isinstance(item, MenuItem):
            getattr(self, f"action_{item.menu_action}")()

    def action_tests(self) -> None:
        self.app.push_screen(CircleScreen())

    def action_guide(self) -> None:
        self.app.push_screen(GuideScreen())

    def action_credits(self) -> None:
        self.app.push_screen(CreditsScreen())

    def action_quit(self) -> None:
        self.app.exit()


class GuideScreen(Screen):
    BINDINGS = [
        Binding("escape", "back", "Back"),
        Binding("q", "quit", "Quit"),
    ]

    def compose(self) -> ComposeResult:
        yield Static("Use guide", id="hero")
        yield Static("Skip, calls, and how a result is judged.", classes="sub")
        with VerticalScroll(id="guide-scroll"):
            yield Static(GUIDE, id="guide-body")
        yield Footer()

    def action_back(self) -> None:
        self.app.pop_screen()


class CreditsScreen(Screen):
    BINDINGS = [
        Binding("escape", "back", "Back"),
        Binding("q", "quit", "Quit"),
    ]

    def compose(self) -> ComposeResult:
        yield Static("Credits", id="hero")
        with VerticalScroll(id="credits-scroll"):
            yield Static(CREDITS, id="credits-body")
        yield Footer()

    def action_back(self) -> None:
        self.app.pop_screen()


class ProjectItem(ListItem):
    def __init__(self, project: str, meta: str) -> None:
        super().__init__(Static(f"{project}\n{meta}", classes="item"))
        self.project = project


class CircleItem(ListItem):
    def __init__(self, circle: str, title: str, meta: str) -> None:
        super().__init__(Static(f"{circle}   {title}\n{meta}", classes="item"))
        self.circle = circle


class CircleScreen(Screen):
    BINDINGS = [
        Binding("escape", "back", "Back"),
        Binding("q", "quit", "Quit"),
    ]

    def compose(self) -> ComposeResult:
        yield Static("Available tests", id="hero")
        yield Static("Pick a circle.", id="status", classes="sub")
        yield ListView(
            CircleItem("00", "Circle 00", "libft · subject v19.2"),
            CircleItem(
                "01",
                "Circle 01",
                "get_next_line v14.3 · ft_printf v12.1 · push_swap v1.2",
            ),
            CircleItem("02", "Circle 02", "Python modules"),
            id="projects",
        )
        yield Footer()

    def on_mount(self) -> None:
        view = self.query_one("#projects", ListView)
        if view.children:
            view.index = 0
        view.focus()

    def action_back(self) -> None:
        self.app.pop_screen()

    def on_list_view_selected(self, event: ListView.Selected) -> None:
        item = event.item
        if not isinstance(item, CircleItem):
            return
        if item.circle == "02":
            self.app.push_screen(PythonScreen())
            return
        projects = _CIRCLE_00 if item.circle == "00" else _CIRCLE_01
        self.app.push_screen(ProjectScreen(item.circle, projects))


class ProjectScreen(Screen):
    BINDINGS = [
        Binding("escape", "back", "Back"),
        Binding("q", "quit", "Quit"),
    ]

    def __init__(self, circle: str, projects: tuple[str, ...]) -> None:
        super().__init__()
        self.circle = circle
        self.projects = projects

    def compose(self) -> ComposeResult:
        yield Static(f"Circle {self.circle}", id="hero")
        yield Static("Loading tests…", id="status", classes="sub")
        yield ListView(id="projects")
        yield Footer()

    def on_mount(self) -> None:
        self.run_worker(self._load, thread=True, exclusive=True)

    def _load(self) -> None:
        counts: dict = {}
        try:
            catalog = load_catalog()
        except CatalogError:
            catalog = None
        else:
            self.app.catalog = catalog
            counts = catalog.get("counts", {}).get("by_project", {})
        self.app.call_from_thread(self._ready, counts)

    def _ready(self, counts: dict) -> None:
        view = self.query_one("#projects", ListView)
        for name in self.projects:
            label = _SUBJECT_LABEL[name]
            if name in counts:
                label = f"{counts[name]} catalog rows · {label}"
            view.append(ProjectItem(name, label))
        self.query_one("#status", Static).update("Pick a project. Enter opens it.")
        if view.children:
            view.index = 0
        view.focus()

    def action_back(self) -> None:
        self.app.pop_screen()

    def on_list_view_selected(self, event: ListView.Selected) -> None:
        item = event.item
        if isinstance(item, ProjectItem):
            self.app.push_screen(PathScreen(item.project))


class PythonScreen(Screen):
    """Circle 02 is its own window. More modules are appended to PY_MODULES."""

    BINDINGS = [
        Binding("escape", "back", "Back"),
        Binding("q", "quit", "Quit"),
    ]

    def compose(self) -> ComposeResult:
        yield Static("Circle 02", id="hero")
        yield Static("Python modules. Each row is the subject version.", id="status", classes="sub")
        yield ListView(
            *[
                ProjectItem(item.name, _SUBJECT_LABEL[item.name])
                for item in PY_MODULES
            ],
            id="projects",
        )
        yield Footer()

    def on_mount(self) -> None:
        view = self.query_one("#projects", ListView)
        if view.children:
            view.index = 0
        view.focus()

    def action_back(self) -> None:
        self.app.pop_screen()

    def on_list_view_selected(self, event: ListView.Selected) -> None:
        item = event.item
        if isinstance(item, ProjectItem):
            self.app.push_screen(PathScreen(item.project))


class PathScreen(Screen):
    BINDINGS = [
        Binding("escape", "back", "Back"),
        Binding("q", "quit", "Quit"),
    ]

    def __init__(self, project: str) -> None:
        super().__init__()
        self.project = project

    def compose(self) -> ComposeResult:
        ready = self.project in _READY
        hint = "Folder that contains the Makefile and the sources."
        if self.project == "get_next_line":
            hint = "Folder with get_next_line.c and get_next_line.h at the root."
        elif self.project in {item.name for item in PY_MODULES}:
            hint = "Folder with the exercise files, in ex0/, ex1/, and so on."
        if not ready:
            hint = "This project is in the catalog. The runner is not built yet."
        yield Static(self.project, id="hero")
        yield Static(hint, classes="sub")
        yield Input(
            value=self.app.paths.get(self.project, ""),
            placeholder=_PLACEHOLDER.get(self.project, "/home/you/project"),
            id="path",
        )
        yield Static("", id="look", classes="sub")
        with Horizontal(id="actions"):
            yield Button("Run tests", id="run", disabled=not ready)
            yield Button("Back", id="back")
        yield Footer()

    def on_mount(self) -> None:
        field = self.query_one("#path", Input)
        field.focus()
        self._look(field.value)

    def on_input_changed(self, event: Input.Changed) -> None:
        if event.input.id == "path":
            self._look(event.value)

    def on_input_submitted(self, event: Input.Submitted) -> None:
        if self.project in _READY:
            self._open(event.value)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "back":
            self.action_back()
        elif event.button.id == "run":
            self._open(self.query_one("#path", Input).value)

    def action_back(self) -> None:
        self.app.pop_screen()

    def _look(self, text: str) -> None:
        if not text.strip():
            self.query_one("#look", Static).update("Paste the project folder.")
            return
        problem = path_problem(normalize(text), self.project)
        if problem:
            self.query_one("#look", Static).update(problem)
            return
        if self.project == "get_next_line":
            self.query_one("#look", Static).update(
                "get_next_line.c and get_next_line.h found."
            )
            return
        if self.project in {item.name for item in PY_MODULES}:
            self.query_one("#look", Static).update("Folder found.")
            return
        self.query_one("#look", Static).update("Makefile found.")

    def _open(self, text: str) -> None:
        folder = normalize(text)
        self.app.paths[self.project] = text.strip()
        problem = path_problem(folder, self.project)
        if problem:
            self.query_one("#look", Static).update(problem)
            return
        self.app.push_screen(RunScreen(self.project, str(folder)))


class RunScreen(Screen):
    BINDINGS = [
        Binding("escape", "back", "Back"),
        Binding("g", "guide", "Use guide"),
        Binding("q", "quit", "Quit"),
        Binding("r", "rerun", "Run again"),
    ]

    def __init__(self, project: str, folder: str) -> None:
        super().__init__()
        self.project = project
        self.folder = folder
        self.rows: dict[str, object] = {}
        self._keys: set[str] = set()
        self._control = RunControl()
        self._running = False

    def compose(self) -> ComposeResult:
        yield Static(self.project, id="hero")
        yield Static(self.folder, id="banner", classes="sub")
        yield DataTable(id="table")
        yield RichLog(id="detail", wrap=True)
        yield Footer()

    def on_mount(self) -> None:
        table = self.query_one("#table", DataTable)
        table.cursor_type = "row"
        table.add_column("Function", key="fn")
        table.add_column("Part", key="part")
        table.add_column("Pass", key="pass")
        table.add_column("Fail", key="fail")
        table.add_column("Warn", key="warn")
        table.add_column("Note", key="note")
        self._start()

    def _start(self) -> None:
        self._running = True
        self._control = RunControl()
        self.run_worker(self._job, thread=True, exclusive=True)

    def _job(self) -> None:
        try:
            for event in run_project(self.project, Path(self.folder), self._control):
                self.app.call_from_thread(self._apply, event)
        except Exception as exc:
            self.app.call_from_thread(self._apply, Done(0, 0, 0, 0, [], str(exc)))

    def _apply(self, event: object) -> None:
        if not self.is_mounted:
            return
        if isinstance(event, Log):
            if "\n" in event.text:
                self.query_one("#detail", RichLog).write(event.text)
            else:
                self.query_one("#banner", Static).update(event.text)
            return
        if isinstance(event, Plan):
            for row in event.rows:
                self._put(row)
            return
        if isinstance(event, Update):
            self._put(event.row)
            return
        if isinstance(event, Done):
            self._running = False
            self._finish(event)

    def _put(self, row) -> None:
        self.rows[row.function] = row
        name = Text(row.function, style="#f4e8e8" if row.declared else "#a06868")
        note_style = "#c4a8a8"
        if row.failed or not row.declared:
            note_style = "#ff8f8f"
        elif row.warned:
            note_style = "#e6c36a"
        if row.note == "running":
            note_style = "#e7c2c2"
        cells = [
            name,
            row.part,
            Text(str(row.passed), style="#8dcea8"),
            Text(str(row.failed), style="#ff6b6b" if row.failed else "#8a7070"),
            Text(str(row.warned), style="#e6c36a" if row.warned else "#8a7070"),
            Text(row.note, style=note_style),
        ]
        table = self.query_one("#table", DataTable)
        keys = ("fn", "part", "pass", "fail", "warn", "note")
        if row.function not in self._keys:
            table.add_row(*cells, key=row.function)
            self._keys.add(row.function)
            return
        for key, value in zip(keys, cells):
            table.update_cell(row.function, key, value)

    def _finish(self, event: Done) -> None:
        if event.error:
            self.query_one("#banner", Static).update(event.error)
            self.query_one("#detail", RichLog).write(event.error)
            return
        missing = ""
        if event.missing:
            missing = "  Missing: " + ", ".join(event.missing[:8])
        summary = (
            f"Pass {event.passed}   Fail {event.failed}   Warn {event.warned}.{missing}"
        )
        self.query_one("#banner", Static).update(summary)
        detail = self.query_one("#detail", RichLog)
        if event.log_path:
            detail.write(f"Log: {event.log_path}")
        detail.write("The log lists failures and warnings. Press g for what a warning means.")
        self.notify(
            f"{event.passed} passed, {event.failed} failed, {event.warned} warnings",
            timeout=4,
        )

    def action_guide(self) -> None:
        self.app.push_screen(GuideScreen())

    def on_data_table_row_highlighted(self, event: DataTable.RowHighlighted) -> None:
        function = str(event.row_key.value)
        row = self.rows.get(function)
        if row is None:
            return
        detail = self.query_one("#detail", RichLog)
        detail.clear()
        detail.write(f"{row.function}  {row.note}".rstrip())
        lines = (row.fails + row.warns) or row.samples
        for line in lines:
            detail.write(line)

    def action_back(self) -> None:
        self._control.stop()
        self.app.pop_screen()

    def action_rerun(self) -> None:
        if self._running:
            return
        table = self.query_one("#table", DataTable)
        table.clear()
        self.rows.clear()
        self._keys.clear()
        self.query_one("#detail", RichLog).clear()
        self.query_one("#banner", Static).update(self.folder)
        self._start()


class HolesApp(App):
    """Project picker, then the folder where that project lives."""

    CSS = CSS
    TITLE = "42_Holes"
    BINDINGS = [Binding("q", "quit", "Quit")]

    def __init__(self) -> None:
        super().__init__()
        self.paths: dict[str, str] = {}
        self.catalog: dict | None = None

    def on_mount(self) -> None:
        self.push_screen(HomeScreen())
