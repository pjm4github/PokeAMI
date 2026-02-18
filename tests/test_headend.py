"""Headend simulator tests.

Tests meter count, type distribution, reading existence, interval count,
and value ranges.
"""

from app.models.enums import MeterType
from app.simulator import SimulatorEngine


class TestHeadendMeterFleet:
    def test_meter_count(self, simulator: SimulatorEngine):
        meters = simulator.get_meters()
        assert len(meters) == 5

    def test_all_meters_have_readings(self, simulator: SimulatorEngine):
        for mrid in simulator.get_meters():
            readings = simulator.get_meter_readings(mrid)
            assert len(readings) > 0, f"Meter {mrid} has no readings"

    def test_reading_types_exist(self, simulator: SimulatorEngine):
        """Each meter should have at least forward energy, demand, and voltage."""
        for mrid in simulator.get_meters():
            readings = simulator.get_meter_readings(mrid)
            rt_mrids = {r.reading_type_mrid for r in readings}
            assert "rt-forward-energy-wh" in rt_mrids
            assert "rt-demand-w" in rt_mrids
            assert "rt-voltage-v" in rt_mrids


class TestHeadendReadings:
    def test_interval_count(self, simulator: SimulatorEngine):
        """3 days * 96 intervals/day = 288 intervals expected."""
        meters = list(simulator.get_meters().values())
        meter = meters[0]
        readings = simulator.get_meter_readings(
            meter.mrid, reading_type_mrid="rt-forward-energy-wh"
        )
        assert len(readings) == 1
        block = readings[0].interval_blocks[0]
        assert len(block.interval_readings) == 288

    def test_energy_values_positive(self, simulator: SimulatorEngine):
        """Forward energy values should be non-negative."""
        for mrid in simulator.get_meters():
            readings = simulator.get_meter_readings(
                mrid, reading_type_mrid="rt-forward-energy-wh"
            )
            for r in readings:
                for block in r.interval_blocks:
                    for ir in block.interval_readings:
                        assert ir.value >= 0.0

    def test_voltage_in_reasonable_range(self, simulator: SimulatorEngine):
        """Voltage should be within a physically reasonable range."""
        for mrid in simulator.get_meters():
            readings = simulator.get_meter_readings(
                mrid, reading_type_mrid="rt-voltage-v"
            )
            for r in readings:
                for block in r.interval_blocks:
                    for ir in block.interval_readings:
                        # Skip MISSING readings (value zeroed out)
                        if ir.value == 0.0:
                            continue
                        # Allow wide range for both 120V and 240V nominal
                        assert 100.0 <= ir.value <= 280.0

    def test_readings_not_validated(self, simulator: SimulatorEngine):
        """Raw headend readings should not be validated."""
        for mrid in simulator.get_meters():
            readings = simulator.get_meter_readings(mrid)
            for r in readings:
                assert r.is_validated is False

    def test_reading_types_catalog(self, simulator: SimulatorEngine):
        """Should have at least 3 reading types in catalog."""
        rt = simulator.get_reading_types()
        assert len(rt) >= 3
        assert "rt-forward-energy-wh" in rt
        assert "rt-demand-w" in rt
        assert "rt-voltage-v" in rt
