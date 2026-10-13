"""Additional extension checks; the original tests/ grading suite is untouched."""
import unittest

from finops.extensions import carbon_schedule, reasoning_budget
from missions import m2_inference_levers as m2, m3_purchasing as m3


class ExtensionChecks(unittest.TestCase):
    def test_reasoning_cap_preserves_token_basis_and_caps_requests(self):
        rows = [dict(input_tokens="1000", output_tokens="100", cached_input_tokens="0",
                     is_batch="0", is_reasoning="1", route_tier="large") for _ in range(10)]
        result = reasoning_budget(rows, m2.MODEL_PRICES)
        self.assertEqual(result["retained_reasoning_requests"], 1)
        self.assertEqual(result["rerouted_requests"], 9)
        self.assertAlmostEqual(result["saved_wh"], 9 * 1.1 * .3 * 79)
        self.assertAlmostEqual(result["saved_usd"], 9 * (0.0045 - 0.00024))
        self.assertEqual(result["groups"]["reasoning"]["tokens"], 11000)

    def test_empty_and_no_reasoning(self):
        self.assertEqual(reasoning_budget([], m2.MODEL_PRICES)["saved_usd"], 0)
        row = dict(input_tokens="100", output_tokens="10", cached_input_tokens="0",
                   is_batch="0", is_reasoning="0", route_tier="small")
        self.assertEqual(reasoning_budget([row], m2.MODEL_PRICES)["saved_wh"], 0)
        with self.assertRaises(ValueError):
            reasoning_budget([], m2.MODEL_PRICES, 1.1)

    def test_carbon_uses_job_days_gpu_count_and_all_regions(self):
        job = dict(job_id="one", interruptible="1", hours_per_day="10", days="2",
                   num_gpus="3", gpu_type="H100")
        result = carbon_schedule([job, dict(job, interruptible="0")], {"H100": {"watts": "700"}})
        self.assertEqual(result["energy_wh"], 42000)
        self.assertEqual(len(result["jobs"]), 1)
        self.assertEqual(len(result["regions"]), 5)
        self.assertAlmostEqual(result["saved_carbon_g"], 42 * (380 - 30))
        self.assertAlmostEqual(result["saved_electricity_usd"], 42 * (.12 - .09))
        self.assertEqual(result["cheapest_region"], "us-east-wa")
        self.assertEqual(result["cleanest_region"], "europe-north1")

    def test_pipeline_reconciles_stages_and_reserved_full_month(self):
        result = m2.run(False)
        stages = result["stages"]
        self.assertAlmostEqual(sum(s["saved_usd"] for s in stages),
                               stages[0]["cost_usd"] - stages[-1]["cost_usd"])
        self.assertAlmostEqual(sum(g["cost_usd"] for g in result["reasoning"]["groups"].values()),
                               stages[-1]["cost_usd"])
        jobs = m3.run(False)["recommendations"]
        search = next(j for j in jobs if j["job_id"] == "job-infer-search")
        self.assertEqual(search["optimized"], 24 * 30 * 4 * .45)


if __name__ == "__main__":
    unittest.main()
