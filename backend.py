import fastapi
from fastapi.responses import HTMLResponse,RedirectResponse
from pydantic import BaseModel
import pymongo
from pymongo import MongoClient
from fastapi import FastAPI, Form, Request
from fastapi.templating import Jinja2Templates
import os
from dotenv import load_dotenv

load_dotenv()
 
app = FastAPI()

mongo_uri=os.getenv("mongo_uri")

mongodb_connection = MongoClient(mongo_uri)


database = mongodb_connection["Todo_list"]
collection=database["Tasks"]
collection1=database["signup"]

templates = Jinja2Templates(directory="templates")

class Task(BaseModel):                               
    task_date: str
    task_time: str
    task_description: str
    task_status: str
    email:str

class Signup(BaseModel):                               
    UserName: str
    Email: str
    Password: str
    Confirm_Password: str

create=0
delete=0
update=0
login=0
mail=""

@app.post("/todo_list")
def add_task(request:Request,date:str=Form(...),time:str=Form(...),description:str=Form(...),status:str=Form(...)):
    try:
        global create
        data=Task(task_date=date,task_time=time,task_description=description,task_status=status,email=mail)
        task_record= collection.insert_one(dict(data))
        create=1
        return RedirectResponse("/todo_list",status_code=303)
    except Exception as e:
        return e
    
@app.get("/todo_list", response_class=HTMLResponse)
def display(request: Request):
    try:
        global create
        global delete
        global update
        global login
        if login==0:
            data= collection.find({"email": mail})
            all_data=list(data)
            if create==1:
                create=0
                return templates.TemplateResponse("frontend.html", {"request": request,"data":all_data,"email":mail,"message": "Task Added successfully"})
            elif delete==1:
                delete=0
                return templates.TemplateResponse("frontend.html", {"request": request,"data":all_data,"email":mail,"message": "Task deleted Successfully"})
            elif update==1:
                update=0
                return templates.TemplateResponse("frontend.html", {"request": request,"data":all_data,"email":mail,"message": "Task updated successfully"})
            else:          
                return templates.TemplateResponse("frontend.html", {"request": request,"data":all_data,"email":mail})
        else:
            return templates.TemplateResponse("login.html", {"request": request})
    except Exception as e:
        return e
    
                                                                                                                                                                     
@app.post("/delete", response_class=HTMLResponse)
def delete(request: Request,date:str=Form(...),time:str=Form(...),description:str=Form(...),status:str=Form(...)):
    try:
        global delete
        delete_data=collection.delete_one({"task_date":date,"task_time":time,"task_description":description,"task_status":status})
        delete=1
        return RedirectResponse("/todo_list",status_code=303)
    except Exception as e:
        return e 
                                                                                                                                                                                                                                                                        
@app.post("/update", response_class=HTMLResponse)
def update_task(request: Request, date: str = Form(...), time: str = Form(...), description: str = Form(...),
                status: str = Form(...), new_status: str = Form(...)):
    try:
        global update
        collection.update_one(
            {"task_date": date, "task_time": time, "task_description": description, "task_status": status},
            {"$set": {"task_status": new_status}}
        )
        update=1
        return RedirectResponse("/todo_list", status_code=303)
    except Exception as e:
        return e
    
@app.get("/", response_class=HTMLResponse)
def signup(request: Request):
    return templates.TemplateResponse("signup.html", {"request": request})

@app.get("/login", response_class=HTMLResponse)
def login(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@app.post("/", response_class=HTMLResponse)
def post_signup(request: Request, name: str = Form(...), email: str = Form(...), password: str = Form(...), confirmpassword: str = Form(...)):
    existing_user = collection1.find_one({"Email": email})
    if existing_user:
        return templates.TemplateResponse("signup.html", {"request": request, "message":"Email Already exists!"})
    elif password != confirmpassword:
        return templates.TemplateResponse("signup.html", {"request": request, "message":"password doesn't match!"})
    data = Signup(UserName=name, Email=email, Password=password, Confirm_Password=confirmpassword)
    user_record = collection1.insert_one(dict(data))
    return RedirectResponse("/login", status_code=303)

@app.post("/login", response_class=HTMLResponse)
def verify_user(request: Request, email: str = Form(...), password: str = Form(...)):
    global mail
    global login
    try:
        existing_user = collection1.find_one({"Email": email})
        if existing_user and existing_user["Password"] == password:
            login=0
            mail=email
            return RedirectResponse("/todo_list", status_code=303)
        else:
            login=1
            return templates.TemplateResponse("login.html",{"request": request, "message":"Invalid Email or Password!"})
    except Exception:
        raise Exception(status_code=500, detail="Internal Server Error")

    
@app.post("/logout",response_class=HTMLResponse)
def logout(request:Request):
    global login
    login=1
    return RedirectResponse("/login",status_code=303)