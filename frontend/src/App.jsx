import { BrowserRouter, Routes, Route, Navigate } from "react-router";
import LoginPage from "./pages/login/LoginPage";


export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Navigate to="/login" />} />
        <Route path="/login" element={<LoginPage />} />
      </Routes>
    </BrowserRouter>
  );
}
