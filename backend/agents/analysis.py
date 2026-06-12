"""
Analysis Agent — LLM-powered result analysis.

Takes raw tool outputs and produces intelligent analysis:
- Correlates findings across tools
- Removes duplicates
- Explains what each finding means
- Prioritizes assets by importance
- Recommends next investigation steps
- Uses RAG to enrich findings with CVE/CWE context
"""

import json
from langchain_core.prompts import ChatPromptTemplate

from backend.config import settings
from backend.utils.llm import get_llm, clean_json_response
from backend.schemas import ToolResult, AnalysisResult, AnalyzedFinding


# ============================================================
# System prompt for the Analysis Agent
# ============================================================

ANALYSIS_SYSTEM_PROMPT = """You are a cybersecurity analysis expert. You analyze reconnaissance results and provide actionable insights.

You will receive:
1. The target that was scanned
2. Raw results from various recon tools
3. Relevant security context from our knowledge base (CVEs, CWEs, OWASP)

Your job is to:
1. **Correlate** findings across different tools
2. **Deduplicate** — merge results from multiple tools
3. **Explain** what each finding means in plain language
4. **Identify** the most important assets and why they matter
5. **Prioritize** findings by severity (critical > high > medium > low > info)
6. **Recommend** specific next investigation steps

RULES:
- Be specific. Don't say "port 443 is open." Say "HTTPS service detected. Technology fingerprinting shows WordPress 6.x. This host should receive WordPress-specific security testing."
- Always explain WHY a finding matters
- Group related findings together
- Reference CVEs when relevant
- Be concise but thorough

Respond with ONLY valid JSON:
{{
    "summary": "Brief overview of all findings",
    "total_assets_found": 42,
    "unique_subdomains": ["sub1.target.com", "sub2.target.com"],
    "live_hosts": ["https://sub1.target.com", "https://sub2.target.com"],
    "technologies": ["WordPress", "Apache", "PHP"],
    "findings": [
        {{
            "title": "Finding title",
            "severity": "high",
            "description": "Detailed explanation of what was found and why it matters",
            "affected_assets": ["sub1.target.com"],
            "recommendations": ["Specific action to take"],
            "related_cves": ["CVE-2024-XXXX"]
        }}
    ],
    "next_steps": ["Specific next investigation step"]
}}"""


# ============================================================
# Analysis Agent
# ============================================================

class AnalysisAgent:
    """
    Analyzes raw recon results using an LLM.
    Enriches findings with RAG context when available.
    """

    def __init__(self):
        self.llm = get_llm(force_json=True)

        self.prompt = ChatPromptTemplate.from_messages([
            ("system", ANALYSIS_SYSTEM_PROMPT),
            ("human", (
                "Target: {target}\n\n"
                "Tool Results:\n{tool_results}\n\n"
                "Security Context (from knowledge base):\n{rag_context}"
            )),
        ])

        self.chain = self.prompt | self.llm

    async def analyze(self, target: str, results: list[ToolResult],
                      rag_context: str = "") -> AnalysisResult:
        """
        Analyze recon results and produce structured findings.
        
        Args:
            target: The scanned target
            results: List of ToolResult from the execution engine
            rag_context: Optional RAG-retrieved security context
            
        Returns:
            AnalysisResult with correlated, prioritized findings
        """
        # Format tool results for the LLM
        formatted_results = self._format_results(results)

        # Ask the LLM to analyze
        response = await self.chain.ainvoke({
            "target": target,
            "tool_results": formatted_results,
            "rag_context": rag_context or "No additional context available.",
        })

        # Parse LLM response
        try:
            data = clean_json_response(response.content)
            return self._parse_analysis(data)
        except Exception:
            # Fallback: create a basic analysis from raw results
            return self._basic_analysis(target, results)

    def _format_results(self, results: list[ToolResult]) -> str:
        """Format tool results into a readable string for the LLM."""
        sections = []
        for r in results:
            section = f"[{r.tool}] Category: {r.category}\n"
            if r.error:
                section += f"  Error: {r.error}\n"
            elif r.results:
                section += f"  Found {len(r.results)} results:\n"
                # Limit to first 50 results to avoid context overflow
                for item in r.results[:50]:
                    section += f"  - {item}\n"
                if len(r.results) > 50:
                    section += f"  ... and {len(r.results) - 50} more\n"
            else:
                section += "  No results found\n"
            sections.append(section)

        return "\n".join(sections)

    def _parse_analysis(self, data: dict) -> AnalysisResult:
        """Parse LLM JSON output into an AnalysisResult."""
        findings = []
        for f in data.get("findings", []):
            findings.append(AnalyzedFinding(
                title=f.get("title", "Unknown Finding"),
                severity=f.get("severity", "info"),
                description=f.get("description", ""),
                affected_assets=f.get("affected_assets", []),
                recommendations=f.get("recommendations", []),
                related_cves=f.get("related_cves", []),
            ))

        return AnalysisResult(
            summary=data.get("summary", "Analysis complete."),
            total_assets_found=data.get("total_assets_found", 0),
            unique_subdomains=data.get("unique_subdomains", []),
            live_hosts=data.get("live_hosts", []),
            technologies=data.get("technologies", []),
            findings=findings,
            next_steps=data.get("next_steps", []),
        )

    def _basic_analysis(self, target: str,
                        results: list[ToolResult]) -> AnalysisResult:
        """Fallback analysis when LLM fails — just aggregate raw data."""
        all_subdomains = set()
        all_urls = set()
        all_findings = []

        for r in results:
            if r.category == "subdomain":
                all_subdomains.update(r.results)
            elif r.category == "live_host":
                all_urls.update(r.results)
            elif r.category == "vulnerability" and r.results:
                all_findings.append(AnalyzedFinding(
                    title=f"Vulnerability found by {r.tool}",
                    severity="medium",
                    description=f"Raw findings: {', '.join(r.results[:5])}",
                    affected_assets=[target],
                ))

        return AnalysisResult(
            summary=f"Found {len(all_subdomains)} subdomains and {len(all_urls)} live hosts for {target}.",
            total_assets_found=len(all_subdomains) + len(all_urls),
            unique_subdomains=list(all_subdomains),
            live_hosts=list(all_urls),
            findings=all_findings,
        )
