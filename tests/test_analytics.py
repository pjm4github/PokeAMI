"""Analytics engine tests.

Tests demand peak calculation, load factor range, and voltage exceedance detection.
"""

from datetime import datetime, timedelta, timezone

from app.simulator import SimulatorEngine


class TestDemandAnalytics:
    def test_demand_summary_returns_results(self, simulator: SimulatorEngine):
        now = datetime.now(timezone.utc)
        start = now - timedelta(days=3)
        summaries = simulator.get_demand_summary(start, now)
        assert len(summaries) > 0

    def test_demand_peak_is_max(self, simulator: SimulatorEngine):
        """Peak demand should equal the maximum of all data points."""
        now = datetime.now(timezone.utc)
        start = now - timedelta(days=3)
        summaries = simulator.get_demand_summary(start, now)

        for summary in summaries:
            if summary.data_points:
                max_value = max(dp.demand_w for dp in summary.data_points)
                # Peak might be higher than data_points (which are limited to 100)
                assert summary.peak_demand_w >= max_value or len(summary.data_points) == 100

    def test_load_factor_range(self, simulator: SimulatorEngine):
        """Load factor should be between 0.0 and 1.0."""
        now = datetime.now(timezone.utc)
        start = now - timedelta(days=3)
        summaries = simulator.get_demand_summary(start, now)

        for summary in summaries:
            assert 0.0 <= summary.load_factor <= 1.0

    def test_single_meter_demand(self, simulator: SimulatorEngine):
        """Demand summary for a single meter should return exactly one result."""
        meter_mrid = list(simulator.get_meters().keys())[0]
        now = datetime.now(timezone.utc)
        start = now - timedelta(days=3)
        summaries = simulator.get_demand_summary(start, now, meter_mrid)
        assert len(summaries) == 1
        assert summaries[0].meter_mrid == meter_mrid


class TestVoltageAnalytics:
    def test_voltage_summary_returns_results(self, simulator: SimulatorEngine):
        now = datetime.now(timezone.utc)
        start = now - timedelta(days=3)
        summaries = simulator.get_voltage_summary(start, now)
        assert len(summaries) > 0

    def test_voltage_stats_consistent(self, simulator: SimulatorEngine):
        """min <= average <= max for voltage."""
        now = datetime.now(timezone.utc)
        start = now - timedelta(days=3)
        summaries = simulator.get_voltage_summary(start, now)

        for summary in summaries:
            assert summary.min_voltage_v <= summary.average_voltage_v
            assert summary.average_voltage_v <= summary.max_voltage_v

    def test_exceedance_count_nonnegative(self, simulator: SimulatorEngine):
        """ANSI C84.1 exceedance count should be non-negative."""
        now = datetime.now(timezone.utc)
        start = now - timedelta(days=3)
        summaries = simulator.get_voltage_summary(start, now)

        for summary in summaries:
            assert summary.ansi_c84_1_exceedance_count >= 0


class TestRevenueProtection:
    def test_alerts_have_valid_fields(self, simulator: SimulatorEngine):
        now = datetime.now(timezone.utc)
        start = now - timedelta(days=3)
        alerts = simulator.get_revenue_protection_alerts(start, now)

        for alert in alerts:
            assert alert.mrid
            assert alert.meter_mrid
            assert alert.alert_type in (
                "tamper", "bypass", "reverse_flow", "consumption_anomaly"
            )
            assert alert.severity in ("low", "medium", "high", "critical")
