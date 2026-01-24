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
    STANDARD_MODULES,
    WormType, WormProfile
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
    messages.extend(_validate_profile(design))
    messages.extend(_validate_worm_type(design))
    messages.extend(_validate_wheel_throated(design))
    messages.extend(_validate_manufacturing_compatibility(design))

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


def _validate_profile(design: WormGearDesign) -> List[ValidationMessage]:
    """Check profile type is valid"""
    messages = []

    # Profile type validation - check it's a valid enum value
    if design.profile not in (WormProfile.ZA, WormProfile.ZK):
        messages.append(ValidationMessage(
            severity=Severity.ERROR,
            code="PROFILE_INVALID",
            message=f"Invalid profile type: {design.profile}",
            suggestion="Use ZA (for CNC machining) or ZK (for 3D printing)"
        ))

    # Info about profile type
    if design.profile == WormProfile.ZK:
        messages.append(ValidationMessage(
            severity=Severity.INFO,
            code="PROFILE_ZK",
            message="ZK profile selected - optimized for 3D printing (FDM)",
            suggestion=None
        ))

    return messages


def _validate_worm_type(design: WormGearDesign) -> List[ValidationMessage]:
    """Check worm type and related parameters"""
    messages = []

    if design.manufacturing is None:
        return messages

    worm_type = design.manufacturing.worm_type

    # Worm type validation - check it's a valid enum value
    if worm_type not in (WormType.CYLINDRICAL, WormType.GLOBOID):
        messages.append(ValidationMessage(
            severity=Severity.ERROR,
            code="WORM_TYPE_INVALID",
            message=f"Invalid worm type: {worm_type}",
            suggestion="Use cylindrical or globoid"
        ))
        return messages

    # Globoid-specific validations
    if worm_type == WormType.GLOBOID:
        # Check throat radii are present
        if design.worm.throat_pitch_radius is None:
            messages.append(ValidationMessage(
                severity=Severity.ERROR,
                code="GLOBOID_MISSING_THROAT",
                message="Globoid worm requires throat radius calculations",
                suggestion="Ensure throat radii are calculated"
            ))
        else:
            # Validate throat reduction value
            if design.worm.throat_reduction is not None:
                throat_reduction = design.worm.throat_reduction
                module = design.worm.module

                # Check reduction is reasonable
                if throat_reduction < 0.02:
                    messages.append(ValidationMessage(
                        severity=Severity.WARNING,
                        code="THROAT_REDUCTION_VERY_SMALL",
                        message=f"Throat reduction {throat_reduction:.3f}mm is very small - minimal hourglass effect",
                        suggestion="Typical values: 0.05-0.1mm for small gears, 0.1-0.2mm for medium"
                    ))
                elif throat_reduction > module * 0.5:
                    messages.append(ValidationMessage(
                        severity=Severity.ERROR,
                        code="THROAT_REDUCTION_TOO_LARGE",
                        message=f"Throat reduction {throat_reduction:.3f}mm is too large (>{module * 0.5:.3f}mm = 50% of module)",
                        suggestion="Reduce throat reduction to less than 50% of module"
                    ))
                elif throat_reduction > module * 0.3:
                    messages.append(ValidationMessage(
                        severity=Severity.WARNING,
                        code="THROAT_REDUCTION_LARGE",
                        message=f"Throat reduction {throat_reduction:.3f}mm is large (>{module * 0.3:.3f}mm = 30% of module)",
                        suggestion="Consider reducing for better manufacturability"
                    ))

            # Check clearance at throat
            clearance = design.centre_distance - (design.worm.throat_tip_radius + design.wheel.root_radius)
            if clearance < 0:
                messages.append(ValidationMessage(
                    severity=Severity.ERROR,
                    code="GLOBOID_INTERFERENCE",
                    message=f"Interference! Worm throat tip intersects wheel root (clearance: {clearance:.3f}mm)",
                    suggestion="Reduce throat reduction or increase centre distance"
                ))
            elif clearance < 0.05:
                messages.append(ValidationMessage(
                    severity=Severity.WARNING,
                    code="GLOBOID_TIGHT_CLEARANCE",
                    message=f"Very tight clearance at throat ({clearance:.3f}mm < 0.05mm)",
                    suggestion="Manufacturing tolerance issues likely - consider increasing clearance"
                ))

            # Verify hourglass geometry
            if design.worm.throat_pitch_radius >= design.worm.pitch_radius:
                messages.append(ValidationMessage(
                    severity=Severity.ERROR,
                    code="GLOBOID_INVALID_GEOMETRY",
                    message="Invalid globoid: throat radius must be less than nominal radius",
                    suggestion="Increase throat reduction or check calculation"
                ))

            # Info about globoid
            actual_reduction = design.worm.pitch_radius - design.worm.throat_pitch_radius
            messages.append(ValidationMessage(
                severity=Severity.INFO,
                code="GLOBOID_WORM",
                message=f"Globoid worm with {actual_reduction:.3f}mm throat reduction provides better contact with wheel",
                suggestion=None
            ))

    return messages


def _validate_wheel_throated(design: WormGearDesign) -> List[ValidationMessage]:
    """Check wheel throated setting is appropriate"""
    messages = []

    if design.manufacturing is None:
        return messages

    worm_type = design.manufacturing.worm_type
    wheel_throated = design.manufacturing.wheel_throated

    # Warn if globoid worm with non-throated wheel
    if worm_type == WormType.GLOBOID and not wheel_throated:
        messages.append(ValidationMessage(
            severity=Severity.WARNING,
            code="GLOBOID_NON_THROATED",
            message="Globoid worm typically requires throated wheel for proper contact",
            suggestion="Consider enabling wheel_throated for better mesh"
        ))

    # Info about throated wheel
    if wheel_throated:
        messages.append(ValidationMessage(
            severity=Severity.INFO,
            code="WHEEL_THROATED",
            message="Throated wheel teeth provide better contact area",
            suggestion=None
        ))

    return messages


def _validate_manufacturing_compatibility(design: WormGearDesign) -> List[ValidationMessage]:
    """Check manufacturing parameters for compatibility, especially for globoid worms"""
    messages = []

    if design.manufacturing is None:
        return messages

    worm_type = design.manufacturing.worm_type
    wheel_width = design.manufacturing.wheel_width
    worm_length = design.manufacturing.worm_length
    max_wheel_width = design.manufacturing.max_wheel_width
    recommended_wheel_width = design.manufacturing.recommended_wheel_width

    if wheel_width is None or worm_length is None:
        return messages

    # Check worm length is adequate for wheel width
    min_worm_length = wheel_width * 1.5
    if worm_type == WormType.GLOBOID and design.worm.throat_reduction:
        # Add transition zones for globoid
        min_worm_length += 4 * design.worm.throat_reduction

    if worm_length < min_worm_length:
        messages.append(ValidationMessage(
            severity=Severity.ERROR,
            code="WORM_LENGTH_INSUFFICIENT",
            message=f"Worm length {worm_length:.2f}mm is too short for wheel width {wheel_width:.2f}mm",
            suggestion=f"Increase worm length to at least {min_worm_length:.2f}mm (1.5× wheel width + transitions)"
        ))
    elif worm_type != WormType.GLOBOID and worm_length < wheel_width * 2.0:
        messages.append(ValidationMessage(
            severity=Severity.WARNING,
            code="WORM_LENGTH_SHORT",
            message=f"Worm length {worm_length:.2f}mm is short for wheel width {wheel_width:.2f}mm",
            suggestion=f"Consider increasing to {wheel_width * 2.0:.2f}mm for better engagement"
        ))

    # Globoid-specific checks
    if worm_type == WormType.GLOBOID:
        # Check wheel width against calculated maximum
        if max_wheel_width is not None:
            if wheel_width > max_wheel_width:
                messages.append(ValidationMessage(
                    severity=Severity.ERROR,
                    code="GLOBOID_WHEEL_EXCEEDS_MAX",
                    message=f"Wheel width {wheel_width:.2f}mm exceeds maximum {max_wheel_width:.2f}mm for this throat reduction",
                    suggestion=f"CRITICAL: This will cause gaps at wheel edges! Reduce width to ≤{max_wheel_width:.2f}mm or reduce throat reduction"
                ))
            elif wheel_width > max_wheel_width * 0.85:
                messages.append(ValidationMessage(
                    severity=Severity.WARNING,
                    code="GLOBOID_WHEEL_NEAR_MAX",
                    message=f"Wheel width {wheel_width:.2f}mm is close to maximum {max_wheel_width:.2f}mm",
                    suggestion=f"Consider using recommended width {recommended_wheel_width:.2f}mm for better safety margin"
                ))

        # Provide helpful info about the constraints
        if design.worm.throat_reduction is not None and design.worm.throat_reduction > 0:
            throat_ratio = design.worm.throat_reduction / design.worm.module

            # Show trade-off information
            if max_wheel_width is not None and recommended_wheel_width is not None:
                messages.append(ValidationMessage(
                    severity=Severity.INFO,
                    code="GLOBOID_WIDTH_CONSTRAINT",
                    message=f"Throat reduction {design.worm.throat_reduction:.3f}mm limits wheel width to {max_wheel_width:.2f}mm max (recommended: {recommended_wheel_width:.2f}mm)",
                    suggestion=f"Trade-off: Reduce throat reduction to {design.worm.throat_reduction * 0.5:.3f}mm for ~2× wider wheel, or keep current for better contact"
                ))

            # Warn about edge gap risk based on specific geometry
            if wheel_width > design.worm.pitch_diameter * 0.5 and throat_ratio > 0.15:
                messages.append(ValidationMessage(
                    severity=Severity.WARNING,
                    code="GLOBOID_EDGE_GAP_RISK",
                    message=f"Combination of throat reduction ({design.worm.throat_reduction:.3f}mm) and wheel width ({wheel_width:.2f}mm) creates edge gap risk",
                    suggestion="Virtual hobbing recommended to verify no gaps at wheel edges"
                ))

        # Info about globoid engagement
        if wheel_width > 0:
            engagement_ratio = worm_length / wheel_width
            messages.append(ValidationMessage(
                severity=Severity.INFO,
                code="GLOBOID_ENGAGEMENT",
                message=f"Globoid engagement: worm length {worm_length:.2f}mm covers {engagement_ratio:.1f}× wheel width ({wheel_width:.2f}mm)",
                suggestion=None
            ))

        # Show what user would get with different choices
        if max_wheel_width is not None and design.worm.throat_reduction is not None:
            alternative_reduction = design.worm.throat_reduction * 0.3
            if alternative_reduction >= 0.02:  # Only suggest if meaningful
                messages.append(ValidationMessage(
                    severity=Severity.INFO,
                    code="GLOBOID_TRADEOFF_OPTION",
                    message=f"Alternative: Reduce throat to {alternative_reduction:.3f}mm for wider wheel (~{max_wheel_width * 2:.1f}mm possible) with less hourglass effect",
                    suggestion=None
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
