import datetime
import os

from bson import ObjectId
from flask import Flask, request, render_template, session, redirect

import pymongo
my_collections = pymongo.MongoClient("mongodb://localhost:27017/")
my_db = my_collections['carPooling']
admin_col = my_db['Admin']
user_col = my_db['User']
vehicle_col = my_db['Vehicle']
bookings_col = my_db['Bookings']
schedule_col = my_db['Schedule']
payments_col = my_db['Payments']

app = Flask(__name__)
app.secret_key = "car"

App_Root = os.path.dirname(__file__)
App_Root = App_Root + "/static"

status_schedule_added = "Schedule Added by Driver"
status_seat_booked = "Seats Booked by Rider"
status_rejected_by_driver = "Booking rejected by Driver"
status_accepted_by_driver = "Booking Accepted by Driver"
status_ride_starts = "Ride Started"
status_transaction_successful = "Transaction Successful"
status_amount_hold = "Amount Should be Hold"
status_ride_completed = "Ride Completed"
status_cancelled_by_rider = "Booking Cancelled by Rider"


@app.route("/")
def userLogin():
    return render_template("userLogin.html")


@app.route("/userLogin1", methods=['post'])
def userLogin1():
    email = request.form.get('email')
    password = request.form.get('password')
    type = request.form.get("type")
    query = {"email": email, "password": password, "type": type}
    count = user_col.count_documents(query)
    if count > 0:
        user = user_col.find_one(query)
        session['user_id'] = str(user['_id'])
        session['type'] = user['type']
        return redirect("/home")
    else:
        return render_template("msg.html", message="Invalid Login Details", color="bg-danger text-white")


@app.route("/home")
def home():
    user_id = session['user_id']
    query = {"_id": ObjectId(user_id)}
    user = user_col.find_one(query)
    return render_template("home.html", user=user)


@app.route("/userRegistration")
def userRegistration():
    return render_template("userRegistration.html")


@app.route("/userRegistration1", methods=['post'])
def userRegistration1():
    name = request.form.get('name')
    phone = request.form.get('phone')
    email = request.form.get('email')
    password = request.form.get('password')
    gender = request.form.get('gender')
    type = request.form.get('type')

    image = request.files.get("image")
    path = App_Root + "/image/" + image.filename
    image.save(path)
    query = {"name": name, "phone": phone, "email": email, "password": password, "gender": gender, "type": type, "image": image.filename}
    user_col.insert_one(query)
    return redirect("/")


@app.route("/add_vehicle")
def add_vehicle():
    return render_template("add_vehicle.html")


@app.route("/add_vehicle1", methods=['post'])
def add_vehicle1():
    user_id = session['user_id']
    vehicle_name = request.form.get('vehicle_name')
    vehicle_number = request.form.get('vehicle_number')
    vehicle_type = request.form.get('vehicle_type')
    vehicle_capacity = request.form.get('vehicle_capacity')
    query = {"vehicle_number": vehicle_number}
    count = vehicle_col.count_documents(query)
    if count > 0:
        return render_template("msg.html", message="Duplicate Vehicle Details", color="bg-danger text-white")
    else:
        query = {"user_id": ObjectId(user_id), "vehicle_name": vehicle_name, "vehicle_number": vehicle_number, "vehicle_type": vehicle_type, "vehicle_capacity": vehicle_capacity}
    vehicle_col.insert_one(query)
    return redirect("/view_vehicle")


@app.route("/view_vehicle")
def view_vehicle():
    user_id = session['user_id']
    query = {"user_id": ObjectId(user_id)}
    vehicles = vehicle_col.find(query)
    vehicles = list(vehicles)
    if len(vehicles) == 0:
        return render_template("msg.html", message="Vehicles Not Available", color="text-danger")
    return render_template("view_vehicle.html", vehicles=vehicles, get_user_id=get_user_id)


def get_user_id(user_id):
    query = {"_id": ObjectId(user_id)}
    user = user_col.find_one(query)
    return user


def get_user_id_by_vehicle(vehicle_id):
    query = {"_id": ObjectId(vehicle_id)}
    vehicle = vehicle_col.find_one(query)
    user_id = vehicle['user_id']
    query = {"_id": ObjectId(user_id)}
    user = user_col.find_one(query)
    return user


@app.route("/add_schedule")
def add_schedule():
    vehicle_id = request.args.get("vehicle_id")
    query ={"_id": ObjectId(vehicle_id)}
    vehicle = vehicle_col.find_one(query)
    vehicle_capacity = vehicle['vehicle_capacity']
    return render_template("add_schedule.html", vehicle_id=vehicle_id, vehicle_capacity=vehicle_capacity)


@app.route("/add_schedule1", methods=['post'])
def add_schedule1():
    vehicle_id = request.form.get("vehicle_id")
    source = request.form.get("source")
    destination = request.form.get("destination")

    start_date_time = request.form.get("start_date_time")
    end_date_time = request.form.get("end_date_time")
    start_date_time = start_date_time.replace("T", " ")
    end_date_time = end_date_time.replace("T", " ")
    start_date_time = datetime.datetime.strptime(start_date_time, '%Y-%m-%d %H:%M')
    end_date_time = datetime.datetime.strptime(end_date_time, '%Y-%m-%d %H:%M')
    if start_date_time > end_date_time:
        return render_template("msg.html", message="Invalid End Date Time", color="text-danger")
    ride_type = request.form.get("ride_type")
    distance = request.form.get("distance")
    no_of_seats = request.form.get("no_of_seats")
    occupied_seats = 0
    price = request.form.get("price")
    description = request.form.get("description")
    status = status_schedule_added
    query = {"vehicle_id": ObjectId(vehicle_id), "source": source, "destination": destination, "start_date_time": start_date_time, "end_date_time": end_date_time, "ride_type": ride_type, "distance": distance, "no_of_seats": no_of_seats, "occupied_seats": occupied_seats, "price": price, "description": description, "status": status}
    schedule_col.insert_one(query)
    return redirect("/view_schedule")


@app.route("/view_schedule")
def view_schedule():
    query = {}
    if session['type'] == "Driver":
        user_id = session['user_id']
        query = {"user_id": ObjectId(user_id)}
        vehicles = vehicle_col.find(query)
        vehicle_ids = []
        for vehicle in vehicles:
            vehicle_ids.append({"vehicle_id": vehicle['_id']})
        if len(vehicle_ids) == 0:
            return render_template("msg.html", message="Schedules Not Available", color="text-danger")
        query = {"$or": vehicle_ids}
    elif session['type'] == "Rider":
        today = datetime.datetime.now()
        query = {"start_date_time": {"$gte": today}}
    schedules = schedule_col.find(query)
    schedules = list(schedules)
    if len(schedules) == 0:
        return render_template("msg.html", message="Schedules Not Available", color="text-danger")
    return render_template("view_schedule.html", status_seat_booked=status_seat_booked, schedules=schedules, get_seats_by_schedule_id=get_seats_by_schedule_id, get_vehicle_id=get_vehicle_id, int=int, status_schedule_added=status_schedule_added, str=str)


def get_vehicle_id(vehicle_id):
    query = {"_id": ObjectId(vehicle_id)}
    vehicle = vehicle_col.find_one(query)
    return vehicle


@app.route("/book_seats")
def book_seats():
    schedule_id = request.args.get("schedule_id")
    query = {"_id": ObjectId(schedule_id)}
    schedule = schedule_col.find_one(query)
    no_of_seats = schedule['no_of_seats']
    occupied_seats = schedule['occupied_seats']
    available_seats = int(no_of_seats)-int(occupied_seats)
    return render_template("book_seats.html", schedule_id=schedule_id, available_seats=available_seats)


@app.route("/book_seats1", methods=['post'])
def book_seats1():
    user_id = session['user_id']
    schedule_id = request.form.get("schedule_id")
    query = {"_id": ObjectId(schedule_id)}
    schedule = schedule_col.find_one(query)
    occupied_seats = schedule['occupied_seats']
    pick_up_location = request.form.get("pick_up_location")
    status = status_seat_booked
    booked_seats = request.form.get("booked_seats")
    persons = []
    for i in range(1, int(booked_seats) + 1):
        name = request.form.get("name" + str(i))
        persons.append({"name": name})

    query = {"user_id": ObjectId(user_id), "schedule_id": ObjectId(schedule_id), "pick_up_location": pick_up_location, "booked_seats": booked_seats, "persons": persons, "status": status}
    bookings_col.insert_one(query)

    query = {"_id": ObjectId(schedule_id)}
    query1 = {"$set": {"status": status_seat_booked}}
    schedule_col.update_one(query, query1)
    return redirect("/view_booking?schedule_id="+str(schedule_id))


def get_seats_by_schedule_id(schedule_id):
    query = {"_id": ObjectId(schedule_id)}
    schedule = schedule_col.find_one(query)
    no_of_seats = schedule['no_of_seats']
    occupied_seats = schedule['occupied_seats']
    if int(no_of_seats) == int(occupied_seats):
        return True
    else:
        return False


@app.route("/view_booking")
def view_booking():
    query = {}
    if session['type'] == "Driver":
        schedule_id = request.args.get("schedule_id")
        query = {"schedule_id": ObjectId(schedule_id)}
    elif session['type'] == "Rider":
        user_id = session['user_id']
        query = {"user_id": ObjectId(user_id)}
    bookings = bookings_col.find(query)
    return render_template("view_booking.html", status_accepted_by_driver=status_accepted_by_driver, bookings=bookings, int=int,  get_schedule_id=get_schedule_id, get_user_id=get_user_id, get_booking_by_schedule_vehicle_id=get_booking_by_schedule_vehicle_id, status_seat_booked=status_seat_booked, status_ride_starts=status_ride_starts)


@app.route("/accept_booking")
def accept_booking():
    booking_id = request.args.get("booking_id")
    schedule_id = request.args.get("schedule_id")
    query = {"_id": ObjectId(booking_id)}
    booking = bookings_col.find_one(query)
    booked_seats = booking['booked_seats']
    query = {"_id": ObjectId(schedule_id)}
    schedule = schedule_col.find_one(query)
    occupied_seats = schedule['occupied_seats']
    no_of_seats = schedule['no_of_seats']
    available_seats = int(no_of_seats) - int(occupied_seats)
    if int(available_seats) >= int(booked_seats):
        query = {"_id": ObjectId(booking_id)}
        query1 = {"$set": {"status": status_accepted_by_driver}}
        bookings_col.update_one(query, query1)
        query = {"_id": ObjectId(schedule_id)}
        query1 = {"$set": {"occupied_seats": int(occupied_seats) + int(booked_seats)}}
        schedule_col.update_one(query, query1)

    else:
        booking_id = request.args.get("booking_id")
        query = {'_id': ObjectId(booking_id)}
        query1 = {"$set": {"status": status_rejected_by_driver}}
        bookings_col.update_one(query, query1)
        return render_template("msg.html", message="InSufficient Seats So Remaining Seats Rejected", color="text-danger")

    schedule = schedule_col.find_one({"_id": ObjectId(schedule_id)})
    if int(schedule['no_of_seats'])-int(schedule['occupied_seats']) == 0:
        query = {'schedule_id': ObjectId(schedule_id), "status": status_seat_booked}
        query1 = {"$set": {"status": status_rejected_by_driver}}
        bookings_col.update_many(query, query1)
    return redirect("/view_booking?schedule_id=" + str(schedule_id))


@app.route("/reject_booking")
def reject_booking():
    booking_id = request.args.get("booking_id")
    schedule_id = request.args.get("schedule_id")
    query = {'_id': ObjectId(booking_id)}
    query1 = {"$set": {"status": status_rejected_by_driver}}
    bookings_col.update_one(query, query1)
    return redirect("/view_booking?schedule_id="+str(schedule_id))


def get_schedule_id(schedule_id):
    query = {"_id": ObjectId(schedule_id)}
    schedule = schedule_col.find_one(query)
    return schedule


def get_booking_by_schedule_vehicle_id(schedule_id):
    query = {"_id": ObjectId(schedule_id)}
    schedule = schedule_col.find_one(query)
    vehicle_id = schedule['vehicle_id']
    query = {"_id": ObjectId(vehicle_id)}
    vehicle = vehicle_col.find_one(query)
    user_id = vehicle['user_id']
    query = {"_id": ObjectId(user_id)}
    driver = user_col.find_one(query)
    return vehicle, driver


@app.route("/driver_details")
def driver_details():
    schedule_id = request.args.get("schedule_id")
    query = {"_id": ObjectId(schedule_id)}
    schedule = schedule_col.find_one(query)
    vehicle_id = schedule['vehicle_id']
    query = {"_id": ObjectId(vehicle_id)}
    vehicle = vehicle_col.find_one(query)
    user_id = vehicle['user_id']
    query = {"_id": ObjectId(user_id)}
    user = user_col.find_one(query)
    return render_template("driver_details.html", user=user)


@app.route("/rider_details")
def rider_details():
    booking_id = request.args.get("booking_id")
    query = {"_id": ObjectId(booking_id)}
    booking = bookings_col.find_one(query)
    user_id = booking['user_id']
    query = {"_id": ObjectId(user_id)}
    user = user_col.find_one(query)
    return render_template("rider_details.html", user=user)


@app.route("/vehicle_details")
def vehicle_details():
    schedule_id = request.args.get("schedule_id")
    query = {"_id": ObjectId(schedule_id)}
    schedule = schedule_col.find_one(query)
    vehicle_id = schedule['vehicle_id']
    query = {"_id": ObjectId(vehicle_id)}
    vehicle = vehicle_col.find_one(query)
    return render_template("vehicle_details.html", vehicle=vehicle)


@app.route("/pay_amount")
def pay_amount():
    booking_id = request.args.get("booking_id")
    query = {"_id": ObjectId(booking_id)}
    booking = bookings_col.find_one(query)
    price = request.args.get("price")
    schedule_id = booking['schedule_id']
    query = {"_id": ObjectId(schedule_id)}
    schedule = schedule_col.find_one(query)
    start_date_time = schedule['start_date_time']
    end_date_time = schedule['end_date_time']
    delta = end_date_time - start_date_time
    days = delta.days
    if days == 0:
        amount = price
    else:
        price = schedule['price']
        amount = int(price) * days
    return render_template("pay_amount.html", booking_id=booking_id, amount=amount)


@app.route("/pay_amount1", methods=['post'])
def pay_amount1():
    booking_id = request.form.get("booking_id")
    query = {"_id": ObjectId(booking_id)}
    booking = bookings_col.find_one(query)
    schedule_id = booking['schedule_id']
    amount = request.form.get("amount")
    card_number = request.form.get("card_number")
    holder_name = request.form.get("holder_name")
    date = datetime.datetime.now()
    status = status_amount_hold
    query = {"booking_id": ObjectId(booking_id), "amount": amount, "card_number": card_number, "holder_name": holder_name, "date": date, "status": status}
    payments_col.insert_one(query)

    query = {"_id": ObjectId(booking_id)}
    query1 = {"$set": {"status": status_ride_starts, "amount_status": status_amount_hold}}
    bookings_col.update_one(query, query1)
    return redirect("/view_booking")


@app.route("/view_payments")
def view_payments():
    query = {}
    if session['type'] == "Driver":
        user_id = session['user_id']
        query = {"user_id": ObjectId(user_id)}
        vehicles = vehicle_col.find(query)
        vehicle_ids = []
        for vehicle in vehicles:
            vehicle_ids.append({"vehicle_id": vehicle['_id']})
        if len(vehicle_ids) == 0:
            return render_template("msg.html", message="Payments Not Available", color="text-danger")
        query = {"$or": vehicle_ids}
        schedules = schedule_col.find(query)
        schedule_ids = []
        for schedule in schedules:
            schedule_ids.append({"schedule_id": schedule['_id']})
        if len(schedule_ids) == 0:
            return render_template("msg.html", message="Payments Not Available", color="text-danger")
        query = {"$or": schedule_ids}
        bookings = bookings_col.find(query)
        booking_ids = []
        for booking in bookings:
            booking_ids.append({"booking_id": booking['_id']})
        if len(booking_ids) == 0:
            return render_template("msg.html", message="Payments Not Available", color="text-danger")
        query = {"$or": booking_ids}
        payments = payments_col.find(query)
        payments_ids = []
        for payment in payments:
            payments_ids.append({"_id": payment['_id']})
        if len(payments_ids) == 0:
            return render_template("msg.html", message="Payments Not Available", color="text-danger")
        query = {"$or": payments_ids}
    elif session['type'] == "Rider":
        user_id = session['user_id']
        query = {"user_id": ObjectId(user_id)}
        bookings = bookings_col.find(query)
        booking_ids = []
        for booking in bookings:
            booking_ids.append({"booking_id": booking['_id']})
        if len(booking_ids) == 0:
            return render_template("msg.html", message="Payments Not Available", color="text-danger")
        query = {"$or": booking_ids}
    payments = payments_col.find(query)
    return render_template("view_payments.html", payments=payments, get_booking_payment_id=get_booking_payment_id)


def get_booking_payment_id(booking_id):
    query = {"_id": ObjectId(booking_id)}
    booking = bookings_col.find_one(query)
    schedule_id = booking['schedule_id']
    query = {"_id": ObjectId(schedule_id)}
    schedule = schedule_col.find_one(query)
    vehicle_id = schedule['vehicle_id']
    query = {"_id": ObjectId(vehicle_id)}
    vehicle = vehicle_col.find_one(query)
    user_id = vehicle['user_id']
    query = {"_id": ObjectId(user_id)}
    driver = user_col.find_one(query)
    return driver


@app.route("/cancel_booking")
def cancel_booking():
    booking_id = request.args.get("booking_id")
    query = {"_id": ObjectId(booking_id)}
    booking = bookings_col.find_one(query)
    booked_seats = booking['booked_seats']
    schedule_id = request.args.get("schedule_id")
    query = {"_id": ObjectId(schedule_id)}
    schedule = schedule_col.find_one(query)
    occupied_seats = schedule['occupied_seats']
    if booking['status'] == "Seats Booked by Rider":
        query = {'_id': ObjectId(booking_id)}
        query1 = {"$set": {"status": status_cancelled_by_rider}}
        bookings_col.update_one(query, query1)
    elif booking['status'] == "Booking Accepted by Driver":
        query = {'_id': ObjectId(booking_id)}
        query1 = {"$set": {"status": status_cancelled_by_rider}}
        bookings_col.update_one(query, query1)
        query = {'_id': ObjectId(schedule_id)}
        query1 = {"$set": {"occupied_seats": int(occupied_seats) - int(booked_seats)}}
        schedule_col.update_one(query, query1)
    return redirect("/view_booking")


@app.route("/complete_booking")
def complete_booking():
    booking_id = request.args.get("booking_id")
    schedule_id = request.args.get("schedule_id")
    query = {'_id': ObjectId(booking_id)}
    query1 = {"$set": {"status": status_ride_completed}}
    bookings_col.update_one(query, query1)

    query = {"booking_id": ObjectId(booking_id)}
    payment = payments_col.find_one(query)
    payment_id = payment['_id']
    query = {'_id': ObjectId(payment_id)}
    query1 = {"$set": {"status": status_transaction_successful}}
    payments_col.update_one(query, query1)
    return redirect("/view_booking?schedule_id=" + str(schedule_id))


@app.route("/logout")
def logout():
    session.clear()
    return render_template("userLogin.html")


app.run(debug=True)