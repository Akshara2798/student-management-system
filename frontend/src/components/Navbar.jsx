
import "./Navbar.css";

function Navbar({ admin, onLogout, loggingOut = false }) {
    const initial = (admin?.full_name || "A")
        .trim()
        .charAt(0)
        .toUpperCase();

    return (
        <nav className="navbar">
            <div className="navbar-left">
                <div className="navbar-logo">
                    <svg
                        viewBox="0 0 24 24"
                        fill="none"
                        stroke="currentColor"
                        strokeWidth="1.8"
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        aria-hidden="true"
                    >
                        <path d="m2 10 10-5 10 5-10 5-10-5Z" />
                        <path d="M6 12v5c3.5 3 8.5 3 12 0v-5" />
                        <path d="M22 10v6" />
                    </svg>
                </div>

                <div className="navbar-brand">
                    <h2>StudentHub</h2>
                    <span>STUDENT MANAGEMENT</span>
                </div>
            </div>

            <div className="navbar-center">
                <span className="navbar-status-dot" />
                <span>Admin Dashboard</span>
            </div>

            <div className="navbar-right">
                <div className="navbar-profile">
                    <div className="admin-avatar" aria-hidden="true">
                        {initial}
                    </div>

                    <div className="admin-details">
                        <span className="admin-name">
                            {admin?.full_name || "Administrator"}
                        </span>
                        <span className="admin-role">Administrator</span>
                    </div>
                </div>

                <div className="navbar-divider" />

                <button
                    type="button"
                    className="logout-button"
                    onClick={onLogout}
                    disabled={loggingOut}
                    aria-label="Log out of your admin account"
                >
                    <svg
                        viewBox="0 0 24 24"
                        fill="none"
                        stroke="currentColor"
                        strokeWidth="1.8"
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        aria-hidden="true"
                    >
                        <path d="M10 17l5-5-5-5" />
                        <path d="M15 12H3" />
                        <path d="M12 3h6a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2h-6" />
                    </svg>

                    <span>
                        {loggingOut ? "Logging out..." : "Logout"}
                    </span>
                </button>
            </div>
        </nav>
    );
}

export default Navbar;
