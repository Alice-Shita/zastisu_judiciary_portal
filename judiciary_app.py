from flask import (
    Flask,
    render_template,
    request,
    redirect,
    session,
    flash,
    send_from_directory
)
import json
from werkzeug.utils import secure_filename
import os

app = Flask(
    __name__,
    template_folder="judiciary_templates",
    static_folder="judiciary_static"
)


app.secret_key = "judiciary_secret_key"
app.config["MAX_CONTENT_LENGTH"] = 5 * 1024 * 1024

UPLOAD_FOLDER = "judiciary_uploads"

app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER


os.makedirs(
    UPLOAD_FOLDER,
    exist_ok=True
)

ALLOWED_EXTENSIONS = {

    "png",
    "jpg",
    "jpeg",
    "pdf"

}


def load_users():

    with open(
        "judiciary_users.json",
        "r"
    ) as file:

        return json.load(file)

def save_users(users):

    with open("judiciary_users.json", "w") as f:

        json.dump(
            users,
            f,
            indent=4
        )

def allowed_file(filename):

    return (
        "." in filename
        and
        filename.rsplit(".", 1)[1].lower()
        in ALLOWED_EXTENSIONS
    )

def load_applications():

    with open(
        "judiciary_applications.json",
        "r"
    ) as file:

        return json.load(file)



def save_applications(applications):

    with open(
        "judiciary_applications.json",
        "w"
    ) as file:

        json.dump(
            applications,
            file,
            indent=4
        )

def load_progress():

    try:

        with open(
            "judiciary_progress.json",
            "r"
        ) as file:

            return json.load(file)


    except (
        FileNotFoundError,
        json.JSONDecodeError
    ):

        return []



def save_progress(progress):

    with open(
        "judiciary_progress.json",
        "w"
    ) as file:

        json.dump(
            progress,
            file,
            indent=4
        )



def get_applicant_progress(user_id):

    progress = load_progress()


    if user_id in progress:

        return progress[user_id]


    new_applicant = {

        "user_id": user_id,

        "personal": {},

        "academic": {},

        "answers": {},

        "documents": {},

        "status": "In Progress"

    }


    progress[user_id] = new_applicant


    save_progress(
        progress
    )


    return new_applicant

def recommend_position(answers):

    text = " ".join(
        answers.values()
    ).lower()


    scores = {

        "Chairperson": 0,

        "Vice Chairperson": 0,

        "Secretary General": 0,

        "Vice Secretary": 0,

        "Treasurer": 0,

        "Committee Member": 0

    }


    leadership = [
        "leader",
        "lead",
        "justice",
        "fair",
        "integrity",
        "discipline",
        "vision",
        "constitutional",
        "decision"
    ]

    teamwork = [
        "team",
        "support",
        "assist",
        "cooperate",
        "collaborate"
    ]

    communication = [
        "communicate",
        "writing",
        "records",
        "minutes",
        "organise",
        "public speaking",
        "listen"
    ]

    finance = [
        "budget",
        "finance",
        "money",
        "accountability",
        "audit"
    ]

    organisation = [
        "planning",
        "detail",
        "accurate",
        "coordination",
        "schedule"
    ]

    service = [
        "serve",
        "community",
        "volunteer",
        "participate",
        "student"
    ]


    for word in leadership:

        if word in text:

            scores["Chairperson"] += 10

            scores["Vice Chairperson"] += 5


    for word in teamwork:

        if word in text:

            scores["Vice Chairperson"] += 10

            scores["Committee Member"] += 5


    for word in communication:

        if word in text:

            scores["Secretary General"] += 10

            scores["Vice Secretary"] += 6


    for word in finance:

        if word in text:

            scores["Treasurer"] += 12


    for word in organisation:

        if word in text:

            scores["Vice Secretary"] += 10

            scores["Secretary General"] += 4


    for word in service:

        if word in text:

            scores["Committee Member"] += 8


    recommended = max(
        scores,
        key=scores.get
    )


    confidence = min(

        60 + scores[recommended],

        98

    )


    return {

        "role": recommended,

        "confidence": confidence,

        "scores": scores

    }

@app.route("/", methods=["GET", "POST"])
def home():

    if request.method == "POST":

        user_id = request.form["id"]

        password = request.form["password"]

        users = load_users()


        for user in users:

            if (
                user["id"] == user_id
                and user["password"] == password
            ):


                session["user"] = user["name"]

                session["user_id"] = user["id"]

                session["role"] = user.get(
                    "role",
                    "applicant"
                )


                # Admin goes directly to admin panel

                if session["role"] == "admin":

                    return redirect("/admin")



                # Create or load applicant progress

                get_applicant_progress(
                    session["user_id"]
                )



                if user.get(
                    "accepted_terms",
                    False
                ):

                    return redirect(
                        "/dashboard"
                    )


                return redirect(
                    "/terms"
                )



        flash(
            "Invalid Applicant ID or Password",
            "error"
        )

        return redirect("/")



    return render_template(
        "judiciary_login.html"
    )


@app.route("/dashboard")
def dashboard():

    if "user" not in session:

        return redirect("/")


    applicant = get_applicant_progress(
        session["user_id"]
    )


    progress = 0


    personal_status = "Not Started"

    academic_status = "Locked"

    questions_status = "Locked"

    documents_status = "Locked"

    review_status = "Locked"



    # Personal Information

    if applicant.get("personal"):

        progress = 20

        personal_status = "Completed"

        academic_status = "Available"



    # Academic Information

    if applicant.get("academic"):

        progress = 40

        academic_status = "Completed"

        questions_status = "Available"



    # Judiciary Questions

    if applicant.get("answers"):

        progress = 60

        questions_status = "Completed"

        documents_status = "Available"



    # Documents

    if applicant.get("documents"):

        progress = 80

        documents_status = "Completed"

        review_status = "Available"



    # Final Submission

    if applicant.get("status") == "Submitted":

        progress = 100

        review_status = "Completed"



    return render_template(

        "judiciary_dashboard.html",

        name=session["user"],

        progress=progress,

        personal_status=personal_status,

        academic_status=academic_status,

        questions_status=questions_status,

        documents_status=documents_status,

        review_status=review_status

    )
    
@app.route(
    "/terms",
    methods=["GET", "POST"]
)
def terms():

    if "user" not in session:

        return redirect("/")


    if session.get("role") == "admin":

        return redirect("/admin")



    if request.method == "POST":


        users = load_users()


        for user in users:

            if user["id"] == session["user_id"]:

                user["accepted_terms"] = True

                break



        with open(
            "judiciary_users.json",
            "w"
        ) as file:

            json.dump(
                users,
                file,
                indent=4
            )



        return redirect(
            "/apply"
        )



    return render_template(
        "judiciary_terms.html"
    )
    
@app.route(
    "/apply",
    methods=["GET", "POST"]
)
def apply():

    if "user" not in session:

        return redirect("/")


    applicant = get_applicant_progress(
        session["user_id"]
    )


    # Prevent editing after completion

    if applicant["personal"]:

        return redirect("/academic")



    if request.method == "POST":


        personal_details = {

            "fullname": request.form["fullname"],

            "student_id": request.form["student_id"],

            "nrc": request.form["nrc"],

            "dob": request.form["dob"],

            "gender": request.form["gender"],

            "phone": request.form["phone"],

            "email": request.form["email"],

            "address": request.form["address"]

        }



        progress = load_progress()


        for user in progress:

            if user["user_id"] == session["user_id"]:

                user["personal"] = personal_details



        save_progress(progress)



        return redirect(
            "/academic"
        )



    return render_template(
        "judiciary_apply.html",
        applicant_name=session["user"]
    )
    
@app.route(
    "/academic",
    methods=["GET", "POST"]
)
def academic():

    if "user" not in session:

        return redirect("/")


    applicant = get_applicant_progress(
        session["user_id"]
    )


    # Personal details must be completed first

    if not applicant["personal"]:

        return redirect("/apply")



    # Prevent editing after completion

    if applicant["academic"]:

        return redirect("/questions")



    if request.method == "POST":


        academic_details = {


            "programme":
            request.form["programme"],


            "year":
            request.form["year"],


            "student_number":
            request.form["student_number"]

        }



        progress = load_progress()


        for user in progress:

            if user["user_id"] == session["user_id"]:

                user["academic"] = academic_details



        save_progress(progress)



        return redirect(
            "/questions"
        )



    return render_template(
        "judiciary_academic.html"
    )

@app.route(
    "/questions",
    methods=["GET", "POST"]
)
def questions():

    if "user" not in session:
        return redirect("/")

    applicant = get_applicant_progress(
        session["user_id"]
    )

    # Academic details must be completed first
    if not applicant["academic"]:
        return redirect("/academic")

    # Prevent editing after completion
    if applicant["answers"]:
        return redirect("/documents")

    if request.method == "POST":

        if not request.form.get("declaration"):

            flash(
                "You must accept the declaration before continuing."
            )

            return redirect("/questions")

        answers = {

            "q1": request.form["q1"],

            "q2": request.form["q2"],

            "q3": request.form["q3"],

            "q4": request.form["q4"],

            "q5": request.form["q5"],

            "q6": request.form["q6"],

            "q7": request.form["q7"]

        }

        progress = load_progress()

        for user in progress:

            if user["user_id"] == session["user_id"]:

                user["answers"] = answers

        save_progress(progress)

        return redirect("/documents")

    return render_template(
        "judiciary_questions.html"
    )

@app.route(
    "/documents",
    methods=["GET", "POST"]
)
def documents():

    if "user" not in session:

        return redirect("/")


    applicant = get_applicant_progress(
        session["user_id"]
    )


    # Questions must be completed first

    if not applicant["answers"]:

        return redirect("/questions")



    # Prevent re-uploading after completion

    if applicant["documents"]:

        return redirect("/review")



    if request.method == "POST":


        student_id_file = request.files.get(
            "student_id"
        )

        payment_file = request.files.get(
            "payment"
        )



        if (
            student_id_file
            and payment_file
            and allowed_file(student_id_file.filename)
            and allowed_file(payment_file.filename)
        ):


            user_id = session["user_id"]



            student_id_filename = secure_filename(
                user_id
                + "_student_id_"
                + student_id_file.filename
            )


            payment_filename = secure_filename(
                user_id
                + "_payment_"
                + payment_file.filename
            )



            student_id_file.save(
                os.path.join(
                    app.config["UPLOAD_FOLDER"],
                    student_id_filename
                )
            )



            payment_file.save(
                os.path.join(
                    app.config["UPLOAD_FOLDER"],
                    payment_filename
                )
            )



            documents = {

                "student_id": student_id_filename,

                "payment": payment_filename

            }



            progress = load_progress()



            for user in progress:

                if user["user_id"] == session["user_id"]:

                    user["documents"] = documents



            save_progress(progress)



            return redirect(
                "/review"
            )



    return render_template(
        "judiciary_documents.html"
    )

@app.route(
    "/review",
    methods=["GET", "POST"]
)
def review():

    if "user" not in session:
        return redirect("/")


    progress = load_progress()

    user_id = session["user_id"]


    if user_id not in progress:
        return redirect("/dashboard")


    applicant = progress[user_id]


    if "documents" not in applicant:
        return redirect("/documents")


    if applicant.get("submitted"):
        return redirect("/success")


    if request.method == "POST":

        applications = load_applications()


        # Prevent duplicate submissions
        for app in applications:

            if app.get("user_id") == user_id:
                return redirect("/success")


        recommendation = recommend_position(
            applicant["answers"]
        )


        application = {

            "user_id": user_id,

            "name": session["user"],

            "personal": applicant["personal"],

            "academic": applicant["academic"],

            "answers": applicant["answers"],

            "documents": applicant["documents"],

            "recommended_role": recommendation["role"],

            "confidence": recommendation["confidence"],

            "scores": recommendation["scores"],

            "status": "Pending Review"

        }


        applications.append(
            application
        )


        save_applications(
            applications
        )


        applicant["submitted"] = True


        save_progress(
            progress
        )


        return redirect(
            "/success"
        )


    return render_template(

        "judiciary_review.html",

        personal=applicant["personal"],

        academic=applicant["academic"],

        answers=applicant["answers"],

        documents=applicant["documents"]

    )

@app.route("/success")
def success():

    if "user" not in session:

        return redirect("/")

    return render_template(
        "judiciary_success.html",
        name=session["user"]
    )

@app.route("/logout")
def logout():

    session.clear()

    return redirect("/")

@app.route(
    "/admin",
    methods=["GET", "POST"]
)
def admin():

    if request.method == "POST":

        username = request.form["username"]

        password = request.form["password"]

        admins = load_admins()

        for admin in admins:

            if (
                admin["username"] == username
                and admin["password"] == password
            ):

                session["admin"] = admin["name"]

                return redirect(
                    "/admin/dashboard"
                )

        flash(
            "Invalid administrator credentials.",
            "error"
        )

        return redirect("/admin")

    return render_template(
        "admin_login.html"
    )

@app.route("/admin/dashboard")
def admin_dashboard():

    if "admin" not in session:

        return redirect("/admin")

    applications = load_applications()

    total = len(applications)

    pending = len(
        [
            a
            for a in applications
            if a.get("status") == "Pending Review"
        ]
    )

    shortlisted = len(
        [
            a
            for a in applications
            if a.get("status") == "Shortlisted"
        ]
    )

    approved = len(
        [
            a
            for a in applications
            if a.get("status") == "Approved"
        ]
    )

    rejected = len(
        [
            a
            for a in applications
            if a.get("status") == "Rejected"
        ]
    )

    return render_template(

        "admin_dashboard.html",

        admin=session["admin"],

        applications=applications,

        total=total,

        pending=pending,

        shortlisted=shortlisted,

        approved=approved,

        rejected=rejected

    )

@app.route(
    "/admin/application/<user_id>",
    methods=["GET", "POST"]
)
def admin_application(user_id):

    if "admin" not in session:

        return redirect("/admin")


    applications = load_applications()


    application = None


    for app in applications:

        if app["user_id"] == user_id:

            application = app

            break


    if application is None:

        return redirect("/admin/dashboard")


    if request.method == "POST":

        action = request.form["action"]


        if action == "approve":

            application["status"] = "Approved"


        elif action == "reject":

            application["status"] = "Rejected"


        elif action == "shortlist":

            shortlisted = len(

                [
                    a
                    for a in applications
                    if a.get("status") == "Shortlisted"
                ]

            )


            if shortlisted < 5:

                application["status"] = "Shortlisted"


        save_applications(
            applications
        )


        return redirect(
            "/admin/application/" + user_id
        )


    return render_template(

        "admin_application.html",

        application=application

    )
    
@app.route("/judiciary_uploads/<filename>")
def uploaded_file(filename):

    if "admin" not in session:
        return redirect("/admin")

    return send_from_directory(
        app.config["UPLOAD_FOLDER"],
        filename
    )    


@app.route("/admin/logout")
def admin_logout():

    session.pop(
        "admin",
        None
    )

    return redirect("/admin")


if __name__ == "__main__":

    app.run(
        host="0.0.0.0",
        port=5000,
        debug=True
    )