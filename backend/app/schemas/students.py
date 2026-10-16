from pydantic import BaseModel, ConfigDict, Field


class StudentCreate(BaseModel):

    # Limits match the database columns, so bad input gives a clean 422 instead of a 500
    model_config = ConfigDict(str_strip_whitespace=True)

    name: str = Field(min_length=1, max_length=100)
    age: int = Field(ge=1, le=120)
    course: str = Field(min_length=1, max_length=100)


'''StudentResponse is for the data your API sends back. 
StudentCreate checks what comes in, and StudentResponse controls what goes out.
Converts the database object to JSON. Your function returns a SQLAlchemy Student object. FastAPI can't send that directly, 
so StudentResponse reads id, name, age, and course from it. That's why from_attributes = True is there '''
class StudentResponse(BaseModel):

    id: int
    name: str
    age: int
    course: str

    model_config = ConfigDict(from_attributes=True)
