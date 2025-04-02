"""Orchestrates the corporate analysis process using specialized agents."""

from google.adk.agents import SequentialAgent, Agent

from .ca_lib import (
    domain_verifier,
    logo_finder,
    report_generator,
    sec_10k_report_downloader,
    sec_10k_retriever,
    sec_10k_extractor,
    ticker_finder,
    zoom_info_enricher,
)

sequencer_agent = SequentialAgent(
    name="sequencer_agent",
    description="The agent call orchestrator",
    sub_agents=[
        ticker_finder,
        sec_10k_retriever,
        sec_10k_report_downloader,
        sec_10k_extractor,
        domain_verifier,
        logo_finder,
        zoom_info_enricher,
        report_generator,
    ],
)

ROOT_AGENT_PROMPT = """
Help the user generate a corporate analysis report for the 
company the user is searching for using the agents at your disposal.
Prompt the user to supply the information needed by the sub agents.
""".strip()

root_agent = Agent(
    model="gemini-2.0-flash",
    name="corporate_analyst_agent",
    description="Analyzes a corporation given its ticker",
    instruction=ROOT_AGENT_PROMPT,
    sub_agents=[
        sequencer_agent,
    ],
)
