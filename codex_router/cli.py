"""CLI entry point for codex-router."""

import click
from pathlib import Path
from codex_router import __version__
from codex_router.config import Config
from codex_router.router import TaskRouter
from codex_router.orchestrator import Orchestrator
from codex_router.tracker import CostTracker
from codex_router.display import Display


@click.group()
@click.version_option(version=__version__)
def main():
    """Intelligent routing and orchestration for multi-model AI coding agents."""
    # Click group serves as command dispatcher
    return 0


@main.command()
@click.argument("description")
@click.option("--model", "-m", help="Force specific model (claude, gpt-4, gemini)")
@click.option("--parallel", "-p", type=int, default=1, help="Number of parallel agents")
@click.option("--budget", "-b", type=float, help="Maximum budget in USD")
def task(description: str, model: str, parallel: int, budget: float):
    """Execute a coding task with intelligent routing."""
    try:
        config = Config.load()
    except FileNotFoundError:
        click.echo("Error: Config not found. Run 'codex-router config --init' first.", err=True)
        raise SystemExit(1)

    display = Display()
    tracker = CostTracker()

    if budget and budget <= 0:
        click.echo("Error: Budget must be positive", err=True)
        raise SystemExit(1)

    router = TaskRouter(config)

    if parallel > 1:
        display.info(f"Splitting task into {parallel} parallel agents")
        orchestrator = Orchestrator(config, tracker)
        try:
            result = orchestrator.run_parallel(description, parallel, model, budget)
            display.success(f"DONE - Total: {result['total_tokens']} tokens (${result['total_cost']:.3f})")
        except Exception as e:
            display.error(f"Orchestration failed: {str(e)}")
            raise SystemExit(2)
    else:
        display.info("Analyzing task complexity...")
        try:
            selected_model = router.select_model(description, force_model=model)
            display.info(f"Selected model: {selected_model}")

            result = router.execute_task(description, selected_model, budget)
            tracker.record_usage(selected_model, result["tokens"], result["cost"])

            display.show_result(result["output"])
            display.success(f"DONE - {result['tokens']} tokens (${result['cost']:.3f})")
        except ValueError as e:
            display.error(str(e))
            raise SystemExit(1)
        except Exception as e:
            display.error(f"Task execution failed: {str(e)}")
            raise SystemExit(2)


@main.command()
@click.option("--show-costs", is_flag=True, help="Show cost breakdown by provider")
@click.option("--days", "-d", type=int, default=7, help="Number of days to show")
@click.option("--html", is_flag=True, help="Generate HTML report and open in browser")
def status(show_costs: bool, days: int, html: bool):
    """Show usage statistics and costs."""
    tracker = CostTracker()
    display = Display()

    try:
        stats = tracker.get_stats(days)
    except Exception as e:
        click.echo(f"Error: Failed to load statistics: {str(e)}", err=True)
        raise SystemExit(2)

    if html:
        import webbrowser
        from codex_router.report import export_html
        report_path = export_html(stats, days)
        click.echo(f"Report saved: {report_path}")
        webbrowser.open(f"file://{report_path}")
        return

    if show_costs:
        display.show_cost_table(stats, days)
    else:
        click.echo(f"Total requests (last {days} days): {stats['total_requests']}")
        click.echo(f"Total tokens: {stats['total_tokens']}")
        click.echo(f"Total cost: ${stats['total_cost']:.2f}")


@main.command()
@click.option("--set", "set_value", nargs=2, metavar="KEY VALUE", help="Set config value")
@click.option("--set-default-model", metavar="MODEL", help="Set default model")
@click.option("--init", is_flag=True, help="Initialize config with defaults")
def config(set_value: tuple, set_default_model: str, init: bool):
    """Manage configuration."""
    if init:
        try:
            Config.init_default()
            click.echo("Config initialized at ~/.codex-router/config.yaml")
        except Exception as e:
            click.echo(f"Error: Failed to initialize config: {str(e)}", err=True)
            raise SystemExit(2)
        return

    try:
        cfg = Config.load()
    except FileNotFoundError:
        click.echo("Error: Config not found. Run 'codex-router config --init' first.", err=True)
        raise SystemExit(1)

    if set_value:
        key, value = set_value
        try:
            cfg.set(key, value)
            cfg.save()
            click.echo(f"Set {key} = {value}")
        except ValueError as e:
            click.echo(f"Error: {str(e)}", err=True)
            raise SystemExit(1)

    if set_default_model:
        valid_models = ["claude", "gpt-4", "gpt-3.5", "gemini"]
        if set_default_model not in valid_models:
            click.echo(f"Error: Invalid model. Choose from: {', '.join(valid_models)}", err=True)
            raise SystemExit(1)
        cfg.set("default_model", set_default_model)
        cfg.save()
        click.echo(f"Set default_model = {set_default_model}")


if __name__ == "__main__":
    main()
