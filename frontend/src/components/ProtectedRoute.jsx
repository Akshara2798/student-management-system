import { Navigate, Outlet } from "react-router-dom";

import { useAuth } from "../context/AuthContext";

function AuthLoading() {
    return (
        <div className="auth-loading" role="status" aria-live="polite">
            <div className="spinner" aria-hidden="true" />
            <p>Checking your session...</p>
        </div>
    );
}

// Pages for logged-in admins only. Everyone else is sent to /admin/login.
// (This only controls what the screen shows: the backend enforces access separately.)
function ProtectedRoute() {

    const { admin, checking } = useAuth();

    if (checking) {
        return <AuthLoading />;
    }

    if (!admin) {
        return <Navigate to="/admin/login" replace />;
    }

    return <Outlet />;
}

// Login / register pages: a logged-in admin is sent straight to the dashboard
export function GuestRoute() {

    const { admin, checking } = useAuth();

    if (checking) {
        return <AuthLoading />;
    }

    if (admin) {
        return <Navigate to="/admin/students" replace />;
    }

    return <Outlet />;
}

export default ProtectedRoute;
