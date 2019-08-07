from ..spec import (
    SpecLoader, SpecLoaderException, SpecConfigException)
from ..enums import (
    SPEC_PHASES,
    SPEC_CORE_PLUGINS
)
from ..state import app
from .. import log
from pathlib import Path
import sys
import click
import pkg_resources
from pprint import pformat


@click.group()
@click.option(
    "--spec", metavar="<spec>", required=False, multiple=True, help="OGC Spec"
)
@click.option("--debug", is_flag=True)
def cli(spec, debug):
    """ Processes a OGC Spec which defines how a build/test/task is performed
    """
    app.debug = debug
    app.log = log

    specs = []
    # Check for local spec
    if Path("ogc.yml").exists():
        specs.append(Path("ogc.yml"))

    for sp in spec:
        _path = Path(sp)
        if not _path.exists():
            app.log.error(f"Unable to find spec: {sp}")
            sys.exit(1)
        specs.append(_path)
    app.spec = SpecLoader.load(specs)

    # Handle the plugin loader, initializing the plugin class
    plugins = {
        entry_point.name: entry_point.load()
        for entry_point in pkg_resources.iter_entry_points("ogc.plugins")
    }

    phase_mapping = {}
    for phase in app.spec.keys():
        if phase in SPEC_CORE_PLUGINS:
            continue
        if phase not in SPEC_PHASES:
            app.log.error(f'`{phase}` is an incorrect phase for this spec, please review the specfile.')
            sys.exit(1)
        _plugins = []

        for plugin in app.spec[phase]:
            check_plugin = plugins.get(plugin, None)
            if not check_plugin:
                app.log.debug(
                    f"Could not find plugin {plugin}, install with `pip install ogc-plugins-{plugin.lower()}`"
                )
                continue

            _specs = app.spec[phase][plugin]
            if not isinstance(_specs, list):
                _specs = [_specs]

            app.log.info(f"{phase} phase: found {len(_specs)} {plugin} plugin(s)")

            for _spec in _specs:
                runner = check_plugin(phase, _spec, app.spec)

                # Validate spec is compatible with plugin
                try:
                    runner.check()
                except SpecConfigException as error:
                    app.log.error(error)
                    sys.exit(1)

                app.phases[phase].append(runner)
