export function locateFinding(result, findingId, requestedPath) {
  const matches = [];
  if (result.files && requestedPath === '@project') {
    const finding = result.security_analysis?.candidates?.find((item) => item.id === findingId);
    if (finding) {
      const label = `${finding.cross_file?.source_file ?? 'Unknown'} → ${finding.cross_file?.target_file ?? 'Unknown'}`;
      return { finding, file: { artifact: { relative_path: label } } };
    }
    return null;
  }
  for (const file of result.files ?? [result]) {
    const finding = file.security_analysis?.candidates?.find((item) => item.id === findingId);
    if (finding) matches.push({ finding, file });
  }
  if (requestedPath) {
    return matches.find(({ file }) => (file.artifact?.relative_path ?? file.artifact?.filename) === requestedPath) ?? null;
  }
  return matches.length === 1 ? matches[0] : null;
}
