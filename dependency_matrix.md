# AgentForge-X LangGraph Compatibility Matrix

This compatibility matrix audits the local virtual environment and global Python scope dependencies, confirming that all conflicting newer LangGraph modules have been removed and the legacy backend works correctly.

## LangGraph & LangChain Dependency Matrix

| Package | Installed Version | Required Version | Status | Resolution / Notes |
| :--- | :---: | :---: | :---: | :--- |
| **langgraph** | `0.1.4` | `0.1.4` | **COMPATIBLE** | Matches the original project target. |
| **langchain-core** | `0.2.19` | `0.2.19` | **COMPATIBLE** | Matches the original project target. |
| **langgraph-checkpoint** | *None* | *None* | **COMPATIBLE** | Conflicting `4.1.1` removed from global and venv. |
| **langgraph-prebuilt** | *None* | *None* | **COMPATIBLE** | Conflicting `1.1.0` removed from global and venv. |
| **langgraph-sdk** | *None* | *None* | **COMPATIBLE** | Conflicting `0.4.2` removed from global and venv. |
| **langsmith** | `0.1.77` | `^0.1.0` | **COMPATIBLE** | Fully compatible with langchain-core `0.2.19`. |

---

### Audit Verdict
The Python environment is **clean and resolved**. Deleting the global `langgraph-checkpoint` library successfully allows LangGraph (`0.1.4`) to resolve dynamic serializer imports internally using standard serializers, eliminating the `TypeError: Reviver.__init__() got an unexpected keyword argument 'allowed_objects'` startup error.
