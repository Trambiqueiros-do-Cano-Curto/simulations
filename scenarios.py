from __future__ import annotations

from typing import List

from config import get_base_config


def _make_scenario(name: str, overrides: dict) -> dict:
    config = get_base_config(overrides)
    config["scenario_name"] = name
    return config


def build_block_a_leadership_policies() -> List[dict]:
    # Política de liderança
    common = {
        "cluster_size": 5,
        "rotation_mode": "time_driven",
        "rotation_every": 2,
        "wifi_failure_prob": 0.0,
        "max_wifi_retries": 0,
        "election_failure_prob": 0.0,
        "max_election_retries": 0,
        "dual_leader_conflict_prob": 0.0,
        "max_rounds": 600,
        "cooldown_rounds": 6,
    }

    return [
        _make_scenario(
            "A_round_robin_time_driven",
            {
                **common,
                "leadership_policy": "round_robin",
            },
        ),
        _make_scenario(
            "A_energy_time_driven",
            {
                **common,
                "leadership_policy": "energy",
            },
        ),
        _make_scenario(
            "A_energy_cooldown_time_driven",
            {
                **common,
                "leadership_policy": "energy_cooldown",
            },
        ),
    ]


def build_block_b_rotation_modes() -> List[dict]:
    # Time-driven vs Event-driven
    common = {
        "cluster_size": 5,
        "leadership_policy": "energy_cooldown",
        "wifi_failure_prob": 0.0,
        "max_wifi_retries": 0,
        "election_failure_prob": 0.0,
        "max_election_retries": 0,
        "dual_leader_conflict_prob": 0.0,
        "max_rounds": 600,
        "cooldown_rounds": 3,
    }

    return [
        _make_scenario(
            "B_energy_cooldown_time_driven",
            {
                **common,
                "rotation_mode": "time_driven",
                "rotation_every": 5,
            },
        ),
        _make_scenario(
            "B_energy_cooldown_event_driven",
            {
                **common,
                "rotation_mode": "event_driven",
                "event_threshold_ratio": 0.85,
            },
        ),
    ]


def build_block_c_wifi_robustness() -> List[dict]:
    # Robustez do uplink Wi-Fi
    common = {
        "cluster_size": 5,
        "leadership_policy": "energy_cooldown",
        "rotation_mode": "event_driven",
        "event_threshold_ratio": 0.90,
        "cooldown_rounds": 3,
        "election_failure_prob": 0.0,
        "max_election_retries": 0,
        "dual_leader_conflict_prob": 0.0,
        "max_rounds": 600,
    }

    return [
        _make_scenario(
            "C_wifi_no_failure",
            {
                **common,
                "wifi_failure_prob": 0.0,
                "max_wifi_retries": 0,
            },
        ),
        _make_scenario(
            "C_wifi_failure_no_retry",
            {
                **common,
                "wifi_failure_prob": 0.30,
                "max_wifi_retries": 0,
            },
        ),
        _make_scenario(
            "C_wifi_failure_with_retry",
            {
                **common,
                "wifi_failure_prob": 0.30,
                "max_wifi_retries": 2,
            },
        ),
    ]


def build_block_d_election_robustness() -> List[dict]:
    # Robustez da eleição
    common = {
        "cluster_size": 5,
        "leadership_policy": "energy_cooldown",
        "rotation_mode": "time_driven",
        "rotation_every": 2,
        "cooldown_rounds": 3,
        "wifi_failure_prob": 0.0,
        "max_wifi_retries": 0,
        "dual_leader_conflict_prob": 0.0,
        "max_rounds": 150,
    }

    return [
        _make_scenario(
            "D_election_no_failure",
            {
                **common,
                "election_failure_prob": 0.0,
                "max_election_retries": 0,
            },
        ),
        _make_scenario(
            "D_election_failure_no_retry",
            {
                **common,
                "election_failure_prob": 0.30,
                "max_election_retries": 0,
            },
        ),
        _make_scenario(
            "D_election_failure_with_retry",
            {
                **common,
                "election_failure_prob": 0.30,
                "max_election_retries": 2,
            },
        ),
    ]


def build_block_e_dual_leader_conflict() -> List[dict]:
    # Conflito dual-leader
    common = {
        "cluster_size": 5,
        "leadership_policy": "energy_cooldown",
        "rotation_mode": "time_driven",
        "rotation_every": 2,
        "cooldown_rounds": 3,
        "wifi_failure_prob": 0.0,
        "max_wifi_retries": 0,
        "election_failure_prob": 0.0,
        "max_election_retries": 0,
        "max_rounds": 150,
    }

    return [
        _make_scenario(
            "E_conflict_none",
            {
                **common,
                "dual_leader_conflict_prob": 0.0,
                "conflict_resolution_control_cost_multiplier": 1.0,
            },
        ),
        _make_scenario(
            "E_conflict_moderate",
            {
                **common,
                "dual_leader_conflict_prob": 0.30,
                "conflict_resolution_control_cost_multiplier": 1.0,
            },
        ),
        _make_scenario(
            "E_conflict_aggressive",
            {
                **common,
                "dual_leader_conflict_prob": 0.60,
                "conflict_resolution_control_cost_multiplier": 2.0,
            },
        ),
    ]


def build_block_f_scalability() -> List[dict]:
    # Escalabilidade por tamanho do cluster
    scenarios = []
    for cluster_size in (3, 5, 7):
        scenarios.append(
            _make_scenario(
                f"F_scalability_cluster_{cluster_size}",
                {
                    "cluster_size": cluster_size,
                    "leadership_policy": "energy_cooldown",
                    "rotation_mode": "event_driven",
                    "event_threshold_ratio": 0.90,
                    "cooldown_rounds": 3,
                    "wifi_failure_prob": 0.0,
                    "max_wifi_retries": 0,
                    "election_failure_prob": 0.0,
                    "max_election_retries": 0,
                    "dual_leader_conflict_prob": 0.0,
                    "max_rounds": 600,
                },
            )
        )
    return scenarios


def build_all_scenarios() -> List[dict]:
    scenarios = []
    scenarios.extend(build_block_a_leadership_policies())
    scenarios.extend(build_block_b_rotation_modes())
    scenarios.extend(build_block_c_wifi_robustness())
    scenarios.extend(build_block_d_election_robustness())
    scenarios.extend(build_block_e_dual_leader_conflict())
    scenarios.extend(build_block_f_scalability())
    return scenarios