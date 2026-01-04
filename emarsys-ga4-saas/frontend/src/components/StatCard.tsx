type StatCardProps = {
  label: string;
  value: string;
  delta: string;
  variant?: "positive" | "negative" | "neutral";
  icon: string;
};

function StatCard({ label, value, delta, variant = "neutral", icon }: StatCardProps) {
  return (
    <article className={`stat-card ${variant}`}>
      <div className="stat-icon">{icon}</div>
      <div>
        <p className="stat-label">{label}</p>
        <p className="stat-value">{value}</p>
      </div>
      <span className="stat-delta">{delta}</span>
    </article>
  );
}

export default StatCard;
