"""MDM/VEE pipeline tests.

Tests that VEE processing correctly validates, estimates, and edits readings.
"""

from datetime import datetime, timedelta, timezone

from app.models.enums import ReadingQualityType
from app.simulator import SimulatorEngine


class TestVEEPipeline:
    def test_validated_readings_marked(self, simulator: SimulatorEngine):
        """VEE-processed readings should have is_validated=True."""
        meter_mrid = list(simulator.get_meters().keys())[0]
        readings = simulator.get_meter_readings(
            meter_mrid, validated_only=True
        )
        for r in readings:
            assert r.is_validated is True

    def test_missing_readings_estimated(self, simulator: SimulatorEngine):
        """MISSING readings should be replaced with ESTIMATED after VEE."""
        meter_mrid = list(simulator.get_meters().keys())[0]
        validated = simulator.get_meter_readings(
            meter_mrid,
            reading_type_mrid="rt-forward-energy-wh",
            validated_only=True,
        )
        for r in validated:
            for block in r.interval_blocks:
                for ir in block.interval_readings:
                    # After VEE, there should be no MISSING quality
                    quality_types = [q.quality_type for q in ir.quality]
                    assert ReadingQualityType.MISSING not in quality_types

    def test_estimated_values_nonzero(self, simulator: SimulatorEngine):
        """Estimated readings should have interpolated non-zero values (mostly)."""
        meter_mrid = list(simulator.get_meters().keys())[0]
        validated = simulator.get_meter_readings(
            meter_mrid,
            reading_type_mrid="rt-forward-energy-wh",
            validated_only=True,
        )
        estimated_values = []
        for r in validated:
            for block in r.interval_blocks:
                for ir in block.interval_readings:
                    if any(
                        q.quality_type == ReadingQualityType.ESTIMATED
                        for q in ir.quality
                    ):
                        estimated_values.append(ir.value)

        # Some readings may have been estimated; if so, most should be > 0
        if estimated_values:
            nonzero = [v for v in estimated_values if v > 0]
            assert len(nonzero) >= len(estimated_values) * 0.5


class TestBillingDeterminants:
    def test_billing_determinants(self, simulator: SimulatorEngine):
        """Billing determinants should return valid totals."""
        meter_mrid = list(simulator.get_meters().keys())[0]
        now = datetime.now(timezone.utc)
        start = now - timedelta(days=3)
        result = simulator.get_billing_determinants(meter_mrid, start, now)

        assert "total_kwh" in result
        assert "peak_kw" in result
        assert "on_peak_kwh" in result
        assert "off_peak_kwh" in result
        assert result["total_kwh"] >= 0
        assert result["peak_kw"] >= 0

    def test_on_off_peak_sum(self, simulator: SimulatorEngine):
        """On-peak + off-peak should approximately equal total."""
        meter_mrid = list(simulator.get_meters().keys())[0]
        now = datetime.now(timezone.utc)
        start = now - timedelta(days=3)
        result = simulator.get_billing_determinants(meter_mrid, start, now)

        total = result["total_kwh"]
        combined = result["on_peak_kwh"] + result["off_peak_kwh"]
        assert abs(total - combined) < 0.1
