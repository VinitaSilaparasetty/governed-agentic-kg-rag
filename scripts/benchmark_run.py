"""
Benchmark runner: runs all 5 evaluation queries with real Ollama/Mistral LLM
synthesis and mock KG/RAG data (no live Neo4j required).
Prints JSON-serialisable results for updating the paper.

Usage: python scripts/benchmark_run.py
"""
import sys, os, json
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault("LLM_PROVIDER", "ollama")
os.environ.setdefault("LLM_MODEL", "mistral:latest")
os.environ.setdefault("AUDIT_LOG_PATH", "/tmp/benchmark_audit.jsonl")

from src.agents.schemas import (
    AgentState, PlannerOutput, SubTask,
    KGAgentOutput, KGResult, RAGAgentOutput, RAGChunk,
)
from src.agents.synthesis_agent import run_synthesis_agent

QUERIES = [
    {
        "id": 1,
        "query": "Why is Pump-14 vibrating?",
        "equipment": "Pump-14",
        "kg_rows": [
            KGResult(equipment="Pump-14", component="Bearing-P14-DE", fault="Bearing Wear",
                     symptoms=["excessive vibration","high temperature","noise"],
                     severity="HIGH", procedure="Bearing Replacement",
                     steps=["Issue LOTO permit","Remove coupling guard","Extract bearing with puller",
                            "Inspect shaft journal","Press new bearing","Reassemble and grease","Align and test"],
                     estimated_time="4h", skill_level="Technician"),
            KGResult(equipment="Pump-14", component="Coupling-P14", fault="Misalignment",
                     symptoms=["vibration","coupling heat","axial thrust"],
                     severity="MEDIUM", procedure="Laser Alignment",
                     steps=["Attach alignment targets","Rotate shaft","Record offset/angularity",
                            "Adjust shims","Repeat until within 0.05mm"],
                     estimated_time="3h", skill_level="Technician"),
        ],
        "rag_chunks": [
            RAGChunk(content="TITLE: Centrifugal Pump Bearing Wear\nBearing wear in centrifugal pumps is typically caused by insufficient lubrication, contaminated lubricant, overloading, or misalignment. Symptoms include elevated vibration at 1x and 2x RPM, increased bearing temperature, and audible noise. Early detection using vibration analysis (FFT spectrum) showing raised 1x component is critical to prevent catastrophic failure.", source_file="bearing_wear.txt", score=0.82),
            RAGChunk(content="TITLE: General Vibration Diagnostics\nVibration in rotating machinery can arise from imbalance (1x RPM), misalignment (1x and 2x RPM), bearing defects (sub-synchronous or high-frequency), or resonance. Diagnosis requires a calibrated accelerometer and FFT analyser. Always cross-reference with operating temperature and acoustic emission data.", source_file="vibration_diagnostics_general.txt", score=0.71),
            RAGChunk(content="TITLE: Misalignment in Pump-Motor Couplings\nAngular and parallel misalignment in pump-motor couplings produces vibration at 2x RPM and generates heat at the coupling faces. Laser alignment tools achieve tolerances of 0.02mm offset and 0.02mm/100mm angularity. Re-check alignment after thermal expansion at operating temperature.", source_file="misalignment.txt", score=0.59),
        ],
    },
    {
        "id": 2,
        "query": "Motor-03 is overheating and smells of burning",
        "equipment": "Motor-03",
        "kg_rows": [
            KGResult(equipment="Motor-03", component="Stator-M03", fault="Stator Winding Fault",
                     symptoms=["current imbalance","overheating","burning smell"],
                     severity="CRITICAL", procedure="Stator Rewinding",
                     steps=["Full motor disassembly","Burn out old winding","Rewind with correct gauge",
                            "Varnish and cure","Reassemble","HV insulation test"],
                     estimated_time="24h", skill_level="Specialist"),
        ],
        "rag_chunks": [
            RAGChunk(content="TITLE: Electric Motor Stator Winding Failure\nStator winding faults are the most common cause of electric motor failure, accounting for approximately 30-40% of motor breakdowns. Causes include insulation degradation from thermal cycling, moisture ingress, voltage spikes, and mechanical vibration. A burning smell indicates immediate risk of complete winding failure and possible fire. Insulation resistance should be tested with a megger (500V DC); values below 1 MΩ indicate immediate replacement.", source_file="stator_winding.txt", score=0.89),
            RAGChunk(content="TITLE: Motor Thermal Protection and Overheating\nOverheating in electric motors reduces insulation life by half for every 10°C above rated temperature (Arrhenius rule). Overheating causes include overloading, blocked ventilation, high ambient temperature, and winding faults. Thermal imaging cameras can identify hot-spots before failure. Check current draw on all three phases; imbalance above 2% indicates a winding problem.", source_file="motor_overheating.txt", score=0.77),
        ],
    },
    {
        "id": 3,
        "query": "Valve-09 is responding slowly to control signals",
        "equipment": "Valve-09",
        "kg_rows": [
            KGResult(equipment="Valve-09", component="Actuator-V09", fault="Actuator Sticking",
                     symptoms=["slow valve response","control deviation","oscillation"],
                     severity="MEDIUM", procedure="Actuator Service",
                     steps=["Isolate air supply","Remove actuator","Disassemble",
                            "Inspect diaphragm and spring","Lubricate or replace parts",
                            "Reassemble and bench-test"],
                     estimated_time="3h", skill_level="Technician"),
        ],
        "rag_chunks": [
            RAGChunk(content="TITLE: Pneumatic Actuator Maintenance\nPneumatic actuator sticking is caused by diaphragm hardening, corroded stem, inadequate lubrication, or contaminated instrument air. Bench-test the actuator at 3, 9, and 15 PSI (for a 3-15 PSI instrument) to verify stroke and hysteresis. Hysteresis above 2% of span indicates diaphragm or packing wear.", source_file="actuator_maintenance.txt", score=0.74),
            RAGChunk(content="TITLE: Control Valve Troubleshooting\nSlow valve response can also indicate a positioner fault, instrument air pressure loss (<40 PSI), or a blocked signal line. Before removing the actuator, verify the positioner input signal and supply pressure. A valve responding at 30% of rated speed with correct signal confirms an actuator mechanical problem.", source_file="control_valve.txt", score=0.61),
        ],
    },
    {
        "id": 4,
        "query": "Comp-07 shows reduced discharge pressure and blow-by",
        "equipment": "Comp-07",
        "kg_rows": [
            KGResult(equipment="Comp-07", component="Piston-C07", fault="Piston Ring Wear",
                     symptoms=["reduced pressure","blow-by","oil consumption"],
                     severity="MEDIUM", procedure="Piston Ring Replacement",
                     steps=["Depressurise compressor","Remove cylinder head","Extract piston",
                            "Replace rings","Check bore wear","Reassemble","Run-in test"],
                     estimated_time="6h", skill_level="Technician"),
        ],
        "rag_chunks": [
            RAGChunk(content="TITLE: Reciprocating Compressor Piston Ring Wear\nPiston ring wear in reciprocating compressors reduces compression efficiency and allows blow-by (combustion gas passing the rings into the crankcase). Indicators include reduced discharge pressure, increased oil consumption, and elevated crankcase pressure. Measure ring end gap and side clearance; replace if end gap exceeds 0.5mm above new specification.", source_file="piston_ring_wear.txt", score=0.78),
            RAGChunk(content="TITLE: Compressor Cylinder Bore Inspection\nWhen replacing piston rings, always measure cylinder bore with a bore gauge at three heights and two orientations. Taper above 0.05mm or ovality above 0.03mm requires boring or honing before new rings are fitted. Fitting new rings to a worn bore will not restore compression and rings will wear rapidly.", source_file="compressor_maintenance.txt", score=0.62),
        ],
    },
    {
        "id": 5,
        "query": "Unit-99 is making a strange noise",
        "equipment": None,
        "kg_rows": [],  # Deliberate: no KG match — tests graceful degradation
        "rag_chunks": [
            RAGChunk(content="TITLE: General Vibration Diagnostics\nVibration in rotating machinery can arise from imbalance, misalignment, bearing defects, or resonance. Diagnosis requires a calibrated accelerometer and FFT analyser.", source_file="vibration_diagnostics_general.txt", score=0.31),
            RAGChunk(content="TITLE: Centrifugal Pump Bearing Wear\nBearing wear causes vibration at 1x and 2x RPM and elevated temperature.", source_file="bearing_wear.txt", score=0.28),
        ],
    },
]


def run_benchmark():
    results = []
    print("\n" + "═"*70)
    print("  BENCHMARK: 5 queries with live Ollama/Mistral synthesis")
    print("═"*70)

    for q in QUERIES:
        print(f"\n[Query {q['id']}] {q['query']}")
        print("  Calling Mistral... ", end="", flush=True)

        plan = PlannerOutput(
            original_query=q["query"],
            sub_tasks=[SubTask(
                target="both",
                question=q["query"],
                equipment_name=q["equipment"],
                fault_hint=None,
            )],
        )
        kg_output = KGAgentOutput(sub_task_question=q["query"], results=q["kg_rows"])
        rag_output = RAGAgentOutput(sub_task_question=q["query"], chunks=q["rag_chunks"])

        state = AgentState(
            user_query=q["query"],
            plan=plan,
            kg_output=kg_output,
            rag_output=rag_output,
        )

        result_state = run_synthesis_agent(state)
        s = result_state.synthesis

        print("done")
        print(f"  Confidence : {s.confidence:.0%}")
        print(f"  DIAGNOSIS  : {s.diagnosis}")
        print(f"  ACTION     : {s.recommended_action}")
        print(f"  Reasoning  : {s.reasoning[:120]}...")

        results.append({
            "id": q["id"],
            "query": q["query"],
            "diagnosis": s.diagnosis,
            "recommended_action": s.recommended_action,
            "confidence": s.confidence,
            "evidence_sources": s.evidence_sources,
            "reasoning": s.reasoning,
            "kg_rows": len(q["kg_rows"]),
            "rag_chunks": len(q["rag_chunks"]),
        })

    print("\n" + "═"*70)
    print("  JSON OUTPUT (for PAPER.md)")
    print("═"*70)
    print(json.dumps(results, indent=2))
    return results


if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()
    run_benchmark()
