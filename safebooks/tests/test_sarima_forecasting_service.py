from decimal import Decimal
from unittest.mock import patch

from django.test import SimpleTestCase

from safebooks.services.forecasting_service import build_sarima_forecast


class SarimaForecastingServiceTests(SimpleTestCase):
    @staticmethod
    def _monthly_history(count=24):
        return {
            (2024 + (index // 12), (index % 12) + 1): Decimal(1000 + (index * 25))
            for index in range(count)
        }

    @staticmethod
    def _quarterly_history():
        periods = [
            (2024, 3),
            (2024, 6),
            (2024, 9),
            (2024, 12),
            (2025, 3),
            (2025, 6),
            (2025, 9),
            (2025, 12),
        ]
        return {
            period: Decimal(5000 + (index * 100))
            for index, period in enumerate(periods)
        }

    def test_monthly_history_generates_sarima_forecast(self):
        result = build_sarima_forecast(
            period_totals=self._monthly_history(),
            frequency="monthly",
            forecast_through=(2026, 3),
        )

        self.assertEqual(result["status"], "forecast")
        self.assertEqual(result["model_label"], "SARIMA (0,1,0)(0,1,0)[12]")
        self.assertEqual(result["observation_count"], 24)
        self.assertEqual(
            set(result["forecast_by_period"]),
            {(2026, 1), (2026, 2), (2026, 3)},
        )
        self.assertTrue(all(value >= 0 for value in result["forecast_by_period"].values()))

    def test_quarterly_history_uses_quarterly_seasonality(self):
        result = build_sarima_forecast(
            period_totals=self._quarterly_history(),
            frequency="quarterly",
            forecast_through=(2026, 12),
        )

        self.assertEqual(result["status"], "forecast")
        self.assertEqual(result["model_label"], "SARIMA (0,1,0)(0,1,0)[4]")
        self.assertEqual(
            set(result["forecast_by_period"]),
            {(2026, 3), (2026, 6), (2026, 9), (2026, 12)},
        )

    def test_short_history_is_not_replaced_with_another_algorithm(self):
        result = build_sarima_forecast(
            period_totals=self._monthly_history(count=23),
            frequency="monthly",
            forecast_through=(2026, 3),
        )

        self.assertEqual(result["status"], "insufficient_history")
        self.assertEqual(result["forecast_by_period"], {})
        self.assertEqual(result["observation_count"], 23)
        self.assertEqual(result["minimum_observations"], 24)
        self.assertEqual(result["remaining_observations"], 1)
        self.assertIn("24", result["message"])

    def test_irregular_history_is_not_silently_imputed(self):
        history = self._monthly_history()
        del history[(2024, 8)]

        result = build_sarima_forecast(
            period_totals=history,
            frequency="monthly",
            forecast_through=(2026, 3),
        )

        self.assertEqual(result["status"], "irregular_history")
        self.assertEqual(result["forecast_by_period"], {})

    def test_annual_history_is_explicitly_unsupported(self):
        result = build_sarima_forecast(
            period_totals={(2024, 1): Decimal("1000"), (2025, 1): Decimal("1200")},
            frequency="annually",
            forecast_through=(2027, 12),
        )

        self.assertEqual(result["status"], "unsupported_frequency")
        self.assertEqual(result["forecast_by_period"], {})

    @patch("safebooks.services.forecasting_service._fit_sarima", return_value=[-1.0])
    def test_negative_projection_is_rejected(self, _mock_fit):
        result = build_sarima_forecast(
            period_totals=self._monthly_history(),
            frequency="monthly",
            forecast_through=(2026, 1),
        )

        self.assertEqual(result["status"], "unreliable_result")
        self.assertEqual(result["forecast_by_period"], {})

    @patch("safebooks.services.forecasting_service._fit_sarima", side_effect=ValueError("fit failed"))
    def test_model_failure_returns_controlled_status(self, _mock_fit):
        result = build_sarima_forecast(
            period_totals=self._monthly_history(),
            frequency="monthly",
            forecast_through=(2026, 1),
        )

        self.assertEqual(result["status"], "model_error")
        self.assertEqual(result["forecast_by_period"], {})
