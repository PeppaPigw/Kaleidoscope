"""Seed script — populate the database with the 65 RSS sources from source.md."""

import asyncio

from app.dependencies import async_session_factory
from app.models.feed import RSSFeed

# --- RSS Sources from source.md ---
RSS_SOURCES = [
    # arXiv (direct PDF)
    {
        "url": "https://rss.arxiv.org/rss/cond-mat",
        "name": "arXiv: Condensed Matter",
        "publisher": "arXiv",
        "category": "physics",
        "pdf_capability": "direct",
    },
    {
        "url": "https://rss.arxiv.org/rss/physics",
        "name": "arXiv: Physics",
        "publisher": "arXiv",
        "category": "physics",
        "pdf_capability": "direct",
    },
    {
        "url": "https://rss.arxiv.org/rss/cs.LG",
        "name": "arXiv: Machine Learning",
        "publisher": "arXiv",
        "category": "cs",
        "pdf_capability": "direct",
    },
    {
        "url": "https://rss.arxiv.org/rss/stat.ML",
        "name": "arXiv: Statistical ML",
        "publisher": "arXiv",
        "category": "cs",
        "pdf_capability": "direct",
    },
    {
        "url": "https://rss.arxiv.org/rss/cs.AI",
        "name": "arXiv: Artificial Intelligence",
        "publisher": "arXiv",
        "category": "cs",
        "pdf_capability": "direct",
    },
    {
        "url": "https://rss.arxiv.org/rss/cond-mat.supr-con",
        "name": "arXiv: Superconductivity + Materials",
        "publisher": "arXiv",
        "category": "physics",
        "pdf_capability": "direct",
    },
    # ChemRxiv (direct PDF)
    {
        "url": "https://chemrxiv.org/engage/rss/chemrxiv",
        "name": "ChemRxiv",
        "publisher": "ChemRxiv",
        "category": "chemistry",
        "pdf_capability": "direct",
    },
    # Research Square (direct PDF)
    {
        "url": "https://www.researchsquare.com/rss.xml",
        "name": "Research Square",
        "publisher": "Research Square",
        "category": "multidisciplinary",
        "pdf_capability": "direct",
    },
    # APS OA (direct PDF)
    {
        "url": "https://feeds.aps.org/rss/recent/prx.xml",
        "name": "Physical Review X",
        "publisher": "APS",
        "category": "physics",
        "pdf_capability": "direct",
    },
    {
        "url": "https://feeds.aps.org/rss/recent/prxenergy.xml",
        "name": "PRX Energy",
        "publisher": "APS",
        "category": "physics",
        "pdf_capability": "direct",
    },
    {
        "url": "https://feeds.aps.org/rss/recent/prresearch.xml",
        "name": "Physical Review Research",
        "publisher": "APS",
        "category": "physics",
        "pdf_capability": "direct",
    },
    {
        "url": "https://feeds.aps.org/rss/recent/physics.xml",
        "name": "Physics Magazine",
        "publisher": "APS",
        "category": "physics",
        "pdf_capability": "direct",
    },
    # APS subscription
    {
        "url": "https://feeds.aps.org/rss/allsuggestions.xml",
        "name": "APS Editor's Suggestions",
        "publisher": "APS",
        "category": "physics",
        "pdf_capability": "unpaywall",
    },
    {
        "url": "https://feeds.aps.org/rss/recent/prl.xml",
        "name": "Physical Review Letters",
        "publisher": "APS",
        "category": "physics",
        "pdf_capability": "unpaywall",
    },
    {
        "url": "https://feeds.aps.org/rss/recent/rmp.xml",
        "name": "Reviews of Modern Physics",
        "publisher": "APS",
        "category": "physics",
        "pdf_capability": "metadata_only",
    },
    {
        "url": "https://feeds.aps.org/rss/recent/prb.xml",
        "name": "Physical Review B",
        "publisher": "APS",
        "category": "physics",
        "pdf_capability": "unpaywall",
    },
    {
        "url": "https://feeds.aps.org/rss/recent/prmaterials.xml",
        "name": "Physical Review Materials",
        "publisher": "APS",
        "category": "physics",
        "pdf_capability": "unpaywall",
    },
    {
        "url": "https://feeds.aps.org/rss/recent/prapplied.xml",
        "name": "Physical Review Applied",
        "publisher": "APS",
        "category": "physics",
        "pdf_capability": "unpaywall",
    },
    # Nature OA
    {
        "url": "https://www.nature.com/ncomms.rss",
        "name": "Nature Communications",
        "publisher": "Springer Nature",
        "category": "multidisciplinary",
        "pdf_capability": "direct",
    },
    {
        "url": "https://www.nature.com/npjcompumats.rss",
        "name": "npj Computational Materials",
        "publisher": "Springer Nature",
        "category": "materials",
        "pdf_capability": "direct",
    },
    {
        "url": "https://www.nature.com/npjquantmats.rss",
        "name": "npj Quantum Materials",
        "publisher": "Springer Nature",
        "category": "physics",
        "pdf_capability": "direct",
    },
    {
        "url": "https://www.nature.com/npj2dmaterials.rss",
        "name": "npj 2D Materials and Applications",
        "publisher": "Springer Nature",
        "category": "materials",
        "pdf_capability": "direct",
    },
    # Nature subscription
    {
        "url": "https://www.nature.com/nature.rss",
        "name": "Nature",
        "publisher": "Springer Nature",
        "category": "multidisciplinary",
        "pdf_capability": "unpaywall",
    },
    {
        "url": "https://www.nature.com/nphys.rss",
        "name": "Nature Physics",
        "publisher": "Springer Nature",
        "category": "physics",
        "pdf_capability": "unpaywall",
    },
    {
        "url": "https://www.nature.com/nchem.rss",
        "name": "Nature Chemistry",
        "publisher": "Springer Nature",
        "category": "chemistry",
        "pdf_capability": "unpaywall",
    },
    {
        "url": "https://www.nature.com/natcomputsci.rss",
        "name": "Nature Computational Science",
        "publisher": "Springer Nature",
        "category": "cs",
        "pdf_capability": "unpaywall",
    },
    {
        "url": "https://www.nature.com/natmachintell.rss",
        "name": "Nature Machine Intelligence",
        "publisher": "Springer Nature",
        "category": "cs",
        "pdf_capability": "unpaywall",
    },
    {
        "url": "https://www.nature.com/natrevmats.rss",
        "name": "Nature Reviews Materials",
        "publisher": "Springer Nature",
        "category": "materials",
        "pdf_capability": "metadata_only",
    },
    {
        "url": "https://www.nature.com/natrevchem.rss",
        "name": "Nature Reviews Chemistry",
        "publisher": "Springer Nature",
        "category": "chemistry",
        "pdf_capability": "metadata_only",
    },
    {
        "url": "https://www.nature.com/natrevphys.rss",
        "name": "Nature Reviews Physics",
        "publisher": "Springer Nature",
        "category": "physics",
        "pdf_capability": "metadata_only",
    },
    {
        "url": "https://www.nature.com/natelectron.rss",
        "name": "Nature Electronics",
        "publisher": "Springer Nature",
        "category": "physics",
        "pdf_capability": "unpaywall",
    },
    {
        "url": "https://www.nature.com/nnano.rss",
        "name": "Nature Nanotechnology",
        "publisher": "Springer Nature",
        "category": "materials",
        "pdf_capability": "unpaywall",
    },
    {
        "url": "https://www.nature.com/nphoton.rss",
        "name": "Nature Photonics",
        "publisher": "Springer Nature",
        "category": "physics",
        "pdf_capability": "unpaywall",
    },
    # Science / AAAS
    {
        "url": "https://www.science.org/action/showFeed?type=etoc&feed=rss&jc=science",
        "name": "Science",
        "publisher": "AAAS",
        "category": "multidisciplinary",
        "pdf_capability": "unpaywall",
    },
    {
        "url": "https://www.science.org/action/showFeed?type=etoc&feed=rss&jc=sciadv",
        "name": "Science Advances",
        "publisher": "AAAS",
        "category": "multidisciplinary",
        "pdf_capability": "direct",
    },
    # ACS
    {
        "url": "https://feeds.feedburner.com/acs/jacsat",
        "name": "JACS",
        "publisher": "ACS",
        "category": "chemistry",
        "pdf_capability": "tdm",
    },
    {
        "url": "https://pubs.acs.org/action/showFeed?type=etoc&feed=rss&jc=ancac3",
        "name": "ACS Nano",
        "publisher": "ACS",
        "category": "materials",
        "pdf_capability": "tdm",
    },
    {
        "url": "https://pubs.acs.org/action/showFeed?type=etoc&feed=rss&jc=nalefd",
        "name": "Nano Letters",
        "publisher": "ACS",
        "category": "materials",
        "pdf_capability": "tdm",
    },
    {
        "url": "https://pubs.acs.org/action/showFeed?type=etoc&feed=rss&jc=jpclcd",
        "name": "J. Phys. Chem. Lett.",
        "publisher": "ACS",
        "category": "chemistry",
        "pdf_capability": "tdm",
    },
    {
        "url": "https://pubs.acs.org/action/showFeed?type=etoc&feed=rss&jc=jctcce",
        "name": "J. Chem. Theory Comput.",
        "publisher": "ACS",
        "category": "chemistry",
        "pdf_capability": "tdm",
    },
    {
        "url": "https://pubs.acs.org/action/showFeed?type=etoc&feed=rss&jc=chreay",
        "name": "Chemical Reviews",
        "publisher": "ACS",
        "category": "chemistry",
        "pdf_capability": "metadata_only",
    },
    {
        "url": "https://feeds.feedburner.com/acs/achre4",
        "name": "Accounts of Chemical Research",
        "publisher": "ACS",
        "category": "chemistry",
        "pdf_capability": "metadata_only",
    },
    # Wiley
    {
        "url": "https://onlinelibrary.wiley.com/action/showFeed?jc=15213773&type=etoc&feed=rss",
        "name": "Angewandte Chemie",
        "publisher": "Wiley",
        "category": "chemistry",
        "pdf_capability": "tdm",
    },
    {
        "url": "https://onlinelibrary.wiley.com/action/showFeed?jc=15214095&type=etoc&feed=rss",
        "name": "Advanced Materials",
        "publisher": "Wiley",
        "category": "materials",
        "pdf_capability": "tdm",
    },
    {
        "url": "https://onlinelibrary.wiley.com/action/showFeed?jc=16163028&type=etoc&feed=rss",
        "name": "Advanced Functional Materials",
        "publisher": "Wiley",
        "category": "materials",
        "pdf_capability": "tdm",
    },
    {
        "url": "https://onlinelibrary.wiley.com/action/showFeed?jc=21983844&type=etoc&feed=rss",
        "name": "Advanced Energy Materials",
        "publisher": "Wiley",
        "category": "materials",
        "pdf_capability": "tdm",
    },
    # AIP
    {
        "url": "https://aip.scitation.org/action/showFeed?type=etoc&feed=rss&jc=jcp",
        "name": "J. Chemical Physics",
        "publisher": "AIP",
        "category": "chemistry",
        "pdf_capability": "unpaywall",
    },
    {
        "url": "https://aip.scitation.org/action/showFeed?type=etoc&feed=rss&jc=apl",
        "name": "Applied Physics Letters",
        "publisher": "AIP",
        "category": "physics",
        "pdf_capability": "unpaywall",
    },
    {
        "url": "https://pubs.aip.org/rss/site_1000043/1000024.xml",
        "name": "APL Machine Learning",
        "publisher": "AIP",
        "category": "cs",
        "pdf_capability": "direct",
    },
    # IOP
    {
        "url": "https://iopscience.iop.org/journal/rss/2632-2153",
        "name": "ML: Science and Technology",
        "publisher": "IOP",
        "category": "cs",
        "pdf_capability": "direct",
    },
    # RSC
    {
        "url": "https://feeds.rsc.org/rss/dd",
        "name": "Digital Discovery",
        "publisher": "RSC",
        "category": "chemistry",
        "pdf_capability": "direct",
    },
    # PNAS
    {
        "url": "https://www.pnas.org/rss/Physics.xml",
        "name": "PNAS: Physics",
        "publisher": "NAS",
        "category": "physics",
        "pdf_capability": "unpaywall",
    },
    {
        "url": "https://www.pnas.org/rss/Applied_Physical_Sciences.xml",
        "name": "PNAS: Applied Physical Sciences",
        "publisher": "NAS",
        "category": "physics",
        "pdf_capability": "unpaywall",
    },
    # Elsevier
    {
        "url": "https://rss.sciencedirect.com/publication/science/20959273",
        "name": "Science Bulletin",
        "publisher": "Elsevier",
        "category": "multidisciplinary",
        "pdf_capability": "tdm",
    },
    {
        "url": "https://rss.sciencedirect.com/publication/science/09270256",
        "name": "Computational Materials Science",
        "publisher": "Elsevier",
        "category": "materials",
        "pdf_capability": "tdm",
    },
    {
        "url": "https://rss.sciencedirect.com/publication/science/00104655",
        "name": "Computer Physics Communications",
        "publisher": "Elsevier",
        "category": "physics",
        "pdf_capability": "tdm",
    },
    {
        "url": "https://rss.sciencedirect.com/publication/science/13697021",
        "name": "Materials Today",
        "publisher": "Elsevier",
        "category": "materials",
        "pdf_capability": "tdm",
    },
    # Annual Reviews
    {
        "url": "https://www.annualreviews.org/action/showFeed?type=etoc&feed=rss&jc=conmatphys",
        "name": "Annual Review: Condensed Matter Physics",
        "publisher": "Annual Reviews",
        "category": "physics",
        "pdf_capability": "metadata_only",
    },
    {
        "url": "https://www.annualreviews.org/action/showFeed?type=etoc&feed=rss&jc=physchem",
        "name": "Annual Review: Physical Chemistry",
        "publisher": "Annual Reviews",
        "category": "chemistry",
        "pdf_capability": "metadata_only",
    },
    # Oxford
    {
        "url": "https://academic.oup.com/rss/site_5332/3198.xml",
        "name": "National Science Review",
        "publisher": "OUP",
        "category": "multidisciplinary",
        "pdf_capability": "unpaywall",
    },
    # News
    {
        "url": "https://phys.org/rss-feed/physics-news/",
        "name": "Phys.org Physics News",
        "publisher": "Phys.org",
        "category": "news",
        "pdf_capability": "metadata_only",
    },
    {
        "url": "https://feeds.feedburner.com/physicstodaynews",
        "name": "Physics Today",
        "publisher": "AIP",
        "category": "news",
        "pdf_capability": "metadata_only",
    },
]


async def seed_rss_feeds():
    """Seed the database with RSS sources."""
    async with async_session_factory() as session:
        for source in RSS_SOURCES:
            from sqlalchemy import select

            existing = await session.execute(
                select(RSSFeed).where(RSSFeed.url == source["url"])
            )
            if existing.scalar_one_or_none():
                continue

            feed = RSSFeed(**source)
            session.add(feed)

        await session.commit()
        print(f"Seeded {len(RSS_SOURCES)} RSS feeds.")


if __name__ == "__main__":
    asyncio.run(seed_rss_feeds())
