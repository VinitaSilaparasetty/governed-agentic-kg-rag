"""
Human-in-the-loop CLI checkpoint.

No recommendation is returned to the caller without passing through this gate.
The operator may approve, reject, or edit the candidate before it is finalised.
This implements the human oversight requirement described in EU AI Act Article 50(3)
for high-risk agentic AI systems operating in safety-relevant domains.
"""
from .audit_log import log_human_decision
from ..agents.schemas import AgentState, FinalOutput, SynthesisOutput


def _display_candidate(synthesis: SynthesisOutput, query: str) -> None:
    print("\n" + "═" * 60)
    print("  CANDIDATE RECOMMENDATION — PENDING HUMAN APPROVAL")
    print("═" * 60)
    print(f"  Query       : {query}")
    print(f"  Confidence  : {synthesis.confidence:.0%}")
    print(f"  Sources     : {', '.join(synthesis.evidence_sources)}")
    print()
    print(f"  DIAGNOSIS:")
    print(f"  {synthesis.diagnosis}")
    print()
    print(f"  RECOMMENDED ACTION:")
    print(f"  {synthesis.recommended_action}")
    print()
    print(f"  REASONING:")
    print(f"  {synthesis.reasoning}")
    print("═" * 60)


def run_human_checkpoint(state: AgentState) -> AgentState:
    synthesis = state.synthesis
    if not synthesis:
        return state.model_copy(update={"error": "Checkpoint: no synthesis output"})

    _display_candidate(synthesis, state.user_query)

    while True:
        choice = input("\n  [A]pprove  [R]eject  [E]dit  > ").strip().lower()

        if choice == "r":
            log_human_decision("rejected", synthesis.recommended_action, None)
            print("\n  Recommendation rejected. No output will be returned.")
            return state.model_copy(update={
                "final": FinalOutput(
                    user_query=state.user_query,
                    diagnosis=synthesis.diagnosis,
                    recommended_action=synthesis.recommended_action,
                    confidence=synthesis.confidence,
                    evidence_sources=synthesis.evidence_sources,
                    reasoning=synthesis.reasoning,
                    human_approved=False,
                )
            })

        if choice == "a":
            log_human_decision("approved", synthesis.recommended_action, None)
            return state.model_copy(update={
                "final": FinalOutput(
                    user_query=state.user_query,
                    diagnosis=synthesis.diagnosis,
                    recommended_action=synthesis.recommended_action,
                    confidence=synthesis.confidence,
                    evidence_sources=synthesis.evidence_sources,
                    reasoning=synthesis.reasoning,
                    human_approved=True,
                )
            })

        if choice == "e":
            print("  Enter your edited recommendation (blank line to finish):")
            lines: list[str] = []
            while True:
                line = input("  > ")
                if line == "":
                    break
                lines.append(line)
            edited = "\n".join(lines)
            log_human_decision("edited", synthesis.recommended_action, edited)
            return state.model_copy(update={
                "final": FinalOutput(
                    user_query=state.user_query,
                    diagnosis=synthesis.diagnosis,
                    recommended_action=edited,
                    confidence=synthesis.confidence,
                    evidence_sources=synthesis.evidence_sources,
                    reasoning=synthesis.reasoning,
                    human_approved=True,
                    human_edit=edited,
                )
            })

        print("  Please enter A, R, or E.")
