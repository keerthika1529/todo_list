# Import necessary libraries
import fastapi
from fastapi.responses import HTMLResponse,RedirectResponse
from pydantic import BaseModel
import pymongo
from pymongo import MongoClient
from fastapi import FastAPI, Form, Request
from fastapi.templating import Jinja2Templates
import os
from dotenv import load_dotenv
from passlib.context import CryptContext

from fastapi.responses import HTMLResponse

#Load environment variables from a .env file
load_dotenv()
 

#Creates a FastAPI app instance
app = FastAPI()

# Creating an instance of CryptContext for password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Function to hash a password
def hash_password(password: str):
    return pwd_context.hash(password)

def verify_password(password: str, hashed_password: str):
    return pwd_context.verify(password, hashed_password)

# Authentication part
# Function to get user details based on email from the MongoDB collection
def get_user(email: str):
    Existing_mail = collection1.find_one({'Email': email})
    if not Existing_mail:
        return False
    else:
        return Existing_mail

# Function to authenticate a user based on username (email) and password
def authenticate_user(username: str, password: str):
    user = get_user(username)
    if not user:
        return False
    if not verify_password(password, user["Password"]):
        return False
    return user


#Retrieve MongoDB connection URI from environment variables
mongo_uri=os.getenv("mongo_uri")


#Connect to MongoDB with the retrieved uri
mongodb_connection = MongoClient(mongo_uri)


#Select MongoDB database and collections
database = mongodb_connection["Todo_list"]
collection=database["Tasks"]
collection1=database["signup"]


#Initialize templates for HTML rendering
templates = Jinja2Templates(directory="templates")

#Pydantic model for Task
class Task(BaseModel):                               
    task_date: str
    task_description: str
    task_deadline:str
    task_status: str
    email:str
    
#Pydantic model for Signup
class Signup(BaseModel):                               
    UserName: str
    Email: str
    Password: str
    Confirm_Password: str
    role:str='user'

#global variables
# Variables to track state across requests
create=0
delete=0
update=0
login=0
mail=""
Role=""

# POST request to create a task with date,time,description and status
@app.post("/todo_list")
def add_task(request:Request,date:str=Form(...),description:str=Form(...),deadline:str=Form(...),status:str=Form(...)):
    try:
        global create
        data=Task(task_date=date,task_description=description,task_deadline=deadline,task_status=status,email=mail)
        #To store the date, time, description and status in mongodb
        task_record= collection.insert_one(dict(data))
        create=1
        return RedirectResponse("/todo_list",status_code=303)
    except Exception as e:
        return e
    
 # GET request to display tasks  
@app.get("/todo_list", response_class=HTMLResponse)
def display(request: Request):
    try:
        global create
        global delete
        global update
        global login
        global Role
        # Check if the user is logged in
        if login==0:
            data= collection.find({"email": mail})#get the data with the provided email
            all_data=list(data)
            admindata = collection.find()
            admimsdata = list(admindata)   
            if Role=="admin":
                return templates.TemplateResponse("admin.html", {"request": request,"data":admimsdata,"email":mail})
            elif create==1:
                create=0
                #to display successfully task added message
                return templates.TemplateResponse("frontend.html", {"request": request,"data":all_data,"email":mail,"message": "Task Added successfully"})
            elif delete==1:
                delete=0
                 #to display successfully task deleted message
                return templates.TemplateResponse("frontend.html", {"request": request,"data":all_data,"email":mail,"message": "Task deleted Successfully"})
            elif update==1:
                update=0    
                #to display successfully task updated message
                return templates.TemplateResponse("frontend.html", {"request": request,"data":all_data,"email":mail,"message": "Task updated successfully"})
            else:          
                return templates.TemplateResponse("frontend.html", {"request": request,"data":all_data,"email":mail})
        else:
            return RedirectResponse("/login", status_code=303)
    except Exception as e:
        return e
    
    
 # POST request to delete a task                                                                                                                                                                   
@app.post("/delete", response_class=HTMLResponse)
def delete(request: Request,date:str=Form(...),description:str=Form(...),status:str=Form(...)):
    try:
        global delete
        #delete the time,date,description and status related to the logged in person
        delete_data=collection.delete_one({"task_date":date,"task_description":description,"task_status":status})
        delete=1
        return RedirectResponse("/todo_list",status_code=303)
    except Exception as e:
        return e 
    
    
# POST request to update a task                                                                                                                                                                                                
@app.post("/update", response_class=HTMLResponse)
def update_task(request: Request, date: str = Form(...), deadline: str = Form(...), description: str = Form(...),
                status: str = Form(...), new_status: str = Form(...)):
    try:
        global update
        #updates task status related to the logged in person
        collection.update_one(
            {"task_date": date, "task_deadline": deadline, "task_description": description, "task_status": status},
            {"$set": {"task_status": new_status}}
        )
        update=1
        return RedirectResponse("/todo_list", status_code=303)
    except Exception as e:
        return e
    
    
#GET request to render the signup page
@app.get("/", response_class=HTMLResponse)
def signup(request: Request):
    return templates.TemplateResponse("signup.html", {"request": request})


 #GET request to render the login page
@app.get("/login", response_class=HTMLResponse)
def login(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})


 #POST request for user registration
@app.post("/", response_class=HTMLResponse)
def post_signup(request: Request, name: str = Form(...), email: str = Form(...), password: str = Form(...), confirmpassword: str = Form(...)):
   # Check if the email already exists in the signup collection
    existing_user = collection1.find_one({"Email": email})
    hashed_password = hash_password(password)
    if existing_user:
        return templates.TemplateResponse("signup.html", {"request": request, "message":"Email Already exists!"})
        # Check if the passwords match
    elif password != confirmpassword:
        return templates.TemplateResponse("signup.html", {"request": request, "message":"password doesn't match!"})
    data = Signup(UserName=name, Email=email, Password=hashed_password, Confirm_Password=hashed_password)
       # Insert user data into the signup collection
    user_record = collection1.insert_one(dict(data))
    return RedirectResponse("/login", status_code=303)


#POST request for user login
@app.post("/login", response_class=HTMLResponse)
def verify_user(request: Request, email: str = Form(...), password: str = Form(...)):
    global mail
    global login
    global Role
    try:
        user= authenticate_user(email,password)
        existing_user = collection1.find_one({"Email": email})
         # Check if the provided email and password match a user in the signup collection
        if user:
            login=0
            mail=email
            Role=existing_user['role']
            return RedirectResponse("/todo_list", status_code=303)
        else:
            login=1
            return templates.TemplateResponse("login.html",{"request": request, "message":"Invalid Email or Password!"})
    except Exception:
        raise Exception(status_code=500, detail="Internal Server Error")


#POST request to logout from the task page
@app.post("/logout",response_class=HTMLResponse)
def logout(request:Request):
    global login
    login=1
    return RedirectResponse("/login",status_code=303)

@app.get("/admin", response_class=HTMLResponse)
def admin(request: Request):
    return templates.TemplateResponse("admin.html", {"request": request})
