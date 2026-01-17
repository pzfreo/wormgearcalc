"""
Worm Gear Calculator - Validation Rules

Engineering validation based on:
- DIN 3975 / DIN 3996 standards
- Common engineering practice
- Manufacturing constraints
"""

from dataclasses import dataclass, field
from typing import List, Optional
from enum import Enum

from .core import (
    WormGearDesign, DesignResult,
    is_standard_module, nearest_standard_module,
    STANDARD_MODULES
)
from math import sin, radians


def calculate_minimum_teeth(pressure_angle_deg: float) -> int:
    """
    Calculate minimum teeth without undercut for given pressure angle.

    Formula: z_min = 2 / sin²(α)

    Args:
        pressure_angle_deg: Pressure angle in degrees

    Returns:
        Minimum number of teeth (rounded up)
    """
    alpha_rad = radians(pressure_angle_deg)
    sin_alpha = sin(alpha_rad)
    z_min = 2.0 / (sin_alpha ** 2)
    return int(z_min) + 1  # Round up for safety


def calculate_profile_shift(num_teeth: int, pressure_angle_deg: float) -> Optional[float]:
    """
    Calculate recommended profile shift coefficient to avoid undercut.

    Profile shift (x) moves the tooth away from the blank to eliminate undercut.
    Positive shift increases addendum, decreases dedendum.

    Args:
        num_teeth: Number of teeth
        pressure_angle_deg: Pressure angle in degrees

    Returns:
        Recommended profile shift coefficient (dimensionless), or None if not needed
    """
    z_min = calculate_minimum_teeth(pressure_angle_deg)

    if num_teeth >= z_min:
        return None  # No shift needed

    # Formula for minimum profile shift to avoid undercut:
    # x_min = (z_min - z) / z_min
    # We add a small safety factor
    x_min = (z_min - num_teeth) / z_min * 1.1

    # Clamp to reasonable range
    return min(max(x_min, 0.0), 0.8)


class Severity(Enum):
    """Validation message severity"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"


@dataclass
class ValidationMessage:
    """A single validation finding"""
    severity: Severity
    code: str
    message: str
    suggestion: Optional[str] = None


@dataclass 
class ValidationResult:
    """Complete validation result"""
    valid: bool  # True if no errors
    messages: List[ValidationMessage] = field(default_factory=list)
    
    @property
    def errors(self) -> List[ValidationMessage]:
        return [m for m in self.messages if m.severity == Severity.ERROR]
    
    @property
    def warnings(self) -> List[ValidationMessage]:
        return [m for m in self.messages if m.severity == Severity.WARNING]
    
    @property
    def infos(self) -> List[ValidationMessage]:
        return [m for m in self.messages if m.severity == Severity.INFO]


def validate_design(design: WormGearDesign) -> ValidationResult:
    """
    Validate a worm gear design against engineering rules.
    
    Returns ValidationResult with all findings.
    """
    messages: List[ValidationMessage] = []
    
    # Run all validation checks
    messages.extend(_validate_lead_angle(design))
    messages.extend(_validate_module(design))
    messages.extend(_validate_teeth_count(design))
    messages.extend(_validate_worm_proportions(design))
    messages.extend(_validate_pressure_angle(design))
    messages.extend(_validate_efficiency(design))
    messages.extend(_validate_centre_distance(design))
    
    # Design is valid if no errors
    has_errors = any(m.severity == Severity.ERROR for m in messages)
    
    return ValidationResult(
        valid=not has_errors,
        messages=messages
    )


def _validate_lead_angle(design: WormGearDesign) -> List[ValidationMessage]:
    """Check lead angle is within practical range"""
    messages = []
    lead_angle = design.worm.lead_angle
    
    if lead_angle < 1.0:
        messages.append(ValidationMessage(
            severity=Severity.ERROR,
            code="LEAD_ANGLE_TOO_LOW",
            message=f"Lead angle {lead_angle:.1f}° is too low for practical manufacture",
            suggestion="Increase worm pitch diameter or reduce module"
        ))
    elif lead_angle < 3.0:
        messages.append(ValidationMessage(
            severity=Severity.WARNING,
            code="LEAD_ANGLE_VERY_LOW",
            message=f"Lead angle {lead_angle:.1f}° is very low. Efficiency ~{design.efficiency_estimate*100:.0f}%",
            suggestion="Consider increasing worm diameter for better efficiency"
        ))
    elif lead_angle < 5.0:
        messages.append(ValidationMessage(
            severity=Severity.INFO,
            code="LEAD_ANGLE_LOW",
            message=f"Lead angle {lead_angle:.1f}° gives low efficiency (~{design.efficiency_estimate*100:.0f}%) but good self-locking",
            suggestion=None
        ))
    elif lead_angle > 25.0:
        messages.append(ValidationMessage(
            severity=Severity.WARNING,
            code="LEAD_ANGLE_HIGH",
            message=f"Lead angle {lead_angle:.1f}° is high. Drive will not self-lock.",
            suggestion="This is fine if self-locking is not required"
        ))
    elif lead_angle > 45.0:
        messages.append(ValidationMessage(
            severity=Severity.ERROR,
            code="LEAD_ANGLE_TOO_HIGH",
            message=f"Lead angle {lead_angle:.1f}° exceeds practical limits",
            suggestion="Reduce worm pitch diameter or increase module"
        ))
    
    return messages


def _validate_module(design: WormGearDesign) -> List[ValidationMessage]:
    """Check module is standard or flag non-standard"""
    messages = []
    module = design.worm.module
    
    if not is_standard_module(module):
        nearest = nearest_standard_module(module)
        deviation = abs(module - nearest) / nearest * 100
        
        if deviation > 10:
            messages.append(ValidationMessage(
                severity=Severity.WARNING,
                code="MODULE_NON_STANDARD",
                message=f"Module {module:.3f}mm is non-standard (ISO 54)",
                suggestion=f"Nearest standard module: {nearest}mm. Consider adjusting envelope constraints."
            ))
        else:
            messages.append(ValidationMessage(
                severity=Severity.INFO,
                code="MODULE_NEAR_STANDARD",
                message=f"Module {module:.3f}mm is close to standard {nearest}mm",
                suggestion=f"Could round to {nearest}mm with minor OD changes"
            ))
    
    # Check module is reasonable size
    if module < 0.3:
        messages.append(ValidationMessage(
            severity=Severity.ERROR,
            code="MODULE_TOO_SMALL",
            message=f"Module {module:.3f}mm is too small for practical worm gears",
            suggestion="Minimum practical module is ~0.3mm for precision applications"
        ))
    elif module < 0.5:
        messages.append(ValidationMessage(
            severity=Severity.WARNING,
            code="MODULE_VERY_SMALL",
            message=f"Module {module:.3f}mm requires precision manufacturing",
            suggestion="Consider if tolerances are achievable"
        ))
    
    return messages


def _validate_teeth_count(design: WormGearDesign) -> List[ValidationMessage]:
    """Check wheel tooth count with pressure angle consideration"""
    messages = []
    num_teeth = design.wheel.num_teeth
    pressure_angle = design.pressure_angle

    # Calculate minimum teeth for this pressure angle
    z_min = calculate_minimum_teeth(pressure_angle)

    # Calculate recommended profile shift if needed
    recommended_shift = calculate_profile_shift(num_teeth, pressure_angle)

    if num_teeth < z_min:
        if recommended_shift is not None:
            messages.append(ValidationMessage(
                severity=Severity.ERROR,
                code="TEETH_TOO_FEW",
                message=f"Wheel has {num_teeth} teeth (min {z_min} for {pressure_angle}° pressure angle without undercut)",
                suggestion=f"Apply profile shift coefficient x = {recommended_shift:.3f} or increase to {z_min}+ teeth"
            ))
        else:
            messages.append(ValidationMessage(
                severity=Severity.ERROR,
                code="TEETH_TOO_FEW",
                message=f"Wheel has {num_teeth} teeth - severe undercut risk",
                suggestion=f"Increase to minimum {z_min} teeth for {pressure_angle}° pressure angle"
            ))
    elif num_teeth < z_min * 1.4:  # Within 40% of minimum
        if recommended_shift is not None:
            messages.append(ValidationMessage(
                severity=Severity.WARNING,
                code="TEETH_LOW",
                message=f"Wheel has {num_teeth} teeth - some undercut risk at {pressure_angle}° pressure angle",
                suggestion=f"Consider profile shift x = {recommended_shift:.3f} for better tooth form"
            ))
        else:
            messages.append(ValidationMessage(
                severity=Severity.INFO,
                code="TEETH_ACCEPTABLE",
                message=f"Wheel has {num_teeth} teeth - acceptable for {pressure_angle}° pressure angle",
                suggestion=None
            ))
    elif num_teeth > 100:
        messages.append(ValidationMessage(
            severity=Severity.INFO,
            code="TEETH_HIGH",
            message=f"Wheel has {num_teeth} teeth - large gear, verify space available",
            suggestion=None
        ))

    return messages


def _validate_worm_proportions(design: WormGearDesign) -> List[ValidationMessage]:
    """Check worm diameter proportions"""
    messages = []
    
    worm = design.worm
    module = worm.module
    
    # Check pitch diameter relative to module
    # Rule of thumb: pitch_dia >= 4 × module for adequate shaft strength
    dia_to_module = worm.pitch_diameter / module
    
    if dia_to_module < 3:
        messages.append(ValidationMessage(
            severity=Severity.ERROR,
            code="WORM_TOO_THIN",
            message=f"Worm pitch diameter is only {dia_to_module:.1f}× module - shaft will be weak",
            suggestion="Increase worm diameter or reduce module"
        ))
    elif dia_to_module < 5:
        messages.append(ValidationMessage(
            severity=Severity.WARNING,
            code="WORM_THIN",
            message=f"Worm pitch diameter is {dia_to_module:.1f}× module - verify shaft strength",
            suggestion="Consider increasing worm diameter"
        ))
    
    # Check root diameter is positive and reasonable
    if worm.root_diameter < 2:
        messages.append(ValidationMessage(
            severity=Severity.ERROR,
            code="WORM_ROOT_TOO_SMALL",
            message=f"Worm root diameter {worm.root_diameter:.2f}mm is too small",
            suggestion="Increase worm pitch diameter"
        ))
    
    return messages


def _validate_pressure_angle(design: WormGearDesign) -> List[ValidationMessage]:
    """Check pressure angle is standard"""
    messages = []
    pa = design.pressure_angle
    
    standard_angles = [14.5, 20.0, 25.0]
    
    if pa not in standard_angles:
        messages.append(ValidationMessage(
            severity=Severity.INFO,
            code="PRESSURE_ANGLE_NON_STANDARD",
            message=f"Pressure angle {pa}° is non-standard",
            suggestion="Standard values: 14.5°, 20°, 25°. 20° is most common."
        ))
    
    if pa < 14.5:
        messages.append(ValidationMessage(
            severity=Severity.WARNING,
            code="PRESSURE_ANGLE_LOW",
            message=f"Pressure angle {pa}° is low - may cause interference",
            suggestion="Consider 20° for general use"
        ))
    elif pa > 25:
        messages.append(ValidationMessage(
            severity=Severity.WARNING,
            code="PRESSURE_ANGLE_HIGH",
            message=f"Pressure angle {pa}° is high - increased radial loads",
            suggestion="Consider 20° for general use"
        ))
    
    return messages


def _validate_efficiency(design: WormGearDesign) -> List[ValidationMessage]:
    """Add efficiency information"""
    messages = []
    eff = design.efficiency_estimate
    
    if eff < 0.3:
        messages.append(ValidationMessage(
            severity=Severity.WARNING,
            code="EFFICIENCY_VERY_LOW",
            message=f"Estimated efficiency {eff*100:.0f}% is very low",
            suggestion="Most input power will be lost to friction/heat"
        ))
    elif eff < 0.5:
        messages.append(ValidationMessage(
            severity=Severity.INFO,
            code="EFFICIENCY_LOW",
            message=f"Estimated efficiency {eff*100:.0f}% - typical for self-locking drives",
            suggestion=None
        ))
    elif eff > 0.85:
        messages.append(ValidationMessage(
            severity=Severity.INFO,
            code="EFFICIENCY_HIGH",
            message=f"Estimated efficiency {eff*100:.0f}% - good efficiency but not self-locking",
            suggestion=None
        ))
    
    # Self-locking note
    if design.self_locking:
        messages.append(ValidationMessage(
            severity=Severity.INFO,
            code="SELF_LOCKING",
            message="Drive should be self-locking (lead angle < 6°)",
            suggestion="Verify with actual materials and lubrication"
        ))
    
    return messages


def _validate_centre_distance(design: WormGearDesign) -> List[ValidationMessage]:
    """Check centre distance is reasonable"""
    messages = []
    cd = design.centre_distance
    
    if cd < 5:
        messages.append(ValidationMessage(
            severity=Severity.WARNING,
            code="CENTRE_DISTANCE_SMALL",
            message=f"Centre distance {cd:.2f}mm is very small",
            suggestion="Verify assembly is practical"
        ))
    
    return messages


def create_design_result(design: WormGearDesign) -> DesignResult:
    """
    Create a complete DesignResult with validation.
    
    Convenience function that combines design with validation.
    """
    validation = validate_design(design)
    
    return DesignResult(
        design=design if validation.valid else design,  # Include design even if warnings
        valid=validation.valid,
        warnings=[m.message for m in validation.warnings],
        errors=[m.message for m in validation.errors],
        suggestions=[m.suggestion for m in validation.messages if m.suggestion]
    )
