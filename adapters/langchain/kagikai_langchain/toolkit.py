"""KagikaiToolkit: factory that returns all 29 Kagikai LangChain tools."""

from __future__ import annotations

from langchain_core.tools import BaseTool, BaseToolkit

from kagikai_langchain._http import KagikaiAPI
from kagikai_langchain.tools import (
    KagikaiHealth,
    KagikaiCreateInstrument,
    KagikaiConfirmInstrument,
    KagikaiVerifyAddress,
    KagikaiGetAttestation,
    KagikaiGetStatus,
    KagikaiCreateBatch,
    KagikaiGetBatchStatus,
    KagikaiWatchReceipt,
    KagikaiDeleteWatch,
    KagikaiGetAgent,
    KagikaiUpdateAgent,
    KagikaiGetAgentCard,
    KagikaiGetReputation,
    KagikaiSubmitInstrument,
    KagikaiCompleteInstrument,
    KagikaiRejectInstrument,
    KagikaiVerifyTdxQuote,
    KagikaiEscrowCreate,
    KagikaiEscrowStatus,
    KagikaiEscrowRelease,
    KagikaiEscrowCancel,
    KagikaiSetDestination,
    KagikaiListAvailable,
    KagikaiRecycleInstrument,
    KagikaiRefundInstrument,
    KagikaiFeeEstimate,
    KagikaiDisputeInstrument,
    KagikaiResolveDispute,
)


class KagikaiToolkit(BaseToolkit):
    """Instantiates all 29 Kagikai tools with shared API configuration.

    Usage::

        toolkit = KagikaiToolkit(base_url="https://...", api_key="...")
        tools = toolkit.get_tools()

    Environment variables ``KAGIKAI_BASE_URL`` and ``KAGIKAI_API_KEY`` are
    used as fallbacks when constructor args are empty.
    """

    base_url: str = ""
    api_key: str = ""

    def get_tools(self) -> list[BaseTool]:
        api = KagikaiAPI(base_url=self.base_url, api_key=self.api_key)
        return [
            KagikaiHealth(api=api),
            KagikaiCreateInstrument(api=api),
            KagikaiConfirmInstrument(api=api),
            KagikaiVerifyAddress(api=api),
            KagikaiGetAttestation(api=api),
            KagikaiGetStatus(api=api),
            KagikaiCreateBatch(api=api),
            KagikaiGetBatchStatus(api=api),
            KagikaiWatchReceipt(api=api),
            KagikaiDeleteWatch(api=api),
            KagikaiGetAgent(api=api),
            KagikaiUpdateAgent(api=api),
            KagikaiGetAgentCard(api=api),
            KagikaiGetReputation(api=api),
            KagikaiSubmitInstrument(api=api),
            KagikaiCompleteInstrument(api=api),
            KagikaiRejectInstrument(api=api),
            KagikaiVerifyTdxQuote(api=api),
            KagikaiEscrowCreate(api=api),
            KagikaiEscrowStatus(api=api),
            KagikaiEscrowRelease(api=api),
            KagikaiEscrowCancel(api=api),
            KagikaiSetDestination(api=api),
            KagikaiListAvailable(api=api),
            KagikaiRecycleInstrument(api=api),
            KagikaiRefundInstrument(api=api),
            KagikaiFeeEstimate(api=api),
            KagikaiDisputeInstrument(api=api),
            KagikaiResolveDispute(api=api),
        ]
