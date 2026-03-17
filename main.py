from scenarios import build_all_scenarios, build_block_a_leadership_policies
from runner import build_summary, run_all_scenarios, save_results

def main() -> None:
    scenarios = build_all_scenarios()
    n_runs = 20

    raw_df = run_all_scenarios(scenarios, n_runs=n_runs)
    summary_df = build_summary(raw_df)

    save_results(raw_df, summary_df, output_dir="outputs")
    print(summary_df)

if __name__ == "__main__":
    main()