import { useState } from "react";
import { Link } from "react-router-dom";

import { useAuth } from "../context/AuthContext";
import { getErrorMessage } from "../services/api";

const EMAIL_PATTERN = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

function AdminLogin() {

    const { login, notice, setNotice } = useAuth();

    const [email, setEmail] = useState("");
    const [password, setPassword] = useState("");
    const [showPassword, setShowPassword] = useState(false);
    const [fieldErrors, setFieldErrors] = useState({});
    const [error, setError] = useState("");
    const [submitting, setSubmitting] = useState(false);

    const validate = () => {
        const errors = {};

        if (!email.trim()) {
            errors.email = "Enter your email address.";
        } else if (!EMAIL_PATTERN.test(email.trim())) {
            errors.email = "Enter a valid email address.";
        }

        if (!password) {
            errors.password = "Enter your password.";
        }

        return errors;
    };

    const handleSubmit = async (event) => {

        event.preventDefault();

        if (submitting) {
            return; // blocks double submits
        }

        const errors = validate();
        setFieldErrors(errors);
        setError("");

        if (Object.keys(errors).length > 0) {
            return;
        }

        setNotice("");
        setSubmitting(true);

        try {
            // On success AuthContext stores the admin, and the route guard
            // moves the user to /admin/students automatically.
            await login(email.trim(), password);
        } catch (err) {
            setError(getErrorMessage(err, "Unable to sign in. Please try again."));
            setSubmitting(false);
        }
    };

    return (

        <main className="auth-page">

            <div className="auth-card">

                <div className="auth-brand">
                    <div className="logo" aria-hidden="true">🎓</div>
                    <div>
                        <h1>StudentHub</h1>
                        <span>Admin sign in</span>
                    </div>
                </div>

                {notice && (
                    <div className="success-message" role="status">
                        ✓ {notice}
                    </div>
                )}

                {error && (
                    <div className="error-message" role="alert">
                        ⚠ {error}
                    </div>
                )}

                <form onSubmit={handleSubmit} noValidate>

                    <div className="auth-field">
                        <label htmlFor="email">Email</label>
                        <input
                            id="email"
                            type="email"
                            autoComplete="username"
                            placeholder="you@example.com"
                            value={email}
                            onChange={(event) => setEmail(event.target.value)}
                            aria-invalid={Boolean(fieldErrors.email)}
                            aria-describedby={fieldErrors.email ? "email-error" : undefined}
                            disabled={submitting}
                            autoFocus
                        />
                        {fieldErrors.email && (
                            <p className="field-error" id="email-error">{fieldErrors.email}</p>
                        )}
                    </div>

                    <div className="auth-field">
                        <label htmlFor="password">Password</label>
                        <div className="password-wrapper">
                            <input
                                id="password"
                                type={showPassword ? "text" : "password"}
                                autoComplete="current-password"
                                placeholder="Enter your password"
                                value={password}
                                onChange={(event) => setPassword(event.target.value)}
                                aria-invalid={Boolean(fieldErrors.password)}
                                aria-describedby={fieldErrors.password ? "password-error" : undefined}
                                disabled={submitting}
                            />
                            <button
                                type="button"
                                className="toggle-password"
                                onClick={() => setShowPassword((visible) => !visible)}
                                aria-label={showPassword ? "Hide password" : "Show password"}
                                aria-pressed={showPassword}
                            >
                                {showPassword ? "Hide" : "Show"}
                            </button>
                        </div>
                        {fieldErrors.password && (
                            <p className="field-error" id="password-error">{fieldErrors.password}</p>
                        )}
                    </div>

                    <button type="submit" className="auth-submit" disabled={submitting}>
                        {submitting ? (
                            <>
                                <span className="button-spinner" aria-hidden="true" />
                                Signing in...
                            </>
                        ) : (
                            "Sign in"
                        )}
                    </button>

                </form>

                <p className="auth-switch">
                    First time here? <Link to="/admin/register">Register as Admin</Link>
                </p>

            </div>

        </main>
    );
}

export default AdminLogin;
