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


class WormProfile(Enum):
    """Worm tooth profile type per DIN 3975"""
    ZA = "ZA"  # Straight trapezoidal flanks - best for CNC machining
    ZK = "ZK"  # Slightly convex flanks - better for 3D printing (FDM layer adhesion)


class WormType(Enum):
    """Worm geometry type"""
    CYLINDRICAL = "cylindrical"  # Standard cylindrical worm
    GLOBOID = "globoid"  # Hourglass-shaped worm for better contact


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
    # Globoid worm parameters (only set when worm_type is GLOBOID)
    throat_reduction: Optional[float] = None     # Throat reduction from nominal (mm)
    throat_pitch_radius: Optional[float] = None  # Pitch radius at throat (mm)
    throat_tip_radius: Optional[float] = None    # Outer radius at throat (mm)
    throat_root_radius: Optional[float] = None   # Inner radius at throat (mm)

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
    profile_shift: float = 0.0      # Profile shift coefficient (dimensionless)
    
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
class ManufacturingParams:
    """Manufacturing parameters for geometry generation (worm-gear-3d compatibility)"""
    worm_type: WormType = WormType.CYLINDRICAL  # Worm geometry type
    worm_length: float = 40.0                   # Suggested worm length (mm)
    wheel_width: Optional[float] = None         # Suggested wheel face width (mm), None for auto
    wheel_throated: bool = False                # True for hobbed/throated teeth, False for helical
    profile: WormProfile = WormProfile.ZA       # Tooth profile type per DIN 3975
    max_wheel_width: Optional[float] = None     # Maximum wheel width to avoid gaps (mm) - globoid only
    recommended_wheel_width: Optional[float] = None  # Recommended wheel width (mm)


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

    # Performance estimates (calculated in __post_init__)
    efficiency_estimate: float = field(default=0.0)  # Estimated efficiency (0-1)
    self_locking: bool = field(default=False)        # Whether drive is self-locking

    # Optional parameters with defaults
    profile: WormProfile = WormProfile.ZA  # Tooth profile type per DIN 3975

    # Manufacturing parameters for geometry generation
    manufacturing: Optional[ManufacturingParams] = None

    def __post_init__(self):
        # Calculate efficiency and self-locking based on lead angle
        self.efficiency_estimate = estimate_efficiency(
            self.worm.lead_angle,
            self.pressure_angle
        )
        self.self_locking = self.worm.lead_angle < 6.0  # Conservative threshold

        # Initialize manufacturing params if not provided
        if self.manufacturing is None:
            self.manufacturing = ManufacturingParams(profile=self.profile)


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
    clearance_factor: float = 0.25,
    profile_shift: float = 0.0
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
        profile_shift: Profile shift coefficient (dimensionless, default 0.0)
                      Positive shift increases addendum, decreases dedendum

    Returns:
        WheelParameters with all dimensions
    """
    # Pitch diameter (unaffected by profile shift)
    pitch_diameter = module * num_teeth

    # Tooth proportions with profile shift
    # Profile shift moves the reference line relative to the pitch circle
    addendum = module * (1.0 + profile_shift)
    dedendum = module * (1.0 + clearance_factor - profile_shift)

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
        dedendum=dedendum,
        profile_shift=profile_shift
    )


def calculate_centre_distance(
    worm_pitch_diameter: float,
    wheel_pitch_diameter: float
) -> float:
    """Calculate centre distance between worm and wheel axes"""
    return (worm_pitch_diameter + wheel_pitch_diameter) / 2


def calculate_globoid_throat_radii(
    centre_distance: float,
    wheel_pitch_diameter: float,
    addendum: float,
    dedendum: float
) -> Tuple[float, float, float]:
    """
    Calculate throat radii for a globoid (hourglass) worm.

    For a globoid worm, the throat (waist) radius is sized to contact
    the wheel at the correct center distance.

    Args:
        centre_distance: Center distance between axes (mm)
        wheel_pitch_diameter: Wheel pitch diameter (mm)
        addendum: Tooth addendum (mm)
        dedendum: Tooth dedendum (mm)

    Returns:
        Tuple of (throat_pitch_radius, throat_tip_radius, throat_root_radius)
    """
    wheel_pitch_radius = wheel_pitch_diameter / 2
    throat_pitch_radius = centre_distance - wheel_pitch_radius
    throat_tip_radius = throat_pitch_radius + addendum
    throat_root_radius = throat_pitch_radius - dedendum
    return throat_pitch_radius, throat_tip_radius, throat_root_radius


def calculate_max_wheel_width_for_globoid(
    throat_reduction: float,
    worm_pitch_radius: float,
    wheel_root_radius: float,
    centre_distance: float,
    addendum: float,
    dedendum: float,
    safety_factor: float = 0.8
) -> Tuple[float, float]:
    """
    Calculate maximum wheel width for a globoid worm to avoid gaps at edges.

    The hourglass shape means the worm radius varies along its length.
    If the wheel is too wide, the worm won't cut deep enough at the edges,
    creating gaps between worm and wheel.

    This uses an empirically-derived model based on the relationship between
    throat reduction and allowable wheel width.

    Args:
        throat_reduction: Throat reduction from nominal (mm)
        worm_pitch_radius: Nominal worm pitch radius (mm)
        wheel_root_radius: Wheel root radius (mm)
        centre_distance: Centre distance (mm)
        addendum: Worm addendum (mm)
        dedendum: Worm dedendum (mm)
        safety_factor: Safety factor for clearance (default 0.8)

    Returns:
        Tuple of (max_width, recommended_width) in mm
    """
    if throat_reduction <= 0.001:
        # Essentially cylindrical - no constraint
        return float('inf'), worm_pitch_radius * 1.3

    # Empirical model based on real-world constraints:
    # The throat reduction creates a varying radius along the worm length.
    # The wheel width is limited by how much the radius can vary while
    # still maintaining proper mesh.

    # Key insight: The allowable wheel width is roughly proportional to
    # the worm diameter divided by the throat reduction severity.

    # Calculate throat reduction ratio (relative to worm size)
    throat_ratio = throat_reduction / (worm_pitch_radius * 2)  # As fraction of diameter

    # Empirical formula: max_width ≈ worm_diameter * k / throat_ratio
    # where k is a constant (≈ 0.15 based on real examples)
    # This gives: for 0.05mm reduction on 6.8mm diameter (ratio ≈ 0.0074),
    #             max_width ≈ 6.8 * 0.15 / 0.0074 ≈ 138mm (way too large, so we cap it)

    # Alternative empirical approach based on user's example:
    # 0.05mm reduction → 1.5mm max width
    # This suggests max_width ≈ throat_reduction * 30 (for small gears)

    # More sophisticated model:
    # The transition from throat to nominal happens over a length roughly
    # equal to the worm pitch diameter. The wheel width should be small enough
    # that the radius variation over half the wheel width is acceptable.

    # For a taper/transition: radius increases by throat_reduction over length ≈ worm_diameter
    # So over distance z: radius_increase ≈ throat_reduction * (z / worm_diameter)
    # We want: radius_increase < addendum (roughly)
    # So: throat_reduction * (half_width / worm_diameter) < addendum * safety_factor
    # half_width < (addendum * safety_factor * worm_diameter) / throat_reduction
    # width < 2 * (addendum * safety_factor * worm_diameter) / throat_reduction

    worm_diameter = worm_pitch_radius * 2
    max_half_width = (addendum * safety_factor * worm_diameter) / throat_reduction
    max_width = 2 * max_half_width

    # Apply practical limits
    # Max width shouldn't exceed worm diameter
    max_width = min(max_width, worm_diameter * 0.8)

    # Also shouldn't be much larger than pitch radius
    max_width = min(max_width, worm_pitch_radius * 1.0)

    # Recommended width is more conservative (70% of max)
    recommended_width = max_width * 0.7

    # Ensure minimum practical values
    min_practical_width = addendum * 3  # At least 3× addendum
    max_width = max(max_width, min_practical_width)
    recommended_width = max(recommended_width, min_practical_width * 0.7)

    return max_width, recommended_width


def calculate_manufacturing_params(
    worm_lead: float,
    module: float,
    worm_type: WormType = WormType.CYLINDRICAL,
    wheel_throated: bool = False,
    profile: WormProfile = WormProfile.ZA,
    worm_pitch_diameter: Optional[float] = None,
    throat_reduction: Optional[float] = None,
    centre_distance: Optional[float] = None,
    wheel_root_radius: Optional[float] = None,
    addendum: Optional[float] = None,
    dedendum: Optional[float] = None
) -> ManufacturingParams:
    """
    Calculate suggested manufacturing parameters.

    Args:
        worm_lead: Worm lead (mm)
        module: Module (mm)
        worm_type: Type of worm geometry
        wheel_throated: Whether wheel has throated teeth
        profile: Tooth profile type
        worm_pitch_diameter: Worm pitch diameter for globoid calculations (mm)
        throat_reduction: Throat reduction for globoid (mm)
        centre_distance: Centre distance for globoid calculations (mm)
        wheel_root_radius: Wheel root radius for globoid calculations (mm)
        addendum: Addendum for globoid calculations (mm)
        dedendum: Dedendum for globoid calculations (mm)

    Returns:
        ManufacturingParams with suggested dimensions
    """
    max_wheel_width = None
    recommended_wheel_width = None

    # Calculate wheel width constraints for globoid
    if worm_type == WormType.GLOBOID and worm_pitch_diameter is not None:
        worm_pitch_radius = worm_pitch_diameter / 2

        if (throat_reduction is not None and throat_reduction > 0 and
            centre_distance is not None and wheel_root_radius is not None and
            addendum is not None and dedendum is not None):

            # Calculate max wheel width based on hourglass geometry
            max_width, recommended_width = calculate_max_wheel_width_for_globoid(
                throat_reduction=throat_reduction,
                worm_pitch_radius=worm_pitch_radius,
                wheel_root_radius=wheel_root_radius,
                centre_distance=centre_distance,
                addendum=addendum,
                dedendum=dedendum
            )

            max_wheel_width = max_width
            recommended_wheel_width = recommended_width
            wheel_width = recommended_width
        else:
            # Fallback to simple rule if we don't have all parameters
            wheel_width = min(worm_pitch_diameter * 0.67, module * 10.0)
            recommended_wheel_width = wheel_width
    else:
        # For cylindrical: ~10× module
        wheel_width = module * 10.0
        recommended_wheel_width = wheel_width

    # Calculate worm length
    # Base calculation: ~4× lead for cylindrical, ~3× lead for globoid
    if worm_type == WormType.CYLINDRICAL:
        base_worm_length = max(worm_lead * 4.0, module * 10)
    else:  # GLOBOID
        # For globoid, need extra length for transition zones
        # Transition zone: ~1× throat_reduction on each side of engagement
        transition_per_side = throat_reduction if throat_reduction else 0
        base_worm_length = max(worm_lead * 3.0, module * 8)

    # Ensure worm length is adequate for wheel width
    # Worm should extend at least 1.5× wheel width for proper engagement
    # Plus transition zones for globoid
    min_worm_length = wheel_width * 1.5

    if worm_type == WormType.GLOBOID and throat_reduction:
        # Add transition zones: 2× throat reduction on each side
        min_worm_length += 4 * throat_reduction

    worm_length = max(base_worm_length, min_worm_length)

    return ManufacturingParams(
        worm_type=worm_type,
        worm_length=round(worm_length, 2),
        wheel_width=round(wheel_width, 2),
        wheel_throated=wheel_throated,
        profile=profile,
        max_wheel_width=round(max_wheel_width, 2) if max_wheel_width is not None and max_wheel_width != float('inf') else None,
        recommended_wheel_width=round(recommended_wheel_width, 2) if recommended_wheel_width is not None else None
    )


def design_from_envelope(
    worm_od: float,
    wheel_od: float,
    ratio: int,
    pressure_angle: float = 20.0,
    backlash: float = 0.0,
    num_starts: int = 1,
    clearance_factor: float = 0.25,
    hand: Hand = Hand.RIGHT,
    profile_shift: float = 0.0,
    profile: WormProfile = WormProfile.ZA,
    worm_type: WormType = WormType.CYLINDRICAL,
    throat_reduction: float = 0.0,
    wheel_throated: bool = False
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
        profile_shift: Profile shift coefficient for wheel (dimensionless, default 0.0)
        profile: Tooth profile type per DIN 3975 (ZA or ZK)
        worm_type: Worm geometry type (cylindrical or globoid)
        throat_reduction: Throat reduction for globoid worms (mm, default 0.0)
                         Typical: 0.05-0.1mm for small gears, 0.1-0.2mm for medium
        wheel_throated: Whether wheel has throated teeth (hobbed)

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
    dedendum = module * (1 + clearance_factor)
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
        clearance_factor=clearance_factor,
        profile_shift=profile_shift
    )

    # Calculate centre distance
    # For cylindrical: standard calculation
    # For globoid: reduce by throat_reduction to create hourglass effect
    standard_centre_distance = calculate_centre_distance(
        worm.pitch_diameter,
        wheel.pitch_diameter
    )

    if worm_type == WormType.GLOBOID:
        centre_distance = standard_centre_distance - throat_reduction
    else:
        centre_distance = standard_centre_distance

    # Calculate globoid throat radii if needed
    if worm_type == WormType.GLOBOID:
        throat_pitch, throat_tip, throat_root = calculate_globoid_throat_radii(
            centre_distance=centre_distance,
            wheel_pitch_diameter=wheel.pitch_diameter,
            addendum=worm.addendum,
            dedendum=worm.dedendum
        )
        # Update worm with throat parameters
        worm = WormParameters(
            module=worm.module,
            num_starts=worm.num_starts,
            pitch_diameter=worm.pitch_diameter,
            tip_diameter=worm.tip_diameter,
            root_diameter=worm.root_diameter,
            lead=worm.lead,
            axial_pitch=worm.axial_pitch,
            lead_angle=worm.lead_angle,
            addendum=worm.addendum,
            dedendum=worm.dedendum,
            thread_thickness=worm.thread_thickness,
            throat_reduction=throat_reduction,
            throat_pitch_radius=throat_pitch,
            throat_tip_radius=throat_tip,
            throat_root_radius=throat_root
        )

    # Calculate manufacturing parameters
    manufacturing = calculate_manufacturing_params(
        worm_lead=worm.lead,
        module=module,
        worm_type=worm_type,
        wheel_throated=wheel_throated,
        profile=profile,
        worm_pitch_diameter=worm.pitch_diameter,
        throat_reduction=throat_reduction if worm_type == WormType.GLOBOID else None,
        centre_distance=centre_distance,
        wheel_root_radius=wheel.root_radius,
        addendum=addendum,
        dedendum=dedendum
    )

    return WormGearDesign(
        worm=worm,
        wheel=wheel,
        centre_distance=centre_distance,
        ratio=ratio,
        pressure_angle=pressure_angle,
        backlash=backlash,
        hand=hand,
        profile=profile,
        efficiency_estimate=0,  # Set in __post_init__
        self_locking=False,     # Set in __post_init__
        manufacturing=manufacturing
    )


def design_from_wheel(
    wheel_od: float,
    ratio: int,
    target_lead_angle: float = 7.0,
    pressure_angle: float = 20.0,
    backlash: float = 0.0,
    num_starts: int = 1,
    clearance_factor: float = 0.25,
    hand: Hand = Hand.RIGHT,
    profile_shift: float = 0.0,
    profile: WormProfile = WormProfile.ZA,
    worm_type: WormType = WormType.CYLINDRICAL,
    throat_reduction: float = 0.0,
    wheel_throated: bool = False
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
        profile_shift: Profile shift coefficient for wheel (dimensionless, default 0.0)
        profile: Tooth profile type per DIN 3975 (ZA or ZK)
        worm_type: Worm geometry type (cylindrical or globoid)
        throat_reduction: Throat reduction for globoid worms (mm, default 0.0)
        wheel_throated: Whether wheel has throated teeth (hobbed)

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
    worm_pitch_diameter_cylindrical = lead / (pi * tan(target_rad))

    # For globoid, increase pitch diameter to create hourglass effect
    if worm_type == WormType.GLOBOID:
        worm_pitch_diameter = worm_pitch_diameter_cylindrical + 2 * throat_reduction
    else:
        worm_pitch_diameter = worm_pitch_diameter_cylindrical

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
        hand=hand,
        profile_shift=profile_shift,
        profile=profile,
        worm_type=worm_type,
        throat_reduction=throat_reduction,
        wheel_throated=wheel_throated
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
    hand: Hand = Hand.RIGHT,
    profile_shift: float = 0.0,
    profile: WormProfile = WormProfile.ZA,
    worm_type: WormType = WormType.CYLINDRICAL,
    throat_reduction: float = 0.0,
    wheel_throated: bool = False
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
        profile_shift: Profile shift coefficient for wheel (dimensionless, default 0.0)
        profile: Tooth profile type per DIN 3975 (ZA or ZK)
        worm_type: Worm geometry type (cylindrical or globoid)
        throat_reduction: Throat reduction for globoid worms (mm, default 0.0)
        wheel_throated: Whether wheel has throated teeth (hobbed)

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
        worm_pitch_diameter_cylindrical = lead / (pi * tan(target_rad))

        # For globoid, increase pitch diameter to create hourglass effect
        if worm_type == WormType.GLOBOID:
            worm_pitch_diameter = worm_pitch_diameter_cylindrical + 2 * throat_reduction
        else:
            worm_pitch_diameter = worm_pitch_diameter_cylindrical
    # else: use provided worm_pitch_diameter (assumed to be nominal for globoid)

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
        hand=hand,
        profile_shift=profile_shift,
        profile=profile,
        worm_type=worm_type,
        throat_reduction=throat_reduction,
        wheel_throated=wheel_throated
    )


def design_from_centre_distance(
    centre_distance: float,
    ratio: int,
    worm_to_wheel_ratio: float = 0.3,
    pressure_angle: float = 20.0,
    backlash: float = 0.0,
    num_starts: int = 1,
    clearance_factor: float = 0.25,
    hand: Hand = Hand.RIGHT,
    profile_shift: float = 0.0,
    profile: WormProfile = WormProfile.ZA,
    worm_type: WormType = WormType.CYLINDRICAL,
    throat_reduction: float = 0.0,
    wheel_throated: bool = False
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
        profile_shift: Profile shift coefficient for wheel (dimensionless, default 0.0)
        profile: Tooth profile type per DIN 3975 (ZA or ZK)
        worm_type: Worm geometry type (cylindrical or globoid)
        throat_reduction: Throat reduction for globoid worms (mm, default 0.0)
        wheel_throated: Whether wheel has throated teeth (hobbed)

    Returns:
        WormGearDesign with all parameters
    """
    # Number of teeth on wheel
    num_teeth = ratio * num_starts

    # For globoid, the given centre_distance is the actual distance
    # We need to calculate what the standard centre would be
    # standard_centre = centre_distance + throat_reduction
    if worm_type == WormType.GLOBOID:
        standard_centre_distance = centre_distance + throat_reduction
    else:
        standard_centre_distance = centre_distance

    # Solve for diameters
    # standard_centre_distance = (worm_pd + wheel_pd) / 2
    # wheel_pd = module × num_teeth
    # worm_pd = k × wheel_pd (where k = worm_to_wheel_ratio)
    #
    # 2 × cd = k × wheel_pd + wheel_pd = wheel_pd × (k + 1)
    # wheel_pd = 2 × cd / (k + 1)

    wheel_pitch_diameter = 2 * standard_centre_distance / (worm_to_wheel_ratio + 1)
    worm_pitch_diameter = standard_centre_distance * 2 - wheel_pitch_diameter

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
        hand=hand,
        profile_shift=profile_shift,
        profile=profile,
        worm_type=worm_type,
        throat_reduction=throat_reduction,
        wheel_throated=wheel_throated
    )
