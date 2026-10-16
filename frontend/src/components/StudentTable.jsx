// StudentTable: shows all students in a table, or a message when there are none
// Props (data received from the parent component):
//   students -> the list of student objects to display
//   onEdit   -> function to call when the Edit button is clicked
//   onDelete -> function to call when the Delete button is clicked
//   onView   -> function to call when the View button is clicked
function StudentTable({
    students,
    onEdit,
    onDelete,
    onView
}) {

    // EMPTY STATE: if the list has no students, show a friendly message
    // and stop here (return ends the function, so the table below is skipped)
    if (students.length === 0) {

        return (
            <div className="empty-state">

                {/* Big icon above the message */}
                <div className="empty-icon">
                    🎓
                </div>

                <h3>
                    No students found
                </h3>

                <p>
                    Add your first student to get started.
                </p>

            </div>
        );
    }

    // TABLE: runs only when there is at least one student
    return (
        // Container lets the table scroll sideways on small screens
        <div className="table-container">

            <table>

                {/* TABLE HEADER: column names */}
                <thead>

                    <tr>
                        <th>ID</th>
                        <th>Name</th>
                        <th>Age</th>
                        <th>Course</th>
                        <th>Actions</th>
                    </tr>

                </thead>

                {/* TABLE BODY: one row for each student */}
                <tbody>

                    {/* map() loops through the students list and creates a row for each one */}
                    {students.map((student) => (

                        // key helps React track each row; it must be unique, so we use the id
                        <tr key={student.id}>

                            {/* ID column */}
                            <td>
                                <span className="student-id">
                                    #{student.id}
                                </span>
                            </td>

                            {/* NAME column: avatar circle + full name */}
                            <td>

                                <div className="student-name">

                                   

                                    <span>
                                        {student.name}
                                    </span>

                                </div>

                            </td>

                            {/* AGE column */}
                            <td>
                                {student.age}
                            </td>

                            {/* COURSE column: shown as a small badge */}
                            <td>

                                <span className="course-badge">
                                    {student.course}
                                </span>

                            </td>

                            {/* ACTIONS column: view, edit and delete buttons */}
                            <td>

                                <div className="action-buttons">

                                    {/* VIEW: sends the whole student object to the parent */}
                                    <button
                                        className="view-button"
                                        onClick={() =>
                                            onView(student)
                                        }
                                        title="View"
                                    >
                                        👁
                                    </button>

                                    {/* EDIT: sends the whole student object so the form can be filled */}
                                    <button
                                        className="edit-button"
                                        onClick={() =>
                                            onEdit(student)
                                        }
                                        title="Edit"
                                    >
                                        ✏️
                                    </button>

                                    {/* DELETE: sends only the id, which is enough to delete */}
                                    <button
                                        className="delete-button"
                                        onClick={() =>
                                            onDelete(student.id)
                                        }
                                        title="Delete"
                                    >
                                        🗑️
                                    </button>

                                </div>

                            </td>

                        </tr>

                    ))}

                </tbody>

            </table>

        </div>
    );
}

// Export so other files (like App.jsx) can use this component
export default StudentTable;