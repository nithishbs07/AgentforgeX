import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import pytest
from research.experiment_runner import ExperimentRunner

def test_experiment_runner_simulator():
    # Run with limit=2 (very fast)
    runner = ExperimentRunner(use_simulator=True, limit=2)
    
    # Assert initialized properties
    assert len(runner.queries) == 2
    assert os.path.exists(runner.dataset_path)
    
    # Run experiments
    results = runner.run_experiments()
    
    # Assert strategy outputs exist
    assert "Vector RAG" in results
    assert "Deep Research RAG" in results
    assert len(results["Vector RAG"]) == 2
    
    # Verify outputs written to results directory
    json_path = os.path.join(runner.results_dir, "benchmark_results.json")
    csv_path = os.path.join(runner.results_dir, "benchmark_results.csv")
    md_path = os.path.join(runner.results_dir, "benchmark_summary.md")
    
    assert os.path.exists(json_path)
    assert os.path.exists(csv_path)
    assert os.path.exists(md_path)
