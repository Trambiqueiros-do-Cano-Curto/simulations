from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd


BASE_DIR = Path(__file__).resolve().parent
SUMMARY_CSV_PATH = BASE_DIR / "outputs" / "summary_results.csv"
OUTPUT_DIR = BASE_DIR / "outputs" / "plots"


# Ajustes globais de fonte para os gráficos ficarem mais apresentáveis
plt.rcParams.update(
    {
        "figure.titlesize": 20,
        "axes.titlesize": 20,
        "axes.labelsize": 16,
        "xtick.labelsize": 13,
        "ytick.labelsize": 13,
        "legend.fontsize": 12,
    }
)


BLOCK_A_ORDER = [
    "A_round_robin_time_driven",
    "A_energy_time_driven",
    "A_energy_cooldown_time_driven",
]
BLOCK_A_LABELS = {
    "A_round_robin_time_driven": "Round-Robin",
    "A_energy_time_driven": "Energia",
    "A_energy_cooldown_time_driven": "Energia + Cooldown",
}

BLOCK_B_ORDER = [
    "B_energy_cooldown_time_driven",
    "B_energy_cooldown_event_driven",
]
BLOCK_B_LABELS = {
    "B_energy_cooldown_time_driven": "Time-Driven",
    "B_energy_cooldown_event_driven": "Event-Driven",
}

BLOCK_C_ORDER = [
    "C_wifi_no_failure",
    "C_wifi_failure_no_retry",
    "C_wifi_failure_with_retry",
]
BLOCK_C_LABELS = {
    "C_wifi_no_failure": "Sem falha",
    "C_wifi_failure_no_retry": "Falha sem retry",
    "C_wifi_failure_with_retry": "Falha com retry",
}

BLOCK_D_ORDER = [
    "D_election_no_failure",
    "D_election_failure_no_retry",
    "D_election_failure_with_retry",
]
BLOCK_D_LABELS = {
    "D_election_no_failure": "Sem falha",
    "D_election_failure_no_retry": "Falha sem retry",
    "D_election_failure_with_retry": "Falha com retry",
}

BLOCK_E_ORDER = [
    "E_conflict_none",
    "E_conflict_moderate",
    "E_conflict_aggressive",
]
BLOCK_E_LABELS = {
    "E_conflict_none": "Sem conflito",
    "E_conflict_moderate": "Conflito moderado",
    "E_conflict_aggressive": "Conflito agressivo",
}


def ensure_output_dir() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def load_summary(path=SUMMARY_CSV_PATH) -> pd.DataFrame:
    return pd.read_csv(path)


def prepare_block(
    df: pd.DataFrame,
    prefix: str,
    order: list[str] | None = None,
    labels: dict[str, str] | None = None,
) -> pd.DataFrame:
    block_df = df[df["scenario_name"].str.startswith(prefix)].copy()

    if order is not None:
        block_df["scenario_name"] = pd.Categorical(
            block_df["scenario_name"],
            categories=order,
            ordered=True,
        )
        block_df = block_df.sort_values("scenario_name")

    block_df["display_label"] = block_df["scenario_name"].astype(str)
    if labels is not None:
        block_df["display_label"] = block_df["display_label"].map(labels)

    return block_df


def save_bar_chart(
    df: pd.DataFrame,
    value_col: str,
    std_col: str | None,
    title: str,
    ylabel: str,
    filename: str,
    ylim: tuple[float, float] | None = None,
) -> None:
    plt.figure(figsize=(11, 6.5))

    labels = df["display_label"].tolist()
    values = df[value_col].tolist()

    if std_col and std_col in df.columns:
        errors = df[std_col].fillna(0).tolist()
        plt.bar(labels, values, yerr=errors, capsize=6)
    else:
        plt.bar(labels, values)

    plt.title(title, pad=10)
    plt.xlabel("")
    plt.ylabel(ylabel)
    plt.xticks(rotation=0)

    if ylim is not None:
        plt.ylim(*ylim)

    plt.tight_layout()
    plt.savefig(OUTPUT_DIR / filename, dpi=300, bbox_inches="tight")
    plt.close()


def save_line_chart_with_error(
    df: pd.DataFrame,
    x_col: str,
    y_col: str,
    std_col: str | None,
    title: str,
    ylabel: str,
    filename: str,
    ylim: tuple[float, float] | None = None,
) -> None:
    plot_df = df.sort_values(by=x_col).copy()

    x = plot_df[x_col].tolist()
    y = plot_df[y_col].tolist()

    plt.figure(figsize=(10, 6.5))

    if std_col and std_col in plot_df.columns:
        yerr = plot_df[std_col].fillna(0).tolist()
        plt.errorbar(x, y, yerr=yerr, marker="o", capsize=6)
    else:
        plt.plot(x, y, marker="o")

    plt.title(title, pad=10)
    plt.xlabel("Tamanho do cluster")
    plt.ylabel(ylabel)

    if ylim is not None:
        plt.ylim(*ylim)

    plt.tight_layout()
    plt.savefig(OUTPUT_DIR / filename, dpi=300, bbox_inches="tight")
    plt.close()


# =========================
# Bloco A
# =========================
def plot_block_a_fnd(df: pd.DataFrame) -> None:
    a = prepare_block(df, "A_", BLOCK_A_ORDER, BLOCK_A_LABELS)
    save_bar_chart(
        df=a,
        value_col="fnd_round_mean",
        std_col="fnd_round_std",
        title="Bloco A - FND por política de liderança",
        ylabel="FND médio (rodadas)",
        filename="block_a_fnd.png",
    )


def plot_block_a_fairness(df: pd.DataFrame) -> None:
    a = prepare_block(df, "A_", BLOCK_A_ORDER, BLOCK_A_LABELS)
    save_bar_chart(
        df=a,
        value_col="leader_fairness_std_mean",
        std_col="leader_fairness_std_std",
        title="Bloco A - Desvio padrão da liderança",
        ylabel="Desvio padrão da liderança",
        filename="block_a_fairness.png",
    )


# =========================
# Bloco B
# =========================
def plot_block_b_switches(df: pd.DataFrame) -> None:
    b = prepare_block(df, "B_", BLOCK_B_ORDER, BLOCK_B_LABELS)
    save_bar_chart(
        df=b,
        value_col="leader_switches_mean",
        std_col="leader_switches_std",
        title="Bloco B - Trocas de líder",
        ylabel="Trocas médias de líder",
        filename="block_b_leader_switches.png",
    )


def plot_block_b_fnd(df: pd.DataFrame) -> None:
    b = prepare_block(df, "B_", BLOCK_B_ORDER, BLOCK_B_LABELS)
    save_bar_chart(
        df=b,
        value_col="fnd_round_mean",
        std_col="fnd_round_std",
        title="Bloco B - FND: Time-Driven vs Event-Driven",
        ylabel="FND médio (rodadas)",
        filename="block_b_fnd.png",
    )


# =========================
# Bloco C
# =========================
def plot_block_c_overall_pdr(df: pd.DataFrame) -> None:
    c = prepare_block(df, "C_", BLOCK_C_ORDER, BLOCK_C_LABELS)
    save_bar_chart(
        df=c,
        value_col="overall_pdr_mean",
        std_col="overall_pdr_std",
        title="Bloco C - PDR geral",
        ylabel="PDR geral médio",
        filename="block_c_overall_pdr.png",
        ylim=(0.90, 1.01),
    )


def plot_block_c_uplink_pdr(df: pd.DataFrame) -> None:
    c = prepare_block(df, "C_", BLOCK_C_ORDER, BLOCK_C_LABELS)
    save_bar_chart(
        df=c,
        value_col="uplink_pdr_mean",
        std_col="uplink_pdr_std",
        title="Bloco C - PDR do uplink Wi-Fi",
        ylabel="PDR uplink médio",
        filename="block_c_uplink_pdr.png",
        ylim=(0.60, 1.01),
    )


def plot_block_c_fnd(df: pd.DataFrame) -> None:
    c = prepare_block(df, "C_", BLOCK_C_ORDER, BLOCK_C_LABELS)
    save_bar_chart(
        df=c,
        value_col="fnd_round_mean",
        std_col="fnd_round_std",
        title="Bloco C - FND nos cenários de robustez do Wi-Fi",
        ylabel="FND médio (rodadas)",
        filename="block_c_fnd.png",
    )


# =========================
# Bloco D
# =========================
def plot_block_d_failed_elections(df: pd.DataFrame) -> None:
    d = prepare_block(df, "D_", BLOCK_D_ORDER, BLOCK_D_LABELS)
    save_bar_chart(
        df=d,
        value_col="total_failed_elections_mean",
        std_col="total_failed_elections_std",
        title="Bloco D - Falhas completas de eleição",
        ylabel="Falhas completas médias",
        filename="block_d_failed_elections.png",
    )


def plot_block_d_election_retries(df: pd.DataFrame) -> None:
    d = prepare_block(df, "D_", BLOCK_D_ORDER, BLOCK_D_LABELS)
    save_bar_chart(
        df=d,
        value_col="total_election_retries_mean",
        std_col="total_election_retries_std",
        title="Bloco D - Retries de eleição",
        ylabel="Retries médios de eleição",
        filename="block_d_election_retries.png",
    )


# =========================
# Bloco E
# =========================
def plot_block_e_conflicts(df: pd.DataFrame) -> None:
    e = prepare_block(df, "E_", BLOCK_E_ORDER, BLOCK_E_LABELS)
    save_bar_chart(
        df=e,
        value_col="total_dual_leader_conflicts_mean",
        std_col="total_dual_leader_conflicts_std",
        title="Bloco E - Conflitos dual-leader",
        ylabel="Conflitos médios",
        filename="block_e_conflicts.png",
    )


def plot_block_e_overrides(df: pd.DataFrame) -> None:
    e = prepare_block(df, "E_", BLOCK_E_ORDER, BLOCK_E_LABELS)
    save_bar_chart(
        df=e,
        value_col="total_conflict_overrides_mean",
        std_col="total_conflict_overrides_std",
        title="Bloco E - Overrides por conflito",
        ylabel="Overrides médios",
        filename="block_e_overrides.png",
    )


# =========================
# Bloco F
# =========================
def plot_block_f_fnd(df: pd.DataFrame) -> None:
    f = df[df["scenario_name"].str.startswith("F_")].copy()
    save_line_chart_with_error(
        df=f,
        x_col="cluster_size",
        y_col="fnd_round_mean",
        std_col="fnd_round_std",
        title="Bloco F - FND por tamanho do cluster",
        ylabel="FND médio (rodadas)",
        filename="block_f_fnd.png",
    )


def plot_block_f_switches(df: pd.DataFrame) -> None:
    f = df[df["scenario_name"].str.startswith("F_")].copy()
    save_line_chart_with_error(
        df=f,
        x_col="cluster_size",
        y_col="leader_switches_mean",
        std_col="leader_switches_std",
        title="Bloco F - Trocas de líder por tamanho do cluster",
        ylabel="Trocas médias de líder",
        filename="block_f_leader_switches.png",
    )


def generate_all_plots(summary_csv_path=SUMMARY_CSV_PATH) -> None:
    ensure_output_dir()
    df = load_summary(summary_csv_path)

    plot_block_a_fnd(df)
    plot_block_a_fairness(df)

    plot_block_b_switches(df)
    plot_block_b_fnd(df)

    plot_block_c_overall_pdr(df)
    plot_block_c_uplink_pdr(df)
    plot_block_c_fnd(df)

    plot_block_d_failed_elections(df)
    plot_block_d_election_retries(df)

    plot_block_e_conflicts(df)
    plot_block_e_overrides(df)

    plot_block_f_fnd(df)
    plot_block_f_switches(df)

    print(f"Gráficos salvos em: {OUTPUT_DIR.resolve()}")


if __name__ == "__main__":
    generate_all_plots()