"""
Worm Gear Calculator - Core Calculations

Pure mathematical functions for worm gear design.
No external dependencies beyond stdlib.

Reference standards:
- DIN 3975 (worm geometry)
- DIN 3996 (worm gear load capacity)
- ISO 54 (standard modules)
"""

from dataclasses import dataclass, field
from math import pi, tan, atan, degrees, radians, cos, sin, sqrt
from typing import Optional, List, Tuple
from enum import Enum


# ISO 54 / DIN 780 standard modules (mm)
STANDARD_MODULES = [
    0.3, 0.4, 0.5, 0.6, 0.7, 0.75, 0.8, 0.9, 1.0,
    1.125, 1.25, 1.375, 1.5, 1.75, 2.0, 2.25, 2.5, 2.75,
    3.0, 3.5, 4.0, 4.5, 5.0, 5.5, 6.0, 7.0, 8.0, 9.0, 10.0,
    11.0, 12.0, 14.0, 16.0, 18.0, 20.0, 22.0, 25.0
]


class Hand(Enum):
    """Thread hand / helix direction"""
    RIGHT = "right"
    LEFT = "left"


@dataclass
class WormParameters:
    """Calculated worm dimensions"""
    module: float                   # Axial module (mm)
    num_starts: int                 # Number of thread starts
    pitch_diameter: float           # Pitch diameter (mm)
    tip_diameter: float             # Outside/tip diameter (mm)
    root_diameter: float            # Root diameter (mm)
    lead: float                     # Lead = axial_pitch × num_starts (mm)
    axial_pitch: float              # Distance between threads (mm)
    lead_angle: float               # Lead angle (degrees)
    addendum: float                 # Tooth height above pitch (mm)
    dedendum: float                 # Tooth depth below pitch (mm)
    thread_thickness: float         # Thread thickness at pitch line (mm)
    
    @property
    def pitch_radius(self) -> float:
        return self.pitch_diameter / 2
    
    @property
    def tip_radius(self) -> float:
        return self.tip_diameter / 2
    
    @property
    def root_radius(self) -> float:
        return self.root_diameter / 2


@dataclass
class WheelParameters:
    """Calculated worm wheel dimensions"""
    module: float                   # Transverse module (mm)
    num_teeth: int                  # Number of teeth
    pitch_diameter: float           # Pitch diameter (mm)
    tip_diameter: float             # Outside/tip diameter (mm)
    root_diameter: float            # Root diameter (mm)
    throat_diameter: float          # Throat diameter for enveloping (mm)
    helix_angle: float              # Helix angle (degrees)
    addendum: float                 # Tooth height above pitch (mm)
    dedendum: float                 # Tooth depth below pitch (mm)
    
    @property
    def pitch_radius(self) -> float:
        return self.pitch_diameter / 2
    
    @property
    def tip_radius(self) -> float:
        return self.tip_diameter / 2
    
    @property
    def root_radius(self) -> float:
        return self.root_diameter / 2


@dataclass
class WormGearDesign:
    """Complete worm gear pair design"""
    worm: WormParameters
    wheel: WheelParameters
    
    # Assembly parameters
    centre_distance: float          # Axis-to-axis distance (mm)
    ratio: float                    # Gear ratio (wheel_teeth / worm_starts)
    
    # Design inputs (for reference)
    pressure_angle: float           # Pressure angle (degrees)
    backlash: float                 # Backlash allowance (mm)
    hand: Hand                      # Thread direction
    
    # Performance estimates
    efficiency_estimate: float      # Estimated efficiency (0-1)
    self_locking: bool              # Whether drive is self-locking
    
    def __post_init__(self):
        # Calculate efficiency and self-locking based on lead angle
        self.efficiency_estimate = estimate_efficiency(
            self.worm.lead_angle,
            self.pressure_angle
        )
        self.self_locking = self.worm.lead_angle < 6.0  # Conservative threshold


@dataclass
class DesignResult:
    """Result from design calculation including validation"""
    design: Optional[WormGearDesign]
    valid: bool
    warnings: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    suggestions: List[str] = field(default_factory=list)


def nearest_standard_module(module: float) -> float:
    """Find nearest ISO standard module"""
    return min(STANDARD_MODULES, key=lambda m: abs(m - module))


def is_standard_module(module: float, tolerance: float = 0.001) -> bool:
    """Check if module is a standard value"""
    nearest = nearest_standard_module(module)
    return abs(module - nearest) < tolerance


def estimate_efficiency(lead_angle_deg: float, pressure_angle_deg: float = 20.0, 
                        friction_coefficient: float = 0.05) -> float:
    """
    Estimate worm drive efficiency.
    
    Based on simplified formula:
    η = tan(γ) / tan(γ + ρ)
    
    Where:
    - γ = lead angle
    - ρ = friction angle = atan(μ / cos(α))
    - μ = friction coefficient
    - α = pressure angle
    
    Typical friction coefficients:
    - Steel on bronze, lubricated: 0.03-0.05
    - Steel on cast iron: 0.05-0.08
    - Steel on steel: 0.08-0.12
    """
    gamma = radians(lead_angle_deg)
    alpha = radians(pressure_angle_deg)
    
    # Friction angle
    rho = atan(friction_coefficient / cos(alpha))
    
    # Efficiency
    if gamma + rho >= pi / 2:
        return 0.0
    
    efficiency = tan(gamma) / tan(gamma + rho)
    return max(0.0, min(1.0, efficiency))


def calculate_worm(
    module: float,
    num_starts: int,
    pitch_diameter: float,
    pressure_angle: float = 20.0,
    clearance_factor: float = 0.25,
    backlash: float = 0.0
) -> WormParameters:
    """
    Calculate worm dimensions from basic parameters.
    
    Args:
        module: Axial module (mm)
        num_starts: Number of thread starts (typically 1-4)
        pitch_diameter: Pitch diameter (mm)
        pressure_angle: Pressure angle (degrees)
        clearance_factor: Bottom clearance as fraction of module
        backlash: Backlash allowance (mm) - reduces thread thickness
    
    Returns:
        WormParameters with all dimensions
    """
    # Axial pitch
    axial_pitch = module * pi
    
    # Lead
    lead = axial_pitch * num_starts
    
    # Lead angle
    lead_angle_rad = atan(lead / (pi * pitch_diameter))
    lead_angle = degrees(lead_angle_rad)
    
    # Tooth proportions
    addendum = module
    dedendum = module * (1 + clearance_factor)
    
    # Diameters
    tip_diameter = pitch_diameter + 2 * addendum
    root_diameter = pitch_diameter - 2 * dedendum
    
    # Thread thickness at pitch line (nominal is half axial pitch)
    # Reduce by backlash allowance
    thread_thickness = (axial_pitch / 2) - backlash
    
    return WormParameters(
        module=module,
        num_starts=num_starts,
        pitch_diameter=pitch_diameter,
        tip_diameter=tip_diameter,
        root_diameter=root_diameter,
        lead=lead,
        axial_pitch=axial_pitch,
        lead_angle=lead_angle,
        addendum=addendum,
        dedendum=dedendum,
        thread_thickness=thread_thickness
    )


def calculate_wheel(
    module: float,
    num_teeth: int,
    worm_pitch_diameter: float,
    worm_lead_angle: float,
    pressure_angle: float = 20.0,
    clearance_factor: float = 0.25
) -> WheelParameters:
    """
    Calculate worm wheel dimensions.
    
    Args:
        module: Transverse module (= worm axial module) (mm)
        num_teeth: Number of teeth
        worm_pitch_diameter: Pitch diameter of mating worm (mm)
        worm_lead_angle: Lead angle of mating worm (degrees)
        pressure_angle: Pressure angle (degrees)
        clearance_factor: Bottom clearance as fraction of module
    
    Returns:
        WheelParameters with all dimensions
    """
    # Pitch diameter
    pitch_diameter = module * num_teeth
    
    # Tooth proportions
    addendum = module
    dedendum = module * (1 + clearance_factor)
    
    # Diameters
    tip_diameter = pitch_diameter + 2 * addendum
    root_diameter = pitch_diameter - 2 * dedendum
    
    # Throat diameter (for enveloping geometry)
    # This is the diameter at the deepest point of the throat
    throat_diameter = pitch_diameter + module  # Simplified
    
    # Helix angle = 90° - lead angle (for perpendicular axes)
    helix_angle = 90.0 - worm_lead_angle
    
    return WheelParameters(
        module=module,
        num_teeth=num_teeth,
        pitch_diameter=pitch_diameter,
        tip_diameter=tip_diameter,
        root_diameter=root_diameter,
        throat_diameter=throat_diameter,
        helix_angle=helix_angle,
        addendum=addendum,
        dedendum=dedendum
    )


def calculate_centre_distance(
    worm_pitch_diameter: float,
    wheel_pitch_diameter: float
) -> float:
    """Calculate centre distance between worm and wheel axes"""
    return (worm_pitch_diameter + wheel_pitch_diameter) / 2


def design_from_envelope(
    worm_od: float,
    wheel_od: float,
    ratio: int,
    pressure_angle: float = 20.0,
    backlash: float = 0.0,
    num_starts: int = 1,
    clearance_factor: float = 0.25,
    hand: Hand = Hand.RIGHT
) -> WormGearDesign:
    """
    Design worm gear pair from outside diameter constraints.
    
    Args:
        worm_od: Worm outside/tip diameter (mm)
        wheel_od: Wheel outside/tip diameter (mm)
        ratio: Gear ratio (must be divisible by num_starts)
        pressure_angle: Pressure angle (degrees)
        backlash: Backlash allowance (mm)
        num_starts: Number of worm starts
        clearance_factor: Bottom clearance factor
        hand: Thread hand
    
    Returns:
        WormGearDesign with all parameters
    """
    # Number of teeth on wheel
    num_teeth = ratio * num_starts
    
    # Calculate module from wheel OD
    # tip_diameter = module × (num_teeth + 2)
    module = wheel_od / (num_teeth + 2)
    
    # Worm pitch diameter from OD
    addendum = module
    worm_pitch_diameter = worm_od - 2 * addendum
    
    # Calculate components
    worm = calculate_worm(
        module=module,
        num_starts=num_starts,
        pitch_diameter=worm_pitch_diameter,
        pressure_angle=pressure_angle,
        clearance_factor=clearance_factor,
        backlash=backlash
    )
    
    wheel = calculate_wheel(
        module=module,
        num_teeth=num_teeth,
        worm_pitch_diameter=worm_pitch_diameter,
        worm_lead_angle=worm.lead_angle,
        pressure_angle=pressure_angle,
        clearance_factor=clearance_factor
    )
    
    centre_distance = calculate_centre_distance(
        worm.pitch_diameter,
        wheel.pitch_diameter
    )
    
    return WormGearDesign(
        worm=worm,
        wheel=wheel,
        centre_distance=centre_distance,
        ratio=ratio,
        pressure_angle=pressure_angle,
        backlash=backlash,
        hand=hand,
        efficiency_estimate=0,  # Set in __post_init__
        self_locking=False      # Set in __post_init__
    )


def design_from_wheel(
    wheel_od: float,
    ratio: int,
    target_lead_angle: float = 7.0,
    pressure_angle: float = 20.0,
    backlash: float = 0.0,
    num_starts: int = 1,
    clearance_factor: float = 0.25,
    hand: Hand = Hand.RIGHT
) -> WormGearDesign:
    """
    Design worm gear pair from wheel OD constraint.
    Worm sized to achieve target lead angle.
    
    Args:
        wheel_od: Wheel outside/tip diameter (mm)
        ratio: Gear ratio
        target_lead_angle: Desired lead angle (degrees)
        pressure_angle: Pressure angle (degrees)
        backlash: Backlash allowance (mm)
        num_starts: Number of worm starts
        clearance_factor: Bottom clearance factor
        hand: Thread hand
    
    Returns:
        WormGearDesign with all parameters
    """
    # Number of teeth on wheel
    num_teeth = ratio * num_starts
    
    # Calculate module from wheel OD
    module = wheel_od / (num_teeth + 2)
    
    # Calculate worm pitch diameter for target lead angle
    # lead_angle = atan(lead / (π × pitch_dia))
    # pitch_dia = lead / (π × tan(lead_angle))
    lead = pi * module * num_starts
    target_rad = radians(target_lead_angle)
    worm_pitch_diameter = lead / (pi * tan(target_rad))
    
    # Worm OD
    addendum = module
    worm_od = worm_pitch_diameter + 2 * addendum
    
    return design_from_envelope(
        worm_od=worm_od,
        wheel_od=wheel_od,
        ratio=ratio,
        pressure_angle=pressure_angle,
        backlash=backlash,
        num_starts=num_starts,
        clearance_factor=clearance_factor,
        hand=hand
    )


def design_from_module(
    module: float,
    ratio: int,
    worm_pitch_diameter: Optional[float] = None,
    target_lead_angle: float = 7.0,
    pressure_angle: float = 20.0,
    backlash: float = 0.0,
    num_starts: int = 1,
    clearance_factor: float = 0.25,
    hand: Hand = Hand.RIGHT
) -> WormGearDesign:
    """
    Design worm gear pair from module specification.
    
    Args:
        module: Module (mm) - typically a standard value
        ratio: Gear ratio
        worm_pitch_diameter: Worm pitch diameter (mm), or None to calculate from lead angle
        target_lead_angle: Target lead angle if worm_pitch_diameter not specified (degrees)
        pressure_angle: Pressure angle (degrees)
        backlash: Backlash allowance (mm)
        num_starts: Number of worm starts
        clearance_factor: Bottom clearance factor
        hand: Thread hand
    
    Returns:
        WormGearDesign with all parameters
    """
    # Number of teeth on wheel
    num_teeth = ratio * num_starts
    
    # Wheel OD
    addendum = module
    wheel_od = module * num_teeth + 2 * addendum
    
    # Worm pitch diameter
    if worm_pitch_diameter is None:
        # Calculate for target lead angle
        lead = pi * module * num_starts
        target_rad = radians(target_lead_angle)
        worm_pitch_diameter = lead / (pi * tan(target_rad))
    
    # Worm OD
    worm_od = worm_pitch_diameter + 2 * addendum
    
    return design_from_envelope(
        worm_od=worm_od,
        wheel_od=wheel_od,
        ratio=ratio,
        pressure_angle=pressure_angle,
        backlash=backlash,
        num_starts=num_starts,
        clearance_factor=clearance_factor,
        hand=hand
    )


def design_from_centre_distance(
    centre_distance: float,
    ratio: int,
    worm_to_wheel_ratio: float = 0.3,
    pressure_angle: float = 20.0,
    backlash: float = 0.0,
    num_starts: int = 1,
    clearance_factor: float = 0.25,
    hand: Hand = Hand.RIGHT
) -> WormGearDesign:
    """
    Design worm gear pair from centre distance constraint.
    
    Args:
        centre_distance: Required centre distance (mm)
        ratio: Gear ratio
        worm_to_wheel_ratio: Ratio of worm pitch dia to wheel pitch dia (affects lead angle)
        pressure_angle: Pressure angle (degrees)
        backlash: Backlash allowance (mm)
        num_starts: Number of worm starts
        clearance_factor: Bottom clearance factor
        hand: Thread hand
    
    Returns:
        WormGearDesign with all parameters
    """
    # Number of teeth on wheel
    num_teeth = ratio * num_starts
    
    # Solve for diameters
    # centre_distance = (worm_pd + wheel_pd) / 2
    # wheel_pd = module × num_teeth
    # worm_pd = k × wheel_pd (where k = worm_to_wheel_ratio)
    # 
    # 2 × cd = k × wheel_pd + wheel_pd = wheel_pd × (k + 1)
    # wheel_pd = 2 × cd / (k + 1)
    
    wheel_pitch_diameter = 2 * centre_distance / (worm_to_wheel_ratio + 1)
    worm_pitch_diameter = centre_distance * 2 - wheel_pitch_diameter
    
    # Module from wheel
    module = wheel_pitch_diameter / num_teeth
    
    # ODs
    addendum = module
    worm_od = worm_pitch_diameter + 2 * addendum
    wheel_od = wheel_pitch_diameter + 2 * addendum
    
    return design_from_envelope(
        worm_od=worm_od,
        wheel_od=wheel_od,
        ratio=ratio,
        pressure_angle=pressure_angle,
        backlash=backlash,
        num_starts=num_starts,
        clearance_factor=clearance_factor,
        hand=hand
    )
