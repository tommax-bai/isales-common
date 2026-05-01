"""api → scheduler queue: start / pause / resume a campaign.

Spec: service-communication § 通信通道矩阵 (api→scheduler row);
      message-contract § Scenario "v1 必有的消息类".
"""

from __future__ import annotations

from typing import Annotated, Literal

from pydantic import Field

from isales_common.schemas.messages._base import BaseMessage


class StartCampaign(BaseMessage):
    type: Literal["start"] = "start"
    campaign_id: int


class PauseCampaign(BaseMessage):
    type: Literal["pause"] = "pause"
    campaign_id: int


class ResumeCampaign(BaseMessage):
    type: Literal["resume"] = "resume"
    campaign_id: int


CampaignControl = Annotated[
    StartCampaign | PauseCampaign | ResumeCampaign,
    Field(discriminator="type"),
]
