"""
Tests for wormcalc.validation

Test that validation rules catch expected issues.
"""

import pytest

from wormcalc.core import (
    design_from_envelope, design_from_wheel, design_from_module,
    WormProfile, WormType
)
from wormcalc.validation import (
    validate_design,
    Severity,
    ValidationResult,
)


class TestLeadAngleValidation:
    """Tests for lead angle validation rules"""
    
    def test_very_low_lead_angle_error(self):
        """Lead angle < 1° should be an error"""
        # Create design with very low lead angle (large worm diameter)
        design = design_from_wheel(
            wheel_od=64.0,
            ratio=30,
            target_lead_angle=0.5
        )
        
        result = validate_design(design)
        
        error_codes = [m.code for m in result.errors]
        assert "LEAD_ANGLE_TOO_LOW" in error_codes
    
    def test_low_lead_angle_warning(self):
        """Lead angle 1-3° should be a warning"""
        design = design_from_wheel(
            wheel_od=64.0,
            ratio=30,
            target_lead_angle=2.0
        )
        
        result = validate_design(design)
        
        warning_codes = [m.code for m in result.warnings]
        assert "LEAD_ANGLE_VERY_LOW" in warning_codes
    
    def test_normal_lead_angle_ok(self):
        """Lead angle 5-25° should be valid"""
        design = design_from_wheel(
            wheel_od=64.0,
            ratio=30,
            target_lead_angle=10.0
        )
        
        result = validate_design(design)
        
        # Should be valid
        assert result.valid
        
        # Should not have lead angle errors or warnings
        codes = [m.code for m in result.errors + result.warnings]
        assert "LEAD_ANGLE_TOO_LOW" not in codes
        assert "LEAD_ANGLE_VERY_LOW" not in codes
        assert "LEAD_ANGLE_HIGH" not in codes
    
    def test_high_lead_angle_warning(self):
        """Lead angle > 25° should warn about self-locking"""
        design = design_from_wheel(
            wheel_od=64.0,
            ratio=30,
            target_lead_angle=30.0
        )
        
        result = validate_design(design)
        
        warning_codes = [m.code for m in result.warnings]
        assert "LEAD_ANGLE_HIGH" in warning_codes


class TestModuleValidation:
    """Tests for module validation rules"""
    
    def test_standard_module_ok(self):
        """Standard module should not produce warnings"""
        design = design_from_module(
            module=2.0,
            ratio=30
        )
        
        result = validate_design(design)
        
        codes = [m.code for m in result.messages]
        assert "MODULE_NON_STANDARD" not in codes
    
    def test_non_standard_module_warning(self):
        """Non-standard module should warn"""
        design = design_from_module(
            module=2.3,  # Not standard
            ratio=30
        )
        
        result = validate_design(design)
        
        # Should have module warning
        codes = [m.code for m in result.warnings + result.infos]
        assert "MODULE_NON_STANDARD" in codes or "MODULE_NEAR_STANDARD" in codes
    
    def test_very_small_module_error(self):
        """Module < 0.3mm should error"""
        design = design_from_module(
            module=0.2,
            ratio=30
        )
        
        result = validate_design(design)
        
        error_codes = [m.code for m in result.errors]
        assert "MODULE_TOO_SMALL" in error_codes


class TestTeethCountValidation:
    """Tests for wheel teeth count validation"""
    
    def test_very_few_teeth_error(self):
        """< 17 teeth should error"""
        # Use envelope to force low teeth count
        # Small wheel OD + low ratio = few teeth
        design = design_from_envelope(
            worm_od=10.0,
            wheel_od=20.0,  # Very small
            ratio=8  # 8 teeth with 1 start
        )
        
        result = validate_design(design)
        
        error_codes = [m.code for m in result.errors]
        assert "TEETH_TOO_FEW" in error_codes
    
    def test_low_teeth_warning(self):
        """17-24 teeth should warn"""
        design = design_from_envelope(
            worm_od=10.0,
            wheel_od=42.0,
            ratio=20  # 20 teeth
        )
        
        result = validate_design(design)
        
        warning_codes = [m.code for m in result.warnings]
        assert "TEETH_LOW" in warning_codes
    
    def test_normal_teeth_ok(self):
        """24+ teeth should be fine"""
        design = design_from_module(
            module=2.0,
            ratio=30  # 30 teeth
        )
        
        result = validate_design(design)
        
        codes = [m.code for m in result.errors + result.warnings]
        assert "TEETH_TOO_FEW" not in codes
        assert "TEETH_LOW" not in codes


class TestWormProportionsValidation:
    """Tests for worm proportion validation"""
    
    def test_thin_worm_warning(self):
        """Worm pitch dia < 5×module should warn"""
        # Force thin worm by specifying small pitch diameter
        design = design_from_module(
            module=2.0,
            ratio=30,
            worm_pitch_diameter=8.0  # Only 4× module
        )
        
        result = validate_design(design)
        
        warning_codes = [m.code for m in result.warnings]
        assert "WORM_THIN" in warning_codes
    
    def test_very_thin_worm_error(self):
        """Worm pitch dia < 3×module should error"""
        design = design_from_module(
            module=2.0,
            ratio=30,
            worm_pitch_diameter=5.0  # Only 2.5× module
        )
        
        result = validate_design(design)
        
        error_codes = [m.code for m in result.errors]
        assert "WORM_TOO_THIN" in error_codes


class TestOverallValidation:
    """Tests for overall validation result"""
    
    def test_valid_design_passes(self):
        """A sensible design should pass validation"""
        design = design_from_module(
            module=2.0,
            ratio=30,
            target_lead_angle=8.0
        )
        
        result = validate_design(design)
        
        assert result.valid
        assert len(result.errors) == 0
    
    def test_errors_make_invalid(self):
        """Any error should make design invalid"""
        design = design_from_module(
            module=0.2,  # Too small - will error
            ratio=30
        )
        
        result = validate_design(design)
        
        assert not result.valid
        assert len(result.errors) > 0
    
    def test_warnings_still_valid(self):
        """Warnings alone should not invalidate"""
        design = design_from_module(
            module=2.3,  # Non-standard but valid
            ratio=30,
            target_lead_angle=8.0
        )
        
        result = validate_design(design)
        
        # May have warnings but should still be valid
        assert result.valid


class TestSuggestions:
    """Tests that validation provides useful suggestions"""
    
    def test_module_suggestion_includes_nearest(self):
        """Non-standard module should suggest nearest standard"""
        design = design_from_module(
            module=2.3,
            ratio=30
        )
        
        result = validate_design(design)
        
        # Find the module message
        module_msgs = [m for m in result.messages 
                      if "MODULE" in m.code and m.suggestion]
        
        assert len(module_msgs) > 0
        # Suggestion should mention nearest standard (2.25 or 2.5)
        suggestion = module_msgs[0].suggestion
        assert "2.25" in suggestion or "2.5" in suggestion or "2.0" in suggestion
    
    def test_lead_angle_suggestion(self):
        """Low lead angle should suggest increasing worm diameter"""
        design = design_from_wheel(
            wheel_od=64.0,
            ratio=30,
            target_lead_angle=2.5
        )
        
        result = validate_design(design)
        
        # Find lead angle warning
        lead_msgs = [m for m in result.warnings if "LEAD_ANGLE" in m.code]
        
        assert len(lead_msgs) > 0
        assert lead_msgs[0].suggestion is not None


class TestProfileValidation:
    """Tests for profile type validation"""

    def test_za_profile_valid(self):
        """ZA profile should be valid"""
        design = design_from_module(
            module=2.0,
            ratio=30,
            profile=WormProfile.ZA
        )
        result = validate_design(design)

        error_codes = [m.code for m in result.errors]
        assert "PROFILE_INVALID" not in error_codes

    def test_zk_profile_info(self):
        """ZK profile should produce info message"""
        design = design_from_module(
            module=2.0,
            ratio=30,
            profile=WormProfile.ZK
        )
        result = validate_design(design)

        info_codes = [m.code for m in result.infos]
        assert "PROFILE_ZK" in info_codes


class TestWormTypeValidation:
    """Tests for worm type validation"""

    def test_cylindrical_valid(self):
        """Cylindrical worm should be valid"""
        design = design_from_module(
            module=2.0,
            ratio=30,
            worm_type=WormType.CYLINDRICAL
        )
        result = validate_design(design)

        error_codes = [m.code for m in result.errors]
        assert "WORM_TYPE_INVALID" not in error_codes

    def test_globoid_info(self):
        """Globoid worm should produce info message"""
        design = design_from_module(
            module=2.0,
            ratio=30,
            worm_type=WormType.GLOBOID
        )
        result = validate_design(design)

        info_codes = [m.code for m in result.infos]
        assert "GLOBOID_WORM" in info_codes


class TestWheelThroatedValidation:
    """Tests for wheel throated validation"""

    def test_globoid_non_throated_warning(self):
        """Globoid worm with non-throated wheel should warn"""
        design = design_from_module(
            module=2.0,
            ratio=30,
            worm_type=WormType.GLOBOID,
            wheel_throated=False
        )
        result = validate_design(design)

        warning_codes = [m.code for m in result.warnings]
        assert "GLOBOID_NON_THROATED" in warning_codes

    def test_globoid_throated_no_warning(self):
        """Globoid worm with throated wheel should not warn"""
        design = design_from_module(
            module=2.0,
            ratio=30,
            worm_type=WormType.GLOBOID,
            wheel_throated=True
        )
        result = validate_design(design)

        warning_codes = [m.code for m in result.warnings]
        assert "GLOBOID_NON_THROATED" not in warning_codes

    def test_throated_info(self):
        """Throated wheel should produce info message"""
        design = design_from_module(
            module=2.0,
            ratio=30,
            wheel_throated=True
        )
        result = validate_design(design)

        info_codes = [m.code for m in result.infos]
        assert "WHEEL_THROATED" in info_codes


class TestNewFeaturesStillValid:
    """Ensure new features don't break overall validation"""

    def test_globoid_design_valid(self):
        """Globoid design with proper settings should be valid"""
        design = design_from_module(
            module=2.0,
            ratio=30,
            target_lead_angle=8.0,
            worm_type=WormType.GLOBOID,
            wheel_throated=True,
            profile=WormProfile.ZA
        )
        result = validate_design(design)
        assert result.valid

    def test_zk_printing_profile_valid(self):
        """ZK profile design for 3D printing should be valid"""
        design = design_from_module(
            module=2.0,
            ratio=30,
            target_lead_angle=8.0,
            profile=WormProfile.ZK
        )
        result = validate_design(design)
        assert result.valid
