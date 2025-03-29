from django.shortcuts import render, redirect
from django.http import HttpResponse, JsonResponse
from django.contrib import messages
from django.core.mail import *
from django.conf import settings
from pymongo import MongoClient
import bcrypt
import random
from .models import Camps,Task 
import json # Ensure Camp model is properly defined
from django.views.decorators.csrf import csrf_exempt
from datetime import date,datetime,time
import logging

# MongoDB connection
client = MongoClient("mongodb://localhost:27017/")
db = client["reliefcamp"]  # Change to your database name
users_collection = db["users"]
volunteer_collection=db["volunteers"]
district_collection = db["districts"]
camp_collection = db["camps"]
task_collection = db["tasks"]
coordinator_collection=db["coordinators"]
item_collection=db["inventory"]
request_collection=db["requests"]
donor_collection=db["donor"]
#
# Helper function to generate a unique user ID
def generate_unique_uid():
    while True:
        uid = f"UID{random.randint(1000000, 9999999)}"
        if not users_collection.find_one({"userId": uid}):  # Check if UID already exists
            return uid
        
def generate_unique_donorid():
    while True:
        did=f"D{random.randint(100000,999999)}"
        if not donor_collection.find_one({"donorId":did}):
            return did
        
def generate_unique_taskid():
    while True:
        taskid=f"T{random.randint(1000,9999)}"
        if not task_collection.find_one({"taskId":taskid}):
            return taskid
        
def generate_unique_itemid():
    while True:
        itemid=f"ID{random.randint(1000,9999)}"
        if not task_collection.find_one({"itemId":itemid}):
            return itemid
        
def generate_unique_reqid():
    while True:
        reqid=f"RID{random.randint(1000,9999)}"
        if not request_collection.find_one({"requestId":reqid}):
            return reqid
        
def calculate_age(dob):
    today = date.today()
    dob_date = date.fromisoformat(dob)  # Assuming dob is in 'YYYY-MM-DD' format
    age = today.year - dob_date.year - ((today.month, today.day) < (dob_date.month, dob_date.day))
    return age

# Home view
def home(request):
    
    return render(request,'App/home.html')

# Volunteer login view
def volunteerlogin(request):
    if request.method == "POST":
        userId = request.POST['userId']
        pass1 = request.POST['pass1']

        # Custom authentication logic for MongoDB
        user = users_collection.find_one({"userId": userId})
        if user and bcrypt.checkpw(pass1.encode('utf-8'), user['password'].encode('utf-8')):
            # Log the user in (you can use Django sessions or custom logic)
            name = " "+user["first_name"] + " " + user["last_name"]
            request.session['user_id'] = user['userId']
            return render(request,'App/volunteer2.html',{"name":name,"userid":" "+userId})  # Redirect to volunteer dashboard
        else:
            messages.error(request, "Bad Credentials!")
            return redirect('volunteerlogin')

    return render(request, "App/volunteerlogin.html")

# Volunteer dashboard view
def volunteer(request):
    if 'user_id' not in request.session:
        return redirect('volunteerlogin')
    return render(request, "App/volunteer1.html")

# Volunteer registration view
def volunteerreg(request):
    if request.method == "POST":
        # Retrieve all form fields
        fname = request.POST['fname']
        lname = request.POST['lname']
        dob = request.POST['dob']
        gender=request.POST['gender']
        email = request.POST['email']
        pass1 = request.POST['pass1']
        pass2 = request.POST['pass2']
        ph = request.POST['ph']
        addr = request.POST['addr']
        place = request.POST['place']
        district = request.POST['district']
        state = request.POST['state']
        pincode = request.POST['pincode']
        camp_name = request.POST['campName']  # Get the selected camp name from the form

        # Validate passwords
        #if pass1 != pass2:
        #    messages.error(request, "Passwords do not match!")
        #    return redirect('volunteerreg')

        # Hash the password for security
        hashed_password = bcrypt.hashpw(pass1.encode('utf-8'), bcrypt.gensalt())

        # Check if email already exists
        #if users_collection.find_one({"email": email}):
        #    messages.error(request, "Email already registered!")
        #    return redirect('volunteerreg')

        # Check if the selected camp exists and has volunteerNeeded > 0
        #camp = Camps.objects.filter(name=camp_name, volunteerNeeded__gt=0).first()
        #if not camp:
        #    messages.error(request, "Selected camp is not available or no volunteers needed.")
        #    return redirect('volunteerreg')

        # Generate a unique user ID
        user_id = generate_unique_uid()
        age=calculate_age(dob)

        # Prepare user data with all fields
        user_data = {
            "userId": user_id,
            "first_name": fname,
            "last_name": lname,
            "dob": dob,
            "age":age,
            "gender":gender,
            "email": email,
            "password": hashed_password.decode('utf-8'),  # Store hashed password
            "phone": ph,
            "address": addr,
            "place": place,
            "district": district,
            "state": state,
            "pincode": pincode,
            "camp_name": camp_name  # Store the camp name with the user
        }

        # Insert user data into MongoDB
        users_collection.insert_one(user_data)
        volunteer_collection.insert_one(user_data)

        camp = camp_collection.find_one({"name": camp_name}, {"_id": 0, "volunteerNeeded": 1,"volunteerPresent":1})

        if camp and "volunteerNeeded" in camp and camp["volunteerNeeded"] > 0:
             camp_collection.update_one(
            {"name": camp_name},
            {"$inc": {"volunteerNeeded": -1,"volunteerPresent":1}}  # Decrement volunteerNeeded by 1
    )
        # Decrement volunteerNeeded for the selected camp
        #camp.volunteerNeeded -= 1
        #camp.save()

        # Send success message
        messages.success(request, "Your account has been successfully created.")

        # Send welcome email
        subject = "Welcome to Sahayahastam Volunteer Login!!"
        message1 = (
            f"Hello {fname}!!\n"
            "Welcome to Sahayahastam!!\n\n"
            "Thank you for visiting the website.\n"
            "You have been successfully registered as a volunteer.\n\n"
            f"Your User ID: {user_id}\n"
            #f"Your Password: {pass1}\n"
            "Use the User ID and your password to log in to our website.\n\n"
            "Thank you for your participation!"
        )
        from_email = settings.EMAIL_HOST_USER
        to_email = [email]
        send_mail(subject, message1, from_email, to_email, fail_silently=False)

        return redirect('volunteerlogin')
    return render(request, "App/volunteerreg2.html")

@csrf_exempt
def validate_volunteer(request):
    if request.method != "POST":
        return JsonResponse({"error": "Invalid request method"}, status=405)  # 405 Method Not Allowed

    try:
        # ✅ Handle empty body safely
        if not request.body:
            return JsonResponse({"error": "Empty request body"}, status=400)

        data = json.loads(request.body.decode("utf-8"))

        userid = data.get("userid")
        pass1 = data.get("pass")

        if not userid or not pass1:
            return JsonResponse({"error": "Missing userid or password"}, status=400)

        # Default response
        response = {"user": "notok", "passw": "notok"}

        # Fetch user details in a single query
        user_record = volunteer_collection.find_one({"userId": userid}, {"password": 1})

        if user_record:
            response["user"] = "ok"
            hashed_password = user_record.get("password")  # Retrieve hashed password from DB

            if hashed_password and bcrypt.checkpw(pass1.encode("utf-8"), hashed_password.encode("utf-8")):
                response["passw"] = "ok"

        return JsonResponse({"resp": response})

    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON format"}, status=400)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


# Fetch districts for dropdown
def get_districts(request):
    districts = list(district_collection.find({}, {"_id": 0, "name": 1}))  # Fetch only names
    return JsonResponse({"districts": districts})

# Fetch camps for search suggestions
def get_camps(request):
    query = request.GET.get('query', '').lower()
    filter_query = {
        "volunteerNeeded": {"$gt": 0},  # Only camps with volunteerNeeded > 0
        "name": {"$regex": query, "$options": "i"}  # Case-insensitive search for camp names
    }
    #camps = Camps.objects.filter(volunteerNeeded__gt=0, name__icontains=query)
    #camp_list = [{'name': camp.name} for camp in camps]
    camp_list=list(camp_collection.find(filter_query,{"_id":0,"name":1}))
    return JsonResponse({'camps': camp_list})

def get_tasks(request):
    #user_id = request.session.get("user_id")
    user_id=request.session['user_id']
    task_list=list(task_collection.find({"volunteerId":user_id},{"_id":0,"taskId":1,"volunteerId":1,"type":1,"address":1,"time":1,"desc":1,"status":1}))
    #tasks = Task.objects.filter(volunteerId=user_id).values('taskId', 'desc', 'status', 'volunteerId')
    #task_list=list(tasks)
    return JsonResponse({'taskls':task_list})

# def update_task_status(request):
#     if request.method == 'POST':
#         try:
#             # Parse the request body
            
#             taskId=request.POST['taskID']
#             # Find the task by taskId and update its status
#             task_collection.update_one({"taskId":taskId},{"$set":{"status":"Completed"}})
#             # Save the updated task to MongoDB

#             # Return success response
           

#         except Exception as e:
#             # Handle errors
#             return JsonResponse({'message': f'Error updating task status: {str(e)}'}, status=500)

#     else:
#         return JsonResponse({'message': 'Invalid request method'}, status=405)
@csrf_exempt
def update_task_status(request):
    if request.method == 'POST':
        try:
            # Parse the JSON data from request
            data = json.loads(request.body)
            taskId = data.get('taskId')  # Get taskId from request body

            # Ensure taskId is provided
            if not taskId:
                return JsonResponse({'message': 'Task ID is required'}, status=400)

            # Find the task and update its status
            result = task_collection.update_one(
                {"taskId": taskId},  # Find by taskId
                {"$set": {"status": "Completed"}}  # Update status
            )

            # Check if the task was actually updated
            if result.matched_count == 0:
                return JsonResponse({'message': 'Task not found'}, status=404)

            return JsonResponse({
                'message': 'Task status updated successfully',
                'taskId': taskId,
                'status': 'Completed'
            })

        except json.JSONDecodeError:
            return JsonResponse({'message': 'Invalid JSON data'}, status=400)
        except Exception as e:
            return JsonResponse({'message': f'Error updating task status: {str(e)}'}, status=500)

    else:
        return JsonResponse({'message': 'Invalid request method'}, status=405)
    
# def supplytrack(request):
#     return render(request,"App/supplytrack.html")
# @csrf_exempt
# def get_supply_status(request):
#     if request.method=='POST':
#         try:
#             data=json.loads(request.body)
#             taskId=data.get('TaskId')
            
#             if not taskId:
#                 return JsonResponse({'message': 'Task ID is required'}, status=400)

#             result=task_collection.find({'taskId':taskId},{'_id':0,'taskId':1,'status':1})

#             return JsonResponse({'result':result})
#         except Exception as e:
#             return JsonResponse({'message': f'Error updating task status: {str(e)}'}, status=500)
#     else:
#         return JsonResponse({'message': 'Invalid request method'}, status=405)

@csrf_exempt
def get_task_progress(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            task_id = data.get("taskId")
            if not task_id:
                return JsonResponse({"error": "Task ID is required"}, status=400)
            
            result = task_collection.find_one({'taskId': task_id}, {'_id': 0, 'status': 1})
            
            if result is None:
                return JsonResponse({"error": "Task not found"}, status=404)
            
            return JsonResponse({"status": result.get("status")}, status=200)
        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid JSON"}, status=400)
    return JsonResponse({"error": "Invalid request"}, status=400)


@csrf_exempt
def set_task_progress(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            task_id = data.get("taskId")
            new_status = data.get("status")

            if not task_id or new_status is None:
                return JsonResponse({"error": "Task ID and status are required"}, status=400)

            result = task_collection.update_one({'taskId': task_id}, {"$set": {"status": new_status}})

            if result.matched_count == 0:
                return JsonResponse({'error': 'Task not found'}, status=404)

            return JsonResponse({"message": "Task updated successfully", "status": new_status}, status=200)
        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid JSON"}, status=400)
    return JsonResponse({"error": "Invalid request"}, status=400)

def addtask(request):
    camp_name=request.session['camp_name']
    return render(request,'App/addtask.html',{'camp_name':camp_name})

@csrf_exempt
def get_volunteers(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            #campName = data.get('campName')
            campName=request.session['camp_name']
            if not campName:
                return JsonResponse({"error": "campName is required"}, status=400)
            volunteer_list = list(users_collection.find({'camp_name':campName},{'_id':0,'userId':1, 'first_name': 1,'last_name':1, 'gender': 1, 'age': 1}))
            return JsonResponse({'volunteerls': volunteer_list}, safe=False)
        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid JSON"}, status=400)
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)
        
# Coordinator login view
# def coordinatorlogin(request):
#     if request.method == "POST":
#         userId = request.POST['userId']
#         pass1 = request.POST['pass1']

#         # Custom authentication logic for MongoDB
#         user = coordinator_collection.find_one({"userId": userId})
#         if user and bcrypt.checkpw(pass1.encode('utf-8'), user['password'].encode('utf-8')):
#             # Log the user in (you can use Django sessions or custom logic)
#             name = " "+user["first_name"] + " " + user["last_name"]
#             # request.session['user_id'] = user['userId']
#             camp_id=user["camp_id"]
#             camp=camp_collection.find_one({"campId":camp_id})
#             camp_name=camp["name"]
#             return render(request,'App/coordinator.html',{"name":name,"camp_id":" "+camp_id,"camp_name":camp_name})  # Redirect to coordinator dashboard
#         else:
#             messages.error(request, "Bad Credentials!")
#             return redirect('coordinatorlogin')

#     return render(request, "App/coordinatorlogin.html")



def coordinatorlogin(request):
    if request.method == "POST":
        userId = request.POST.get('userId')
        pass1 = request.POST.get('pass1')

        if not userId or not pass1:
            messages.error(request, "User ID and password are required!")
            return redirect('coordinatorlogin')

        try:
            # Fetch coordinator details from MongoDB
            user = coordinator_collection.find_one({"userId": userId})
            if user and bcrypt.checkpw(pass1.encode('utf-8'), user['password'].encode('utf-8')):
                # Fetch camp details and related data using an aggregation pipeline
                camp_id = user.get("camp_id")
                if not camp_id:
                    messages.error(request, "Camp ID not found for this coordinator!")
                    return redirect('coordinatorlogin')
                
                request.session['user_id'] = userId
                request.session['camp_id']=camp_id
                cname=camp_collection.find_one({"campId":camp_id},{"_id":0,"cname":1})
                request.session['camp_name']=cname

                

                # Store coordinator's userId in the session
                
                return render(request, 'App/coordinator.html',{'camp_name':cname})
            else:
                messages.error(request, "Invalid credentials!")
                return redirect('coordinatorlogin')
        except Exception as e:
            messages.error(request, f"An error occurred: {str(e)}")
            return redirect('coordinatorlogin')

    return render(request, "App/coordinatorlogin.html")


# def validate_coordinator(request):
#     data=json.loads(request.body)
#     userid=data.get("userid")
#     pass1=data.get("pass")
#     user='notok'
#     passw='notok'
#     pass2=coordinator_collection.find_one({"userId":userid})
#     if pass2:
#         user="ok"
#         if bcrypt.checkpw(pass1.encode("utf-8"),pass2.encode("utf-8")):
#             passw="ok"
#     res={"user":user,"passw":passw}
#     return JsonResponse({"resp":res})
@csrf_exempt
def validate_coordinator(request):
    if request.method != "POST":
        return JsonResponse({"error": "Invalid request method"}, status=405)  # 405 Method Not Allowed

    try:
        # ✅ Handle empty body safely
        if not request.body:
            return JsonResponse({"error": "Empty request body"}, status=400)

        data = json.loads(request.body.decode("utf-8"))

        userid = data.get("userid")
        pass1 = data.get("pass")

        if not userid or not pass1:
            return JsonResponse({"error": "Missing userid or password"}, status=400)

        # Default response
        response = {"user": "notok", "passw": "notok"}

        # Fetch user details in a single query
        user_record = coordinator_collection.find_one({"userId": userid}, {"password": 1})

        if user_record:
            response["user"] = "ok"
            hashed_password = user_record.get("password")  # Retrieve hashed password from DB

            if hashed_password and bcrypt.checkpw(pass1.encode("utf-8"), hashed_password.encode("utf-8")):
                response["passw"] = "ok"

        return JsonResponse({"resp": response})

    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON format"}, status=400)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


logger = logging.getLogger(__name__)

def loadcoordinator(request):
    try:
        # Retrieve session data
        camp_id = request.session.get('camp_id')
        user_id = request.session.get('user_id')

        if not camp_id or not user_id:
            logger.error("Session data missing: camp_id or user_id not found.")
            return JsonResponse({"error": "Session data missing. Please log in again."}, status=400)

        # Fetch camp data using an aggregation pipeline
        pipeline = [
            {
                "$match": {"campId": camp_id}
            },
            {
                "$lookup": {
                    "from": "tasks",
                    "localField": "campId",
                    "foreignField": "campId",
                    "as": "tasks"
                }
            },
            {
                "$lookup": {
                    "from": "volunteers",
                    "localField": "cname",
                    "foreignField": "camp_name",
                    "as": "volunteers"
                }
            },
            {
                "$project": {
                    "cname": 1,
                    "campId": 1,
                    "occupants": 1,
                    "capacity": 1,
                    "volunteersPresent": 1,
                    "tasks": {
                        "taskId": 1,
                        "status": 1,
                        "volunteerId": 1
                    },
                    "volunteers": {
                        "userId": 1,
                        "first_name": 1,
                        "last_name": 1,
                        "gender": 1,
                        "age": 1
                    }
                }
            }
        ]

        # Execute the aggregation pipeline
        camp_data = list(camp_collection.aggregate(pipeline))
        if not camp_data:
            logger.error(f"No camp data found for camp_id: {camp_id}")
            return JsonResponse({"error": "Camp data not found!"}, status=404)

        camp_data = camp_data[0]  # Since we are matching by campId, there should be only one result
        request.session['camp_name']=camp_data.get('cname')
        # Fetch user data
        user =users_collection.find_one({"userId": user_id})
        if not user:
            logger.error(f"User not found for user_id: {user_id}")
            return JsonResponse({"error": "User data not found!"}, status=404)

        # Calculate statistics
        total_people = camp_data.get("occupants", 0)
        capacity = camp_data.get("capacity", 1)  # Default to 1 to avoid division by zero
        occupancy_percent = round((total_people / capacity) * 100, 2) if capacity > 0 else 0

        # Prepare data for the template
        context = {
            "name": f"{user.get('first_name', '')} {user.get('last_name', '')}",
            "camp_id": camp_id,
            "camp_name": camp_data.get("cname", ""),
            "total_people": total_people,
            "capacity": capacity,
            "occupancy_percent": occupancy_percent,
            "total_volunteers": len(camp_data.get("volunteers", [])),
            "total_tasks": len(camp_data.get("tasks", [])),
            "pending_tasks": len([task for task in camp_data.get("tasks", []) if task.get("status") == "Pending"]),
            "completed_tasks": len(camp_data.get("tasks", [])) - len([task for task in camp_data.get("tasks", []) if task.get("status") == "Pending"]),
            "tasks": camp_data.get("tasks", []),
            "volunteers": camp_data.get("volunteers", [])
        }

        return JsonResponse({'context': context})
    except Exception as e:
        logger.error(f"An error occurred in loadcoordinator: {str(e)}", exc_info=True)
        return JsonResponse({"error": f"An error occurred: {str(e)}"}, status=500)



def insertcoord(request):
    user_id = generate_unique_uid()
    pass1="pass@123"
    hashed_password = bcrypt.hashpw(pass1.encode('utf-8'), bcrypt.gensalt())

    user_data = {
            "userId": user_id,
            "first_name": "Raphael",
            "last_name": "Coord",
            "password": hashed_password.decode('utf-8'),  # Store hashed password
            "camp_id": "CMP237"  # Store the camp name with the user
        }
    users_collection.insert_one(user_data)
    coordinator_collection.insert_one(user_data)
        
def coordinator(request):

    return render(request,'App/coordinator.html')
        
@csrf_exempt        
def insert_task(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            task_id = generate_unique_taskid()
            status="Pending"
            desc=data.get("desc")
            type=data.get('type')
            campId=request.session['camp_id']
            
            userId=data.get('userid')

            if type=='supply':
                address=data.get('address')
                time1=data.get('time')
                time="1999-02-02T"+time1+":00Z"
                task_data = {
                    "taskId": task_id,
                    "volunteerId":userId,
                    "campId":campId,
                    "type": type,
                    "desc": desc,
                    "address":address,
                    "time":time,
                    "status":status,
                }
            else:
                task_data = {
                    "taskId": task_id,
                    "volunteerId":userId,
                    "campId":campId,
                    "type": type,
                    "desc": desc,
                    #"deadline":
                    "status":status,
                }

            result=task_collection.insert_one(task_data)

           
            return JsonResponse({"message": "Task inseryed successfully", }, status=200)
        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid JSON"}, status=400)
    return JsonResponse({"error": "Invalid request"}, status=400)

def campinventory(request):
    return render(request,"App/campinventory.html")

@csrf_exempt
def get_inventory(request):
    camp_id = request.session['camp_id']
    items = list(item_collection.find({"campId": camp_id}, {'_id': 0, 'itemName': 1, 'category': 1, 'quantity': 1, 'itemDesc': 1, 'itemId': 1}))
    return JsonResponse({'itemsList': items})

@csrf_exempt
def add_item(request):
    if request.method == "POST":
        data = json.loads(request.body)
        #task_id = data.get("taskId")
        camp_id = request.session['camp_id']
        new_item = {
            "itemId": generate_unique_itemid(),  # Implement this function
            "campId": camp_id,
            "itemName": data.get("itemName"),
            "category": data.get("category"),
            "quantity": data.get("quantity"),
            "itemDesc": data.get("itemDesc"),
        }
        item_collection.insert_one(new_item)
        return JsonResponse(new_item,status=201)
    return JsonResponse({"error": "Invalid request"}, status=400)

@csrf_exempt
def update_item(request):
    if request.method == "PUT":
        data = json.loads(request.body)
        itemId=data.get("itemId")
        item_collection.update_one({"itemId": itemId}, {"$set": data})
        updated_item = item_collection.find_one({"itemId": itemId}, {'_id': 0})
        return JsonResponse(updated_item)
    return JsonResponse({"error": "Invalid request"}, status=400)

@csrf_exempt
def delete_item(request):
    if request.method == "DELETE":
        data=json.loads(request.body)
        itemId=data.get("itemId")
        item_collection.delete_one({"itemId": itemId})
        return JsonResponse({"success": True})
    return JsonResponse({"error": "Invalid request"}, status=400)

def people(request):
    return render(request,"App/people.html")

def camprequest(request):
    return render(request,"App/camprequest.html")

def addrequest(request):
    return render(request,"App/addrequest.html")

@csrf_exempt
def insert_request(request):
    if request.method == "POST":
        data = json.loads(request.body)
        #task_id = data.get("taskId")
        camp_id = request.session['camp_id']
        camp=camp_collection.find_one({"campId":camp_id},{"_id":0,"address":1})
        address=camp["address"]
        coordinator_details=coordinator_collection.find_one({"camp_id":camp_id},{"_id":0,"first_name":1,"last_name":1})
        #coordname=coordinator_details.get("")
        #address=camp["address"]
        name=" "+coordinator_details['first_name']+" "+coordinator_details['last_name']
        new_request = {
            "requestId": generate_unique_reqid(),  # Implement this function
            "campId": camp_id,
            "campaddress": address,
            "time":datetime.now(),
            "itemName": data.get("itemName"),
            "category": data.get("category"),
            "quantity": data.get("quantity"),
            "itemDesc": data.get("itemDesc"),
            "status": data.get("status"),
            "coordinator_name": name,
        }
        request_collection.insert_one(new_request)
        return JsonResponse({"message":"Ok"},status=201)
    else:
        return JsonResponse({"error": "Invalid request"}, status=400)
    
def get_requests(request):
    camp_id=request.session.get('camp_id')
    #request.session['camp_id']=camp_id
    reqLs=list(request_collection.find({"campId":camp_id},{"_id":0}))
    return JsonResponse({"reqlist":reqLs})

def get_all_requests(request):
    reqLs=list(request_collection.find({},{"_id":0}))
    return JsonResponse({"reqlist":reqLs})

@csrf_exempt
def delete_request(request):
    if request.method == "DELETE":
        data=json.loads(request.body)
        requestId=data.get("requestId")
        request_collection.delete_one({"requestId": requestId})
        return JsonResponse({"success": True})
    return JsonResponse({"error": "Invalid request"}, status=400)

@csrf_exempt
def update_request(request):
    if request.method =="PUT":
        data=json.loads(request.body)
        requestId=data.get("requestId")
        request_collection.update_one({"requestId": requestId}, {"$set": data})
        updated_request = request_collection.find_one({"requestId": requestId}, {'_id': 0})
        return JsonResponse(updated_request)
    return JsonResponse({"error": "Invalid request"}, status=400)

@csrf_exempt
def append_reply(request):
    if request.method =="PUT":
        data=json.loads(request.body)
        requestId=data.get("requestId")
        camp_id=request.session.get('camp_id')
        cordata=coordinator_collection.find_one({"camp_id":camp_id})
        campdata=camp_collection.find_one({"campId":camp_id})
        name=" "+cordata['first_name']+" "+cordata['last_name']
        rqdata=request_collection.find_one({"requestId":requestId})
        newqty=rqdata['quantity']-int(data.get("quantityAvailable"))
        replyData={}
        if(data.get("responderType")=="Coordinator"):
            replyData={
                "responderType":data.get("responderType"),
                "campId":camp_id,
                "campAddress":campdata['address'],
                "coordinator_name":name,
                "coordinatorId":cordata['userId'],
                "quantityAvailable":int(data.get("quantityAvailable")),
                "replyDescription":data.get("replyDescription"),
                "phone":data.get("phone"),
                "emailId":data.get("emailId"),
                "replyTime":datetime.now()
            }
        else:
            ddata=donor_collection.find_one({"phone":data.get("phone")})
            if ddata:
                did=ddata['donorId']
            else:
                did=generate_unique_donorid()
                
            donorData={
                "donorId":did,
                "donorName":data.get("donorName"),
                "donorAddress":data.get("collectionAddress"),
                "phone":data.get("phone"),
                "emailId":data.get("emailId")
            }

            donor_collection.insert_one(donorData)

            replyData={
                "responderType":data.get("responderType"),
                "donorId":did,
                "donor_name":data.get("donorName"),
                "donorAddress":data.get("collectionAddress"),
                "quantityAvailable":int(data.get("quantityAvailable")),
                "replyDescription":data.get("replyDescription"),
                "phone":data.get("phone"),
                "emailId":data.get("emailId"),
                "replyTime":datetime.now()
        }
        request_collection.update_one({"requestId": requestId}, {"$set":{"status":"Replied"},"$set":{"quantity":newqty},"$push":{"replyDetails":replyData}})
        updated_request = request_collection.find_one({"requestId": requestId}, {'_id': 0})
        return JsonResponse(updated_request)
    return JsonResponse({"error": "Invalid request"}, status=400)
    
def donor(request):
    return render(request,"App/donor.html")