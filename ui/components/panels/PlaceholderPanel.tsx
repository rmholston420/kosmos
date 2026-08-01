"use client";
export default function PlaceholderPanel({
  slot,
  populated = false,
}: {
  slot: string;
  populated?: boolean;
}) {
  return (
    <article data-testid={`panel-${slot}`} data-populated={populated}>
      <h2>{slot}</h2>
      {!populated && <p data-testid={`panel-${slot}-empty`}>No panel registered for this slot</p>}
    </article>
  );
}
