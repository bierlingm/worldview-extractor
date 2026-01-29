LOGO = """[cyan]╦ ╦╔═╗╔═╗╦  ╦╔═╗[/cyan]
[cyan]║║║║╣ ╠═╣╚╗╔╝║╣ [/cyan]
[cyan]╚╩╝╚═╝╩ ╩ ╚╝ ╚═╝[/cyan]"""

LOGO_PLAIN = """╦ ╦╔═╗╔═╗╦  ╦╔═╗
║║║║╣ ╠═╣╚╗╔╝║╣ 
╚╩╝╚═╝╩ ╩ ╚╝ ╚═╝"""

TAGLINE = "Worldview Synthesis Engine"
VERSION_TAGLINE = "Synthesize intellectual worldviews from any source"

def print_banner(console=None):
    """Print the wve banner with logo."""
    if console is None:
        from wve.theme import get_console
        console = get_console()
    console.print(LOGO)
    console.print(f"[dim]{TAGLINE}[/dim]")
    console.print()
