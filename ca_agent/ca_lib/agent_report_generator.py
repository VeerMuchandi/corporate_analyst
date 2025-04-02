# Copyright 2025 Google, LLC
# 
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
# 
#     https://www.apache.org/licenses/LICENSE-2.0
# 
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from google.adk.agents import LlmAgent

REPORT_TEMPLATE = """
## Company Snapshot
*   Corporate Headquarters
*   Primary Geography of Operations
*   Year Founded
*   Public or Private
*   Stock Ticker
*   Stock Exchange
*   Company Mission/Vision
*   Latest Fiscal Year Revenue
*   Number of Employees
*   Company Type
*   Recent Acquisitions Mentioned

### Executive Summary
<Insert executive summary here>

### Company Overview
#### Company History

<Insert Company History>

#### Business Model

<Insert Company Business Model>

### SWOT Analysis
    
#### Strengths & Weaknesses    
| **Strengths** | **Weaknesses** |
| --------- | ---------- |


#### Opportunities & Threats 
| **Opportunities** | **Threats** |
| ------------- | ------- |


### Top Company Challenges
<Insert Company Challenges here>

### Strategic Initiatives
<Insert Strategic Initiatives here>

### Top Revenue Streams / Segments
<Insert revenue streams and segments here>

### Top Products and Services

<Insert top products and services here>

### Financial Performance Highlights

<Insert financial performance highlights here>

### Top Competitors

<Insert a list of top competitors here>

### Key Executives

<Insert a list of key executives here>

### Employee Count by Department
<In table format list the department name and employee count per department>
| Department Name | Employee Count |
|-----------------|----------------|

### Company Locations

<List all company locations using the table below>
| Company Locations |
|-------------------|

### Strategy and Health Analysis

<Format the Strategy and Health Analysis as a Markdown table>
| Strategy Name | Health |
|---------------|--------|

### ZoomInfo Confidence Level

<Insert Zoom Info confidence level>
"""

REPORT_GENERATOR_PROMPT = f"""
Using the constraints and steps below you will create a markdown report for the corporate analyst using the markdown template below.

[Goals]
To consolidate all extracted and synthesized information and generate a single, cohesive report.

[Constraints]
- You must receive all the extracted information from the Corporate Analyst agent.
- You must compile the information into a single, cohesive report.
- You must structure the report using Markdown syntax.
- You must include the logo URL (if available).
- You must include the 10-K report link.
- You must add a concluding disclaimer.
- You must deliver the final output as a visually rendered, well-formatted rich-text report.

Execution Flow:

- Receive all the extracted information that is sec_10k_extractor_output, zoominfo_enricher_output, domain_verifier_output, logo_finder_output from the Corporate Analyst agent.
- Consolidate Information:
    - Compile all extracted and synthesized information into a single report.
    - Indicate the whether the data is coming from Sec 10K report or ZoomInfo in the corresponding sections.
    - Include the following sections in the final report:  
- Verify completeness 
    -  Verify again that all the information is filled in the report. 
    -  If any data is missing from the sources, clearly mention that it is not available. 
    -  Do not miss out any sections in the report.
- Format Report:
    -Structure the report using Markdown syntax.
    -Use tables for SWOT Analysis, Employees by Department, Company Locations, and Strategy and Health Analysis.
    -Display the logo on the top of the report.
    -Include the 10-K report link.
    -Add a concluding disclaimer.
- Render Final Report in markdown format:
    - Print the final output as a visually rendered, well-formatted rich-text report.
    
[Markdown Template]
Render the Company Logo from the `logo_finder_output` using the following Markdown syntax: `!Company Logo`

{REPORT_TEMPLATE}
""".strip()

report_generator = LlmAgent(
    model="gemini-2.0-flash",
    name="report_generator_agent",
    description="Generates the final report.",
    instruction=REPORT_GENERATOR_PROMPT,
    output_key = "report_generator_output",
)