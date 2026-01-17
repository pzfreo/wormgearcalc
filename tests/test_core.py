"""
Tests for wormcalc.core

Validation against hand calculations and engineering references.
"""

import pytest
from math import pi, tan, radians, degrees

from wormcalc.core import (
    WormParameters,
    WheelParameters,
    WormGearDesign,
    Hand,
    STANDARD_MODULES,
    calculate_worm,
    calculate_wheel,
    calculate_centre_distance,
    design_from_envelope,
    design_from_wheel,
    design_from_module,
    design_from_centre_distance,
    nearest_standard_module,
    is_standard_module,
    estimate_efficiency,
)


class TestStandardModules:
    """Tests for module-related functions"""
    
    def test_standard_modules_sorted(self):
        """Standard modules should be in ascending order"""
        assert STANDARD_MODULES == sorted(STANDARD_MODULES)
    
    def test_is_standard_module_true(self):
        """Should identify standard modules"""
        assert is_standard_module(2.0)
        assert is_standard_module(1.5)
        assert is_standard_module(0.5)
    
    def test_is_standard_module_false(self):
        """Should reject non-standard modules"""
        assert not is_standard_module(2.1)
        assert not is_standard_module(1.6)
        assert not is_standard_module(0.55)
    
    def test_nearest_standard_module(self):
        """Should find nearest standard"""
        assert nearest_standard_module(2.1) == 2.0
        assert nearest_standard_module(1.9) == 2.0
        assert nearest_standard_module(1.6) == 1.5
        assert nearest_standard_module(2.3) == 2.25


class TestCalculateWorm:
    """Tests for worm calculations"""
    
    def test_basic_calculation(self):
        """Test basic worm geometry"""
        worm = calculate_worm(
            module=2.0,
            num_starts=1,
            pitch_diameter=16.0,
            pressure_angle=20.0
        )
        
        # Axial pitch = π × module
        assert pytest.approx(worm.axial_pitch, rel=1e-6) == pi * 2.0
        
        # Lead = axial_pitch × num_starts
        assert pytest.approx(worm.lead, rel=1e-6) == pi * 2.0
        
        # Tip diameter = pitch + 2 × addendum
        assert pytest.approx(worm.tip_diameter, rel=1e-6) == 16.0 + 2 * 2.0
        
        # Root diameter = pitch - 2 × dedendum
        expected_dedendum = 2.0 * 1.25  # module × (1 + clearance)
        assert pytest.approx(worm.root_diameter, rel=1e-6) == 16.0 - 2 * expected_dedendum
    
    def test_lead_angle_single_start(self):
        """Test lead angle calculation for single start"""
        worm = calculate_worm(
            module=2.0,
            num_starts=1,
            pitch_diameter=16.0
        )
        
        # lead_angle = atan(lead / (π × pitch_dia))
        lead = pi * 2.0 * 1
        expected_angle = degrees(pi * 2.0 / (pi * 16.0))  # Simplified: atan(m/d) for small angles
        
        # For exact: atan(lead / (π × d))
        from math import atan
        exact_angle = degrees(atan(lead / (pi * 16.0)))
        
        assert pytest.approx(worm.lead_angle, rel=1e-6) == exact_angle
    
    def test_lead_angle_multi_start(self):
        """Multi-start worms should have higher lead angles"""
        worm_1 = calculate_worm(module=2.0, num_starts=1, pitch_diameter=16.0)
        worm_2 = calculate_worm(module=2.0, num_starts=2, pitch_diameter=16.0)
        worm_4 = calculate_worm(module=2.0, num_starts=4, pitch_diameter=16.0)
        
        assert worm_2.lead_angle > worm_1.lead_angle
        assert worm_4.lead_angle > worm_2.lead_angle
    
    def test_backlash_reduces_thread_thickness(self):
        """Backlash should reduce thread thickness"""
        worm_no_bl = calculate_worm(module=2.0, num_starts=1, pitch_diameter=16.0, backlash=0.0)
        worm_bl = calculate_worm(module=2.0, num_starts=1, pitch_diameter=16.0, backlash=0.1)
        
        assert worm_bl.thread_thickness < worm_no_bl.thread_thickness
        assert pytest.approx(worm_no_bl.thread_thickness - worm_bl.thread_thickness) == 0.1


class TestCalculateWheel:
    """Tests for wheel calculations"""
    
    def test_basic_calculation(self):
        """Test basic wheel geometry"""
        wheel = calculate_wheel(
            module=2.0,
            num_teeth=30,
            worm_pitch_diameter=16.0,
            worm_lead_angle=7.0
        )
        
        # Pitch diameter = module × teeth
        assert pytest.approx(wheel.pitch_diameter, rel=1e-6) == 2.0 * 30
        
        # Tip diameter = pitch + 2 × addendum
        assert pytest.approx(wheel.tip_diameter, rel=1e-6) == 60.0 + 2 * 2.0
    
    def test_helix_angle_relationship(self):
        """Helix angle should be 90° - lead angle"""
        wheel = calculate_wheel(
            module=2.0,
            num_teeth=30,
            worm_pitch_diameter=16.0,
            worm_lead_angle=7.0
        )
        
        assert pytest.approx(wheel.helix_angle, rel=1e-6) == 90.0 - 7.0


class TestCentreDistance:
    """Tests for centre distance calculation"""
    
    def test_basic_calculation(self):
        """Centre distance = (worm_pd + wheel_pd) / 2"""
        cd = calculate_centre_distance(16.0, 60.0)
        assert pytest.approx(cd, rel=1e-6) == (16.0 + 60.0) / 2


class TestDesignFromEnvelope:
    """Tests for envelope-based design"""
    
    def test_basic_design(self):
        """Test basic envelope design"""
        design = design_from_envelope(
            worm_od=20.0,
            wheel_od=64.0,
            ratio=30
        )
        
        # Check ratio
        assert design.ratio == 30
        
        # Check ODs match input (approximately, accounting for module rounding)
        assert pytest.approx(design.worm.tip_diameter, rel=0.01) == 20.0
        assert pytest.approx(design.wheel.tip_diameter, rel=0.01) == 64.0
    
    def test_module_calculation(self):
        """Module should be derived from wheel OD and teeth"""
        design = design_from_envelope(
            worm_od=20.0,
            wheel_od=64.0,
            ratio=30
        )
        
        # module = wheel_od / (teeth + 2)
        expected_module = 64.0 / (30 + 2)
        assert pytest.approx(design.worm.module, rel=1e-6) == expected_module
    
    def test_centre_distance_consistency(self):
        """Centre distance should be consistent with pitch diameters"""
        design = design_from_envelope(
            worm_od=20.0,
            wheel_od=64.0,
            ratio=30
        )
        
        expected_cd = (design.worm.pitch_diameter + design.wheel.pitch_diameter) / 2
        assert pytest.approx(design.centre_distance, rel=1e-6) == expected_cd


class TestDesignFromWheel:
    """Tests for wheel-constrained design"""
    
    def test_target_lead_angle(self):
        """Design should achieve target lead angle"""
        target = 10.0
        design = design_from_wheel(
            wheel_od=64.0,
            ratio=30,
            target_lead_angle=target
        )
        
        # Should be close to target (within 0.1°)
        assert pytest.approx(design.worm.lead_angle, abs=0.1) == target
    
    def test_wheel_od_preserved(self):
        """Wheel OD should match input"""
        design = design_from_wheel(
            wheel_od=64.0,
            ratio=30,
            target_lead_angle=7.0
        )
        
        assert pytest.approx(design.wheel.tip_diameter, rel=0.01) == 64.0


class TestDesignFromModule:
    """Tests for module-based design"""
    
    def test_module_preserved(self):
        """Module should match input"""
        design = design_from_module(
            module=2.0,
            ratio=30
        )
        
        assert pytest.approx(design.worm.module, rel=1e-6) == 2.0
        assert pytest.approx(design.wheel.module, rel=1e-6) == 2.0
    
    def test_with_specific_worm_diameter(self):
        """Should use specified worm pitch diameter"""
        design = design_from_module(
            module=2.0,
            ratio=30,
            worm_pitch_diameter=20.0
        )
        
        assert pytest.approx(design.worm.pitch_diameter, rel=1e-6) == 20.0


class TestDesignFromCentreDistance:
    """Tests for centre-distance-based design"""
    
    def test_centre_distance_preserved(self):
        """Centre distance should match input"""
        design = design_from_centre_distance(
            centre_distance=40.0,
            ratio=30
        )
        
        assert pytest.approx(design.centre_distance, rel=0.01) == 40.0


class TestEfficiencyEstimate:
    """Tests for efficiency estimation"""
    
    def test_efficiency_increases_with_lead_angle(self):
        """Higher lead angles should give higher efficiency"""
        eff_5 = estimate_efficiency(5.0)
        eff_10 = estimate_efficiency(10.0)
        eff_20 = estimate_efficiency(20.0)
        
        assert eff_10 > eff_5
        assert eff_20 > eff_10
    
    def test_efficiency_bounds(self):
        """Efficiency should be between 0 and 1"""
        for angle in [1, 5, 10, 20, 45]:
            eff = estimate_efficiency(float(angle))
            assert 0 <= eff <= 1
    
    def test_very_low_lead_angle(self):
        """Very low lead angles should have low efficiency"""
        eff = estimate_efficiency(2.0)
        assert eff < 0.5


class TestSelfLocking:
    """Tests for self-locking determination"""
    
    def test_low_lead_angle_self_locks(self):
        """Low lead angle (<6°) should be self-locking"""
        design = design_from_wheel(
            wheel_od=64.0,
            ratio=30,
            target_lead_angle=4.0
        )
        assert design.self_locking
    
    def test_high_lead_angle_not_self_locking(self):
        """High lead angle should not self-lock"""
        design = design_from_wheel(
            wheel_od=64.0,
            ratio=30,
            target_lead_angle=15.0
        )
        assert not design.self_locking


class TestHandedness:
    """Tests for thread handedness"""
    
    def test_right_hand_default(self):
        """Default should be right-hand"""
        design = design_from_envelope(
            worm_od=20.0,
            wheel_od=64.0,
            ratio=30
        )
        assert design.hand == Hand.RIGHT
    
    def test_left_hand_option(self):
        """Should accept left-hand option"""
        design = design_from_envelope(
            worm_od=20.0,
            wheel_od=64.0,
            ratio=30,
            hand=Hand.LEFT
        )
        assert design.hand == Hand.LEFT


class TestReferenceCalculations:
    """Tests against known reference values"""
    
    def test_reference_case_1(self):
        """
        Reference case: Module 2, ratio 30, target lead angle 7°
        
        Hand calculation:
        - Wheel teeth = 30
        - Wheel pitch dia = 2 × 30 = 60mm
        - Wheel tip dia = 60 + 2×2 = 64mm
        - Lead = π × 2 × 1 = 6.283mm
        - Worm pitch dia for 7° = lead / (π × tan(7°)) = 6.283 / (π × 0.1228) = 16.3mm
        """
        design = design_from_module(
            module=2.0,
            ratio=30,
            target_lead_angle=7.0,
            num_starts=1
        )
        
        assert design.wheel.num_teeth == 30
        assert pytest.approx(design.wheel.pitch_diameter, rel=1e-3) == 60.0
        assert pytest.approx(design.wheel.tip_diameter, rel=1e-3) == 64.0
        assert pytest.approx(design.worm.lead, rel=1e-3) == pi * 2.0
        
        # Lead angle should be close to 7°
        assert pytest.approx(design.worm.lead_angle, abs=0.5) == 7.0
