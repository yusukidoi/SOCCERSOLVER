import { Route, Routes } from "react-router-dom";
import Layout from "./components/Layout";
import SearchPage from "./pages/SearchPage";
import ProfilePage from "./pages/ProfilePage";
import ComparisonPage from "./pages/ComparisonPage";

export default function App() {
  return (
    <Layout>
      <Routes>
        <Route path="/" element={<SearchPage />} />
        <Route path="/players/:playerId" element={<ProfilePage />} />
        <Route path="/compare" element={<ComparisonPage />} />
      </Routes>
    </Layout>
  );
}
