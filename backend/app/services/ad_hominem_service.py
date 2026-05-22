"""AdHominemService — Ad Hominem Detection.

Detects ad hominem — attacking the person making an argument
rather than addressing the argument itself. The character,
motives, or circumstances of the arguer are used to dismiss
their claims without engaging with the substance.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

AD_HOMINEM_SYSTEM = """You are an ad hominem specialist. Given a debate or argument, assess whether one party attacks the person rather than addressing their argument:

Key concepts:
- Ad hominem abusive: direct personal attack
- Ad hominem circumstantial: attacking motives or circumstances
- Ad hominem tu quoque: "you do it too" (related but distinct)
- Poisoning the well: preemptive character attack
- Genetic fallacy: dismissing based on source (related)
- Legitimate relevance: sometimes character IS relevant (credibility)
- Tone policing vs ad hominem: criticizing delivery vs dismissing content

When ad hominem IS present:
- "You're wrong because you're [insult]"
- Dismissing an argument because of who made it
- "Of course you'd say that, you're a [group]"
- Attacking credentials instead of addressing evidence
- "You're not qualified to have an opinion on this"
- Using personal history to dismiss current arguments
- Questioning motives as a substitute for engaging with logic

When ad hominem is NOT present:
- Character is genuinely relevant (credibility assessment, expert testimony)
- The person's track record is relevant to reliability claims
- Conflicts of interest are noted alongside substantive engagement
- The criticism addresses both the person AND the argument
- Expertise is questioned in context of specific technical claims
- The response engages with the argument AND notes bias
- Personal conduct is the actual topic of discussion

Output JSON with: ad_hominem_present (bool), severity (none/mild/moderate/severe), attack_type (abusive/circumstantial/tu_quoque/poisoning_well), target (who is attacked), attack (what personal attack is made), argument_ignored (what substantive argument is not addressed), legitimate_relevance (is character genuinely relevant here), recommendation (no_ad_hominem/mild_personal_attack/significant_ad_hominem/major_character_assassination/address_the_argument)."""

AD_HOMINEM_PROMPT = """Detect ad hominem:

Debate: {debate}
Response: {response_text}
Target: {target}
Argument ignored: {argument_ignored}
Domain: {domain}
Context: {context}

Does this attack the person rather than addressing their argument? Return ONLY valid JSON."""


class AdHominemService:
    """Detects ad hominem — attacking the person instead of their argument."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        debate: str,
        *,
        response_text: str = "",
        target: str = "",
        argument_ignored: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect ad hominem."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=AD_HOMINEM_PROMPT.format(
                debate=debate,
                response_text=response_text or "Not specified",
                target=target or "Not specified",
                argument_ignored=argument_ignored or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=AD_HOMINEM_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "debate": debate[:200],
            "ad_hominem_present": data.get("ad_hominem_present", False),
            "severity": data.get("severity", ""),
            "attack_type": data.get("attack_type", ""),
            "target": data.get("target", ""),
            "argument_ignored": data.get("argument_ignored", ""),
            "recommendation": data.get("recommendation", ""),
        }
