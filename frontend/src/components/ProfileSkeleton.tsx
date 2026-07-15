import Skeleton from "./Skeleton";

export default function ProfileSkeleton() {
  return (
    <section className="profile">
      <Skeleton className="skeleton--btn" lines={1} />
      <div className="card profile__header">
        <Skeleton lines={2} />
        <Skeleton className="skeleton--value" lines={1} />
      </div>
      <div className="profile__grid">
        <div className="card">
          <Skeleton lines={1} />
          <Skeleton className="skeleton--chart" lines={1} />
        </div>
        <div className="card">
          <Skeleton lines={6} />
        </div>
      </div>
    </section>
  );
}
