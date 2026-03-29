import typer
from datetime import date
from typing import Optional
from rich.console import Console
from rich.table import Table
from rich import box

from ana.db import get_conn
from ana.dates import parse_date_args, format_event_date, next_occurrence

app = typer.Typer(
    name="ana",
    help="📅 Ana — personal event manager in your terminal.",
    add_completion=False,
    no_args_is_help=True,
)
console = Console()


def purge_past():
    """Delete all events strictly before today."""
    today = date.today()
    conn = get_conn()
    conn.execute(
        "DELETE FROM events WHERE "
        "(year < ?) OR "
        "(year = ? AND month < ?) OR "
        "(year = ? AND month = ? AND day < ?)",
        (today.year, today.year, today.month, today.year, today.month, today.day),
    )
    conn.commit()
    conn.close()


# ── ana greet ──────────────────────────────────────────────────────────────

@app.command()
def greet():
    """Say hello."""
    purge_past()
    console.print("Hello World!")


# ── ana add ────────────────────────────────────────────────────────────────

@app.command(context_settings={"allow_extra_args": True, "ignore_unknown_options": True})
def add(ctx: typer.Context):
    """
    Add an event.\n
      ana add "text"\n
      ana add HH:MM "text"\n
      ana add <day> "text"\n
      ana add <day> HH:MM "text"\n
      ana add <day> <month> "text"\n
      ana add <day> <month> HH:MM "text"\n
      ana add <day> <month> <year> "text"\n
      ana add <day> <month> <year> HH:MM "text"
    """
    args = ctx.args
    if not args:
        console.print("[red]Error:[/red] No arguments given. See: ana add --help")
        raise typer.Exit(1)

    purge_past()

    try:
        resolved, time_str, description = parse_date_args(args)
    except ValueError as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)

    conn = get_conn()
    cur = conn.execute(
        "INSERT INTO events (day, month, year, time, text) VALUES (?, ?, ?, ?, ?)",
        (resolved.day, resolved.month, resolved.year, time_str, description),
    )
    conn.commit()
    event_id = cur.lastrowid
    conn.close()

    date_str = format_event_date(resolved.day, resolved.month, resolved.year, time_str)
    console.print(f"[green]✓[/green] Event [bold]#{event_id}[/bold] added — {date_str}: {description}")


# ── ana ls ─────────────────────────────────────────────────────────────────

@app.command(name="ls", context_settings={"allow_extra_args": True, "ignore_unknown_options": True})
def ls(ctx: typer.Context):
    """
    List events.\n
      ana ls                        → all events\n
      ana ls <day>                  → next occurrence of that day\n
      ana ls <day> <month>          → next occurrence of day/month\n
      ana ls <day> <month> <year>   → exact date
    """
    args = ctx.args
    purge_past()
    conn = get_conn()

    if not args:
        rows = conn.execute(
            "SELECT id, day, month, year, time, text FROM events ORDER BY year, month, day, time, id"
        ).fetchall()
        title = "All events"
    else:
        try:
            nums = [int(a) for a in args]
        except ValueError:
            console.print("[red]Error:[/red] ls only accepts numeric date components.")
            conn.close()
            raise typer.Exit(1)

        if len(nums) == 1:
            resolved = next_occurrence(nums[0])
        elif len(nums) == 2:
            resolved = next_occurrence(nums[0], nums[1])
        elif len(nums) == 3:
            resolved = next_occurrence(nums[0], nums[1], nums[2])
        else:
            console.print("[red]Error:[/red] Too many arguments.")
            conn.close()
            raise typer.Exit(1)

        rows = conn.execute(
            "SELECT id, day, month, year, time, text FROM events "
            "WHERE day=? AND month=? AND year=? ORDER BY time, id",
            (resolved.day, resolved.month, resolved.year),
        ).fetchall()
        title = f"Events on {resolved.day:02d}/{resolved.month:02d}/{resolved.year}"

    conn.close()

    if not rows:
        console.print("[dim]No events found.[/dim]")
        return

    table = Table(title=title, box=box.ROUNDED, show_lines=False)
    table.add_column("ID",    style="cyan",          justify="right", no_wrap=True)
    table.add_column("Date",  style="white",          no_wrap=True)
    table.add_column("Time",  style="bright_yellow",  no_wrap=True)
    table.add_column("Event", style="bright_white")

    for row_id, day, month, year, time_str, text in rows:
        table.add_row(str(row_id), f"{day:02d}/{month:02d}/{year}", time_str or "—", text)

    console.print(table)


# ── ana rm ─────────────────────────────────────────────────────────────────

@app.command(name="rm")
def rm(event_id: int = typer.Argument(..., help="Event ID (from ana ls)")):
    """
    Remove an event by ID.\n
      ana rm <id>
    """
    purge_past()
    conn = get_conn()
    row = conn.execute(
        "SELECT id, day, month, year, time, text FROM events WHERE id=?",
        (event_id,),
    ).fetchone()

    if row is None:
        console.print(f"[red]Not found:[/red] No event with ID #{event_id}.")
        conn.close()
        raise typer.Exit(1)

    conn.execute("DELETE FROM events WHERE id=?", (event_id,))
    conn.commit()
    conn.close()

    date_str = format_event_date(row[1], row[2], row[3], row[4])
    console.print(f"[green]✓[/green] Deleted event [bold]#{row[0]}[/bold] — {date_str}: {row[5]}")


# ── ana edit ───────────────────────────────────────────────────────────────

@app.command()
def edit(
    event_id: int = typer.Argument(..., help="Event ID (from ana ls)"),
    text: str = typer.Argument(..., help="New event description"),
):
    """
    Edit an event's text by ID.\n
      ana edit <id> "new text"
    """
    purge_past()
    conn = get_conn()
    row = conn.execute(
        "SELECT id, day, month, year, time FROM events WHERE id=?",
        (event_id,),
    ).fetchone()

    if row is None:
        console.print(f"[red]Not found:[/red] No event with ID #{event_id}.")
        conn.close()
        raise typer.Exit(1)

    conn.execute("UPDATE events SET text=? WHERE id=?", (text, event_id))
    conn.commit()
    conn.close()

    date_str = format_event_date(row[1], row[2], row[3], row[4])
    console.print(f"[green]✓[/green] Event [bold]#{event_id}[/bold] updated — {date_str}: {text}")


# ── ana clear ─────────────────────────────────────────────────────────────

@app.command()
def clear():
    """Delete all events."""
    conn = get_conn()
    conn.execute("DELETE FROM events")
    conn.commit()
    conn.close()
    console.print("[green]✓[/green] All events deleted.")


def main():
    try:
        app()
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        #raise typer.Exit(1)


if __name__ == "__main__":
    main()
