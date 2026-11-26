"""Generate a structured interpretation of a completed spatial analysis."""
import json
from typing import Any, Dict

import requests
from pydantic import BaseModel, Field

from app.core.config import settings


class Narrative(BaseModel):
    text: str = Field(min_length=1)
    highlights: list[str]
    method: str


def generate_insight(analysis_result: dict, context: dict | None = None) -> dict:
    response = requests.post(
        "https://api.navigator.ai.ufl.edu/v1/chat/completions",
        headers={"Authorization": f"Bearer {settings.navigator_toolkit_api_key}"},
        json={
            "model": settings.navigator_model,
            "messages": [{"role": "user", "content": _build_prompt(analysis_result, context)}],
            "response_format": {"type": "json_object"},
            "max_tokens": settings.ai_max_output_tokens,
        },
        timeout=(5, 45),
        allow_redirects=False,
    )
    response.raise_for_status()
    output = response.json()["choices"][0]["message"]["content"]
    return Narrative.model_validate_json(output).model_dump()


def _build_prompt(analysis_result: Dict[str, Any], context: Dict[str, Any] | None = None) -> str:
	"""Build the prompt for NaviGator."""
	
	summary = analysis_result.get("summary", {})
	clustering = analysis_result.get("clustering", {})
	
	# Extract key metrics
	total_points = summary.get("total_points", 0)
	category_counts = summary.get("category_counts", {})
	bbox = summary.get("bbox")
	mean_center = summary.get("mean_center")
	num_clusters = clustering.get("num_clusters", 0)
	num_noise = clustering.get("num_noise", 0)
	clusters = clustering.get("clusters", [])
	
	prompt_parts = [
		"You are a geospatial data analyst. Analyze the following geospatial analysis results and provide insights.",
		"",
		"CRITICAL RULES:",
		"1. DO NOT invent or make up any data. Only reference fields that are present in the analysis_result.",
		"2. Use hedging language: 'suggests', 'may indicate', 'appears to', 'likely', 'possibly'.",
		"3. Include numeric proportions when available (percentages, counts).",
		"4. If data is missing, explicitly state that limitation.",
		"",
		"ANALYSIS DATA:",
		f"- Total points: {total_points}",
	]
	
	if category_counts:
		# Sort by count and show top categories
		sorted_cats = sorted(category_counts.items(), key=lambda x: x[1] if isinstance(x[1], (int, float)) else 0, reverse=True)
		prompt_parts.append("- Category distribution:")
		for cat, count in sorted_cats[:10]:  # Top 10
			pct = (count / total_points * 100) if total_points > 0 else 0
			prompt_parts.append(f"  * {cat}: {count} ({pct:.1f}%)")
	else:
		prompt_parts.append("- Category counts: Not available")
	
	if bbox:
		prompt_parts.append(f"- Bounding box: {json.dumps(bbox)}")
	
	if mean_center:
		prompt_parts.append(f"- Mean center: {json.dumps(mean_center)}")
	
	prompt_parts.append(f"- Clustering: {num_clusters} clusters, {num_noise} noise points")
	
	if clusters:
		largest = max(clusters, key=lambda c: c.get("size", 0), default=None)
		if largest:
			prompt_parts.append(f"- Largest cluster: size {largest.get('size', 0)} at {json.dumps(largest.get('centroid', {}))}")
	
	if context:
		if context.get("city_name"):
			prompt_parts.append(f"- Context: City: {context['city_name']}")
		if context.get("viewport_bbox"):
			prompt_parts.append(f"- Viewport: {json.dumps(context['viewport_bbox'])}")
	
	prompt_parts.extend([
		"",
		"OUTPUT FORMAT: Return ONLY a valid JSON object (no markdown, no code blocks, no explanations). The JSON must have exactly these fields:",
		"{",
		'  "text": "A concise scientific-style narrative paragraph (3-5 sentences) summarizing the spatial patterns, distribution characteristics, and notable findings. Use hedging language and reference specific numbers from the data.",',
		'  "highlights": ["Bullet point 1 with key finding and %", "Bullet point 2", "Bullet point 3"],',
		'  "method": "Brief note on methodology/assumptions (e.g., DBSCAN clustering, category field used, spatial extent)"',
		"}",
		"",
		"IMPORTANT: Return ONLY the JSON object, nothing else. No markdown code blocks, no explanations, just the raw JSON.",
		"",
		"Generate the insight now:",
	])
	
	return "\n".join(prompt_parts)

