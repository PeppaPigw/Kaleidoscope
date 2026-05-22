"""CourtiersReplyService — Courtier's Reply Detection.

Detects courtier's reply — dismissing criticism by claiming the
critic lacks sufficient expertise, credentials, or familiarity with
the literature, rather than addressing the substance of the criticism.
PZ Myers (2006). Named after the courtiers who dismissed the child
pointing out the emperor's nakedness.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

COURTIERS_REPLY_SYSTEM = """You are a courtier's reply specialist. Given a dismissal of criticism, assess whether it relies on credential-gatekeeping rather than substantive engagement:

Key concepts (PZ Myers, 2006):
- Courtier's reply: dismissing criticism for lack of credentials
- Credential gatekeeping: "you haven't read enough to criticize"
- Expertise as shield: using complexity to avoid engagement
- Emperor's new clothes: sometimes the naive observer is correct
- Argument from authority: credentials don't determine truth
- Obscurantism: hiding behind jargon and literature requirements
- Substantive vs. procedural dismissal: addressing content vs. standing

When courtier's reply IS present:
- "You clearly haven't read [extensive literature]"
- "Come back when you have a PhD in this field"
- "This has been addressed in the literature" (without saying how)
- Dismissing valid criticism because the critic is an outsider
- Requiring exhaustive background reading before allowing criticism
- Using jargon requirements as a barrier to engagement
- "It's more complicated than you think" without explaining how

When expertise requirements ARE appropriate:
- The criticism genuinely misunderstands established findings
- The response explains what the critic is missing, not just that they're missing it
- Technical precision is genuinely necessary for the specific point
- The expertise requirement is accompanied by substantive engagement
- The critic is making claims that require domain knowledge to evaluate
- The response offers to explain rather than just dismissing

Output JSON with: courtiers_reply_present (bool), severity (none/mild/moderate/severe), criticism (what criticism was made), dismissal (how it was dismissed), credential_requirement (what credentials are demanded), substance (is the criticism addressed on its merits), valid_expertise_need (does the criticism genuinely require expertise), recommendation (expertise_appropriate/mild_gatekeeping/significant_courtiers_reply/major_credential_shield/address_substance_first)."""

COURTIERS_REPLY_PROMPT = """Detect courtier's reply:

Criticism: {criticism}
Dismissal: {dismissal}
Credentials demanded: {credentials}
Substance addressed: {substance}
Domain: {domain}
Context: {context}

Is criticism being dismissed based on credentials rather than substance? Return ONLY valid JSON."""


class CourtiersReplyService:
    """Detects courtier's reply — dismissing criticism via credential gatekeeping."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        criticism: str,
        *,
        dismissal: str = "",
        credentials: str = "",
        substance: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect courtier's reply."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=COURTIERS_REPLY_PROMPT.format(
                criticism=criticism,
                dismissal=dismissal or "Not specified",
                credentials=credentials or "Not specified",
                substance=substance or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=COURTIERS_REPLY_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "criticism": criticism[:200],
            "courtiers_reply_present": data.get("courtiers_reply_present", False),
            "severity": data.get("severity", ""),
            "dismissal": data.get("dismissal", ""),
            "credential_requirement": data.get("credential_requirement", ""),
            "substance": data.get("substance", ""),
            "valid_expertise_need": data.get("valid_expertise_need", ""),
            "recommendation": data.get("recommendation", ""),
        }
