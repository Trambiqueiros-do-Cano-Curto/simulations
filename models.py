from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class Node:
    node_id: int
    initial_charge: float
    remaining_charge: float
    alive: bool = True
    times_as_leader: int = 0
    cooldown_remaining: int = 0
    signal_quality: str = "medium"
    failed_tx_count: int = 0
    retry_count: int = 0
    leadership_history: List[int] = field(default_factory=list)

    def consume(self, amount: float) -> None:
        if amount < 0:
            raise ValueError("O consumo de energia não pode ser negativo.")
        self.remaining_charge = max(0.0, self.remaining_charge - amount)
        self.alive = self.remaining_charge > 0.0

    @property
    def charge_ratio(self) -> float:
        if self.initial_charge <= 0:
            return 0.0
        return self.remaining_charge / self.initial_charge


@dataclass
class RoundSnapshot:
    round_index: int
    leader_id: Optional[int]
    charges: Dict[int, float]
    alive_count: int


@dataclass
class ClusterState:
    nodes: List[Node]
    current_leader_id: Optional[int] = None
    round_index: int = 0
    leader_history: List[int] = field(default_factory=list)
    leader_switches: int = 0
    election_count: int = 0

    # Métricas globais de entrega
    packets_sent: int = 0
    packets_delivered: int = 0

    # Métricas específicas de uplink Wi-Fi
    uplink_packets_sent: int = 0
    uplink_packets_delivered: int = 0

    leader_charge_at_election: Optional[float] = None

    # Métricas de Wi-Fi
    total_retransmissions: int = 0
    total_failed_uplinks: int = 0
    total_dropped_uplinks: int = 0
    total_wifi_attempts: int = 0

    # Métricas de eleição
    total_election_attempts: int = 0
    total_election_retries: int = 0
    total_failed_election_attempts: int = 0
    total_failed_elections: int = 0
    rounds_without_leader: int = 0

    # Métricas de conflito de liderança
    total_dual_leader_conflicts: int = 0
    total_conflict_resolutions: int = 0
    total_conflict_overrides: int = 0

    def get_node(self, node_id: int) -> Node:
        for node in self.nodes:
            if node.node_id == node_id:
                return node
        raise ValueError(f"Nó {node_id} não encontrado.")

    def alive_nodes(self) -> List[Node]:
        return [node for node in self.nodes if node.alive]

    def alive_count(self) -> int:
        return len(self.alive_nodes())

    def get_current_leader(self) -> Optional[Node]:
        if self.current_leader_id is None:
            return None
        leader = self.get_node(self.current_leader_id)
        return leader if leader.alive else None


@dataclass
class SimulationResult:
    scenario_name: str
    total_rounds: int
    fnd_round: Optional[int]
    leader_history: List[int]
    leader_switches: int
    election_count: int

    overall_pdr: float
    uplink_pdr: float

    total_packets_sent: int
    total_packets_delivered: int
    total_uplink_packets_sent: int
    total_uplink_packets_delivered: int

    total_retransmissions: int
    total_failed_uplinks: int
    total_dropped_uplinks: int
    total_wifi_attempts: int

    total_election_attempts: int
    total_election_retries: int
    total_failed_election_attempts: int
    total_failed_elections: int
    rounds_without_leader: int

    total_dual_leader_conflicts: int
    total_conflict_resolutions: int
    total_conflict_overrides: int

    snapshots: List[RoundSnapshot]