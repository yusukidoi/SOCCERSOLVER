import { useParams } from "react-router-dom";

export default function ProfilePage() {
  const { playerId } = useParams();
  return (
    <section>
      <h1>Player profile</h1>
      <p className="muted">Profile for player {playerId} — implemented in a later step.</p>
    </section>
  );
}
