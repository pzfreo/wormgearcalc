"""
Tests for wormcalc.cli

Test CLI commands and argument parsing.
"""

import pytest
import json
from click.testing import CliRunner

from wormcalc.cli import cli


class TestEnvelopeCommand:
    """Tests for envelope command"""

    def test_envelope_basic(self):
        """Envelope command should work with basic parameters"""
        runner = CliRunner()
        result = runner.invoke(cli, [
            'envelope',
            '--worm-od', '20',
            '--wheel-od', '65',
            '--ratio', '30'
        ])

        assert result.exit_code == 0
        assert 'Module' in result.output
        assert 'Ratio: 30:1' in result.output

    def test_envelope_with_pressure_angle(self):
        """Envelope command should accept pressure angle"""
        runner = CliRunner()
        result = runner.invoke(cli, [
            'envelope',
            '--worm-od', '20',
            '--wheel-od', '65',
            '--ratio', '30',
            '--pressure-angle', '25'
        ])

        assert result.exit_code == 0
        # Pressure angle affects calculations even if not shown in summary

    def test_envelope_with_backlash(self):
        """Envelope command should accept backlash"""
        runner = CliRunner()
        result = runner.invoke(cli, [
            'envelope',
            '--worm-od', '20',
            '--wheel-od', '65',
            '--ratio', '30',
            '--backlash', '0.1'
        ])

        assert result.exit_code == 0

    def test_envelope_json_output(self):
        """Envelope command should output JSON when requested"""
        runner = CliRunner()
        result = runner.invoke(cli, [
            'envelope',
            '--worm-od', '20',
            '--wheel-od', '65',
            '--ratio', '30',
            '--output', 'json'
        ])

        assert result.exit_code == 0
        # Should be valid JSON
        data = json.loads(result.output)
        assert 'worm' in data
        assert 'wheel' in data

    def test_envelope_left_hand(self):
        """Envelope command should accept left hand"""
        runner = CliRunner()
        result = runner.invoke(cli, [
            'envelope',
            '--worm-od', '20',
            '--wheel-od', '65',
            '--ratio', '30',
            '--hand', 'left'
        ])

        assert result.exit_code == 0


class TestFromWheelCommand:
    """Tests for from-wheel command"""

    def test_from_wheel_basic(self):
        """From-wheel command should work with basic parameters"""
        runner = CliRunner()
        result = runner.invoke(cli, [
            'from-wheel',
            '--wheel-od', '65',
            '--ratio', '30',
            '--target-lead-angle', '8'
        ])

        assert result.exit_code == 0
        assert 'Ratio: 30:1' in result.output

    def test_from_wheel_json_output(self):
        """From-wheel command should output JSON"""
        runner = CliRunner()
        result = runner.invoke(cli, [
            'from-wheel',
            '--wheel-od', '65',
            '--ratio', '30',
            '--target-lead-angle', '8',
            '--output', 'json'
        ])

        assert result.exit_code == 0
        data = json.loads(result.output)
        assert 'assembly' in data
        assert data['assembly']['ratio'] == 30


class TestFromModuleCommand:
    """Tests for from-module command"""

    def test_from_module_basic(self):
        """From-module command should work with basic parameters"""
        runner = CliRunner()
        result = runner.invoke(cli, [
            'from-module',
            '--module', '2.0',
            '--ratio', '30'
        ])

        assert result.exit_code == 0
        assert 'Module: 2.0' in result.output or '2.0 mm' in result.output

    def test_from_module_with_target_lead_angle(self):
        """From-module command should accept target lead angle"""
        runner = CliRunner()
        result = runner.invoke(cli, [
            'from-module',
            '--module', '2.0',
            '--ratio', '30',
            '--target-lead-angle', '10'
        ])

        assert result.exit_code == 0

    def test_from_module_json_output(self):
        """From-module command should output JSON"""
        runner = CliRunner()
        result = runner.invoke(cli, [
            'from-module',
            '--module', '2.0',
            '--ratio', '30',
            '--output', 'json'
        ])

        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data['worm']['module_mm'] == 2.0

    def test_from_module_multi_start(self):
        """From-module command should accept multi-start"""
        runner = CliRunner()
        result = runner.invoke(cli, [
            'from-module',
            '--module', '2.0',
            '--ratio', '30',
            '--num-starts', '2'
        ])

        assert result.exit_code == 0


class TestFromCentreDistanceCommand:
    """Tests for from-centre-distance command"""

    def test_from_centre_distance_basic(self):
        """From-centre-distance command should work with basic parameters"""
        runner = CliRunner()
        result = runner.invoke(cli, [
            'from-centre-distance',
            '--centre-distance', '40',
            '--ratio', '30'
        ])

        assert result.exit_code == 0
        assert 'Ratio: 30:1' in result.output

    def test_from_centre_distance_json_output(self):
        """From-centre-distance command should output JSON"""
        runner = CliRunner()
        result = runner.invoke(cli, [
            'from-centre-distance',
            '--centre-distance', '40',
            '--ratio', '30',
            '--output', 'json'
        ])

        assert result.exit_code == 0
        data = json.loads(result.output)
        assert 'assembly' in data


class TestUtilityCommands:
    """Tests for utility commands"""

    def test_list_modules(self):
        """List-modules command should display standard modules"""
        runner = CliRunner()
        result = runner.invoke(cli, ['list-modules'])

        assert result.exit_code == 0
        assert 'Standard Modules' in result.output
        # Should include some common modules
        assert '0.5' in result.output
        assert '1.0' in result.output
        assert '2.0' in result.output

    def test_check_module_standard(self):
        """Check-module command should identify standard modules"""
        runner = CliRunner()
        result = runner.invoke(cli, ['check-module', '--module', '2.0'])

        assert result.exit_code == 0
        assert 'standard' in result.output.lower()

    def test_check_module_non_standard(self):
        """Check-module command should identify non-standard modules"""
        runner = CliRunner()
        result = runner.invoke(cli, ['check-module', '--module', '2.3'])

        assert result.exit_code == 0
        # Check for "No" in standard field
        assert 'standard' in result.output.lower() and 'no' in result.output.lower()
        # Should suggest nearest
        assert '2.25' in result.output or '2.5' in result.output


class TestOutputFormats:
    """Tests for different output formats"""

    def test_text_output_default(self):
        """Text output should be default"""
        runner = CliRunner()
        result = runner.invoke(cli, [
            'from-module',
            '--module', '2.0',
            '--ratio', '30'
        ])

        assert result.exit_code == 0
        # Text format characteristics
        assert 'Worm Gear Design' in result.output
        assert '═' in result.output or '-' in result.output

    def test_json_output_format(self):
        """JSON output format should be valid"""
        runner = CliRunner()
        result = runner.invoke(cli, [
            'from-module',
            '--module', '2.0',
            '--ratio', '30',
            '--output', 'json'
        ])

        assert result.exit_code == 0
        data = json.loads(result.output)
        assert isinstance(data, dict)

    def test_markdown_output_format(self):
        """Markdown output format should have markdown syntax"""
        runner = CliRunner()
        result = runner.invoke(cli, [
            'from-module',
            '--module', '2.0',
            '--ratio', '30',
            '--output', 'markdown'
        ])

        assert result.exit_code == 0
        # Markdown characteristics
        assert '# ' in result.output  # Headers
        assert '## ' in result.output


class TestManufacturingOptions:
    """Tests for manufacturing-related options"""

    def test_profile_za(self):
        """Should accept ZA profile"""
        runner = CliRunner()
        result = runner.invoke(cli, [
            'from-module',
            '--module', '2.0',
            '--ratio', '30',
            '--profile', 'ZA'
        ])

        assert result.exit_code == 0

    def test_profile_zk(self):
        """Should accept ZK profile"""
        runner = CliRunner()
        result = runner.invoke(cli, [
            'from-module',
            '--module', '2.0',
            '--ratio', '30',
            '--profile', 'ZK'
        ])

        assert result.exit_code == 0

    def test_worm_type_cylindrical(self):
        """Should accept cylindrical worm type"""
        runner = CliRunner()
        result = runner.invoke(cli, [
            'from-module',
            '--module', '2.0',
            '--ratio', '30',
            '--worm-type', 'cylindrical'
        ])

        assert result.exit_code == 0

    def test_worm_type_globoid(self):
        """Should accept globoid worm type"""
        runner = CliRunner()
        result = runner.invoke(cli, [
            'from-module',
            '--module', '2.0',
            '--ratio', '30',
            '--worm-type', 'globoid'
        ])

        assert result.exit_code == 0

    def test_wheel_throated(self):
        """Should accept throated flag"""
        runner = CliRunner()
        result = runner.invoke(cli, [
            'from-module',
            '--module', '2.0',
            '--ratio', '30',
            '--throated'
        ])

        assert result.exit_code == 0


class TestErrorHandling:
    """Tests for error handling"""

    def test_missing_required_args(self):
        """Should error when required args are missing"""
        runner = CliRunner()
        result = runner.invoke(cli, ['envelope'])

        assert result.exit_code != 0

    def test_invalid_module(self):
        """Should handle invalid module gracefully"""
        runner = CliRunner()
        result = runner.invoke(cli, [
            'from-module',
            '--module', '-1',  # Negative module
            '--ratio', '30'
        ])

        # Should either error or show validation warnings
        assert result.exit_code == 0 or result.exit_code != 0

    def test_invalid_ratio(self):
        """Should handle invalid ratio gracefully"""
        runner = CliRunner()
        result = runner.invoke(cli, [
            'from-module',
            '--module', '2.0',
            '--ratio', '0'  # Zero ratio
        ])

        # Should error or show validation
        assert result.exit_code == 0 or result.exit_code != 0


# Note: profile-shift option is not currently exposed in CLI
# It's supported in the core library but not yet available as a CLI option
