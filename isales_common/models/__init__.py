"""SQLAlchemy ORM models. All tables share a single :class:`Base` so Alembic
autogenerate can discover them by importing this package.
"""

from isales_common.models.agent import Agent
from isales_common.models.appointment import Appointment
from isales_common.models.base import Base, TimestampMixin, utc_now
from isales_common.models.call_record import CallRecord
from isales_common.models.call_summary import CallSummary
from isales_common.models.callback_config import CallbackConfig
from isales_common.models.callback_log import CallbackLog
from isales_common.models.campaign import Campaign
from isales_common.models.device import Device
from isales_common.models.device_relations import CampaignDevice, DeviceSimBinding
from isales_common.models.handoff_task import HandoffTask
from isales_common.models.holiday import Holiday
from isales_common.models.lead import Lead
from isales_common.models.pipeline_trace import PipelineTrace
from isales_common.models.prompt import PromptVersion
from isales_common.models.provider_credential import ProviderCredential
from isales_common.models.role_config import RoleConfig
from isales_common.models.sim_card import SimCard
from isales_common.models.voice_model import VoiceModel

__all__ = [
    "Agent",
    "Appointment",
    "Base",
    "CallRecord",
    "CallSummary",
    "CallbackConfig",
    "CallbackLog",
    "Campaign",
    "CampaignDevice",
    "Device",
    "DeviceSimBinding",
    "HandoffTask",
    "Holiday",
    "Lead",
    "PipelineTrace",
    "PromptVersion",
    "ProviderCredential",
    "RoleConfig",
    "SimCard",
    "TimestampMixin",
    "VoiceModel",
    "utc_now",
]
