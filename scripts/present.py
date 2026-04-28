import os
import sys

from rich.align import Align
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel


def main() -> None:
    if len(sys.argv) < 2:
        print("Usage: uv run scripts/present.py <markdown_file>")
        return

    file_path = sys.argv[1]
    if not os.path.exists(file_path):
        print(f"Error: File '{file_path}' not found.")
        return

    with open(file_path, encoding="utf-8") as f:
        content = f.read()

    # Split slides by '---' with optional whitespace
    slides = [s.strip() for s in content.split("\n---")]
    # Filter out empty slides (common at start/end of file)
    slides = [s for s in slides if s]

    console = Console()

    for i, slide in enumerate(slides):
        console.clear()

        # Strip pyfiglet/marp tags that aren't standard markdown
        clean_slide = "\n".join(
            line
            for line in slide.split("\n")
            if not line.startswith("marp:")
            and not line.startswith("theme:")
            and not line.startswith("paginate:")
            and not line.startswith("_class:")
        ).replace("# !pyfiglet ", "# ")

        # Create a centered layout
        markdown = Markdown(clean_slide)
        panel = Panel(
            Align.center(markdown, vertical="middle"),
            title=f"Kinetic [ {i + 1} / {len(slides)} ]",
            border_style="bright_blue",
            padding=(2, 4),
        )

        console.print(panel)

        if i < len(slides) - 1:
            try:
                # Use input() to pause; on some terminals this needs a nudge
                console.print(
                    "\n[dim]Press Enter for next slide... (or Ctrl+C to exit)[/dim]",
                    justify="center",
                )
                input()
            except KeyboardInterrupt:
                console.print("\n[yellow]Presentation exited.[/yellow]")
                sys.exit(0)

    console.clear()
    console.print(
        Panel(
            Align.center("# [green]Fin.[/green]\n\nDemo session ready.", vertical="middle"),
            border_style="green",
        )
    )


if __name__ == "__main__":
    main()
