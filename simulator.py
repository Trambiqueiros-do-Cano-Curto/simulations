from __future__ import annotations
import random
from typing import Optional
from models import ClusterState, Node, RoundSnapshot, SimulationResult


def initialize_cluster(config: dict, rng: random.Random) -> ClusterState:
    nodes = []

    for node_id in range(config["cluster_size"]):
        charge = rng.gauss(
            config["initial_charge_mean"],
            config["initial_charge_std"],
        )
        charge = max(config["min_initial_charge"], charge)
        charge = min(config["max_initial_charge"], charge)

        node = Node(
            node_id=node_id,
            initial_charge=charge,
            remaining_charge=charge,
            signal_quality="medium",
        )
        nodes.append(node)

    cluster = ClusterState(nodes=nodes)
    elect_leader(cluster, config, rng, initial=True)
    return cluster


def select_leader(cluster: ClusterState, config: dict, exclude_current: bool) -> Optional[int]:
    alive_nodes = cluster.alive_nodes()
    if not alive_nodes:
        return None

    policy = config["leadership_policy"]

    if policy == "round_robin":
        return select_leader_round_robin(cluster)

    candidates = alive_nodes

    if exclude_current and cluster.current_leader_id is not None and len(alive_nodes) > 1:
        candidates = [n for n in alive_nodes if n.node_id != cluster.current_leader_id]

    if policy == "energy":
        chosen = max(
            candidates,
            key=lambda n: (n.remaining_charge, -n.node_id),
        )
        return chosen.node_id

    if policy == "energy_cooldown":
        def cooldown_score(n: Node):
            is_available = 1 if n.cooldown_remaining <= 0 else 0

            return (
                is_available,            # disponível é melhor
                -n.cooldown_remaining,   # se todos estiverem bloqueados, menos bloqueado é melhor
                -n.times_as_leader,      # menos vezes líder é melhor
                n.remaining_charge,      # depois vem energia
                -n.node_id,              # desempate
            )

        chosen = max(candidates, key=cooldown_score)
        return chosen.node_id

    raise ValueError(f"Política desconhecida: {policy}")


def select_leader_round_robin(cluster: ClusterState) -> Optional[int]:
    alive_nodes = cluster.alive_nodes()
    if not alive_nodes:
        return None

    alive_ids = [node.node_id for node in alive_nodes]

    if cluster.current_leader_id is None:
        return alive_ids[0]

    if cluster.current_leader_id not in alive_ids:
        for node_id in alive_ids:
            if node_id > cluster.current_leader_id:
                return node_id
        return alive_ids[0]

    current_index = alive_ids.index(cluster.current_leader_id)
    next_index = (current_index + 1) % len(alive_ids)
    return alive_ids[next_index]


def apply_election_control_cost(cluster: ClusterState, config: dict) -> None:
    for node in cluster.alive_nodes():
        node.consume(config["control_cost"])


def elect_leader(
    cluster: ClusterState,
    config: dict,
    rng: random.Random,
    initial: bool = False,
) -> Optional[int]:
    old_leader_id = cluster.current_leader_id
    old_leader = cluster.get_current_leader()
    exclude_current = not initial

    max_attempts = 1 + config["max_election_retries"]

    for attempt_index in range(max_attempts):
        candidate_id = select_leader(
            cluster=cluster,
            config=config,
            exclude_current=exclude_current,
        )

        if candidate_id is None:
            cluster.total_failed_elections += 1
            cluster.current_leader_id = None
            cluster.leader_charge_at_election = None
            return None

        apply_election_control_cost(cluster, config)
        cluster.total_election_attempts += 1

        if attempt_index > 0:
            cluster.total_election_retries += 1

        candidate = cluster.get_node(candidate_id)

        # Se o candidato morreu por custo de controle
        if not candidate.alive:
            cluster.total_failed_election_attempts += 1
            continue

        failed = election_attempt_failed(config, rng)
        if failed:
            cluster.total_failed_election_attempts += 1
            continue

        # Eleição base bem-sucedida; agora pode haver conflito dual-leader
        final_leader_id = candidate_id

        if dual_leader_conflict_happened(config, rng):
            conflicting_id = select_conflicting_leader_candidate(
                cluster=cluster,
                elected_leader_id=candidate_id,
            )

            if conflicting_id is not None:
                cluster.total_dual_leader_conflicts += 1
                final_leader_id = resolve_dual_leader_conflict(
                    cluster=cluster,
                    elected_leader_id=candidate_id,
                    conflicting_leader_id=conflicting_id,
                    config=config,
                )

        final_leader = cluster.get_node(final_leader_id)

        # Se o líder final morreu após resolução, trata como falha da tentativa
        if not final_leader.alive:
            cluster.total_failed_election_attempts += 1
            continue

        # Sucesso final da eleição
        cluster.current_leader_id = final_leader_id
        cluster.election_count += 1

        if old_leader_id is not None and old_leader_id != final_leader_id:
            cluster.leader_switches += 1

        apply_cooldown_to_previous_leader(
            cluster=cluster,
            old_leader_id=old_leader_id,
            new_leader_id=final_leader_id,
            config=config,
        )

        final_leader.times_as_leader += 1
        final_leader.leadership_history.append(cluster.round_index)
        cluster.leader_charge_at_election = final_leader.remaining_charge
        cluster.leader_history.append(final_leader_id)
        return final_leader_id

    # Se chegou aqui, todas as tentativas falharam
    cluster.total_failed_elections += 1

    # Fallback: mantém líder antigo, se ele ainda estiver vivo
    if old_leader is not None and old_leader.alive:
        cluster.current_leader_id = old_leader_id
        return old_leader_id

    cluster.current_leader_id = None
    cluster.leader_charge_at_election = None
    return None

def should_rotate_leader(cluster: ClusterState, config: dict) -> bool:
    leader = cluster.get_current_leader()

    if leader is None:
        return True

    if config["rotation_mode"] == "time_driven":
        return cluster.round_index > 0 and cluster.round_index % config["rotation_every"] == 0

    if config["rotation_mode"] == "event_driven":
        if cluster.leader_charge_at_election is None:
            return False

        threshold_charge = (
            cluster.leader_charge_at_election * config["event_threshold_ratio"]
        )
        return leader.remaining_charge <= threshold_charge

    raise ValueError(f"rotation_mode inválido: {config['rotation_mode']}")

def apply_cooldown_to_previous_leader(
    cluster: ClusterState,
    old_leader_id: Optional[int],
    new_leader_id: Optional[int],
    config: dict,
) -> None:
    if old_leader_id is None:
        return

    if new_leader_id is None:
        return

    if old_leader_id == new_leader_id:
        return

    old_leader = cluster.get_node(old_leader_id)
    if old_leader.alive:
        old_leader.cooldown_remaining = config["cooldown_rounds"]

def apply_base_idle_cost(cluster: ClusterState, config: dict) -> None:
    for node in cluster.alive_nodes():
        node.consume(config["base_idle_cost"])


def apply_member_costs(cluster: ClusterState, config: dict) -> None:
    leader = cluster.get_current_leader()
    if leader is None:
        return

    alive_nodes = cluster.alive_nodes()
    members = [node for node in alive_nodes if node.node_id != leader.node_id]

    for member in members:
        member.consume(config["espnow_tx_cost"])

    leader.consume(config["espnow_rx_cost"] * len(members))

    # Cada membro envia 1 pacote local por rodada
    cluster.packets_sent += len(members)
    cluster.packets_delivered += len(members)


def apply_leader_uplink_with_failures(
    cluster: ClusterState,
    config: dict,
    rng: random.Random,
) -> None:
    leader = cluster.get_current_leader()
    if leader is None:
        return

    # 1 uplink lógico agregado por rodada
    cluster.packets_sent += 1
    cluster.uplink_packets_sent += 1

    # custo de iniciar/associar uma vez por uplink
    leader.consume(config["wifi_assoc_cost"])

    if not leader.alive:
        cluster.total_failed_uplinks += 1
        cluster.total_dropped_uplinks += 1
        return

    max_attempts = 1 + config["max_wifi_retries"]

    for attempt_index in range(max_attempts):
        leader.consume(config["wifi_tx_cost"] + config["wifi_ack_cost"])
        cluster.total_wifi_attempts += 1

        if attempt_index > 0:
            cluster.total_retransmissions += 1
            leader.retry_count += 1

        if not leader.alive:
            cluster.total_failed_uplinks += 1
            cluster.total_dropped_uplinks += 1
            return

        failed = wifi_attempt_failed(config, rng)

        if not failed:
            cluster.packets_delivered += 1
            cluster.uplink_packets_delivered += 1
            return

    # se saiu do loop, todas as tentativas falharam
    leader.failed_tx_count += 1
    cluster.total_failed_uplinks += 1
    cluster.total_dropped_uplinks += 1


def record_snapshot(cluster: ClusterState) -> RoundSnapshot:
    charges = {
        node.node_id: round(node.remaining_charge, 4)
        for node in cluster.nodes
    }

    return RoundSnapshot(
        round_index=cluster.round_index,
        leader_id=cluster.current_leader_id,
        charges=charges,
        alive_count=cluster.alive_count(),
    )


def first_dead_node_exists(cluster: ClusterState) -> bool:
    return any(not node.alive for node in cluster.nodes)


def run_single_round(cluster: ClusterState, config: dict, rng: random.Random) -> None:
    cluster.round_index += 1

    if should_rotate_leader(cluster, config):
        elect_leader(cluster, config, rng)

    apply_base_idle_cost(cluster, config)

    if cluster.get_current_leader() is None:
        cluster.rounds_without_leader += 1
        update_cooldowns(cluster)
        return

    apply_member_costs(cluster, config)

    if cluster.get_current_leader() is None:
        cluster.rounds_without_leader += 1
        update_cooldowns(cluster)
        return

    apply_leader_uplink_with_failures(cluster, config, rng)

    update_cooldowns(cluster)

def run_simulation(config: dict) -> SimulationResult:
    rng = random.Random(config["seed"])
    cluster = initialize_cluster(config, rng)

    snapshots = [record_snapshot(cluster)]
    fnd_round = None

    for _ in range(config["max_rounds"]):
        if cluster.alive_count() == 0:
            break

        run_single_round(cluster, config, rng)
        snapshots.append(record_snapshot(cluster))

        if fnd_round is None and first_dead_node_exists(cluster):
            fnd_round = cluster.round_index
            if config["stop_on_fnd"]:
                break

    overall_pdr = 1.0
    if cluster.packets_sent > 0:
        overall_pdr = cluster.packets_delivered / cluster.packets_sent

    uplink_pdr = 1.0
    if cluster.uplink_packets_sent > 0:
        uplink_pdr = cluster.uplink_packets_delivered / cluster.uplink_packets_sent

    return SimulationResult(
        scenario_name=config["scenario_name"],
        total_rounds=cluster.round_index,
        fnd_round=fnd_round,
        leader_history=cluster.leader_history,
        leader_switches=cluster.leader_switches,
        election_count=cluster.election_count,
        overall_pdr=overall_pdr,
        uplink_pdr=uplink_pdr,
        total_packets_sent=cluster.packets_sent,
        total_packets_delivered=cluster.packets_delivered,
        total_uplink_packets_sent=cluster.uplink_packets_sent,
        total_uplink_packets_delivered=cluster.uplink_packets_delivered,
        total_retransmissions=cluster.total_retransmissions,
        total_failed_uplinks=cluster.total_failed_uplinks,
        total_dropped_uplinks=cluster.total_dropped_uplinks,
        total_wifi_attempts=cluster.total_wifi_attempts,
        total_election_attempts=cluster.total_election_attempts,
        total_election_retries=cluster.total_election_retries,
        total_failed_election_attempts=cluster.total_failed_election_attempts,
        total_failed_elections=cluster.total_failed_elections,
        rounds_without_leader=cluster.rounds_without_leader,
        total_dual_leader_conflicts=cluster.total_dual_leader_conflicts,
        total_conflict_resolutions=cluster.total_conflict_resolutions,
        total_conflict_overrides=cluster.total_conflict_overrides,
        snapshots=snapshots,
    )

def update_cooldowns(cluster: ClusterState) -> None:
    for node in cluster.alive_nodes():
        if node.cooldown_remaining > 0:
            node.cooldown_remaining -= 1

def wifi_attempt_failed(config: dict, rng: random.Random) -> bool:
    return rng.random() < config["wifi_failure_prob"]

def election_attempt_failed(config: dict, rng: random.Random) -> bool:
    return rng.random() < config["election_failure_prob"]

def dual_leader_conflict_happened(config: dict, rng: random.Random) -> bool:
    return rng.random() < config["dual_leader_conflict_prob"]

def select_conflicting_leader_candidate(
    cluster: ClusterState,
    elected_leader_id: int,
) -> Optional[int]:
    candidates = [
        node for node in cluster.alive_nodes()
        if node.node_id != elected_leader_id
    ]

    if not candidates:
        return None

    # escolhe o mais forte entre os outros vivos
    chosen = max(
        candidates,
        key=lambda n: (n.remaining_charge, -n.node_id),
    )
    return chosen.node_id

def resolve_dual_leader_conflict(
    cluster: ClusterState,
    elected_leader_id: int,
    conflicting_leader_id: int,
    config: dict,
) -> int:
    elected = cluster.get_node(elected_leader_id)
    conflicting = cluster.get_node(conflicting_leader_id)

    # custo extra de controle para resolver o conflito
    extra_cost = config["control_cost"] * config["conflict_resolution_control_cost_multiplier"]
    for node in cluster.alive_nodes():
        node.consume(extra_cost)

    cluster.total_conflict_resolutions += 1

    # se algum morrer pelo custo extra, o outro vence se continuar vivo
    if elected.alive and not conflicting.alive:
        return elected.node_id

    if conflicting.alive and not elected.alive:
        return conflicting.node_id

    if not elected.alive and not conflicting.alive:
        # nenhum dos dois sobreviveu; tenta manter o eleito original como referência,
        # mas a validação de alive será feita depois
        return elected.node_id

    # regra determinística
    if conflicting.remaining_charge > elected.remaining_charge:
        cluster.total_conflict_overrides += 1
        return conflicting.node_id

    if conflicting.remaining_charge < elected.remaining_charge:
        return elected.node_id

    # empate: menor ID vence
    if conflicting.node_id < elected.node_id:
        cluster.total_conflict_overrides += 1
        return conflicting.node_id

    return elected.node_id