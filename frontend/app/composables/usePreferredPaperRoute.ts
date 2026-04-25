export function usePreferredPaperRoute() {
  const localPaperRoutesByArxiv = useState<Record<string, string>>(
    "preferred-paper-routes",
    () => ({}),
  );
  const { resolvePapersByArxivIds } = useApi();

  function isArxivPaperId(id?: string | null) {
    return Boolean(id && /^\d{4}\.\d{4,5}(v\d+)?$/.test(id));
  }

  async function resolveLocalPaperRoutes(
    arxivIds: Array<string | null | undefined>,
  ) {
    const pendingIds = [
      ...new Set(
        arxivIds
          .filter((id): id is string => Boolean(id))
          .filter((id) => !localPaperRoutesByArxiv.value[id]),
      ),
    ];

    if (!pendingIds.length) return;

    try {
      const res = await resolvePapersByArxivIds(pendingIds);
      localPaperRoutesByArxiv.value = {
        ...localPaperRoutesByArxiv.value,
        ...Object.fromEntries(
          res.matches.map((match) => [
            match.arxiv_id,
            `/papers/${match.paper_id}`,
          ]),
        ),
      };
    } catch (err) {
      console.warn("[PaperRoute] Failed to resolve local paper routes:", err);
    }
  }

  function preferredPaperRoute(
    arxivId?: string | null,
    fallback = "/deepxiv/trending",
  ) {
    if (!arxivId) return fallback;
    return (
      localPaperRoutesByArxiv.value[arxivId] ?? `/deepxiv/papers/${arxivId}`
    );
  }

  async function openPreferredPaper(
    arxivId?: string | null,
    fallback = "/deepxiv/trending",
  ) {
    if (!arxivId) {
      return navigateTo(fallback);
    }
    await resolveLocalPaperRoutes([arxivId]);
    return navigateTo(preferredPaperRoute(arxivId, fallback));
  }

  return {
    localPaperRoutesByArxiv,
    isArxivPaperId,
    resolveLocalPaperRoutes,
    preferredPaperRoute,
    openPreferredPaper,
  };
}
