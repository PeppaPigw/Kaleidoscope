function normalizePath(path: string): string {
  const pathname = path.split(/[?#]/, 1)[0] ?? '/'
  const trimmed = pathname.replace(/\/+$/, '')

  return trimmed || '/'
}

function isPathBoundaryMatch(currentPath: string, candidatePath: string): boolean {
  if (candidatePath === '/') return currentPath === '/'

  return currentPath === candidatePath || currentPath.startsWith(`${candidatePath}/`)
}

export function getActiveSidebarPath(currentPath: string, itemPaths: string[]): string | null {
  const normalizedCurrentPath = normalizePath(currentPath)

  return itemPaths
    .map(normalizePath)
    .filter(candidatePath => isPathBoundaryMatch(normalizedCurrentPath, candidatePath))
    .sort((left, right) => right.length - left.length)[0] ?? null
}

export function isSidebarItemActive(currentPath: string, itemPath: string, itemPaths: string[]): boolean {
  return getActiveSidebarPath(currentPath, itemPaths) === normalizePath(itemPath)
}
