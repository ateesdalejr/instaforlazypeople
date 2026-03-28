import os
from typing import Dict, Any
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.graph import StateGraph, END
from caption_models import (
    CaptionInput,
    CaptionAgentState,
    CaptionAgentOutput,
    ScriptAnalysis,
    CaptionDraft,
    HookOutput,
    RefinedCaption
)
import json


class CaptionAgent:
    """LangGraph agent for generating Instagram captions from video scripts"""

    def __init__(self, openai_api_key: str = None):
        """Initialize the caption agent with OpenAI"""
        self.api_key = openai_api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OpenAI API key is required")

        self.llm = ChatOpenAI(
            model="gpt-4o-mini",
            temperature=0.7,
            api_key=self.api_key,
            timeout=30,
            max_retries=2
        )

        # Build the graph
        self.graph = self._build_graph()

    def _build_graph(self) -> StateGraph:
        """Build the LangGraph workflow"""
        workflow = StateGraph(CaptionAgentState)

        # Add nodes
        workflow.add_node("analyze_script", self.analyze_script)
        workflow.add_node("generate_caption", self.draft_caption)
        workflow.add_node("create_hook", self.create_hook)
        workflow.add_node("refine_caption", self.refine_caption)

        # Define linear flow
        workflow.set_entry_point("analyze_script")
        workflow.add_edge("analyze_script", "generate_caption")
        workflow.add_edge("generate_caption", "create_hook")
        workflow.add_edge("create_hook", "refine_caption")
        workflow.add_edge("refine_caption", END)

        return workflow.compile()

    def analyze_script(self, state: CaptionAgentState) -> Dict[str, Any]:
        """
        Node 1: Analyze the script to extract key themes, tone, and message
        """
        script = state["script"]

        system_prompt = """You are an expert content analyst specializing in social media.
Analyze the given video script and extract:
1. Key themes (2-4 main topics)
2. Main message (1-2 sentences)
3. Detected tone (e.g., casual, professional, inspiring, humorous)
4. Target keywords for Instagram hashtags (5-10 keywords)
5. Emotional appeal type (e.g., inspirational, educational, entertaining)

Return your analysis in JSON format."""

        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=f"Script to analyze:\n\n{script}")
        ]

        print(f"[analyze_script] Calling LLM...")
        response = self.llm.invoke(messages)
        print(f"[analyze_script] LLM responded")
        content = response.content

        # Parse JSON response
        try:
            # Extract JSON from markdown code blocks if present
            if "```json" in content:
                json_str = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                json_str = content.split("```")[1].split("```")[0].strip()
            else:
                json_str = content

            # Clean up common JSON issues
            json_str = json_str.replace("\\n", " ").replace("\\t", " ")

            analysis_data = json.loads(json_str)

            analysis = ScriptAnalysis(
                key_themes=analysis_data.get("key_themes", []),
                main_message=analysis_data.get("main_message", ""),
                tone_detected=analysis_data.get("detected_tone", "engaging"),
                target_keywords=analysis_data.get("target_keywords", []),
                emotional_appeal=analysis_data.get("emotional_appeal", "engaging")
            )

            return {"script_analysis": analysis}

        except json.JSONDecodeError as e:
            # Fallback if JSON parsing fails
            return {
                "script_analysis": ScriptAnalysis(
                    key_themes=["content creation"],
                    main_message=script[:100],
                    tone_detected="engaging",
                    target_keywords=["instagram", "content"],
                    emotional_appeal="engaging"
                ),
                "processing_errors": state.get("processing_errors", []) + [f"JSON parse error: {str(e)}"]
            }

    def draft_caption(self, state: CaptionAgentState) -> Dict[str, Any]:
        """
        Node 2: Generate initial caption draft based on script analysis
        """
        analysis = state["script_analysis"]
        script = state["script"]

        system_prompt = """You are an expert Instagram caption writer.
Based on the script analysis, write an engaging Instagram caption that:
- Captures the essence of the video
- Uses a conversational, engaging tone
- Is 100-150 characters long (not including hashtags)
- Speaks directly to the audience

Do NOT include hashtags or emojis yet - just the core caption text.
Also suggest 8-12 relevant hashtags based on the content."""

        user_prompt = f"""Script: {script}

Analysis:
- Main Message: {analysis.main_message}
- Key Themes: {', '.join(analysis.key_themes)}
- Tone: {analysis.tone_detected}
- Keywords: {', '.join(analysis.target_keywords)}

Generate a caption body and suggest hashtags. Return in JSON format with keys: caption_body, suggested_hashtags"""

        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_prompt)
        ]

        response = self.llm.invoke(messages)
        content = response.content

        try:
            # Extract JSON
            if "```json" in content:
                json_str = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                json_str = content.split("```")[1].split("```")[0].strip()
            else:
                json_str = content

            caption_data = json.loads(json_str)

            draft = CaptionDraft(
                caption_body=caption_data.get("caption_body", ""),
                suggested_hashtags=caption_data.get("suggested_hashtags", []),
                char_count=len(caption_data.get("caption_body", ""))
            )

            return {"caption_draft": draft}

        except json.JSONDecodeError as e:
            # Fallback
            return {
                "caption_draft": CaptionDraft(
                    caption_body=script[:150],
                    suggested_hashtags=["#content", "#instagram"],
                    char_count=len(script[:150])
                ),
                "processing_errors": state.get("processing_errors", []) + [f"Caption generation JSON error: {str(e)}"]
            }

    def create_hook(self, state: CaptionAgentState) -> Dict[str, Any]:
        """
        Node 3: Create an attention-grabbing hook/first line
        """
        analysis = state["script_analysis"]
        draft = state["caption_draft"]

        system_prompt = """You are an expert at creating scroll-stopping Instagram hooks.
Create a powerful first line (hook) that:
- Grabs attention immediately
- Makes people want to read more
- Is 30-50 characters
- Can be a question, bold statement, or intriguing fact
- Relates to the main message

Return JSON with: hook_line, hook_type (question/statement/statistic/challenge)"""

        user_prompt = f"""Main Message: {analysis.main_message}
Caption Body: {draft.caption_body}
Emotional Appeal: {analysis.emotional_appeal}

Create an engaging hook."""

        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_prompt)
        ]

        response = self.llm.invoke(messages)
        content = response.content

        try:
            if "```json" in content:
                json_str = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                json_str = content.split("```")[1].split("```")[0].strip()
            else:
                json_str = content

            hook_data = json.loads(json_str)

            hook = HookOutput(
                hook_line=hook_data.get("hook_line", ""),
                hook_type=hook_data.get("hook_type", "statement")
            )

            return {"hook_output": hook}

        except json.JSONDecodeError as e:
            return {
                "hook_output": HookOutput(
                    hook_line="Check this out!",
                    hook_type="statement"
                ),
                "processing_errors": state.get("processing_errors", []) + [f"Hook generation JSON error: {str(e)}"]
            }

    def refine_caption(self, state: CaptionAgentState) -> Dict[str, Any]:
        """
        Node 4: Refine and assemble the final caption with all elements
        """
        hook = state["hook_output"]
        draft = state["caption_draft"]
        analysis = state["script_analysis"]

        system_prompt = """You are an expert Instagram caption optimizer.
Create the FINAL Instagram caption by:
1. Starting with the hook line
2. Adding the caption body with strategic line breaks
3. Adding 2-3 emojis throughout (not at the start)
4. Including a clear call-to-action (e.g., "Double tap if you agree!", "Tag someone who needs this!", "Save this for later!")
5. Ending with hashtags (8-12 relevant ones)

Format with proper line breaks for Instagram readability.
Return JSON with: final_caption (complete formatted text), hook, body, cta, hashtags (array), total_length, line_count"""

        user_prompt = f"""Hook: {hook.hook_line}
Caption Body: {draft.caption_body}
Suggested Hashtags: {', '.join(draft.suggested_hashtags)}
Tone: {analysis.tone_detected}

Create the final polished Instagram caption."""

        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_prompt)
        ]

        response = self.llm.invoke(messages)
        content = response.content

        try:
            if "```json" in content:
                json_str = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                json_str = content.split("```")[1].split("```")[0].strip()
            else:
                json_str = content

            refined_data = json.loads(json_str)

            refined = RefinedCaption(
                final_caption=refined_data.get("final_caption", ""),
                hook=refined_data.get("hook", hook.hook_line),
                body=refined_data.get("body", draft.caption_body),
                cta=refined_data.get("cta", ""),
                hashtags=refined_data.get("hashtags", draft.suggested_hashtags),
                total_length=refined_data.get("total_length", len(refined_data.get("final_caption", ""))),
                line_count=refined_data.get("line_count", refined_data.get("final_caption", "").count("\n") + 1)
            )

            return {"refined_caption": refined}

        except json.JSONDecodeError as e:
            # Fallback: assemble manually
            final_caption = f"{hook.hook_line}\n\n{draft.caption_body}\n\n💬 What do you think?\n\n{' '.join(['#' + tag for tag in draft.suggested_hashtags[:10]])}"

            return {
                "refined_caption": RefinedCaption(
                    final_caption=final_caption,
                    hook=hook.hook_line,
                    body=draft.caption_body,
                    cta="What do you think?",
                    hashtags=draft.suggested_hashtags[:10],
                    total_length=len(final_caption),
                    line_count=final_caption.count("\n") + 1
                ),
                "processing_errors": state.get("processing_errors", []) + [f"Refinement JSON error: {str(e)}"]
            }

    async def generate_caption(self, caption_input: CaptionInput) -> CaptionAgentOutput:
        """
        Main entry point to generate a caption
        """
        try:
            initial_state: CaptionAgentState = {
                "script": caption_input.script,
                "video_url": caption_input.video_url,
                "processing_errors": []
            }

            # Run the graph
            final_state = await self.graph.ainvoke(initial_state)

            # Extract results
            refined = final_state.get("refined_caption")
            analysis = final_state.get("script_analysis")

            if not refined:
                return CaptionAgentOutput(
                    caption="",
                    success=False,
                    error_message="Failed to generate caption",
                    metadata={}
                )

            return CaptionAgentOutput(
                caption=refined.final_caption,
                script_analysis=analysis,
                metadata={
                    "hook": refined.hook,
                    "body": refined.body,
                    "cta": refined.cta,
                    "hashtags": refined.hashtags,
                    "total_length": refined.total_length,
                    "line_count": refined.line_count,
                    "processing_errors": final_state.get("processing_errors", [])
                },
                success=True
            )

        except Exception as e:
            return CaptionAgentOutput(
                caption="",
                success=False,
                error_message=str(e),
                metadata={}
            )


# Convenience function for easy usage
async def generate_instagram_caption(script: str, video_url: str = None, api_key: str = None) -> CaptionAgentOutput:
    """
    Convenience function to generate an Instagram caption from a script

    Args:
        script: The video script
        video_url: Optional URL of the uploaded video
        api_key: Optional OpenAI API key (uses env var if not provided)

    Returns:
        CaptionAgentOutput with the generated caption
    """
    agent = CaptionAgent(openai_api_key=api_key)
    caption_input = CaptionInput(script=script, video_url=video_url)
    return await agent.generate_caption(caption_input)
