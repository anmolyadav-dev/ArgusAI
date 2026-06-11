"""
Planner Agent — LLM-powered reconnaissance planner.

This agent takes a user's objective and decides:
- Which reconnaissance stages are needed
- Which tools to run in each stage
- The execution order

It NEVER executes commands. It only makes decisions.
"""

import json
from langchain_core.prompts import ChatPromptTemplate

from backend.config import settings
from backend.utils.llm import get_llm, clean_json_response
from backend.schemas import ReconPlan, PlannedStage, ReconStage
from backend.tools import get_available_tools


# ============================================================
# System prompt that teaches the LLM about reconnaissance
# ============================================================

PLANNER_SYSTEM_PROMPT = """You are a reconnaissance planning expert. Your job is to create a structured plan for security reconnaissance.

You will receive:
1. A target domain or IP
2. The user's objective
3. A list of available tools

Your job is to decide:
- Which reconnaissance stages are needed
- Which tools to use in each stage
- The correct execution order

AVAILABLE STAGES:
- subdomain_enumeration: Find subdomains (tools: subfinder, assetfinder, sublist3r)
- dns_enumeration: DNS records lookup (tools: dnsx)
- live_hosts: Find which hosts are alive (tools: httpx)
- web_crawling: Crawl websites for URLs (tools: katana, gospider)
- directory_enumeration: Find hidden directories (tools: ffuf)
- technology_detection: Identify technologies (tools: httpx with tech mode)
- vulnerability_scan: Scan for known vulnerabilities (tools: nuclei)
- historical_urls: Find old URLs from archives (tools: waybackurls)
- js_analysis: Analyze JavaScript files (tools: katana)
- cloud_enumeration: Find cloud resources (tools: cloud_enum)

RULES:
1. Always start with subdomain_enumeration for domain targets
2. Always do live_hosts after subdomain_enumeration
3. Technology detection should come before vulnerability scanning
4. Vulnerability scanning should be the last stage
5. Only include stages that match the user's objective
6. Only use tools from the available tools list
7. For a "complete" assessment, include most stages
8. For targeted requests, only include relevant stages

Respond with ONLY valid JSON in this exact format:
{{
    "target": "example.com",
    "objective": "user's objective here",
    "reasoning": "brief explanation of why you chose these stages",
    "plan": [
        {{
            "stage": "stage_name",
            "tools": ["tool1", "tool2"],
            "description": "why this stage is needed"
        }}
    ]
}}

Do not include any text before or after the JSON."""


# ============================================================
# Planner Agent
# ============================================================

class PlannerAgent:
    """
    Creates reconnaissance plans using an LLM.
    
    The planner understands the available tools and stages,
    and produces a structured JSON plan based on the user's objective.
    """

    def __init__(self):
        self.llm = get_llm(force_json=True)

        self.prompt = ChatPromptTemplate.from_messages([
            ("system", PLANNER_SYSTEM_PROMPT),
            ("human", "Target: {target}\nObjective: {objective}\nAvailable tools: {available_tools}"),
        ])

        self.chain = self.prompt | self.llm

    async def plan(self, target: str, objective: str) -> ReconPlan:
        """
        Generate a reconnaissance plan.
        
        Args:
            target: Domain or IP to scan
            objective: What the user wants to achieve
            
        Returns:
            ReconPlan with ordered stages and tools
        """
        available = get_available_tools()

        # Ask the LLM to create a plan
        response = await self.chain.ainvoke({
            "target": target,
            "objective": objective,
            "available_tools": ", ".join(available),
        })

        # Parse the LLM's JSON response
        try:
            plan_data = clean_json_response(response.content)
        except Exception:
            # If the LLM doesn't return valid JSON, use a default plan
            return self._default_plan(target, objective, available)

        # Validate and convert to Pydantic model
        try:
            stages = []
            for stage_data in plan_data.get("plan", []):
                stage_name = stage_data.get("stage", "")
                # Validate stage name
                try:
                    stage_enum = ReconStage(stage_name)
                except ValueError:
                    continue  # Skip invalid stages

                # Filter to only available tools
                tools = [
                    t for t in stage_data.get("tools", [])
                    if t in available
                ]

                if tools:  # Only add stages with available tools
                    stages.append(PlannedStage(
                        stage=stage_enum,
                        tools=tools,
                        description=stage_data.get("description", ""),
                    ))

            if not stages:
                return self._default_plan(target, objective, available)

            return ReconPlan(
                target=target,
                objective=objective,
                plan=stages,
                reasoning=plan_data.get("reasoning", ""),
            )

        except Exception:
            return self._default_plan(target, objective, available)

    def _default_plan(self, target: str, objective: str,
                      available: list[str]) -> ReconPlan:
        """
        Fallback plan if the LLM fails to produce valid output.
        A sensible default that covers the basics.
        """
        stages = []

        # Subdomain enumeration
        sub_tools = [t for t in ["subfinder", "assetfinder"] if t in available]
        if sub_tools:
            stages.append(PlannedStage(
                stage=ReconStage.SUBDOMAIN_ENUMERATION,
                tools=sub_tools,
                description="Discover subdomains",
            ))

        # Live hosts
        if "httpx" in available:
            stages.append(PlannedStage(
                stage=ReconStage.LIVE_HOSTS,
                tools=["httpx"],
                description="Find live hosts",
            ))

        # Technology detection
        if "httpx" in available:
            stages.append(PlannedStage(
                stage=ReconStage.TECHNOLOGY_DETECTION,
                tools=["httpx"],
                description="Detect technologies",
            ))

        # Vulnerability scan
        if "nuclei" in available:
            stages.append(PlannedStage(
                stage=ReconStage.VULNERABILITY_SCAN,
                tools=["nuclei"],
                description="Scan for vulnerabilities",
            ))

        return ReconPlan(
            target=target,
            objective=objective,
            plan=stages,
            reasoning="Default plan — LLM output was not valid",
        )
