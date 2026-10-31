"""Dark red and black terminal UI."""

from pathlib import Path

from rich.text import Text
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical, VerticalScroll
from textual.screen import Screen
from textual.widgets import Button, DataTable, Footer, Input, ListItem, ListView, RichLog, Static

from cc_holes.catalog import CatalogError, load_catalog, project_names
from cc_holes.guide import CREDITS, GUIDE, LOGO, TAGLINE
from cc_holes.runner import Done, Log, Plan, RunControl, Update, run_libft

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


def path_problem(path: Path) -> str:
    if not str(path).strip() or path == Path.cwd() / "":
        return ""
    if not path.exists():
        return "That folder does not exist."
    if not path.is_dir():
        return "That path is a file. Pass the project folder."
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
        self.app.push_screen(PickScreen())

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


class PickScreen(Screen):
    BINDINGS = [
        Binding("escape", "back", "Back"),
        Binding("q", "quit", "Quit"),
    ]

    def compose(self) -> ComposeResult:
        yield Static("Available tests", id="hero")
        yield Static("Loading tests…", id="status", classes="sub")
        yield ListView(id="projects")
        yield Footer()

    def on_mount(self) -> None:
        self.run_worker(self._load, thread=True, exclusive=True)

    def _load(self) -> None:
        try:
            catalog = load_catalog()
        except CatalogError as exc:
            self.app.call_from_thread(self._failed, str(exc))
            return
        self.app.call_from_thread(self._ready, catalog)

    def _failed(self, message: str) -> None:
        self.query_one("#status", Static).update(message)

    def _ready(self, catalog: dict) -> None:
        self.app.catalog = catalog
        counts = catalog.get("counts", {}).get("by_project", {})
        view = self.query_one("#projects", ListView)
        for name in project_names(catalog):
            total = counts.get(name, 0)
            state = "ready" if name == "libft" else "runner not built yet"
            view.append(ProjectItem(name, f"{total} tests · {state}"))
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


class PathScreen(Screen):
    BINDINGS = [
        Binding("escape", "back", "Back"),
        Binding("q", "quit", "Quit"),
    ]

    def __init__(self, project: str) -> None:
        super().__init__()
        self.project = project

    def compose(self) -> ComposeResult:
        ready = self.project == "libft"
        hint = "Folder that contains the Makefile and the sources."
        if not ready:
            hint = "This project is in the catalog. The runner is not built yet."
        yield Static(self.project, id="hero")
        yield Static(hint, classes="sub")
        yield Input(
            value=self.app.paths.get(self.project, ""),
            placeholder="/home/you/libft",
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
        if self.project == "libft":
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
        problem = path_problem(normalize(text))
        if problem:
            self.query_one("#look", Static).update(problem)
            return
        self.query_one("#look", Static).update("Makefile found.")

    def _open(self, text: str) -> None:
        folder = normalize(text)
        self.app.paths[self.project] = text.strip()
        problem = path_problem(folder)
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
        table.add_column("Skip", key="skip")
        table.add_column("Note", key="note")
        self._start()

    def _start(self) -> None:
        self._running = True
        self._control = RunControl()
        self.run_worker(self._job, thread=True, exclusive=True)

    def _job(self) -> None:
        try:
            for event in run_libft(Path(self.folder), self._control):
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
        note_style = "#ff8f8f" if row.failed or not row.declared else "#c4a8a8"
        if row.note == "running":
            note_style = "#e7c2c2"
        cells = [
            name,
            row.part,
            Text(str(row.passed), style="#8dcea8"),
            Text(str(row.failed), style="#ff6b6b" if row.failed else "#8a7070"),
            Text(str(row.skipped), style="#c4a8a8"),
            Text(row.note, style=note_style),
        ]
        table = self.query_one("#table", DataTable)
        keys = ("fn", "part", "pass", "fail", "skip", "note")
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
        other = ""
        if event.other:
            other = f"  Old functions not in this libft: {event.other} tests."
        summary = (
            f"Pass {event.passed}   Fail {event.failed}   Skip {event.skipped}.{missing}{other}"
        )
        self.query_one("#banner", Static).update(summary)
        detail = self.query_one("#detail", RichLog)
        if event.log_path:
            detail.write(f"Log: {event.log_path}")
        detail.write(
            "Skip counts calls that were not executed. Press g to read what each call means."
        )
        self.notify(f"{event.passed} passed, {event.failed} failed", timeout=4)

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
        lines = row.fails or row.samples
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
