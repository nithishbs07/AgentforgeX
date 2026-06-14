import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from research.ablation_study import AblationStudy

def test_ablation_study_simulator():
    # Run with limit=2 (very fast)
    study = AblationStudy(use_simulator=True, limit=2)
    
    assert len(study.queries) == 2
    
    results = study.run_ablation()
    
    assert "Full AgentForge-X" in results
    assert "Without Verifier Agent" in results
    
    # Check that keys are computed
    metrics = results["Full AgentForge-X"]
    assert "faithfulness" in metrics
    assert "verification_score" in metrics
    assert "grounding_score" in metrics
    assert "answer_relevancy" in metrics
    assert "latency_ms" in metrics
    
    # Verify report output exists
    report_path = os.path.join(study.results_dir, "ablation_report.md")
    assert os.path.exists(report_path)
