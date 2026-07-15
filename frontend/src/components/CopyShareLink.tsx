import { useState } from "react";

/** Copy the current page URL — useful for sharing comparisons with colleagues. */
export default function CopyShareLink() {
  const [copied, setCopied] = useState(false);

  const copy = async () => {
    try {
      await navigator.clipboard.writeText(window.location.href);
      setCopied(true);
      window.setTimeout(() => setCopied(false), 2000);
    } catch {
      setCopied(false);
    }
  };

  return (
    <button type="button" className="button button--ghost share-link" onClick={copy}>
      {copied ? "Link copied ✓" : "Copy share link"}
    </button>
  );
}
