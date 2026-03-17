from __future__ import annotations
from copy import deepcopy

def get_base_config(overrides: dict | None = None) -> dict:
    config = {
        "scenario_name": "baseline",

        # Estrutura
        "cluster_size": 5,
        "max_rounds": 300,
        "stop_on_fnd": True,
        "seed": 42,

        # Carga inicial dos nós
        "initial_charge_mean": 100.0,
        "initial_charge_std": 5.0,
        "min_initial_charge": 90.0,
        "max_initial_charge": 110.0,

        # Política de liderança
        # opções: "round_robin", "energy", "energy_cooldown"
        "leadership_policy": "round_robin",

        # Política de rotação
        # opções: "time_driven", "event_driven"
        "rotation_mode": "time_driven",
        "rotation_every": 5,

        # No modo event-driven, troca quando a carga atual do líder
        # cair abaixo de um percentual da carga que ele tinha
        # no momento em que assumiu a liderança
        "event_threshold_ratio": 0.90,

        # Cooldown
        "cooldown_rounds": 3,

        # Custos energéticos básicos por rodada
        "base_idle_cost": 0.02,
        "espnow_tx_cost": 0.06,
        "espnow_rx_cost": 0.04,
        "wifi_assoc_cost": 0.18,
        "wifi_tx_cost": 0.25,
        "wifi_ack_cost": 0.08,
        "control_cost": 0.03,

        # Falhas e retransmissão no uplink Wi-Fi
        "wifi_failure_prob": 0.0,
        "max_wifi_retries": 0,

        # Falhas na eleição
        "election_failure_prob": 0.0,
        "max_election_retries": 0,
        "dual_leader_conflict_prob": 0.0,
        "conflict_resolution_control_cost_multiplier": 1.0,
    }

    if overrides:
        config.update(overrides)

    validate_config(config)
    return deepcopy(config)


def validate_config(config: dict) -> None:
    if config["cluster_size"] < 2:
        raise ValueError("cluster_size deve ser >= 2.")

    if config["max_rounds"] <= 0:
        raise ValueError("max_rounds deve ser > 0.")

    if config["leadership_policy"] not in {"round_robin", "energy", "energy_cooldown"}:
        raise ValueError("leadership_policy inválida.")

    if config["rotation_mode"] not in {"time_driven", "event_driven"}:
        raise ValueError("rotation_mode inválida.")

    if config["rotation_every"] <= 0:
        raise ValueError("rotation_every deve ser > 0.")

    if not (0.0 < config["event_threshold_ratio"] <= 1.0):
        raise ValueError("event_threshold_ratio deve estar em (0, 1].")

    if config["cooldown_rounds"] < 0:
        raise ValueError("cooldown_rounds não pode ser negativo.")

    if not (0.0 <= config["wifi_failure_prob"] <= 1.0):
        raise ValueError("wifi_failure_prob deve estar em [0, 1].")

    if config["max_wifi_retries"] < 0:
        raise ValueError("max_wifi_retries não pode ser negativo.")

    if not (0.0 <= config["election_failure_prob"] <= 1.0):
        raise ValueError("election_failure_prob deve estar em [0, 1].")

    if config["max_election_retries"] < 0:
        raise ValueError("max_election_retries não pode ser negativo.")
    
    if not (0.0 <= config["dual_leader_conflict_prob"] <= 1.0):
        raise ValueError("dual_leader_conflict_prob deve estar em [0, 1].")

    if config["conflict_resolution_control_cost_multiplier"] < 0:
        raise ValueError("conflict_resolution_control_cost_multiplier não pode ser negativo.")

    cost_keys = [
        "base_idle_cost",
        "espnow_tx_cost",
        "espnow_rx_cost",
        "wifi_assoc_cost",
        "wifi_tx_cost",
        "wifi_ack_cost",
        "control_cost",
    ]
    for key in cost_keys:
        if config[key] < 0:
            raise ValueError(f"{key} não pode ser negativo.")