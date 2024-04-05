from fastapi import FastAPI, HTTPException, Query, Path, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from uuid import UUID, uuid4
from motor.motor_asyncio import AsyncIOMotorClient
from typing import Optional 




app = FastAPI()  


# Address Schema
class Address(BaseModel):
    city: str
    country: str 

# Student Schema 
class Student(BaseModel):
    name: str
    age: int = Field(..., gt=0)  # Only +ve Age 
    address: Address



# MongoDB connection setup
MONGODB_URL = "mongodb+srv://amanrana9133:Aman1n1@cluster0.6ohqxgo.mongodb.net/students_db?retryWrites=true&w=majority"  # Update with your MongoDB connection URL
client = AsyncIOMotorClient(MONGODB_URL)
db = client["students_db"]  # Db name
collection = db["students"]  # Collection name




# GET Method
@app.get("/students/", status_code=status.HTTP_201_CREATED)
async def list_students(country: Optional[str] = Query(None),
                        age: Optional[int] = Query(None)):

    # Building filter criteria based on provided query param
    filter_criteria = {}
    if country:
        filter_criteria["address.country"] = country
    if age is not None:
        filter_criteria["age"] = {"$gte": age}

    # Querying the MongoDB collection with the filter criteria
    students = await collection.find(filter_criteria).to_list(None)

    # Formatting res data
    formatted_students = [{"name": student["name"], "age": student["age"], "address": student["address"]} for student in students]

    return {"data": formatted_students}



# GET Method (with specigic Id)
@app.get("/students/{id}", response_model=Student)
async def fetch_student(id: UUID = Path(...)):
   
    id_str = str(id)     # Converting UUID to string
    
    student = await collection.find_one({"_id":  id_str})

    # If student is not found, raise HTTPException with status code 404
    if student is None:
        raise HTTPException(status_code=404, detail="Student not found")

     # Convert MongoDB document to Student model
    return Student(**student)



# POST Method 
@app.post("/students/", status_code=201)
async def create_student(student: Student):
    # Create a new student document
    new_student_id = str(uuid4())

    new_student_data = {
        "_id": new_student_id,
        "name": student.name,
        "age": student.age,   
        "address": student.address.dict()
    }

    # Insert the new student document into the MongoDB collection
    await collection.insert_one(new_student_data)

    return new_student_data



# PATCH Method
@app.patch("/students/{id}", status_code=204) 
async def update_student(id: UUID = Path(...), student: Student = None):

    # Converting UUID to string
    id_str = str(id) 

    # Construct the update dictionary
    update_dict = {}
    if student is not None:
        if student.name is not None:
            update_dict["name"] = student.name
        if student.age is not None:
            update_dict["age"] = student.age
        if student.address is not None:
            if student.address.country is not None:
                update_dict["address.country"] = student.address.country
            if student.address.city is not None:
                update_dict["address.city"] = student.address.city

    # Updating student in Db
    result = await collection.update_one({"_id": id_str}, {"$set": update_dict})

    # Means Student is not found
    if result.modified_count == 0:   
        raise HTTPException(status_code=404, detail="Student not found")
    
    # If successfully updated, we get 204 status code
    return {"message": "Student updated successfully"}                



# DELETE Method 
@app.delete("/students/{id}")
async def delete_student(id: UUID = Path(...)):
    
    id_str = str(id)

    # Check if the student exists
    existing_student = await collection.find_one({"_id": id_str})
    if existing_student is None:
        raise HTTPException(status_code=404, detail="Student not found")

    # Delete the student from the database
    await collection.delete_one({"_id": id_str})
    return {"message": "Student deleted successfully"}





if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)   # It will listen on http://localhost:8000
