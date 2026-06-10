"""
RAG Retriever — Searches the knowledge base for relevant security context.

Given a list of queries (tool results, technologies, etc.),
retrieves the most relevant CVE, CWE, and OWASP information
to enrich the Analysis Agent's output.
"""

import requests
from backend.rag.embeddings import get_collection, build_knowledge_base


class RAGRetriever:
    """
    Simple retriever that searches the local ChromaDB knowledge base.
    
    Usage:
        retriever = RAGRetriever()
        context = await retriever.retrieve(["Apache 2.4", "WordPress"])
    """

    def __init__(self):
        # Ensure knowledge base is populated
        self.collection = build_knowledge_base()

    async def retrieve(self, queries: list[str], top_k: int = 5) -> str:
        """
        Search the knowledge base for relevant security information.
        
        Args:
            queries: List of search terms (technologies, vuln names, etc.)
            top_k: Number of results to return per query
            
        Returns:
            Formatted string with relevant security context
        """
        if not queries:
            return ""

        all_results = []
        seen_ids = set()

        for query in queries[:10]:  # Limit to 10 queries
            if not query or len(query) < 3:
                continue

            try:
                results = self.collection.query(
                    query_texts=[query],
                    n_results=min(top_k, 3),  # Top 3 per query
                )

                # Extract unique results
                if results and results["documents"]:
                    for i, doc in enumerate(results["documents"][0]):
                        doc_id = results["ids"][0][i] if results["ids"] else str(i)
                        if doc_id not in seen_ids:
                            seen_ids.add(doc_id)
                            metadata = results["metadatas"][0][i] if results["metadatas"] else {}
                            all_results.append({
                                "id": doc_id,
                                "type": metadata.get("type", "unknown"),
                                "content": doc,
                            })
            except Exception:
                continue  # Skip failed queries

        # Format results into a readable context string
        if not all_results:
            return "No relevant security context found in knowledge base."

        context_parts = ["Relevant security information from knowledge base:\n"]

        for r in all_results[:15]:  # Limit total context
            context_parts.append(
                f"[{r['type'].upper()}] {r['id']}: {r['content']}\n"
            )

        # Try to fetch live CVE data for a couple of top queries
        live_cves = []
        for query in queries[:2]:  # Only do live search for top 2 to save time/rate limits
            cves = self._fetch_live_cves(query)
            if cves:
                live_cves.extend(cves)

        if live_cves:
            context_parts.append("\nLive CVE Information (from NVD):\n")
            # Deduplicate
            seen = set()
            for c in live_cves:
                if c['id'] not in seen:
                    seen.add(c['id'])
                    context_parts.append(f"[CVE] {c['id']}: {c['description']} (Severity: {c['severity']})\n")

        return "\n".join(context_parts)

    def _fetch_live_cves(self, keyword: str, limit: int = 3) -> list[dict]:
        """Fetch live CVE data from NVD by keyword."""
        try:
            url = f"https://services.nvd.nist.gov/rest/json/cves/2.0?keywordSearch={keyword}&resultsPerPage={limit}"
            headers = {"User-Agent": "AI-Recon-Platform/1.0"}
            response = requests.get(url, headers=headers, timeout=5)
            
            if response.status_code != 200:
                return []
                
            data = response.json()
            cves = []
            
            for item in data.get("vulnerabilities", []):
                cve = item.get("cve", {})
                cve_id = cve.get("id")
                descriptions = cve.get("descriptions", [])
                desc = descriptions[0].get("value") if descriptions else "No description"
                
                # Try to get severity
                severity = "UNKNOWN"
                metrics = cve.get("metrics", {})
                if "cvssMetricV31" in metrics:
                    severity = metrics["cvssMetricV31"][0].get("cvssData", {}).get("baseSeverity", "UNKNOWN")
                
                if cve_id:
                    cves.append({
                        "id": cve_id,
                        "description": desc,
                        "severity": severity
                    })
            return cves
        except Exception:
            return []

    async def search_cves(self, query: str, top_k: int = 5) -> list[dict]:
        """Search specifically for CVEs (uses live data)."""
        return self._fetch_live_cves(query, limit=top_k)
