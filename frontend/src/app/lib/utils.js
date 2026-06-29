export function classNames(...items) {
  return items.filter(Boolean).join(" ");
}

export function formatNumber(value) {
  if (value === null || value === undefined) return "0";
  return new Intl.NumberFormat("en-IN").format(Number(value) || 0);
}

export function sourceBadge(type) {
  const map = {
    text: "TXT",
    file: "FILE",
    pdf: "PDF",
    url: "WEB",
    website: "WEB",
    youtube: "YT",
  };

  return map[String(type || "").toLowerCase()] || "SRC";
}