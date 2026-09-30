import "@/App.css";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import HomePage from "@/pages/HomePage";
import HistoryPage from "@/pages/HistoryPage";

function App() {
  return (
    <div className="App">
      <BrowserRouter basename="/project1_AI_powerd_fake_news_detection">
        <Routes>
          <Route path="/" element={<HomePage />} />
          <Route path="/history" element={<HistoryPage />} />
        </Routes>
      </BrowserRouter>
    </div>
  );
}

export default App;