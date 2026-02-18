"""
Claude-powered generators for research and analysis workflows

All generators follow anti-noise output rules:
- Goal (1 sentence)
- Inputs Used (explicit list)
- Follow template sections
- Max 5 key findings
- Max 3 decisions
- Max 5 next actions
"""

import logging
import os
from typing import Dict, Any
from datetime import datetime
import asyncio

from .llm import generate, LLMError
from .file_loader import load_multiple_files, FileLoaderError
from .slush_api import fetch_slush_data_for_memo, SlushAPIError

logger = logging.getLogger(__name__)

def load_system_docs() -> str:
    """Load system documentation for context"""
    try:
        system_docs_path = os.path.join(os.path.dirname(__file__), "..", "system_docs.md")
        with open(system_docs_path, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        logger.warning(f"Failed to load system docs: {str(e)}")
        return "System documentation not available."

def generate_lead_list(params: Dict[str, Any]) -> str:
    """
    DEPRECATED: Lead scraping functionality removed
    Returns deprecation notice for compatibility
    """
    return """# Lead List Generation - DEPRECATED

## Notice
Lead scraping functionality has been deprecated and removed from Agent Ops Backend.

This service now focuses exclusively on research and analysis workflows using Claude AI:
- `prompt_pack`: Development planning and implementation guides
- `weekly_pilot_memo`: Business performance analysis and strategic planning
- `research_brief`: In-depth research analysis and findings

Please use one of the supported job types for your analysis needs.

---
*Service refocused on research workflows as of February 2026*"""

def generate_prompt_pack(params: Dict[str, Any]) -> str:
    """Generate implementation planning document using Claude"""
    
    # Extract required parameters
    feature_name = params.get("feature_name", "Unnamed Feature")
    feature_description = params.get("feature_description", "No description provided")
    notes = params.get("notes", "")
    source_context = params.get("source_context", "")
    
    # Load optional files
    file_refs = {k: v for k, v in params.items() if k.endswith("_key") and v}
    loaded_files = load_multiple_files(file_refs)
    
    # Build system prompt
    system_prompt = """You are a senior technical architect creating implementation planning documents. 

When source_context is provided, focus on turning suggestions/experiments from memos or research into concrete prompts for a coding agent.
When no source_context, focus on feature implementation planning.

Your output must follow this exact structure:

# Prompt Pack - [Feature Name]

## Goal
[Single sentence describing implementation objective]

## Inputs Used
[List each input source explicitly]

## Context Summary
[Brief description of what needs to be built/modified and why]

### Current State
- [What exists now]
- [Relevant background/constraints]

### Desired End State  
- [What the final result should look like]
- [Success criteria]

## Files Likely Involved
[List specific file paths and their roles]

## Step-by-step Implementation Plan

### Phase 1: [Phase Name]
1. [Specific step]
2. [Specific step]

### Phase 2: [Phase Name]  
1. [Specific step]
2. [Specific step]

[Continue with additional phases]

## Edge Cases
[List and explain how to handle edge cases]

## Test Plan
### Unit Tests
[List specific test requirements]

### Integration Tests  
[List integration test requirements]

## Acceptance Criteria
[List specific functional requirements as checkboxes]

## IMPORTANT NOTE
**DO NOT WRITE CODE** - This is a planning document only.

CRITICAL: Follow anti-noise rules:
- Max 5 key implementation phases
- Max 3 major edge cases  
- Max 5 acceptance criteria
- Be specific and actionable"""
    
    # Build user prompt - prioritize source_context
    inputs_list = [f"Feature: {feature_name}"]
    
    if source_context:
        inputs_list.append("Source context from memo/research")
        user_prompt = f"Turn the following memo/research suggestions into concrete prompts for: {feature_name}\n\n"
        user_prompt += f"## Source Context (Memo/Research Output):\n{source_context}\n\n"
        user_prompt += f"Feature Description: {feature_description}\n"
        if notes:
            inputs_list.append(f"Additional notes: {notes}")
            user_prompt += f"\nAdditional Context: {notes}\n"
    else:
        inputs_list.append(f"Description: {feature_description}")
        if notes:
            inputs_list.append(f"Additional notes: {notes}")
        user_prompt = f"Create an implementation plan for: {feature_name}\n\nDescription: {feature_description}\n"
        if notes:
            user_prompt += f"\nAdditional Context: {notes}\n"
    
    # Add file contents if available
    if loaded_files:
        user_prompt += "\n## Available Context Files:\n"
        for file_ref, content in loaded_files.items():
            inputs_list.append(f"File: {file_ref}")
            file_type = file_ref.replace("_key", "")
            user_prompt += f"\n### {file_type.title()}:\n{content[:2000]}{'...' if len(content) > 2000 else ''}\n"
    
    try:
        result = generate(system_prompt, user_prompt)
        
        # Ensure proper inputs section
        if "## Inputs Used" in result:
            inputs_section = "\n".join([f"- {inp}" for inp in inputs_list])
            result = result.replace("## Inputs Used\n[List each input source explicitly]", 
                                  f"## Inputs Used\n{inputs_section}")
        
        return result
        
    except LLMError as e:
        raise Exception(f"Failed to generate prompt pack: {str(e)}")

async def generate_weekly_pilot_memo(params: Dict[str, Any]) -> str:
    """Generate weekly business analysis memo using Claude with real Slush data"""
    
    # Extract parameters
    pilot_name = params.get("pilot_name", "Slush Operations")
    week_start_date = params.get("week_start_date", datetime.now().strftime("%Y-%m-%d"))
    notes = params.get("notes", "")
    days_back = params.get("range_days", 7)  # Support both "range" and "range_days"
    
    # Handle legacy "range" parameter
    if "range" in params and params["range"] == "last_7_days":
        days_back = 7
    
    # Load optional files
    file_refs = {k: v for k, v in params.items() if k.endswith("_key") and v}
    loaded_files = load_multiple_files(file_refs)
    
    # Load system documentation
    system_docs = load_system_docs()
    
    # Fetch real Slush business data
    try:
        slush_data = await fetch_slush_data_for_memo(days_back)
        logger.info("Successfully fetched Slush data for weekly memo")
    except Exception as e:
        logger.warning(f"Failed to fetch Slush data: {str(e)}")
        slush_data = "=== SLUSH DATA UNAVAILABLE ===\nMemo will be generated without real business data."
    
    # Build system prompt
    system_prompt = """You are a business analyst creating weekly performance and strategy memos.

Your output must follow this exact structure:

# Weekly Pilot Memo - [Pilot Name] - Week of [Date]

## Goal
[Single sentence describing the memo's analytical objective]

## Inputs Used
[List each input source explicitly]

## KPI Snapshot
- [Metric]: [Value] ([Change from last week])
- [Metric]: [Value] ([Change from last week])
- [Metric]: [Value] ([Change from last week])

## What Changed vs Last Week
- [Key change with impact]
- [Key change with impact]
- [Key change with impact]

## Funnel Drop-offs + Hypotheses

### Drop-off Point: [Stage]
- **Data**: [Numbers/rates]
- **Hypothesis**: [Why this is happening]
- **Confidence**: [High/Medium/Low]

## 3 Experiments Next Week

### Experiment 1: [Name]
- **Change**: [Specific action]
- **Why**: [Hypothesis]
- **Expected Impact**: [Predicted outcome]
- **Measurement**: [Success tracking]
- **Stop Condition**: [When to halt]

[Repeat for experiments 2 and 3]

## Risks (Max 3)
1. [Risk and impact]
2. [Risk and impact]  
3. [Risk and impact]

## Action List

### [OWNER]
- [ ] [Specific task]
- [ ] [Specific task]

## Questions (Max 3)
1. [Decision-requiring question]
2. [Decision-requiring question]
3. [Decision-requiring question]

CRITICAL: Follow anti-noise rules:
- Max 5 KPIs
- Max 3 funnel drop-offs
- Exactly 3 experiments
- Max 3 risks
- Max 5 total action items
- Max 3 questions"""
    
    # Build user prompt
    inputs_list = [f"Pilot: {pilot_name}", f"Week of: {week_start_date}", "Real Slush business data", "System documentation"]
    if notes:
        inputs_list.append(f"Context notes: {notes}")
    
    user_prompt = f"Analyze the weekly performance for: {pilot_name}\nWeek starting: {week_start_date}\n"
    
    if notes:
        user_prompt += f"\nAdditional Context: {notes}\n"
    
    # Add system documentation for context
    user_prompt += f"\n## System Documentation:\n{system_docs}\n"
    
    # Add real Slush business data
    user_prompt += f"\n## Real Business Data from Slush API:\n{slush_data}\n"
    
    # Add file contents if available  
    if loaded_files:
        user_prompt += "\n## Additional Data Files:\n"
        for file_ref, content in loaded_files.items():
            inputs_list.append(f"Data file: {file_ref}")
            file_type = file_ref.replace("_key", "")
            user_prompt += f"\n### {file_type.title()}:\n{content[:3000]}{'...' if len(content) > 3000 else ''}\n"
    
    user_prompt += "\nIMPORTANT: Base your analysis on the REAL business data provided above. Use actual metrics, identify real funnel drop-offs, and propose experiments based on the actual data patterns you see."
    
    try:
        result = generate(system_prompt, user_prompt)
        
        # Ensure proper inputs section
        if "## Inputs Used" in result:
            inputs_section = "\n".join([f"- {inp}" for inp in inputs_list])
            result = result.replace("## Inputs Used\n[List each input source explicitly]", 
                                  f"## Inputs Used\n{inputs_section}")
        
        return result
        
    except LLMError as e:
        raise Exception(f"Failed to generate weekly pilot memo: {str(e)}")

def generate_research_brief(params: Dict[str, Any]) -> str:
    """Generate research analysis brief using Claude"""
    
    # Extract required parameters
    topic = params.get("topic", "Research Topic")
    questions = params.get("questions", [])
    context_notes = params.get("context_notes", "")
    
    # Handle questions as string or list
    if isinstance(questions, str):
        questions = [q.strip() for q in questions.split("\n") if q.strip()]
    elif not isinstance(questions, list):
        questions = []
    
    # Load optional files
    file_refs = {k: v for k, v in params.items() if k.endswith("_key") and v}
    loaded_files = load_multiple_files(file_refs)
    
    # Load system documentation
    system_docs = load_system_docs()
    
    # Build system prompt
    system_prompt = """You are a senior research analyst creating comprehensive research briefs.

Your output must follow this exact structure:

# Research Brief - [Topic]

## Goal
[Single sentence describing the research objective]

## Inputs Used
[List each input source explicitly]

## Research Questions
1. [Primary question]
2. [Secondary question]
3. [Additional question if relevant]

## Key Findings (Max 5)

### Finding 1: [Title]
**Evidence**: [Supporting data/observations]
**Implication**: [Business/project impact]

### Finding 2: [Title]
**Evidence**: [Supporting data/observations]
**Implication**: [Business/project impact]

[Continue up to Finding 5]

## Critical Decisions Required (Max 3)

### Decision 1: [Decision point]
**Options**: [2-3 choices]
**Recommendation**: [Preferred option with rationale]
**Timeline**: [Decision deadline]

### Decision 2: [Decision point]
**Options**: [2-3 choices]
**Recommendation**: [Preferred option with rationale]
**Timeline**: [Decision deadline]

## Next Actions (Max 5)

### Immediate (This Week)
- [ ] [Specific task]
- [ ] [Specific task]

### Short Term (Next 2 weeks)
- [ ] [Specific task]

### Medium Term (Next month)
- [ ] [Specific task]

## Knowledge Gaps
- [Missing information]
- [Additional research needed]

## Confidence Assessment
- **High Confidence**: [Strong evidence findings]
- **Medium Confidence**: [Some evidence findings]
- **Low Confidence**: [Hypotheses needing validation]

CRITICAL: Follow anti-noise rules:
- Max 5 key findings
- Max 3 critical decisions
- Max 5 next actions total
- Be specific and evidence-based"""
    
    # Build user prompt
    inputs_list = [f"Topic: {topic}", "System documentation"]
    if context_notes:
        inputs_list.append(f"Context notes: {context_notes}")
    
    user_prompt = f"Research analysis for: {topic}\n\n"
    
    # Add system documentation for context
    user_prompt += f"## System Documentation:\n{system_docs}\n\n"
    
    if questions:
        user_prompt += "Research Questions:\n"
        for i, q in enumerate(questions[:5], 1):  # Max 5 questions
            user_prompt += f"{i}. {q}\n"
        user_prompt += "\n"
    
    if context_notes:
        user_prompt += f"Context: {context_notes}\n\n"
    
    # Add file contents if available
    if loaded_files:
        user_prompt += "## Available Research Materials:\n"
        for file_ref, content in loaded_files.items():
            inputs_list.append(f"Research file: {file_ref}")
            file_type = file_ref.replace("_key", "")
            user_prompt += f"\n### {file_type.title()}:\n{content[:3000]}{'...' if len(content) > 3000 else ''}\n"
    
    try:
        result = generate(system_prompt, user_prompt)
        
        # Ensure proper inputs section
        if "## Inputs Used" in result:
            inputs_section = "\n".join([f"- {inp}" for inp in inputs_list])
            result = result.replace("## Inputs Used\n[List each input source explicitly]", 
                                  f"## Inputs Used\n{inputs_section}")
        
        return result
        
    except LLMError as e:
        raise Exception(f"Failed to generate research brief: {str(e)}")