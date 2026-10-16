import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";

import { useAuth } from "../context/AuthContext";
import { adminApi, getErrorMessage } from "../services/api";

const EMAIL_PATTERN = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

// Same rules as the backend (the backend is the one that really enforces them)
const passwordProblem = (value) => {
    if (value.length < 8) return "Use at least 8 characters.";
    if (new TextEncoder().encode(value).length > 72) return "Use at most 72 characters.";
    if (!/[a-z]/.test(value)) return "Add a lowercase letter.";
    if (!/[A-Z]/.test(value)) return "Add an uppercase letter.";
    if (!/\d/.test(value)) return "Add a number.";
    return "";
};

function AdminRegister() {

    const navigate = useNavigate();
    const { setNotice } = useAuth();

    const [form, setForm] = useState({
        full_name: "",
        email: "",
        password: "",
        confirm_password: "",
        invite_code: "",
    });
    const [showPassword, setShowPassword] = useState(false);
    const [fieldErrors, setFieldErrors] = useState({});
    const [error, setError] = useState("");
    const [submitting, setSubmitting] = useState(false);

    const update = (field) => (event) =>
        setForm((current) => ({ ...current, [field]: event.target.value }));

    const validate = () => {
        const errors = {};

        if (form.full_name.trim().length < 2) {
            errors.full_name = "Enter your full name.";
        }

        if (!form.email.trim()) {
            errors.email = "Enter your email address.";
        } else if (!EMAIL_PATTERN.test(form.email.trim())) {
            errors.email = "Enter a valid email address.";
        }

        const problem = passwordProblem(form.password);
        if (problem) {
            errors.password = problem;
        }

        if (!form.confirm_password) {
            errors.confirm_password = "Confirm your password.";
        } else if (form.password !== form.confirm_password) {
            errors.confirm_password = "Passwords do not match.";
        }

        if (!form.invite_code.trim()) {
            errors.invite_code = "Enter the invitation code you were given.";
        }

        return errors;
    };

    const handleSubmit = async (event) => {

        event.preventDefault();

        if (submitting) {
            return;
        }

        const errors = validate();
        setFieldErrors(errors);
        setError("");

        if (Object.keys(errors).length > 0) {
            return;
        }

        setSubmitting(true);

        try {
            await adminApi.register({
                ...form,
                full_name: form.full_name.trim(),
                email: form.email.trim(),
                invite_code: form.invite_code.trim(),
            });

            setNotice("Admin account created. Sign in to continue.");
            navigate("/admin/login", { replace: true });

        } catch (err) {
            setError(getErrorMessage(err, "Unable to create the account. Please try again."));
            setSubmitting(false);
        }
    };

    const field = (id, label, props = {}) => (
        <div className="auth-field">
            <label htmlFor={id}>{label}</label>
            <input
                id={id}
                value={form[id]}
                onChange={update(id)}
                aria-invalid={Boolean(fieldErrors[id])}
                aria-describedby={fieldErrors[id] ? `${id}-error` : undefined}
                disabled={submitting}
                {...props}
            />
            {fieldErrors[id] && (
                <p className="field-error" id={`${id}-error`}>{fieldErrors[id]}</p>
            )}
        </div>
    );

    return (

        <main className="auth-page">

            <div className="auth-card">

                <div className="auth-brand">
                    <div className="logo" aria-hidden="true">🎓</div>
                    <div>
                        <h1>Create admin account</h1>
                        <span>An invitation code is required</span>
                    </div>
                </div>

                {error && (
                    <div className="error-message" role="alert">
                        ⚠ {error}
                    </div>
                )}

                <form onSubmit={handleSubmit} noValidate>

                    {field("full_name", "Full name", { type: "text", autoComplete: "name", autoFocus: true })}

                    {field("email", "Email", { type: "email", autoComplete: "username" })}

                    <div className="auth-field">
                        <label htmlFor="password">Password</label>
                        <div className="password-wrapper">
                            <input
                                id="password"
                                type={showPassword ? "text" : "password"}
                                autoComplete="new-password"
                                value={form.password}
                                onChange={update("password")}
                                aria-invalid={Boolean(fieldErrors.password)}
                                aria-describedby="password-hint"
                                disabled={submitting}
                            />
                            <button
                                type="button"
                                className="toggle-password"
                                onClick={() => setShowPassword((visible) => !visible)}
                                aria-label={showPassword ? "Hide passwords" : "Show passwords"}
                                aria-pressed={showPassword}
                            >
                                {showPassword ? "Hide" : "Show"}
                            </button>
                        </div>
                        <p
                            className={fieldErrors.password ? "field-error" : "field-hint"}
                            id="password-hint"
                        >
                            {fieldErrors.password || "At least 8 characters with upper case, lower case and a number."}
                        </p>
                    </div>

                    {field("confirm_password", "Confirm password", {
                        type: showPassword ? "text" : "password",
                        autoComplete: "new-password",
                    })}

                    {field("invite_code", "Invitation code", { type: "password", autoComplete: "off" })}

                    <button type="submit" className="auth-submit" disabled={submitting}>
                        {submitting ? (
                            <>
                                <span className="button-spinner" aria-hidden="true" />
                                Creating account...
                            </>
                        ) : (
                            "Create account"
                        )}
                    </button>

                </form>

                <p className="auth-switch">
                    Already registered? <Link to="/admin/login">Back to sign in</Link>
                </p>

            </div>

        </main>
    );
}

export default AdminRegister;
