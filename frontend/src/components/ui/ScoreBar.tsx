interface ScoreBarProps {
  score: number; // 0-2
  max?: number;
}

export function ScoreBar({ score, max = 2 }: ScoreBarProps) {
  return (
    <span className="score-bar" aria-label={`score ${score} of ${max}`}>
      {Array.from({ length: max }).map((_, i) => (
        <span
          key={i}
          className={`score-bar__seg${i < score ? " score-bar__seg--on" : ""}`}
        />
      ))}
      <span className="score-bar__label mono">{score}/{max}</span>
    </span>
  );
}