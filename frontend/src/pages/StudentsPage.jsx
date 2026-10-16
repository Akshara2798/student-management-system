
import { useCallback, useEffect, useState } from "react";

import Navbar from "../components/Navbar";
import StudentForm from "../components/StudentForm";
import StudentTable from "../components/StudentTable";
import { useAuth } from "../context/AuthContext";
import { getErrorMessage } from "../services/api";
import {
    createStudent,
    deleteStudent,
    getStudents,
    updateStudent,
} from "../services/studentApi";

function StudentsPage() {
    const { admin, logout } = useAuth();

    const [students, setStudents] = useState([]);
    const [showForm, setShowForm] = useState(false);
    const [selectedStudent, setSelectedStudent] = useState(null);
    const [search, setSearch] = useState("");
    const [loading, setLoading] = useState(true);
    const [saving, setSaving] = useState(false);
    const [loggingOut, setLoggingOut] = useState(false);
    const [error, setError] = useState("");
    const [formError, setFormError] = useState("");
    const [message, setMessage] = useState("");

    // Convert common FastAPI response formats into a student array.
    const normalizeStudents = (data) => {
        if (Array.isArray(data)) {
            return data;
        }

        if (Array.isArray(data?.students)) {
            return data.students;
        }

        if (Array.isArray(data?.data)) {
            return data.data;
        }

        if (Array.isArray(data?.items)) {
            return data.items;
        }

        if (Array.isArray(data?.results)) {
            return data.results;
        }

        console.error("Unexpected students API response:", data);

        throw new Error(
            "The backend did not return a valid student list. Check GET /students/."
        );
    };

    // Load students from FastAPI.
    const loadStudents = useCallback(async (searchText = "", signal) => {
        try {
            setError("");

            const data = await getStudents({
                search: searchText,
                signal,
            });

            if (signal?.aborted) {
                return;
            }

            const studentList = normalizeStudents(data);
            setStudents(studentList);
        } catch (err) {
            if (err?.code === "ERR_CANCELED" || signal?.aborted) {
                return;
            }

            setError(
                getErrorMessage(err, "Unable to load students.")
            );
        } finally {
            if (!signal?.aborted) {
                setLoading(false);
            }
        }
    }, []);

    // Initial load and debounced search.
    useEffect(() => {
        const controller = new AbortController();

        const timer = setTimeout(() => {
            loadStudents(search, controller.signal);
        }, search.trim() ? 300 : 0);

        return () => {
            clearTimeout(timer);
            controller.abort();
        };
    }, [search, loadStudents]);

    // Display a temporary success message.
    const showMessage = (text) => {
        setMessage(text);

        setTimeout(() => {
            setMessage("");
        }, 3000);
    };

    // Create or update a student.
    const handleSubmit = async (studentData) => {
        if (saving) {
            return;
        }

        try {
            setSaving(true);
            setFormError("");
            setError("");

            if (selectedStudent) {
                await updateStudent(selectedStudent.id, studentData);
                showMessage("Student updated successfully!");
            } else {
                await createStudent(studentData);
                showMessage("Student added successfully!");
            }

            setShowForm(false);
            setSelectedStudent(null);

            await loadStudents(search);
        } catch (err) {
            setFormError(
                getErrorMessage(
                    err,
                    "Unable to save student. Please try again."
                )
            );
        } finally {
            setSaving(false);
        }
    };

    // Delete a student.
    const handleDelete = async (studentId) => {
        const confirmed = window.confirm(
            "Are you sure you want to delete this student?"
        );

        if (!confirmed) {
            return;
        }

        try {
            setError("");

            await deleteStudent(studentId);

            showMessage("Student deleted successfully!");

            await loadStudents(search);
        } catch (err) {
            setError(
                getErrorMessage(err, "Unable to delete student.")
            );
        }
    };

    // Open the edit form.
    const handleEdit = (student) => {
        setSelectedStudent(student);
        setFormError("");
        setShowForm(true);
    };

    // View student details.
    const handleView = (student) => {
        window.alert(
            `Student Details\n\n` +
            `ID: ${student.id}\n` +
            `Name: ${student.name}\n` +
            `Age: ${student.age}\n` +
            `Course: ${student.course}`
        );
    };

    // Open the add form.
    const handleAdd = () => {
        setSelectedStudent(null);
        setFormError("");
        setShowForm(true);
    };

    // Close the form.
    const handleCancel = () => {
        if (saving) {
            return;
        }

        setShowForm(false);
        setSelectedStudent(null);
        setFormError("");
    };

    // Log out the administrator.
    const handleLogout = async () => {
        if (loggingOut) {
            return;
        }

        setLoggingOut(true);

        try {
            await logout();
        } catch (err) {
            setError(
                getErrorMessage(err, "Unable to log out. Please try again.")
            );
        } finally {
            setLoggingOut(false);
        }
    };

    // Calculate unique courses safely.
    const courseCount = new Set(
        students
            .map((student) => student?.course)
            .filter(Boolean)
    ).size;

    return (
        <div className="app">
            <Navbar
                admin={admin}
                onLogout={handleLogout}
                loggingOut={loggingOut}
            />

            <main className="main-content">
                <div className="page-header">
                    <div>
                        <p className="welcome-text">
                            Welcome back, {admin?.full_name || "Admin"}
                        </p>

                        <h1>Student Management</h1>

                        <p className="page-description">
                            Manage student records easily from one place.
                        </p>
                    </div>

                    <button
                        className="add-student-button"
                        onClick={handleAdd}
                        type="button"
                    >
                        + Add Student
                    </button>
                </div>

                {message && (
                    <div className="success-message" role="status">
                        ✓ {message}
                    </div>
                )}

                {error && (
                    <div className="error-message" role="alert">
                        ⚠ {error}
                    </div>
                )}

                <div className="stats-container">
                    <div className="stat-card">
                        <div className="stat-icon">👨‍🎓</div>

                        <div>
                            <p>
                                {search.trim()
                                    ? "Matching Students"
                                    : "Total Students"}
                            </p>
                            <h2>{students.length}</h2>
                        </div>
                    </div>

                    <div className="stat-card">
                        <div className="stat-icon">📚</div>

                        <div>
                            <p>Courses</p>
                            <h2>{courseCount}</h2>
                        </div>
                    </div>

                    <div className="stat-card">
                        <div className="stat-icon">📊</div>

                        <div>
                            <p>Records</p>
                            <h2>{students.length}</h2>
                        </div>
                    </div>
                </div>

                <section className="student-section">
                    <div className="section-header">
                        <div>
                            <h2>Students</h2>
                            <p>View and manage student records</p>
                        </div>

                        <div className="search-container">
                            <span aria-hidden="true">🔍</span>

                            <input
                                type="search"
                                placeholder="Search by name, course or age..."
                                aria-label="Search students"
                                value={search}
                                onChange={(event) =>
                                    setSearch(event.target.value)
                                }
                            />
                        </div>
                    </div>

                    {loading ? (
                        <div className="loading" role="status">
                            Loading students...
                        </div>
                    ) : (
                        <StudentTable
                            students={students}
                            onEdit={handleEdit}
                            onDelete={handleDelete}
                            onView={handleView}
                        />
                    )}
                </section>
            </main>

            {showForm && (
                <StudentForm
                    selectedStudent={selectedStudent}
                    onSubmit={handleSubmit}
                    onCancel={handleCancel}
                    saving={saving}
                    error={formError}
                />
            )}
        </div>
    );
}

export default StudentsPage;
