import type { PlayerScenario } from "../types";

const LEVEL_LABELS: Record<PlayerScenario["upside"], string> = {
  higher: "Higher",
  lower: "Lower",
  similar: "Similar",
};

function ScenarioAxis({
  label,
  one,
  two,
}: {
  label: string;
  one: PlayerScenario["upside"];
  two: PlayerScenario["upside"];
}) {
  return (
    <div className="scenario-axis">
      <span className="scenario-axis__label">{label}</span>
      <div className="scenario-axis__values">
        <span className="scenario-axis__one">{LEVEL_LABELS[one]}</span>
        <span className="muted">vs</span>
        <span className="scenario-axis__two">{LEVEL_LABELS[two]}</span>
      </div>
    </div>
  );
}

export default function ScenarioPanel({
  oneName,
  twoName,
  scenarioOne,
  scenarioTwo,
}: {
  oneName: string;
  twoName: string;
  scenarioOne: PlayerScenario;
  scenarioTwo: PlayerScenario;
}) {
  return (
    <div className="card scenario">
      <h2 className="section-title">Scenario comparison</h2>
      <p className="muted section-hint">
        Investment framing — upside, risk, and consistency beyond raw metric wins.
      </p>

      <div className="scenario__players">
        <div className="scenario__side">
          <strong>{oneName}</strong>
          <p className="muted">{scenarioOne.summary}</p>
        </div>
        <div className="scenario__side">
          <strong>{twoName}</strong>
          <p className="muted">{scenarioTwo.summary}</p>
        </div>
      </div>

      <div className="scenario__axes">
        <ScenarioAxis label="Upside" one={scenarioOne.upside} two={scenarioTwo.upside} />
        <ScenarioAxis label="Risk" one={scenarioOne.risk} two={scenarioTwo.risk} />
        <ScenarioAxis
          label="Consistency"
          one={scenarioOne.consistency}
          two={scenarioTwo.consistency}
        />
      </div>
    </div>
  );
}
