"""
Worm Gear Calculator - Output Formatters

JSON and Markdown output for designs.
"""

import json
from dataclasses import asdict
from typing import Optional

from .core import WormGearDesign, WormParameters, WheelParameters, Hand
from .validation import ValidationResult, ValidationMessage, Severity


def design_to_dict(design: WormGearDesign) -> dict:
    """
    Convert design to a plain dictionary suitable for JSON serialization.
    """
    return {
        "worm": {
            "module_mm": round(design.worm.module, 4),
            "num_starts": design.worm.num_starts,
            "pitch_diameter_mm": round(design.worm.pitch_diameter, 3),
            "tip_diameter_mm": round(design.worm.tip_diameter, 3),
            "root_diameter_mm": round(design.worm.root_diameter, 3),
            "lead_mm": round(design.worm.lead, 3),
            "axial_pitch_mm": round(design.worm.axial_pitch, 3),
            "lead_angle_deg": round(design.worm.lead_angle, 2),
            "addendum_mm": round(design.worm.addendum, 3),
            "dedendum_mm": round(design.worm.dedendum, 3),
            "thread_thickness_mm": round(design.worm.thread_thickness, 3),
        },
        "wheel": {
            "module_mm": round(design.wheel.module, 4),
            "num_teeth": design.wheel.num_teeth,
            "pitch_diameter_mm": round(design.wheel.pitch_diameter, 3),
            "tip_diameter_mm": round(design.wheel.tip_diameter, 3),
            "root_diameter_mm": round(design.wheel.root_diameter, 3),
            "throat_diameter_mm": round(design.wheel.throat_diameter, 3),
            "helix_angle_deg": round(design.wheel.helix_angle, 2),
            "addendum_mm": round(design.wheel.addendum, 3),
            "dedendum_mm": round(design.wheel.dedendum, 3),
        },
        "assembly": {
            "centre_distance_mm": round(design.centre_distance, 3),
            "ratio": design.ratio,
            "pressure_angle_deg": design.pressure_angle,
            "backlash_mm": round(design.backlash, 3),
            "hand": design.hand.value,
        },
        "performance": {
            "efficiency_estimate": round(design.efficiency_estimate, 3),
            "self_locking": design.self_locking,
        }
    }


def validation_to_dict(validation: ValidationResult) -> dict:
    """Convert validation result to dictionary"""
    return {
        "valid": validation.valid,
        "messages": [
            {
                "severity": msg.severity.value,
                "code": msg.code,
                "message": msg.message,
                "suggestion": msg.suggestion
            }
            for msg in validation.messages
        ]
    }


def to_json(
    design: WormGearDesign, 
    validation: Optional[ValidationResult] = None,
    indent: int = 2
) -> str:
    """
    Export design to JSON string.
    
    Args:
        design: The worm gear design
        validation: Optional validation result to include
        indent: JSON indentation (default 2)
    
    Returns:
        JSON string
    """
    data = design_to_dict(design)
    
    if validation:
        data["validation"] = validation_to_dict(validation)
    
    return json.dumps(data, indent=indent)


def to_markdown(
    design: WormGearDesign,
    validation: Optional[ValidationResult] = None,
    title: str = "Worm Gear Design"
) -> str:
    """
    Export design to Markdown format.
    
    Args:
        design: The worm gear design
        validation: Optional validation result to include
        title: Document title
    
    Returns:
        Markdown string
    """
    lines = [
        f"# {title}",
        "",
        "## Summary",
        "",
        f"| Parameter | Value |",
        f"|-----------|-------|",
        f"| Ratio | {design.ratio}:1 |",
        f"| Module | {design.worm.module:.3f} mm |",
        f"| Centre Distance | {design.centre_distance:.2f} mm |",
        f"| Pressure Angle | {design.pressure_angle}° |",
        f"| Hand | {design.hand.value.title()} |",
        f"| Efficiency (est.) | {design.efficiency_estimate*100:.0f}% |",
        f"| Self-Locking | {'Yes' if design.self_locking else 'No'} |",
        "",
        "## Worm",
        "",
        f"| Parameter | Value |",
        f"|-----------|-------|",
        f"| Number of Starts | {design.worm.num_starts} |",
        f"| Pitch Diameter | {design.worm.pitch_diameter:.2f} mm |",
        f"| Tip Diameter (OD) | {design.worm.tip_diameter:.2f} mm |",
        f"| Root Diameter | {design.worm.root_diameter:.2f} mm |",
        f"| Lead | {design.worm.lead:.3f} mm |",
        f"| Axial Pitch | {design.worm.axial_pitch:.3f} mm |",
        f"| Lead Angle | {design.worm.lead_angle:.2f}° |",
        f"| Addendum | {design.worm.addendum:.3f} mm |",
        f"| Dedendum | {design.worm.dedendum:.3f} mm |",
        f"| Thread Thickness | {design.worm.thread_thickness:.3f} mm |",
        "",
        "## Wheel",
        "",
        f"| Parameter | Value |",
        f"|-----------|-------|",
        f"| Number of Teeth | {design.wheel.num_teeth} |",
        f"| Pitch Diameter | {design.wheel.pitch_diameter:.2f} mm |",
        f"| Tip Diameter (OD) | {design.wheel.tip_diameter:.2f} mm |",
        f"| Root Diameter | {design.wheel.root_diameter:.2f} mm |",
        f"| Throat Diameter | {design.wheel.throat_diameter:.2f} mm |",
        f"| Helix Angle | {design.wheel.helix_angle:.2f}° |",
        f"| Addendum | {design.wheel.addendum:.3f} mm |",
        f"| Dedendum | {design.wheel.dedendum:.3f} mm |",
        "",
    ]
    
    # Add validation if provided
    if validation:
        lines.extend([
            "## Validation",
            "",
        ])
        
        if validation.valid:
            lines.append("✅ Design is valid")
        else:
            lines.append("❌ Design has errors")
        
        lines.append("")
        
        if validation.errors:
            lines.append("### Errors")
            lines.append("")
            for msg in validation.errors:
                lines.append(f"- **{msg.code}**: {msg.message}")
                if msg.suggestion:
                    lines.append(f"  - *Suggestion*: {msg.suggestion}")
            lines.append("")
        
        if validation.warnings:
            lines.append("### Warnings")
            lines.append("")
            for msg in validation.warnings:
                lines.append(f"- **{msg.code}**: {msg.message}")
                if msg.suggestion:
                    lines.append(f"  - *Suggestion*: {msg.suggestion}")
            lines.append("")
        
        if validation.infos:
            lines.append("### Information")
            lines.append("")
            for msg in validation.infos:
                lines.append(f"- {msg.message}")
            lines.append("")
    
    # Add notes
    lines.extend([
        "## Notes",
        "",
        "- All dimensions in millimeters unless otherwise noted",
        "- Efficiency estimate assumes steel worm on bronze wheel with lubrication",
        "- Self-locking determination is approximate - verify with actual materials",
        "- Throat diameter is for enveloping (throated) wheel design",
        "",
        "---",
        "*Generated by wormcalc*",
    ])
    
    return "\n".join(lines)


def to_summary(design: WormGearDesign) -> str:
    """
    Generate a brief text summary for terminal output.
    """
    lines = [
        "═══ Worm Gear Design ═══",
        f"Ratio: {design.ratio}:1",
        f"Module: {design.worm.module:.3f} mm",
        "",
        "Worm:",
        f"  Tip diameter (OD): {design.worm.tip_diameter:.2f} mm",
        f"  Pitch diameter:    {design.worm.pitch_diameter:.2f} mm", 
        f"  Root diameter:     {design.worm.root_diameter:.2f} mm",
        f"  Lead angle:        {design.worm.lead_angle:.1f}°",
        f"  Starts:            {design.worm.num_starts}",
        "",
        "Wheel:",
        f"  Tip diameter (OD): {design.wheel.tip_diameter:.2f} mm",
        f"  Pitch diameter:    {design.wheel.pitch_diameter:.2f} mm",
        f"  Root diameter:     {design.wheel.root_diameter:.2f} mm",
        f"  Teeth:             {design.wheel.num_teeth}",
        f"  Helix angle:       {design.wheel.helix_angle:.1f}°",
        "",
        f"Centre distance: {design.centre_distance:.2f} mm",
        f"Efficiency (est): {design.efficiency_estimate*100:.0f}%",
        f"Self-locking: {'Yes' if design.self_locking else 'No'}",
    ]
    return "\n".join(lines)


def validation_summary(validation: ValidationResult) -> str:
    """
    Generate a brief validation summary for terminal output.
    """
    lines = []
    
    if validation.valid:
        lines.append("✓ Design valid")
    else:
        lines.append("✗ Design has errors")
    
    for msg in validation.errors:
        lines.append(f"  ERROR: {msg.message}")
    
    for msg in validation.warnings:
        lines.append(f"  WARN:  {msg.message}")
    
    for msg in validation.infos:
        lines.append(f"  INFO:  {msg.message}")
    
    return "\n".join(lines)
