from backend.agents.graph import create_research_graph

def main():
    print("Initializing 7-Agent Multi-Agent Research System...")
    
    app = create_research_graph()
    
    topic = "Latest advancements in Quantum Computing 2026"
    print(f"\n🚀 Starting research on topic: '{topic}'\n")
    
    initial_state = {
        "task": topic,
        "plan": {},
        "research_data": [],
        "analysis": {},
        "verified_claims": {},
        "summary": "",
        "final_report": "",
        "quality_feedback": "",
        "retry_count": 0
    }
    
    final_state = app.invoke(initial_state)
    
    print("\n" + "="*50)
    print("🎯 FINAL RESEARCH REPORT:")
    print("="*50)
    print(final_state.get("final_report", "No report generated."))
    print("="*50)

if __name__ == "__main__":
    main()