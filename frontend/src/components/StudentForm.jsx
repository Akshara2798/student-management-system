// Import React hooks: useState stores values, useEffect runs code when something changes
import "./StudentForm.css";
import { useEffect, useState } from "react";

// StudentForm: a popup form used for both adding and editing a student
// Props (data received from the parent component):
//   selectedStudent -> the student being edited (null when adding a new one)
//   onSubmit        -> function to call with the form data when the form is saved
//   onCancel        -> function to call when the form should close
//   saving          -> true while the request is running (disables the buttons)
//   error           -> error text to show inside the popup (empty when there is none)
function StudentForm({
    selectedStudent,
    onSubmit,
    onCancel,
    saving = false,
    error = ""
}) {

    // State: one variable for each input box (starts empty)
    const [name, setName] = useState("");
    const [age, setAge] = useState("");
    const [course, setCourse] = useState("");

    // Runs whenever selectedStudent changes
    useEffect(() => {

        if (selectedStudent) {

            // EDIT MODE: fill the boxes with the selected student's details
            setName(selectedStudent.name);
            setAge(selectedStudent.age);
            setCourse(selectedStudent.course);

        } else {

            // ADD MODE: clear all the boxes
            setName("");
            setAge("");
            setCourse("");

        }

    }, [selectedStudent]);

    // Runs when the form is submitted
    const handleSubmit = (event) => {

        // Stop the browser from reloading the page
        event.preventDefault();

        // Ignore a second click while the first request is still running
        if (saving) {
            return;
        }

        // Collect the values into one object
        // Number(age) converts the text from the input into a number, as the API expects
        const studentData = {
            name: name.trim(),
            age: Number(age),
            course: course.trim()
        };

        // Send the data to the parent component, which calls the API
        onSubmit(studentData);
    };

    return (
        // Dark background that covers the page behind the popup
        <div className="modal-overlay">

            {/* White form box in the center */}
            <div className="student-form">

                {/* HEADER: title, subtitle and close button */}
                <div className="form-header">

                    <div>
                        {/* Title changes based on edit or add mode */}
                        <h2>
                            {selectedStudent
                                ? "Edit Student"
                                : "Add New Student"}
                        </h2>

                        {/* Subtitle changes based on edit or add mode */}
                        <p>
                            {selectedStudent
                                ? "Update student information"
                                : "Enter student information"}
                        </p>
                    </div>

                    {/* Close (×) button: closes the popup */}
                    <button
                        type="button"
                        className="close-button"
                        onClick={onCancel}
                        disabled={saving}
                        aria-label="Close"
                    >
                        ×
                    </button>

                </div>

                {/* FORM: handleSubmit runs when the user clicks the submit button */}
                {error && (
                    <div className="error-message" role="alert">
                        ⚠ {error}
                    </div>
                )}

                <form onSubmit={handleSubmit}>

                    {/* Name field */}
                    <div className="form-group">

                        <label htmlFor="student-name">
                            Student Name
                        </label>

                        {/* value + onChange keep the input in sync with the state */}
                        <input
                            id="student-name"
                            type="text"
                            maxLength={100}
                            placeholder="Enter student name"
                            value={name}
                            onChange={(event) =>
                                setName(event.target.value)
                            }
                            required
                        />

                    </div>

                    {/* Age field (number only, minimum 1) */}
                    <div className="form-group">

                        <label htmlFor="student-age">
                            Age
                        </label>

                        <input
                            id="student-age"
                            type="number"
                            max="120"
                            placeholder="Enter age"
                            value={age}
                            onChange={(event) =>
                                setAge(event.target.value)
                            }
                            min="1"
                            required
                        />

                    </div>

                    {/* Course field */}
                    <div className="form-group">

                        <label htmlFor="student-course">
                            Course
                        </label>

                        <input
                            id="student-course"
                            type="text"
                            maxLength={100}
                            placeholder="Enter course"
                            value={course}
                            onChange={(event) =>
                                setCourse(event.target.value)
                            }
                            required
                        />

                    </div>

                    {/* BUTTONS: cancel and submit */}
                    <div className="form-actions">

                        {/* type="button" so it does NOT submit the form */}
                        <button
                            type="button"
                            className="cancel-button"
                            onClick={onCancel}
                            disabled={saving}
                        >
                            Cancel
                        </button>

                        {/* type="submit" triggers handleSubmit; the text changes by mode */}
                        <button
                            type="submit"
                            className="submit-button"
                            disabled={saving}
                        >
                            {saving
                                ? "Saving..."
                                : selectedStudent
                                    ? "Update Student"
                                    : "Add Student"}
                        </button>

                    </div>

                </form>

            </div>

        </div>
    );
}

// Export so other files (like App.jsx) can use this component
export default StudentForm;