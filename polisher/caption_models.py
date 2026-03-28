from pydantic import BaseModel, Field
from typing import List, Optional, TypedDict
from datetime import datetime


class CaptionInput(BaseModel):
    """Input model for caption generation"""
    script: str = Field(..., description="The video script to generate caption from")
    video_url: str = Field(..., description="URL of the uploaded video")
    target_audience: Optional[str] = Field(None, description="Target audience for the content")
    tone: Optional[str] = Field("engaging", description="Desired tone (e.g., casual, professional, inspiring)")


class ScriptAnalysis(BaseModel):
    """Output from script analyzer node"""
    key_themes: List[str] = Field(default_factory=list, description="Main themes identified in script")
    main_message: str = Field(..., description="Core message of the script")
    tone_detected: str = Field(..., description="Detected tone of the script")
    target_keywords: List[str] = Field(default_factory=list, description="Keywords for hashtag generation")
    emotional_appeal: str = Field(..., description="Emotional appeal type (e.g., inspirational, humorous)")


class CaptionDraft(BaseModel):
    """Output from caption generator node"""
    caption_body: str = Field(..., description="Main caption text")
    suggested_hashtags: List[str] = Field(default_factory=list, description="Suggested hashtags")
    char_count: int = Field(..., description="Character count of caption")


class HookOutput(BaseModel):
    """Output from hook creator node"""
    hook_line: str = Field(..., description="Attention-grabbing first line")
    hook_type: str = Field(..., description="Type of hook used (e.g., question, statement, statistic)")


class RefinedCaption(BaseModel):
    """Output from caption refiner node"""
    final_caption: str = Field(..., description="Final polished caption with all elements")
    hook: str = Field(..., description="Opening hook line")
    body: str = Field(..., description="Main caption body")
    cta: str = Field(..., description="Call to action")
    hashtags: List[str] = Field(default_factory=list, description="Final hashtags")
    total_length: int = Field(..., description="Total character count")
    line_count: int = Field(..., description="Number of lines in caption")


class CaptionAgentState(TypedDict, total=False):
    """State object that flows through the LangGraph"""
    # Input data (stored as primitives, not Pydantic models)
    script: str
    video_url: str
    target_audience: Optional[str]
    tone: str

    # Node outputs
    script_analysis: Optional[ScriptAnalysis]
    caption_draft: Optional[CaptionDraft]
    hook_output: Optional[HookOutput]
    refined_caption: Optional[RefinedCaption]

    # Metadata
    processing_errors: List[str]


class CaptionAgentOutput(BaseModel):
    """Final output from the caption agent"""
    caption: str = Field(..., description="Final Instagram caption")
    metadata: dict = Field(default_factory=dict, description="Metadata about generation process")
    script_analysis: Optional[ScriptAnalysis] = None
    success: bool = Field(True, description="Whether generation was successful")
    error_message: Optional[str] = None


class CaptionResponse(BaseModel):
    """Response model for GET /captions endpoint"""
    caption: str = Field(..., description="Generated Instagram caption")
    video: str = Field(..., description="URL of the video")
