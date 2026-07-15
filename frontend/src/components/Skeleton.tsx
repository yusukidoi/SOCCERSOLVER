interface Props {
  lines?: number;
  className?: string;
}

/** Simple pulsing placeholder while data loads. */
export default function Skeleton({ lines = 1, className = "" }: Props) {
  return (
    <div className={`skeleton ${className}`.trim()} aria-hidden="true">
      {Array.from({ length: lines }).map((_, index) => (
        <div key={index} className="skeleton__line" />
      ))}
    </div>
  );
}
