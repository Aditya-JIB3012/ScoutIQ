"""Automated unit and pipeline tests for ScoutIQ."""

import unittest
import numpy as np
import pandas as pd

from scoutiq.data.dataset_generator import generate_player_dataset
from scoutiq.data.preprocessor import (
    parse_currency_to_millions,
    parse_wage_to_weekly_eur,
    parse_contract_years,
    FootballDataCleaner,
    FootballFeatureEngineer
)
from scoutiq.models.regressor import ScoutIQModelManager


class TestScoutIQPipeline(unittest.TestCase):

    def test_messy_data_parsers(self):
        # Currency parsing
        self.assertEqual(parse_currency_to_millions("€180.00m"), 180.0)
        self.assertEqual(parse_currency_to_millions("€900k"), 0.9)
        self.assertEqual(parse_currency_to_millions(" € 25.5 M "), 25.5)
        self.assertEqual(parse_currency_to_millions("€500K"), 0.5)
        self.assertTrue(np.isnan(parse_currency_to_millions("N/A")))

        # Wage parsing
        self.assertEqual(parse_wage_to_weekly_eur("€375,000 / week"), 375000)
        self.assertEqual(parse_wage_to_weekly_eur("€35,000 p/w"), 35000)
        self.assertEqual(parse_wage_to_weekly_eur("€12k"), 12000)

        # Contract years
        self.assertGreater(parse_contract_years("2028-06-30", reference_year=2025.5), 2.0)

    def test_full_pipeline_and_models(self):
        # 1. Dataset Generation
        raw_df = generate_player_dataset(300)
        self.assertGreaterEqual(len(raw_df), 300)
        self.assertIn("market_val_raw", raw_df.columns)

        # 2. Cleaning
        cleaner = FootballDataCleaner()
        df_clean = cleaner.fit_transform(raw_df)
        self.assertIn("market_val_m", df_clean.columns)
        self.assertFalse(df_clean["market_val_m"].isna().any())

        # 3. Feature Engineering
        fe = FootballFeatureEngineer()
        df_processed = fe.transform(df_clean)
        self.assertIn("log_market_val", df_processed.columns)
        self.assertIn("athletic_index", df_processed.columns)
        self.assertIn("age_squared", df_processed.columns)

        # 4. Model Training & Validation
        mgr = ScoutIQModelManager()
        metrics = mgr.train_and_evaluate(df_processed)

        for model_name, m in metrics.items():
            self.assertIn("R2_Score", m)
            self.assertIn("MAE_EUR_M", m)
            if model_name in ["Gradient Boosting", "Random Forest"]:
                self.assertGreater(m["R2_Score"], 0.75, f"{model_name} R2 score too low")
            else:
                self.assertGreater(m["R2_Score"], 0.40, f"{model_name} R2 score too low")

        # 5. Prediction
        sample_player = df_processed.iloc[0:1]
        pred_val = mgr.predict_value(sample_player)
        self.assertGreater(pred_val[0], 0.0)

        # 6. Explanations
        explanations = mgr.explain_player_valuation(df_processed.iloc[0])
        self.assertGreater(len(explanations), 3)

        # 7. Performance Index
        perf = mgr.compute_performance_index(df_processed.iloc[0])
        self.assertGreaterEqual(perf, 50.0)
        self.assertLessEqual(perf, 100.0)


if __name__ == "__main__":
    unittest.main()
