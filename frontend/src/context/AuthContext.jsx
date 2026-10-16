import { createContext, useCallback, useContext, useEffect, useMemo, useRef, useState } from "react";

import { adminApi, setUnauthorizedHandler } from "../services/api";

const AuthContext = createContext(null);

export function AuthProvider({ children }) {

    // admin = the logged-in admin object, or null
    const [admin, setAdmin] = useState(null);

    // true until the first "who am I?" check finishes (stops flicker and wrong redirects)
    const [checking, setChecking] = useState(true);

    // One-time message shown on the login page ("You have been logged out successfully.")
    const [notice, setNotice] = useState("");

    const checkStarted = useRef(false);

    // Restore the session after a browser refresh: the cookie is sent automatically
    useEffect(() => {

        if (checkStarted.current) {
            return; // avoids a duplicate request in React StrictMode (development)
        }
        checkStarted.current = true;

        adminApi
            .me()
            .then(setAdmin)
            .catch(() => setAdmin(null))
            .finally(() => setChecking(false));

    }, []);

    // Any protected request that returns 401 logs the user out of the UI
    useEffect(() => {

        setUnauthorizedHandler(() => {
            setAdmin((current) => {
                if (current) {
                    setNotice("Your session has expired. Please sign in again.");
                }
                return null;
            });
        });

        return () => setUnauthorizedHandler(null);

    }, []);

    const login = useCallback(async (email, password) => {
        const data = await adminApi.login(email, password);
        setNotice("");
        setAdmin(data.admin);
        return data.admin;
    }, []);

    const logout = useCallback(async () => {
        try {
            await adminApi.logout();   // server revokes the token and clears the cookie
        } catch {
            // even if the request fails, the UI must not stay logged in
        }
        setAdmin(null);
        setNotice("You have been logged out successfully.");
    }, []);

    const value = useMemo(
        () => ({ admin, checking, notice, setNotice, login, logout }),
        [admin, checking, notice, login, logout]
    );

    return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export const useAuth = () => {
    const context = useContext(AuthContext);
    if (!context) {
        throw new Error("useAuth must be used inside <AuthProvider>");
    }
    return context;
};
