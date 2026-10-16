
import axios from "axios";

// API configuration.
// Vite can proxy /api requests to your FastAPI backend.
const api = axios.create({
    baseURL: import.meta.env.VITE_API_URL || "/api",
    withCredentials: true,
    timeout: 15000,
});

// AuthContext can register a handler for expired sessions.
let unauthorizedHandler = null;

export const setUnauthorizedHandler = (handler) => {
    unauthorizedHandler = handler;
};

// These requests should handle their own 401 responses.
const AUTH_URLS = [
    "/admin/login",
    "/admin/register",
    "/admin/logout",
    "/admin/me",
];

api.interceptors.response.use(
    (response) => response,

    (error) => {
        const url = error.config?.url || "";

        const isAuthCall = AUTH_URLS.some(
            (path) => url.startsWith(path)
        );

        if (
            error.response?.status === 401 &&
            !isAuthCall &&
            unauthorizedHandler
        ) {
            unauthorizedHandler();
        }

        return Promise.reject(error);
    }
);

// Convert Axios and FastAPI errors into readable messages.
export const getErrorMessage = (
    error,
    fallback = "Something went wrong. Please try again."
) => {
    if (error?.code === "ERR_CANCELED") {
        return "";
    }

    // Backend is unavailable, network failed, or request timed out.
    if (!error?.response) {
        if (error?.message === "Network Error") {
            return "Cannot reach the server. Check that FastAPI is running and the Vite proxy is configured.";
        }

        if (error?.code === "ECONNABORTED") {
            return "The request timed out. Please try again.";
        }

        return error?.message || fallback;
    }

    const { status, data } = error.response;

    if (status >= 500) {
        return "Server error. Please check the FastAPI backend logs.";
    }

    const detail = data?.detail;

    if (typeof detail === "string") {
        return detail;
    }

    // FastAPI validation errors.
    if (Array.isArray(detail) && detail.length > 0) {
        return detail
            .map((item) =>
                String(item.msg || "Invalid input").replace(
                    /^Value error, /,
                    ""
                )
            )
            .filter(Boolean)
            .join(". ");
    }

    if (status === 401) {
        return "Your session has expired. Please log in again.";
    }

    if (status === 403) {
        return "You do not have permission to perform this action.";
    }

    if (status === 404) {
        return "The requested resource was not found. Check the API endpoint.";
    }

    return fallback;
};

// Admin authentication API methods.
export const adminApi = {
    register: (payload) =>
        api.post("/admin/register", payload).then((response) => response.data),

    login: (email, password) =>
        api
            .post("/admin/login", { email, password })
            .then((response) => response.data),

    logout: () =>
        api.post("/admin/logout").then((response) => response.data),

    me: () =>
        api.get("/admin/me").then((response) => response.data),
};

export default api;
