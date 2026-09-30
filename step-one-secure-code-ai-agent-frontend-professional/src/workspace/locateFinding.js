export function locateFinding(result, findingId, requestedPath) {
  const matches = [];
  for (const file of result.files ?? [result]) {
    const finding = file.security_analysis?.candidates?.find((item) => item.id === findingId);
    if (finding) matches.push({ finding, file });
  }
  if (requestedPath) {
    return matches.find(({ file }) => (file.artifact?.relative_path ?? file.artifact?.filename) === requestedPath) ?? null;
  }
  return matches.length === 1 ? matches[0] : null;
}
