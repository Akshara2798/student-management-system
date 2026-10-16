from fastapi import APIRouter, Depends, HTTPException, Query  # Import FastAPI tools for routing, dependency injection, and errors
from sqlalchemy import func, or_                                   # func.lower() makes the search case-insensitive
from sqlalchemy.orm import Session                            # Import SQLAlchemy Session for database operations

from app.auth.dependencies import get_current_admin           # Only a logged-in admin may use these routes

from app.database import get_db                               # Import database session dependency
from app.Model.students import Student                        # Import Student database model
from app.schemas.students import StudentCreate, StudentResponse  # Import request and response schemas


router = APIRouter(                                            # Create an API router
    prefix="/students",                                        # Add /students before every route in this router
    tags=["Students"],                                         # Group these APIs under Students in Swagger
    dependencies=[Depends(get_current_admin)]                  # EVERY route below requires a valid admin session (401/403 otherwise)
)


# CREATE
@router.post(                                                  # Define a POST route for creating a student
    "/",                                                       # Route path becomes /students/
    response_model=StudentResponse                             # Return data according to StudentResponse schema
)
def create_student(                                            # Define function to create a student
    student: StudentCreate,                                    # Receive and validate student data using StudentCreate
    db: Session = Depends(get_db)                              # Get a database session using dependency injection
):

    new_student = Student(                                     # Create a new Student database object
        name=student.name,                                     # Assign the name from the request data
        age=student.age,                                       # Assign the age from the request data
        course=student.course                                  # Assign the course from the request data
    )

    db.add(new_student)                                        # Add the new student to the database session
    db.commit()                                                # Save the new student permanently in the database
    db.refresh(new_student)                                    # Get the updated database object including generated ID

    return new_student                                         # Return the newly created student


# READ ALL
@router.get(                                                   # Define a GET route for retrieving students
    "/",                                                       # Route path becomes /students/
    response_model=list[StudentResponse]                       # Return a list of students using StudentResponse schema
)
def get_students(                                              # Define function to get all students
    search: str | None = Query(None, max_length=100),          # Optional ?search=text  (name, course, or exact age)
    skip: int = Query(0, ge=0),                                # Optional paging: how many records to skip
    limit: int = Query(500, ge=1, le=1000),                    # Optional paging: maximum records to return
    db: Session = Depends(get_db)                              # Get a database session using dependency injection
):

    query = db.query(Student)                                  # Start a query on the Student table

    if search and search.strip():                              # Apply the filter only when the admin typed something
        text = search.strip().lower()
        conditions = [
            func.lower(Student.name).contains(text, autoescape=True),     # name contains the text (case-insensitive)
            func.lower(Student.course).contains(text, autoescape=True),   # course contains the text (case-insensitive)
        ]
        if text.isdigit():                                     # "21" also matches students aged 21
            conditions.append(Student.age == int(text))
        query = query.filter(or_(*conditions))

    return query.order_by(Student.id).offset(skip).limit(limit).all()   # Stable order + paging


# READ ONE
@router.get(                                                   # Define a GET route for retrieving one student
    "/{student_id}",                                           # Route path becomes /students/{student_id}
    response_model=StudentResponse                             # Return data according to StudentResponse schema
)
def get_student(                                               # Define function to get one student
    student_id: int,                                           # Receive student ID as an integer path parameter
    db: Session = Depends(get_db)                              # Get a database session using dependency injection
):

    student = db.query(Student).filter(                        # Query the Student table and apply a filter
        Student.id == student_id                               # Find the student whose ID matches the path parameter
    ).first()                                                   # Return the first matching record

    if student is None:                                        # Check whether the student was found
        raise HTTPException(                                   # Raise an HTTP error
            status_code=404,                                   # Return HTTP 404 Not Found status
            detail="Student not found"                         # Send an error message to the client
        )

    return student                                             # Return the requested student


# UPDATE
@router.put(                                                   # Define a PUT route for updating a student
    "/{student_id}",                                           # Route path becomes /students/{student_id}
    response_model=StudentResponse                             # Return the updated student using StudentResponse
)
def update_student(                                            # Define function to update a student
    student_id: int,                                           # Receive student ID from the URL
    student_data: StudentCreate,                               # Receive new student data using StudentCreate schema
    db: Session = Depends(get_db)                              # Get a database session using dependency injection
):

    student = db.query(Student).filter(                        # Query the Student table and apply a filter
        Student.id == student_id                               # Find the student whose ID matches the given ID
    ).first()                                                   # Return the first matching record

    if student is None:                                        # Check whether the student exists
        raise HTTPException(                                   # Raise an HTTP error
            status_code=404,                                   # Return HTTP 404 Not Found status
            detail="Student not found"                         # Send an error message to the client
        )

    student.name = student_data.name                           # Update the student's name
    student.age = student_data.age                             # Update the student's age
    student.course = student_data.course                       # Update the student's course

    db.commit()                                                # Save the changes to the database
    db.refresh(student)                                        # Refresh the object with the latest database values

    return student                                             # Return the updated student


# DELETE
@router.delete("/{student_id}")                                # Define a DELETE route for deleting a student
def delete_student(                                            # Define function to delete a student
    student_id: int,                                           # Receive student ID from the URL
    db: Session = Depends(get_db)                              # Get a database session using dependency injection
):

    student = db.query(Student).filter(                        # Query the Student table and apply a filter
        Student.id == student_id                               # Find the student whose ID matches the given ID
    ).first()                                                   # Return the first matching record

    if student is None:                                        # Check whether the student exists
        raise HTTPException(                                   # Raise an HTTP error
            status_code=404,                                   # Return HTTP 404 Not Found status
            detail="Student not found"                         # Send an error message to the client
        )

    db.delete(student)                                         # Mark the student for deletion
    db.commit()                                                # Permanently delete the student from the database

    return {                                                   # Return a success response
        "message": "Student deleted successfully"              # Success message sent to the client
    }