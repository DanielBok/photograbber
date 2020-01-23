import time

import click

from PhotoGrab import PhotoGrab


@click.command()
def cli():
    """Copies the photos"""
    t = time.time()
    PhotoGrab().run()
    total_time = round(time.time() - t, 5)
    click.echo(f"Complete. Elapsed time: {total_time}s")


if __name__ == "__main__":
    click.echo("If you're seeing this message, you're using the program incorrectly")
    click.echo("You should instead activate the photo environment first")
    click.echo("Subsequently, just type 'photo'")

