"""
Report Agent — LLM-powered report generation.

Takes the planner decisions, execution results, and analysis
to produce a professional security report with:
- Executive Summary (for management)
- Technical Summary (for engineers)
- Detailed findings
- Recommendations
"""

import json
from langchain_core.prompts import ChatPromptTemplate

from backend.config import settings
from backend.utils.llm import get_llm, clean_json_response
from backend.schemas import (
    ReconPlan, ToolResult, AnalysisResult, ReconReport, AnalyzedFinding
)


# ============================================================
# Report generation prompt
# ============================================================

REPORT_SYSTEM_PROMPT = """You are a cybersecurity report writer. Generate professional security reconnaissance reports.

You will receive:
1. The reconnaissance plan (what was planned)
2. Execution summary (what tools ran and their results)
3. Analysis (correlated findings and insights)

Generate a professional report with TWO sections:

1. **Executive Summary** — Non-technical overview for management.
   - What was assessed
   - Key risks found
   - Overall risk level
   - Top 3 recommendations

2. **Technical Summary** — Detailed technical findings for engineers.
   - Methodology used
   - Tools executed
   - Detailed findings with evidence
   - Technology stack identified
   - Vulnerability details
   - Comprehensive recommendations

Also generate a FULL MARKDOWN report.

Respond with ONLY valid JSON:
{{
    "executive_summary": "Non-technical summary for management...",
    "technical_summary": "Detailed technical findings...",
    "target": "example.com",
    "assets_discovered": ["sub1.example.com", "sub2.example.com"],
    "interesting_hosts": ["admin.example.com — hosts admin panel"],
    "technologies": ["Apache 2.4", "WordPress 6.x"],
    "vulnerabilities": [
        {{
            "title": "Vulnerability name",
            "severity": "high",
            "description": "What and why",
            "affected_assets": ["host1"],
            "recommendations": ["Fix step"],
            "related_cves": ["CVE-XXXX-XXXX"]
        }}
    ],
    "recommendations": [
        "Prioritized recommendation"
    ],
    "full_markdown": "# Full Report\\n\\n## Executive Summary\\n..."
}}"""


# ============================================================
# Report Agent
# ============================================================

class ReportAgent:
    """
    Generates professional security reports from recon data.
    Produces both executive and technical summaries.
    """

    def __init__(self):
        self.llm = get_llm(temperature=0.2, force_json=True)

        self.prompt = ChatPromptTemplate.from_messages([
            ("system", REPORT_SYSTEM_PROMPT),
            ("human", (
                "Target: {target}\n\n"
                "Reconnaissance Plan:\n{plan}\n\n"
                "Execution Summary:\n{execution_summary}\n\n"
                "Analysis:\n{analysis}"
            )),
        ])

        self.chain = self.prompt | self.llm

    async def generate(self, target: str, plan: ReconPlan,
                       results: list[ToolResult],
                       analysis: AnalysisResult) -> ReconReport:
        """
        Generate a full security report.
        
        Args:
            target: Scanned target
            plan: The original recon plan
            results: Raw tool results
            analysis: Analyzed findings
            
        Returns:
            ReconReport with executive and technical summaries
        """
        # Format inputs for the LLM
        plan_text = self._format_plan(plan)
        exec_text = self._format_execution(results)
        analysis_text = self._format_analysis(analysis)

        # Generate report
        response = await self.chain.ainvoke({
            "target": target,
            "plan": plan_text,
            "execution_summary": exec_text,
            "analysis": analysis_text,
        })

        # Parse response
        try:
            data = clean_json_response(response.content)
            return self._parse_report(data, target, analysis)
        except Exception:
            return self._fallback_report(target, analysis)

    def _format_plan(self, plan: ReconPlan) -> str:
        """Format the plan for the LLM."""
        lines = [f"Objective: {plan.objective}", f"Reasoning: {plan.reasoning}", ""]
        for stage in plan.plan:
            lines.append(f"Stage: {stage.stage.value}")
            lines.append(f"  Tools: {', '.join(stage.tools)}")
            lines.append(f"  Purpose: {stage.description}")
        return "\n".join(lines)

    def _format_execution(self, results: list[ToolResult]) -> str:
        """Format execution results for the LLM."""
        lines = []
        for r in results:
            status = "FAILED" if r.error else f"OK ({len(r.results)} results)"
            lines.append(f"[{r.tool}] {r.category}: {status} ({r.execution_time}s)")
            if r.results:
                for item in r.results[:20]:
                    lines.append(f"  - {item}")
                if len(r.results) > 20:
                    lines.append(f"  ... +{len(r.results) - 20} more")
        return "\n".join(lines)

    def _format_analysis(self, analysis: AnalysisResult) -> str:
        """Format analysis for the LLM."""
        lines = [
            f"Summary: {analysis.summary}",
            f"Total assets: {analysis.total_assets_found}",
            f"Subdomains: {len(analysis.unique_subdomains)}",
            f"Live hosts: {len(analysis.live_hosts)}",
            f"Technologies: {', '.join(analysis.technologies)}",
            "",
            "Findings:",
        ]
        for f in analysis.findings:
            lines.append(f"  [{f.severity.upper()}] {f.title}")
            lines.append(f"    {f.description}")
        lines.append(f"\nNext steps: {', '.join(analysis.next_steps)}")
        return "\n".join(lines)

    def _parse_report(self, data: dict, target: str,
                      analysis: AnalysisResult) -> ReconReport:
        """Parse LLM output into a ReconReport."""
        vulns = []
        for v in data.get("vulnerabilities", []):
            vulns.append(AnalyzedFinding(
                title=v.get("title", ""),
                severity=v.get("severity", "info"),
                description=v.get("description", ""),
                affected_assets=v.get("affected_assets", []),
                recommendations=v.get("recommendations", []),
                related_cves=v.get("related_cves", []),
            ))

        return ReconReport(
            executive_summary=data.get("executive_summary", ""),
            technical_summary=data.get("technical_summary", ""),
            target=target,
            assets_discovered=data.get("assets_discovered", analysis.unique_subdomains),
            interesting_hosts=data.get("interesting_hosts", analysis.live_hosts),
            technologies=data.get("technologies", analysis.technologies),
            vulnerabilities=vulns or analysis.findings,
            recommendations=data.get("recommendations", analysis.next_steps),
            full_markdown=data.get("full_markdown", ""),
        )

    def _fallback_report(self, target: str,
                         analysis: AnalysisResult) -> ReconReport:
        """Generate a basic report when LLM fails."""
        markdown = f"""# Reconnaissance Report — {target}

## Executive Summary

A security reconnaissance assessment was performed against {target}.
{analysis.summary}

## Assets Discovered

- Subdomains found: {len(analysis.unique_subdomains)}
- Live hosts: {len(analysis.live_hosts)}

## Technologies

{chr(10).join(f"- {t}" for t in analysis.technologies) or "- None detected"}

## Findings

{chr(10).join(f"### [{f.severity.upper()}] {f.title}{chr(10)}{f.description}" for f in analysis.findings) or "No significant findings."}

## Recommendations

{chr(10).join(f"- {s}" for s in analysis.next_steps) or "- Continue monitoring"}
"""
        return ReconReport(
            executive_summary=analysis.summary,
            technical_summary=analysis.summary,
            target=target,
            assets_discovered=analysis.unique_subdomains,
            interesting_hosts=analysis.live_hosts,
            technologies=analysis.technologies,
            vulnerabilities=analysis.findings,
            recommendations=analysis.next_steps,
            full_markdown=markdown,
        )
