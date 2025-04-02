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

root_agent = Agent(
    model="gemini-2.0-flash",
    name="corporate_analyst_agent",
    description="Analyzes a corporation given its ticker",
    instruction="Help the user generate a report using the agents at your disposal.",
    sub_agents=[
        sequencer_agent,
    ],
)


