import { Navigate, Route, Routes } from "react-router-dom";

import ProtectedRoute, { GuestRoute } from "./components/ProtectedRoute";
import AdminLogin from "./pages/AdminLogin";
import AdminRegister from "./pages/AdminRegister";
import StudentsPage from "./pages/StudentsPage";

import "./App.css";
import "./styles/auth.css";


function App() {

    return (

        <Routes>

            {/* Login and registration: hidden from logged-in admins */}
            <Route element={<GuestRoute />}>
                <Route path="/admin/login" element={<AdminLogin />} />
                <Route path="/admin/register" element={<AdminRegister />} />
            </Route>

            {/* Dashboard: logged-in admins only */}
            <Route element={<ProtectedRoute />}>
                <Route path="/admin/students" element={<StudentsPage />} />
            </Route>

            {/* Everything else goes to the dashboard (which redirects to login if needed) */}
            <Route path="*" element={<Navigate to="/admin/students" replace />} />

        </Routes>

    );
}

export default App;
