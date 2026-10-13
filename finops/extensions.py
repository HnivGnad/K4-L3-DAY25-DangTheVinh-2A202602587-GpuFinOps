"""Measured reasoning and region scenarios using the lab's synthetic inputs.

All energy estimates are illustrative, not measurements of a physical GPU.
"""
from __future__ import annotations

from finops import pricing, sustainability as sust


def reasoning_budget(rows, model_prices, cap_fraction=0.10):
    """Cap reasoning requests; model overflow as standard small-model requests.

    No confidence/quality labels exist in the CSV. For a reproducible scenario,
    retain reasoning on requests with the most output tokens, then request ID.
    Token counts, cache eligibility and batch eligibility stay fixed. Dollar
    savings arise only from routing large -> small, not the energy multiplier.
    """
    if not 0 <= cap_fraction <= 1:
        raise ValueError("cap_fraction must be between 0 and 1")
    rows = list(rows)
    reasoning_ids = [i for i, r in enumerate(rows) if int(r["is_reasoning"])]
    limit = int(len(rows) * cap_fraction)
    keep = set(sorted(reasoning_ids,
                      key=lambda i: (-int(rows[i]["output_tokens"]), i))[:limit])
    groups = {name: {"requests": 0, "tokens": 0, "cost_usd": 0.0,
                     "energy_wh": 0.0, "standard_energy_wh": 0.0}
              for name in ("reasoning", "standard")}
    scenario_cost = scenario_wh = 0.0
    for i, r in enumerate(rows):
        inp, out = int(r["input_tokens"]), int(r["output_tokens"])
        reasoning = bool(int(r["is_reasoning"]))
        pin, pout = model_prices[r["route_tier"]]
        kwargs = {"cached_in": int(r["cached_input_tokens"]),
                  "batch": bool(int(r["is_batch"]))}
        cost = pricing.request_cost(inp, out, pin, pout, **kwargs)
        base_wh = sust.wh_per_query(inp + out)
        wh = sust.wh_per_query(inp + out, is_reasoning=reasoning)
        g = groups["reasoning" if reasoning else "standard"]
        g["requests"] += 1
        g["tokens"] += inp + out
        g["cost_usd"] += cost
        g["energy_wh"] += wh
        g["standard_energy_wh"] += base_wh
        if reasoning and i not in keep:
            pin, pout = model_prices["small"]
            scenario_cost += pricing.request_cost(inp, out, pin, pout, **kwargs)
            scenario_wh += base_wh
        else:
            scenario_cost += cost
            scenario_wh += wh
    cost = sum(g["cost_usd"] for g in groups.values())
    wh = sum(g["energy_wh"] for g in groups.values())
    return {"groups": groups, "cap_fraction": cap_fraction,
            "retained_reasoning_requests": len(keep),
            "rerouted_requests": len(reasoning_ids) - len(keep),
            "scenario_cost_usd": scenario_cost, "scenario_energy_wh": scenario_wh,
            "saved_usd": max(0.0, cost - scenario_cost), "saved_wh": max(0.0, wh - scenario_wh),
            "reasoning_traffic_fraction": len(reasoning_ids) / len(rows) if rows else 0,
            "reasoning_cost_fraction": groups["reasoning"]["cost_usd"] / cost if cost else 0,
            "reasoning_energy_fraction": groups["reasoning"]["energy_wh"] / wh if wh else 0}


def carbon_schedule(jobs, catalog, baseline_region="us-east-1"):
    """Compare every region for interruptible jobs over their actual job days.

    Energy = catalog power * useful GPU hours. Excludes PUE, checkpoint/rework,
    network transfer and regional GPU rental differences.
    """
    if baseline_region not in sust.REGION_CARBON:
        raise ValueError("unknown baseline region")
    cheapest = min(sust.REGION_PRICE_KWH, key=sust.REGION_PRICE_KWH.get)
    cleanest = min(sust.REGION_CARBON, key=sust.REGION_CARBON.get)
    balanced = min(sust.REGION_CARBON, key=lambda region:
                   sust.REGION_CARBON[region] / max(sust.REGION_CARBON.values())
                   + sust.REGION_PRICE_KWH[region] / max(sust.REGION_PRICE_KWH.values()))
    per_job = []
    for j in jobs:
        if not int(j["interruptible"]):
            continue
        hours = float(j["hours_per_day"]) * int(j["days"]) * int(j["num_gpus"])
        wh = hours * float(catalog[j["gpu_type"]]["watts"])
        base_carbon = sust.carbon_g(wh, baseline_region)
        target_carbon = sust.carbon_g(wh, cleanest)
        per_job.append({"job_id": j["job_id"], "days": int(j["days"]),
                        "gpu_hours": hours, "energy_wh": wh,
                        "baseline_carbon_g": base_carbon,
                        "target_carbon_g": target_carbon,
                        "saved_carbon_g": base_carbon - target_carbon})
    total_wh = sum(j["energy_wh"] for j in per_job)
    regions = [{"region": region, "usd_per_kwh": sust.REGION_PRICE_KWH[region],
                "g_per_kwh": intensity, "electricity_usd": sust.energy_cost_usd(total_wh, region),
                "carbon_g": sust.carbon_g(total_wh, region)}
               for region, intensity in sust.REGION_CARBON.items()]
    return {"jobs": per_job, "regions": regions, "energy_wh": total_wh,
            "baseline_region": baseline_region, "cheapest_region": cheapest,
            "cleanest_region": cleanest, "balanced_region": balanced,
            "saved_carbon_g": sust.carbon_g(total_wh, baseline_region) - sust.carbon_g(total_wh, cleanest),
            "saved_electricity_usd": sust.energy_cost_usd(total_wh, baseline_region) - sust.energy_cost_usd(total_wh, cleanest)}
