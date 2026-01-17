"""
Worm Gear Calculator - Command Line Interface

Usage:
    wormcalc envelope --worm-od 20 --wheel-od 65 --ratio 30
    wormcalc from-wheel --wheel-od 65 --ratio 30
    wormcalc from-module --module 2 --ratio 30
    wormcalc from-centre-distance --centre-distance 40 --ratio 30
"""

import sys
import click
from typing import Optional

from .core import (
    Hand,
    design_from_envelope,
    design_from_wheel,
    design_from_module,
    design_from_centre_distance,
)
from .validation import validate_design
from .output import to_json, to_markdown, to_summary, validation_summary


# Common options
def common_options(f):
    """Decorator for options common to all commands"""
    f = click.option('--pressure-angle', '-pa', default=20.0, 
                     help='Pressure angle in degrees (default: 20)')(f)
    f = click.option('--backlash', '-b', default=0.0,
                     help='Backlash allowance in mm (default: 0)')(f)
    f = click.option('--num-starts', '-s', default=1,
                     help='Number of worm starts (default: 1)')(f)
    f = click.option('--hand', type=click.Choice(['right', 'left']), default='right',
                     help='Thread hand (default: right)')(f)
    f = click.option('--output', '-o', type=click.Choice(['text', 'json', 'markdown', 'md']), 
                     default='text', help='Output format')(f)
    f = click.option('--no-validate', is_flag=True,
                     help='Skip validation checks')(f)
    return f


@click.group()
@click.version_option(version='0.1.0')
def cli():
    """
    Worm Gear Calculator
    
    Calculate worm gear dimensions from various input constraints.
    """
    pass


@cli.command()
@click.option('--worm-od', required=True, type=float, help='Worm outside diameter (mm)')
@click.option('--wheel-od', required=True, type=float, help='Wheel outside diameter (mm)')
@click.option('--ratio', '-r', required=True, type=int, help='Gear ratio')
@common_options
def envelope(worm_od: float, wheel_od: float, ratio: int,
             pressure_angle: float, backlash: float, num_starts: int,
             hand: str, output: str, no_validate: bool):
    """
    Design from both outside diameter constraints.
    
    Use when you have specific envelope (space) constraints for both gears.
    """
    design = design_from_envelope(
        worm_od=worm_od,
        wheel_od=wheel_od,
        ratio=ratio,
        pressure_angle=pressure_angle,
        backlash=backlash,
        num_starts=num_starts,
        hand=Hand(hand)
    )
    
    _output_design(design, output, no_validate)


@cli.command('from-wheel')
@click.option('--wheel-od', required=True, type=float, help='Wheel outside diameter (mm)')
@click.option('--ratio', '-r', required=True, type=int, help='Gear ratio')
@click.option('--target-lead-angle', '-la', default=7.0, 
              help='Target lead angle in degrees (default: 7)')
@common_options
def from_wheel(wheel_od: float, ratio: int, target_lead_angle: float,
               pressure_angle: float, backlash: float, num_starts: int,
               hand: str, output: str, no_validate: bool):
    """
    Design from wheel OD constraint.
    
    Worm is sized automatically to achieve target lead angle.
    Use when wheel size is constrained but worm size is flexible.
    """
    design = design_from_wheel(
        wheel_od=wheel_od,
        ratio=ratio,
        target_lead_angle=target_lead_angle,
        pressure_angle=pressure_angle,
        backlash=backlash,
        num_starts=num_starts,
        hand=Hand(hand)
    )
    
    _output_design(design, output, no_validate)


@cli.command('from-module')
@click.option('--module', '-m', required=True, type=float, help='Module in mm')
@click.option('--ratio', '-r', required=True, type=int, help='Gear ratio')
@click.option('--worm-pitch-dia', type=float, default=None,
              help='Worm pitch diameter (mm). If not set, calculated from target lead angle.')
@click.option('--target-lead-angle', '-la', default=7.0,
              help='Target lead angle if worm-pitch-dia not set (default: 7)')
@common_options
def from_module(module: float, ratio: int, worm_pitch_dia: Optional[float],
                target_lead_angle: float, pressure_angle: float, backlash: float,
                num_starts: int, hand: str, output: str, no_validate: bool):
    """
    Design from module specification.
    
    Traditional approach using standard module values.
    """
    design = design_from_module(
        module=module,
        ratio=ratio,
        worm_pitch_diameter=worm_pitch_dia,
        target_lead_angle=target_lead_angle,
        pressure_angle=pressure_angle,
        backlash=backlash,
        num_starts=num_starts,
        hand=Hand(hand)
    )
    
    _output_design(design, output, no_validate)


@cli.command('from-centre-distance')
@click.option('--centre-distance', '-cd', required=True, type=float, 
              help='Required centre distance (mm)')
@click.option('--ratio', '-r', required=True, type=int, help='Gear ratio')
@click.option('--worm-wheel-ratio', default=0.3,
              help='Ratio of worm pitch dia to wheel pitch dia (default: 0.3)')
@common_options
def from_centre_distance(centre_distance: float, ratio: int, worm_wheel_ratio: float,
                         pressure_angle: float, backlash: float, num_starts: int,
                         hand: str, output: str, no_validate: bool):
    """
    Design from centre distance constraint.
    
    Use when fitting into existing housing with fixed shaft positions.
    """
    design = design_from_centre_distance(
        centre_distance=centre_distance,
        ratio=ratio,
        worm_to_wheel_ratio=worm_wheel_ratio,
        pressure_angle=pressure_angle,
        backlash=backlash,
        num_starts=num_starts,
        hand=Hand(hand)
    )
    
    _output_design(design, output, no_validate)


@cli.command()
@click.option('--module', '-m', required=True, type=float, help='Module to check')
def check_module(module: float):
    """
    Check if a module is standard and find nearest standard values.
    """
    from .core import STANDARD_MODULES, is_standard_module, nearest_standard_module
    
    nearest = nearest_standard_module(module)
    is_std = is_standard_module(module)
    
    click.echo(f"Module: {module} mm")
    click.echo(f"Standard (ISO 54): {'Yes' if is_std else 'No'}")
    
    if not is_std:
        click.echo(f"Nearest standard: {nearest} mm")
        
        # Show nearby options
        idx = STANDARD_MODULES.index(nearest)
        nearby = STANDARD_MODULES[max(0, idx-2):idx+3]
        click.echo(f"Nearby standards: {', '.join(str(m) for m in nearby)} mm")


@cli.command()
def list_modules():
    """
    List all standard modules (ISO 54 / DIN 780).
    """
    from .core import STANDARD_MODULES
    
    click.echo("Standard Modules (ISO 54 / DIN 780):")
    click.echo("────────────────────────────────────")
    
    # Group by size range
    small = [m for m in STANDARD_MODULES if m < 1]
    medium = [m for m in STANDARD_MODULES if 1 <= m < 5]
    large = [m for m in STANDARD_MODULES if m >= 5]
    
    click.echo(f"Small (<1mm):   {', '.join(f'{m}' for m in small)}")
    click.echo(f"Medium (1-5mm): {', '.join(f'{m}' for m in medium)}")
    click.echo(f"Large (≥5mm):   {', '.join(f'{m}' for m in large)}")


def _output_design(design, output_format: str, skip_validation: bool):
    """Output design in requested format"""
    
    validation = None if skip_validation else validate_design(design)
    
    if output_format == 'json':
        click.echo(to_json(design, validation))
    
    elif output_format in ('markdown', 'md'):
        click.echo(to_markdown(design, validation))
    
    else:  # text
        click.echo(to_summary(design))
        click.echo()
        if validation:
            click.echo(validation_summary(validation))


def main():
    """Entry point for CLI"""
    cli()


if __name__ == '__main__':
    main()
