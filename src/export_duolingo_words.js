// Run in the DevTools console on https://www.duolingo.com/practice-hub/words
// Uses your existing browser session; no password, token, or dependencies needed.
(async () => {
  if (location.hostname !== "www.duolingo.com" ||
      location.pathname.replace(/\/$/, "") !== "/practice-hub/words") {
    throw new Error("Open https://www.duolingo.com/practice-hub/words first.");
  }

  const sleep = (ms) => new Promise((resolve) => setTimeout(resolve, ms));
  const headings = () => [...document.querySelectorAll("h3")];
  const loadMore = () => [...document.querySelectorAll('button, [role="button"]')]
    .find((button) => /^load more$/i.test(button.textContent.trim()));
  const countHeading = [...document.querySelectorAll("h2")]
    .map((heading) => heading.textContent.trim())
    .find((text) => /^[\d,]+ words$/i.test(text));
  const expected = countHeading ? Number(countHeading.replace(/\D/g, "")) : null;

  for (let page = 0; ; page++) {
    const button = loadMore();
    if (!button) break;
    if (page >= 500) throw new Error("Stopped after 500 pages; no file exported.");
    const before = headings().length;
    button.scrollIntoView({ block: "center" });
    button.click();
    const deadline = Date.now() + 20000;
    while (headings().length <= before && Date.now() < deadline) await sleep(200);
    if (headings().length <= before) {
      throw new Error("Load more did not add words within 20 seconds. Retry when the page finishes loading.");
    }
    console.log(`Loaded ${headings().length}${expected ? ` / ${expected}` : ""} words`);
  }

  const rows = headings().map((heading) => {
    const korean = heading.textContent.trim();
    // Find the nearest row containing translation text as well as this heading.
    let row = heading.parentElement;
    while (row && row.querySelectorAll("h3").length === 1) {
      const lines = row.innerText.split("\n").map((line) => line.trim()).filter(Boolean);
      const index = lines.indexOf(korean);
      const english = lines.slice(index + 1).join(" ");
      if (index >= 0 && english) return { korean, english };
      row = row.parentElement;
    }
    throw new Error(`Could not read translation for ${korean}; no file exported.`);
  });
  if (!rows.length || (expected !== null && rows.length !== expected)) {
    throw new Error(`Found ${rows.length} rows; expected ${expected ?? "a nonempty list"}. No file exported.`);
  }

  const quote = (value) => `"${value.replace(/"/g, '""')}"`;
  const csv = "\uFEFF" + ["korean,english", ...rows.map(({ korean, english }) =>
    [korean, english].map(quote).join(","))].join("\r\n") + "\r\n";
  const url = URL.createObjectURL(new Blob([csv], { type: "text/csv;charset=utf-8" }));
  const link = document.createElement("a");
  link.href = url;
  link.download = `duolingo-korean-words-${new Date().toISOString().slice(0, 10)}.csv`;
  document.body.appendChild(link);
  link.click();
  link.remove();
  setTimeout(() => URL.revokeObjectURL(url), 60000);
  console.log(`Exported ${rows.length} Korean/English word pairs.`, rows);
  return rows;
})();
