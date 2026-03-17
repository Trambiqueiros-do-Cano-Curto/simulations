from __future__ import annotations

import os
from copy import deepcopy
from statistics import pstdev
from typing import List

import pandas as pd

from simulator import run_simulation


def _safe_pstdev(values: list[float]) -> float:
    if len(values) <= 1:
        return 0.0
    return float(pstdev(values))


def _extract_final_charge_stats(result) -> tuple[float, float, float]:
    last_snapshot = result.snapshots[-1]
    charges = list(last_snapshot.charges.values())

    avg_charge = sum(charges) / len(charges)
    std_charge = _safe_pstdev(charges)
    min_charge = min(charges)

    return avg_charge, std_charge, min_charge


def _extract_leadership_fairness(result, cluster_size: int) -> float:
    counts = {node_id: 0 for node_id in range(cluster_size)}
    for leader_id in result.leader_history:
        counts[leader_id] += 1

    values = list(counts.values())
    return _safe_pstdev(values)


def result_to_row(config: dict, result, run_id: int) -> dict:
    avg_final_charge, std_final_charge, min_final_charge = _extract_final_charge_stats(result)
    leader_fairness_std = _extract_leadership_fairness(result, config["cluster_size"])

    fnd_round_value = result.fnd_round if result.fnd_round is not None else config["max_rounds"]
    fnd_observed = 1 if result.fnd_round is not None else 0

    return {
        "scenario_name": config["scenario_name"],
        "run_id": run_id,

        "cluster_size": config["cluster_size"],
        "leadership_policy": config["leadership_policy"],
        "rotation_mode": config["rotation_mode"],
        "rotation_every": config.get("rotation_every"),
        "event_threshold_ratio": config.get("event_threshold_ratio"),
        "cooldown_rounds": config.get("cooldown_rounds"),

        "wifi_failure_prob": config["wifi_failure_prob"],
        "max_wifi_retries": config["max_wifi_retries"],

        "election_failure_prob": config["election_failure_prob"],
        "max_election_retries": config["max_election_retries"],

        "dual_leader_conflict_prob": config["dual_leader_conflict_prob"],
        "conflict_resolution_control_cost_multiplier": config.get(
            "conflict_resolution_control_cost_multiplier", 1.0
        ),

        "total_rounds": result.total_rounds,
        "fnd_round": fnd_round_value,
        "fnd_observed": fnd_observed,

        "overall_pdr": result.overall_pdr,
        "uplink_pdr": result.uplink_pdr,

        "total_packets_sent": result.total_packets_sent,
        "total_packets_delivered": result.total_packets_delivered,
        "total_uplink_packets_sent": result.total_uplink_packets_sent,
        "total_uplink_packets_delivered": result.total_uplink_packets_delivered,

        "leader_switches": result.leader_switches,
        "election_count": result.election_count,

        "total_retransmissions": result.total_retransmissions,
        "total_failed_uplinks": result.total_failed_uplinks,
        "total_dropped_uplinks": result.total_dropped_uplinks,
        "total_wifi_attempts": result.total_wifi_attempts,

        "total_election_attempts": result.total_election_attempts,
        "total_election_retries": result.total_election_retries,
        "total_failed_election_attempts": result.total_failed_election_attempts,
        "total_failed_elections": result.total_failed_elections,
        "rounds_without_leader": result.rounds_without_leader,

        "total_dual_leader_conflicts": result.total_dual_leader_conflicts,
        "total_conflict_resolutions": result.total_conflict_resolutions,
        "total_conflict_overrides": result.total_conflict_overrides,

        "avg_final_charge": avg_final_charge,
        "std_final_charge": std_final_charge,
        "min_final_charge": min_final_charge,
        "leader_fairness_std": leader_fairness_std,
    }


def run_scenario_multiple_times(config: dict, n_runs: int = 20) -> list[dict]:
    rows = []
    base_seed = config.get("seed", 42)

    for run_id in range(n_runs):
        run_config = deepcopy(config)
        run_config["seed"] = base_seed + run_id

        result = run_simulation(run_config)
        row = result_to_row(run_config, result, run_id)
        rows.append(row)

    return rows


def run_all_scenarios(scenarios: List[dict], n_runs: int = 20) -> pd.DataFrame:
    all_rows = []

    total = len(scenarios)
    for idx, scenario in enumerate(scenarios, start=1):
        print(f"[{idx}/{total}] Rodando cenário: {scenario['scenario_name']}")
        rows = run_scenario_multiple_times(scenario, n_runs=n_runs)
        all_rows.extend(rows)

    return pd.DataFrame(all_rows)


def build_summary(raw_df: pd.DataFrame) -> pd.DataFrame:
    group_cols = [
        "scenario_name",
        "cluster_size",
        "leadership_policy",
        "rotation_mode",
        "rotation_every",
        "event_threshold_ratio",
        "cooldown_rounds",
        "wifi_failure_prob",
        "max_wifi_retries",
        "election_failure_prob",
        "max_election_retries",
        "dual_leader_conflict_prob",
        "conflict_resolution_control_cost_multiplier",
    ]

    metric_cols = [
        "total_rounds",
        "fnd_round",
        "fnd_observed",
        "overall_pdr",
        "uplink_pdr",
        "leader_switches",
        "election_count",
        "total_retransmissions",
        "total_failed_uplinks",
        "total_dropped_uplinks",
        "total_wifi_attempts",
        "total_election_attempts",
        "total_election_retries",
        "total_failed_election_attempts",
        "total_failed_elections",
        "rounds_without_leader",
        "total_dual_leader_conflicts",
        "total_conflict_resolutions",
        "total_conflict_overrides",
        "avg_final_charge",
        "std_final_charge",
        "min_final_charge",
        "leader_fairness_std",
    ]

    agg_dict = {}
    for col in metric_cols:
        agg_dict[col] = ["mean", "std"]

    summary = raw_df.groupby(group_cols, dropna=False).agg(agg_dict).reset_index()

    summary.columns = [
        "_".join(col).strip("_") if isinstance(col, tuple) else col
        for col in summary.columns
    ]

    return summary


def save_results(raw_df: pd.DataFrame, summary_df: pd.DataFrame, output_dir: str = "outputs") -> None:
    os.makedirs(output_dir, exist_ok=True)

    raw_path = os.path.join(output_dir, "raw_results.csv")
    summary_path = os.path.join(output_dir, "summary_results.csv")

    raw_df.to_csv(raw_path, index=False)
    summary_df.to_csv(summary_path, index=False)

    print(f"\nResultados brutos salvos em: {raw_path}")
    print(f"Resumo agregado salvo em: {summary_path}")