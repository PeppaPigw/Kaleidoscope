#!/usr/bin/env bash

set -euo pipefail

expected_volume="${EXPECTED_POSTGRES_VOLUME:-kaleidoscope_postgres_data}"
expected_project="${EXPECTED_COMPOSE_PROJECT_NAME:-kaleidoscope}"
compose_file="${COMPOSE_FILE:-backend/docker/docker-compose.yml}"

running_container=""

while IFS= read -r container; do
  [[ -n "${container}" ]] || continue

  mapping="$(docker port "${container}" 5432/tcp 2>/dev/null || true)"
  if echo "${mapping}" | grep -Eq '(^|:)5432$'; then
    running_container="${container}"
    break
  fi
done < <(docker ps --format '{{.Names}}')

if [[ -z "${running_container}" ]]; then
  exit 0
fi

mounted_volumes="$(docker inspect "${running_container}" --format '{{range .Mounts}}{{println .Name}}{{end}}' 2>/dev/null || true)"
if echo "${mounted_volumes}" | grep -qx "${expected_volume}"; then
  exit 0
fi

volume_summary="$(echo "${mounted_volumes}" | awk 'NF' | paste -sd ', ' -)"

echo "❌ localhost:5432 is already served by '${running_container}', but it is not using the expected PostgreSQL volume '${expected_volume}'."
if [[ -n "${volume_summary}" ]]; then
  echo "   Mounted volumes: ${volume_summary}"
fi
echo "   Kaleidoscope expects compose project '${expected_project}' and volume '${expected_volume}'."
echo "   Stop the legacy stack first, for example:"
echo "     docker compose -p docker -f ${compose_file} down"
echo "   Then rerun:"
echo "     make dev"
exit 1
