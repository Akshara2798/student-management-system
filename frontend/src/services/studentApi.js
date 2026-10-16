
import api from "./api";

// GET /students/?search=...
export const getStudents = async ({ search = "", signal } = {}) => {
    const params = search.trim()
        ? { search: search.trim() }
        : undefined;

    const response = await api.get("/students/", {
        params,
        signal,
    });

    return response.data;
};

// GET /students/{id}
export const getStudent = async (studentId) => {
    const response = await api.get(`/students/${studentId}`);
    return response.data;
};

// POST /students/
export const createStudent = async (studentData) => {
    const response = await api.post("/students/", studentData);
    return response.data;
};

// PUT /students/{id}
export const updateStudent = async (studentId, studentData) => {
    const response = await api.put(
        `/students/${studentId}`,
        studentData
    );

    return response.data;
};

// DELETE /students/{id}
export const deleteStudent = async (studentId) => {
    const response = await api.delete(`/students/${studentId}`);
    return response.data;
};
