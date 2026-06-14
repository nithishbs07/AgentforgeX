import os
import re

def test_dashboard_file_structure():
    # Verify dashboard page exists
    dashboard_page_path = os.path.abspath(os.path.join(
        os.path.dirname(__file__), "..", "..", "frontend", "app", "dashboard", "page.tsx"
    ))
    assert os.path.exists(dashboard_page_path), "Dashboard page.tsx must exist"

    # Verify components/Charts.tsx exists
    charts_path = os.path.abspath(os.path.join(
        os.path.dirname(__file__), "..", "..", "frontend", "app", "components", "Charts.tsx"
    ))
    assert os.path.exists(charts_path), "Charts.tsx must exist"

def test_dashboard_components_and_sections():
    dashboard_page_path = os.path.abspath(os.path.join(
        os.path.dirname(__file__), "..", "..", "frontend", "app", "dashboard", "page.tsx"
    ))
    
    with open(dashboard_page_path, "r", encoding="utf-8") as f:
        content = f.read()

    # 1. Verify all backend API requests are made
    assert "/analytics/overview" in content, "Dashboard must fetch overview analytics"
    assert "/analytics/verification" in content, "Dashboard must fetch verification analytics"
    assert "/analytics/routing" in content, "Dashboard must fetch routing analytics"
    assert "/analytics/retrieval" in content, "Dashboard must fetch retrieval analytics"
    assert "/analytics/latency" in content, "Dashboard must fetch latency analytics"
    assert "/analytics/history" in content, "Dashboard must fetch query history"

    # 2. Verify tabs/sections exist
    assert "overview" in content.lower(), "Dashboard must have an Overview section"
    assert "verification" in content.lower(), "Dashboard must have a Verification section"
    assert "routing" in content.lower(), "Dashboard must have a Routing section"
    assert "retrieval" in content.lower(), "Dashboard must have a Retrieval section"
    assert "latency" in content.lower(), "Dashboard must have a Latency section"
    assert "history" in content.lower(), "Dashboard must have a Query History section"

    # 3. Verify Overview Cards exist
    assert "total queries" in content.lower(), "Overview must show Total Queries"
    assert "supported" in content.lower(), "Overview must show Supported %"
    assert "partially supported" in content.lower(), "Overview must show Partially Supported %"
    assert "unsupported" in content.lower(), "Overview must show Unsupported %"
    assert "adaptive retrieval trigger" in content.lower(), "Overview must show Adaptive Retrieval Trigger Rate"

    # 4. Verify table headers exist in Query History
    assert "query" in content.lower(), "Table must have 'Query' header"
    assert "route" in content.lower(), "Table must have 'Route' header"
    assert "verification score" in content.lower(), "Table must have 'Verification Score' header"
    assert "grounding score" in content.lower(), "Table must have 'Grounding Score' header"
    assert "adaptive retrieval" in content.lower(), "Table must have 'Adaptive Retrieval' header"
    assert "timestamp" in content.lower(), "Table must have 'Timestamp' header"

def test_charts_exports():
    charts_path = os.path.abspath(os.path.join(
        os.path.dirname(__file__), "..", "..", "frontend", "app", "components", "Charts.tsx"
    ))
    
    with open(charts_path, "r", encoding="utf-8") as f:
        content = f.read()

    # Verify LineChart, BarChart, PieChart are exported
    assert "export const LineChart" in content, "Charts.tsx must export LineChart"
    assert "export const BarChart" in content, "Charts.tsx must export BarChart"
    assert "export const PieChart" in content, "Charts.tsx must export PieChart"
