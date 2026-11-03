import csv
import sys
from pathlib import Path
from tkinter import Button, Canvas, Frame, Label, Scrollbar, StringVar, Tk, Toplevel, filedialog, messagebox
from typing import Dict, List, Optional, Tuple

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from src.core.graph import load_graph_from_csv, load_nodes_from_csv
from src.core.dtos.search_request_dto import SearchRequestDTO
from src.core.dtos.user_profile_dto import UserProfileDTO
from src.search.astar import AStarSearch
from src.search.ucs import UniformCostSearch

# Player-ul 2D (route_player.py) și sprite-urile sunt în src/graph_generator/
GRAPH_GEN_DIR = Path(__file__).resolve().parents[1] / "graph_generator"
sys.path.insert(0, str(GRAPH_GEN_DIR))
from route_player import RoutePlayer  # noqa: E402

ROLE_HEADERS = {
    "nodes": frozenset({"id", "x", "y"}),
    "edges": frozenset({"from", "to", "minutes"}),
    "tasks": frozenset({"start", "goal"}),
}


def _read_headers(file_path: str) -> frozenset:
    with open(file_path, "r", encoding="utf-8-sig", newline="") as csv_file:
        reader = csv.reader(csv_file)
        headers = next(reader, [])
    return frozenset(header.strip().lower() for header in headers if header.strip())


def identify_csv_role(file_path: str) -> Optional[str]:
    """Identify a supported CSV by its required column names."""
    headers = _read_headers(file_path)
    matches = [
        role for role, required_headers in ROLE_HEADERS.items()
        if required_headers.issubset(headers)
    ]
    return matches[0] if len(matches) == 1 else None


def load_task_rows(file_path: str) -> List[Dict[str, str]]:
    """Read task rows while preserving the fixture column names and values."""
    with open(file_path, "r", encoding="utf-8-sig", newline="") as csv_file:
        reader = csv.DictReader(csv_file)
        return [
            {
                (key or "").strip().lower(): (value or "").strip()
                for key, value in row.items()
                if key is not None
            }
            for row in reader
        ]


def format_task(task: Dict[str, str], index: int) -> str:
    start = task.get("start", "")
    goal = task.get("goal", "")
    details = []
    if task.get("blocked_edges"):
        details.append("blocked: " + task["blocked_edges"])
    if task.get("required_visit"):
        details.append("visit: " + task["required_visit"])
    suffix = " | " + " | ".join(details) if details else ""
    return f"Task {index}: {start} -> {goal}{suffix}"


class CampusRoutePlannerApp:
    def __init__(self, root: Tk) -> None:
        self.root = root
        self.root.title("Campus Route Planner")
        self.root.geometry("1200x720")
        self.root.minsize(850, 520)

        self.loaded_files: Dict[str, str] = {}
        self.tasks: List[Dict[str, str]] = []
        self.status = StringVar(value="Load edges.csv and tasks.csv to begin.")

        self._configure_colors()
        self._build_layout()

    def _configure_colors(self) -> None:
        self.background = "#f4f6f8"
        self.panel = "#ffffff"
        self.border = "#d8dee4"
        self.primary = "#2563eb"
        self.primary_active = "#1d4ed8"
        self.text = "#17202a"
        self.muted = "#667085"

    def _build_layout(self) -> None:
        self.root.configure(bg=self.background)
        self.root.grid_rowconfigure(1, weight=1)
        self.root.grid_columnconfigure(0, weight=0, minsize=260)
        self.root.grid_columnconfigure(1, weight=1)

        header = Frame(self.root, bg=self.panel, highlightbackground=self.border, highlightthickness=1)
        header.grid(row=0, column=0, columnspan=2, sticky="ew", padx=12, pady=(12, 8))
        header.grid_columnconfigure(1, weight=1)

        Label(
            header,
            text="Campus Route Planner",
            bg=self.panel,
            fg=self.text,
            font=("Segoe UI", 16, "bold"),
        ).grid(row=0, column=0, padx=16, pady=12)

        self.load_button = Button(
            header,
            text="Load",
            command=self.load_files,
            bg=self.primary,
            activebackground=self.primary_active,
            fg="white",
            relief="flat",
            padx=22,
            pady=6,
            cursor="hand2",
        )
        self.load_button.grid(row=0, column=2, padx=6, pady=8)

        self._build_task_panel()
        self._build_map_panel()

        Label(
            self.root,
            textvariable=self.status,
            bg=self.background,
            fg=self.muted,
            anchor="w",
        ).grid(row=2, column=0, columnspan=2, sticky="ew", padx=14, pady=(4, 10))

    def _build_task_panel(self) -> None:
        panel = Frame(self.root, bg=self.panel, highlightbackground=self.border, highlightthickness=1)
        panel.grid(row=1, column=0, sticky="nsew", padx=(12, 8), pady=(0, 4))
        panel.grid_rowconfigure(1, weight=1)
        panel.grid_columnconfigure(0, weight=1)

        Label(
            panel,
            text="Tasks",
            bg=self.panel,
            fg=self.text,
            font=("Segoe UI", 12, "bold"),
            anchor="w",
        ).grid(row=0, column=0, sticky="ew", padx=14, pady=(14, 8))

        task_container = Frame(panel, bg=self.panel)
        task_container.grid(row=1, column=0, sticky="nsew", padx=10, pady=(0, 10))
        task_container.grid_rowconfigure(0, weight=1)
        task_container.grid_columnconfigure(0, weight=1)

        task_canvas = Canvas(
            task_container,
            bg="#fbfcfd",
            relief="flat",
            highlightthickness=0,
        )
        task_canvas.grid(row=0, column=0, sticky="nsew")
        self.task_buttons_frame = Frame(task_canvas, bg="#fbfcfd")
        task_window = task_canvas.create_window(
            (0, 0),
            window=self.task_buttons_frame,
            anchor="nw",
        )

        def resize_task_area(event) -> None:
            task_canvas.configure(scrollregion=task_canvas.bbox("all"))
            task_canvas.itemconfigure(task_window, width=event.width)

        self.task_buttons_frame.bind(
            "<Configure>",
            lambda _event: task_canvas.configure(scrollregion=task_canvas.bbox("all")),
        )
        task_canvas.bind("<Configure>", resize_task_area)

        scrollbar = Scrollbar(task_container, orient="vertical", command=task_canvas.yview)
        scrollbar.grid(row=0, column=1, sticky="ns")
        task_canvas.configure(yscrollcommand=scrollbar.set)

    def _build_map_panel(self) -> None:
        panel = Frame(self.root, bg=self.panel, highlightbackground=self.border, highlightthickness=1)
        panel.grid(row=1, column=1, sticky="nsew", padx=(0, 12), pady=(0, 4))
        panel.grid_rowconfigure(1, weight=1)
        panel.grid_columnconfigure(0, weight=1)

        Label(
            panel,
            text="Route animation",
            bg=self.panel,
            fg=self.text,
            font=("Segoe UI", 12, "bold"),
            anchor="w",
        ).grid(row=0, column=0, sticky="ew", padx=14, pady=(14, 8))

        self.player = RoutePlayer(panel, GRAPH_GEN_DIR / "sprites", bg="#ffffff")
        self.player.grid(row=1, column=0, sticky="nsew", padx=14, pady=(0, 14))

    def _clear_animation(self) -> None:
        self.player.clear()

    def load_files(self) -> None:
        selected = filedialog.askopenfilenames(
            title="Select edges.csv, tasks.csv, and optional nodes.csv",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
        )
        if not selected:
            return
        if len(selected) > 3:
            messagebox.showerror("Invalid selection", "Select up to 3 CSV files.")
            return

        roles: Dict[str, str] = {}
        for file_path in selected:
            try:
                role = identify_csv_role(file_path)
            except (OSError, UnicodeError, csv.Error) as error:
                messagebox.showerror("Could not read file", f"{Path(file_path).name}: {error}")
                return
            if role is None or role in roles:
                messagebox.showerror(
                    "Invalid CSV files",
                    "Select at most one CSV for each supported role (nodes, edges, tasks).",
                )
                return
            roles[role] = file_path

        if "edges" not in roles or "tasks" not in roles or len(roles) != len(selected):
            messagebox.showerror(
                "Invalid CSV files",
                "Select an edges CSV, a tasks CSV, and optionally a nodes CSV.",
            )
            return

        try:
            tasks = load_task_rows(roles["tasks"])
        except (OSError, UnicodeError, csv.Error) as error:
            messagebox.showerror("Could not read tasks", str(error))
            return

        self.loaded_files = roles
        self.tasks = tasks
        self._display_tasks()
        self._clear_animation()
        self.status.set(f"Loaded {len(tasks)} tasks. Select a task to choose an algorithm.")

    def _ask_algorithm(self) -> Optional[bool]:
        """Small dialog with two buttons. Returns True for A*, False for UCS, None if closed."""
        choice: Dict[str, Optional[bool]] = {"value": None}
        dialog = Toplevel(self.root)
        dialog.title("Choose route algorithm")
        dialog.configure(bg=self.panel)
        dialog.transient(self.root)
        dialog.resizable(False, False)

        Label(
            dialog,
            text="Choose the algorithm for this task",
            bg=self.panel,
            fg=self.text,
            font=("Segoe UI", 11, "bold"),
        ).pack(padx=28, pady=(20, 14))

        row = Frame(dialog, bg=self.panel)
        row.pack(padx=28, pady=(0, 20))

        def pick(value: bool) -> None:
            choice["value"] = value
            dialog.destroy()

        for label, value in (("A*", True), ("UCS", False)):
            Button(
                row,
                text=label,
                command=lambda v=value: pick(v),
                bg=self.primary,
                activebackground=self.primary_active,
                fg="white",
                relief="flat",
                width=10,
                pady=8,
                cursor="hand2",
            ).pack(side="left", padx=8)

        dialog.update_idletasks()
        x = self.root.winfo_rootx() + (self.root.winfo_width() - dialog.winfo_width()) // 2
        y = self.root.winfo_rooty() + (self.root.winfo_height() - dialog.winfo_height()) // 2
        dialog.geometry(f"+{max(0, x)}+{max(0, y)}")
        dialog.wait_visibility()
        dialog.grab_set()
        dialog.wait_window()
        return choice["value"]

    def _task_selected(self, index: int) -> None:
        if index < 0 or index >= len(self.tasks):
            return

        use_astar = self._ask_algorithm()
        if use_astar is None:
            return

        task = self.tasks[index]
        algorithm_name = "A*" if use_astar else "UCS"
        try:
            graph_manager = load_graph_from_csv(self.loaded_files["edges"])
            if "nodes" in self.loaded_files:
                load_nodes_from_csv(self.loaded_files["nodes"], graph_manager)

            blocked_edges = {
                edge.strip()
                for edge in task.get("blocked_edges", "").split(";")
                if edge.strip()
            }
            required_visit = task.get("required_visit", "").strip() or None
            request = SearchRequestDTO(
                start_node=task.get("start", "").strip(),
                goal_node=task.get("goal", "").strip(),
                required_visit=required_visit,
                blocked_edges=blocked_edges,
                profile=UserProfileDTO(),
            )
            search_engine = AStarSearch() if use_astar else UniformCostSearch()
            response = search_engine.solve(graph_manager.graph_dto, request)
            if not response.route_found:
                messagebox.showerror(
                    "No route found",
                    f"{algorithm_name} could not find a route for {format_task(task, index + 1)}.",
                    parent=self.root,
                )
                self.status.set(f"No route found for Task {index + 1} using {algorithm_name}.")
                return

            self.status.set(f"Generating Task {index + 1} animation with {algorithm_name}...")
            self.root.update_idletasks()
            self.player.play(self.loaded_files["edges"], response.path)
        except (OSError, UnicodeError, ValueError, RuntimeError) as error:
            messagebox.showerror("Could not generate graph animation", str(error), parent=self.root)
            self.status.set(f"Task {index + 1} animation failed.")
            return

        self.status.set(
            f"Task {index + 1} | {algorithm_name} | "
            f"{' -> '.join(response.path)} | {response.total_cost:g} min"
        )

    def _display_tasks(self) -> None:
        for child in self.task_buttons_frame.winfo_children():
            child.destroy()
        for index, task in enumerate(self.tasks, start=1):
            Button(
                self.task_buttons_frame,
                text=format_task(task, index),
                command=lambda task_index=index - 1: self._task_selected(task_index),
                bg="#ffffff",
                activebackground="#dbeafe",
                fg=self.text,
                anchor="w",
                justify="left",
                relief="flat",
                highlightbackground=self.border,
                highlightthickness=1,
                padx=10,
                pady=8,
                wraplength=220,
                cursor="hand2",
            ).pack(fill="x", padx=4, pady=4)

    def run_application(self) -> None:
        self.status.set("Load edges.csv and tasks.csv, then select a task.")


def create_app() -> Tuple[Tk, CampusRoutePlannerApp]:
    root = Tk()
    return root, CampusRoutePlannerApp(root)


def main() -> None:
    root, _app = create_app()
    root.mainloop()


if __name__ == "__main__":
    main()