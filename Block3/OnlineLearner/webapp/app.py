from flask import Flask, render_template, request, redirect, url_for, flash, abort, session
from flask_mysqldb import MySQL
from datetime import datetime, timedelta
import random

app = Flask(__name__)
app.secret_key = "mndkfjkdsfj"
app.permanent_session_lifetime = timedelta(minutes=5)  # to be able to stay user in session even after closing the browser

app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = 'Zihad7788'
app.config['MYSQL_DB'] = 'webapp'

mysql = MySQL(app)


@app.route('/')
@app.route('/view_main')
def view_main():
    # if user is already logged in then redirect to course page
    if "user" in session:
        return redirect(url_for("view_course"))
    return render_template("view_main.html")


@app.route('/register', methods=['GET', 'POST'])
def register():
    try:
        if request.method == 'POST':
            name = request.form.get("nm")
            email = request.form.get("em")
            password = request.form.get("ps")

            # for checking whether the current user with same email in database
            cur = mysql.connection.cursor()
            cur.execute("select * from users")
            eValue = cur.fetchall()

            # check for the same email was used previously
            for ev in eValue:
                if email == ev[0]:
                    flash("You have already an account with this email", "danger")
                    cur.close()
                    return redirect(url_for("view_main"))

            cur.execute("insert into users(email, name, password) values(%s, %s, %s)", (email, name, password))
            mysql.connection.commit()
            cur.close()
            flash("Account has been created successfully", "success")
            return redirect(url_for("login"))
    except Exception as e:
        raise e
    return render_template("view_main.html")


@app.route('/login', methods=['GET', 'POST'])
def login():
    try:
        if request.method == 'POST':
            email = request.form.get("eml")
            password = request.form.get("psl")

            # for checking whether the current user with same email in database
            cur = mysql.connection.cursor()
            cur.execute("SELECT email, password FROM users")
            empass = cur.fetchall()

            cur.execute("SELECT number FROM users where email=%s and password=%s", (email, password))
            value = cur.fetchone()
            cur.close()

            # check for password match
            for ep in empass:
                if email == ep[0]:
                    if password != ep[1]:
                        flash("Wrong password!", "danger")
                        return redirect(url_for("login"))

            # for creating session and store the logged in user id
            if value:
                session.permanent = True  # to be able to stay user in session even after closing the browser
                session["user"] = int(value[0])
                flash("You are successfully logged in", "success")
                return redirect(url_for("view_course"))
            else:
                flash("There is no account with this email. Create one here!", "danger")
                return redirect(url_for("register"))
    except Exception as e:
        raise e
    return render_template("view_main.html")


@app.route('/logout')
def logout():
    session.pop("user", None)
    flash("You are successfully logged out", "danger")
    return redirect(url_for("view_main"))


@app.route('/new_course', methods=['GET', 'POST'])
def new_course():
    # for checking whether there is user in session (logged in user)
    if "user" in session:
        user = session["user"]
    else:
        flash("Log In first", "danger")
        return redirect(url_for("login"))

    cur = mysql.connection.cursor()
    # this querry for autocomplete the search field
    cur.execute("select name from course")
    nameData = cur.fetchall()
    try:
        if request.method == 'POST':
            name = request.form["nm"]
            key = request.form["ek"]
            place = request.form["fp"]
            text = request.form["des"]

            if len(name)==0 or len(name)>50:
                abort(404, description="Enter Valid Name")

            intPlace = int(place)

            if isinstance(intPlace, int)==False or intPlace>100:
                abort(404, description="Enter Valid number of free place")

            if key:
                cur.execute("INSERT INTO course(name, description, enrollmentkey, free_places, creator) VALUES(%s, %s, %s, %s, %s)", (name, text, key, place, user))
                mysql.connection.commit()
            else:
                cur.execute(
                    "INSERT INTO course(name, description, free_places, creator) VALUES(%s, %s, %s, %s)",
                    (name, text, place, user))
                mysql.connection.commit()
            cur.close()
            flash("Course created successfully", "success")
            return redirect(url_for("view_main"))
    except Exception as e:
        raise e

    return render_template("new_course.html", nameData=nameData)


@app.route('/view_course')
def view_course():
    # for checking whether there is user in session (logged in user)
    if "user" in session:
        user = session["user"]
    else:
        flash("Log In first", "danger")
        return redirect(url_for("login"))

    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM view_course WHERE user = %s", (user,))
    value = cur.fetchall()

    cur.execute("select distinct ID, name, description, enrollmentkey, free_places, uname from view_course where ID not in (SELECT ID FROM view_course WHERE user = %s)", (user,))
    values = cur.fetchall()

    # this querry for autocomplete the search field
    cur.execute("select name from course")
    nameData = cur.fetchall()

    cur.close()

    return render_template("view_course.html", value=value, values=values, nameData=nameData)


@app.route('/view_course/<int:cid>')
def view_course_detail(cid):
    # for checking whether there is user in session (logged in user)
    if "user" in session:
        user = session["user"]
    else:
        flash("Log In first", "danger")
        return redirect(url_for("login"))

    infos = [] # list of course id from enroll
    idInfos = [] # list for delete function

    cur = mysql.connection.cursor()
    res = cur.execute("select * from course_detail where ID = %s", (cid,))
    if res>0:
        value = cur.fetchall()

    cur.execute("select * from enroll where user = %s", (user,))
    info = cur.fetchall()

    cur.execute("select ID from course where creator = %s", (user,))
    idInfo = cur.fetchall()

    # this querry for autocomplete the search field
    cur.execute("select name from course")
    nameData = cur.fetchall()

    for i in info:
        infos.append(int(i[1]))

    for j in idInfo:
        idInfos.append(j[0])

    cur.execute("select * from (select st2.number, st2.name, st2.sid, sb.submission_text, st2.nr, st2.user from (select st1.number, t.name, st1.sid, st1.nr, st1.user from (select st.number, nr, sid, user from (select * from tasks left join (select sid, tid, user from submit where cid = %s and user = %s) as s1 on number=s1.tid) as st  where st.nr= %s) as st1 join tasks t on st1.number=t.number) as st2 left join submission sb on st2.sid = sb.id) as st3 left join avgGrade as ag on st3.sid=ag.submission", (cid, user, cid))
    stInfo = cur.fetchall()

    cur.close()

    return render_template("view_course_detail.html", value=value, user=user, infos=infos, idInfos=idInfos, stInfo=stInfo, nameData=nameData)


@app.route('/new_enroll/<int:cid>', methods=['GET', 'POST'])
def new_enroll(cid):
    # for checking whether there is user in session (logged in user)
    if "user" in session:
        user = session["user"]
    else:
        flash("Log In first", "danger")
        return redirect(url_for("login"))

    cur = mysql.connection.cursor()
    cur.execute("select name, enrollmentkey from course where ID = %s", (cid,))
    info = cur.fetchall()
    name = info[0][0]
    key = info[0][1]

    cur.execute("select free_places from course where ID = %s", (cid,))
    free = cur.fetchall()

    # this querry for autocomplete the search field
    cur.execute("select name from course")
    nameData = cur.fetchall()

    # if there is no free place then return to course page
    if not free[0][0]:
        flash("Course is already full", "danger")
        return redirect(url_for("view_course"))

    try:
        if request.method == 'POST':
            if key != None :
                ekey = request.form["ek"]
                if key == ekey:
                    cur.execute(
                        "INSERT INTO enroll(user, course, date_of_entry) VALUES(%s, %s, %s)",
                        (user, cid, datetime.today().strftime('%Y-%m-%d')))
                    mysql.connection.commit()
                    flash("Welcome to the course!!!", "success")

                    red = free[0][0]-1

                    cur.execute(
                        "UPDATE course SET free_places = %s where ID = %s",(red, cid))
                    mysql.connection.commit()
                    cur.close()

                    return redirect(url_for("view_course"))
                else:
                    flash("Wrong enrollment key", "danger")
            else:
                cur.execute(
                    "INSERT INTO enroll(user, course, date_of_entry) VALUES(%s, %s, %s)",
                    (user, cid, datetime.today().strftime('%Y-%m-%d')))
                mysql.connection.commit()
                flash("Welcome to the course!!!", "success")

                red = free[0][0]-1

                cur.execute("UPDATE course SET free_places = %s where ID = %s", (red, cid))
                mysql.connection.commit()
                cur.close()

                return redirect(url_for("view_course"))
    except Exception as e:
        raise e

    cur.close()

    return render_template("new_enroll.html", name=name, key=key, free=free, nameData=nameData)


@app.route('/delete/<int:cid>')
def delete(cid):
    # for checking whether there is user in session (logged in user)
    if "user" in session:
        user = session["user"]
    else:
        flash("Log In first", "danger")
        return redirect(url_for("login"))

    cur = mysql.connection.cursor()
    cur.execute("delete from course where ID = %s", (cid,))
    mysql.connection.commit()
    cur.close()
    flash("Course has been deleted successfully!!!", "success")
    return redirect(url_for("view_course"))


@app.route('/new_assignment/<int:tid>', methods=['GET', 'POST'])
def new_assignment(tid):
    # for checking whether there is user in session (logged in user)
    if "user" in session:
        user = session["user"]
    else:
        flash("Log In first", "danger")
        return redirect(url_for("login"))

    cur = mysql.connection.cursor()
    cur.execute("select * from submit_task where number = %s", (tid,))
    obj = cur.fetchall()

    # this querry for autocomplete the search field
    cur.execute("select name from course")
    nameData = cur.fetchall()

    cur.close()

    try:
        if request.method == "POST":
            text = request.form["txt"]
            cur = mysql.connection.cursor()

            cur.execute("select * from submit")
            asub = cur.fetchall()
            for sub in asub:
                if sub[2] == tid and sub[1] == obj[0][4] and sub[3] == user:
                    abort(404, description="You can not submit for this task")

            cur.execute("insert into submission(submission_text) values(%s)", (text,))
            mysql.connection.commit()
            cur.execute("select id from submission where submission_text = %s", (text,))
            id = cur.fetchall()
            cur.execute("insert into submit values(%s, %s, %s, %s)", (id, obj[0][4], tid, user))
            mysql.connection.commit()

            cur.close()

            flash("Task Submitted successfully", "success")
            return redirect(url_for("view_course_detail", cid=obj[0][4]))
    except Exception as e:
        raise e

    return render_template("new_assignment.html", obj=obj, nameData=nameData)


@app.route('/assess/<int:cid>', methods=['GET', 'POST'])
def assess(cid):
    # for checking whether there is user in session (logged in user)
    if "user" in session:
        user = session["user"]
    else:
        flash("Log In first", "danger")
        return redirect(url_for("login"))

    arrayAssess = [] # array for checking whether a task is already submitted
    arrayAssess2 = [] # array to check wheether a course has submission or not

# for randomly display of tasks in rating option
    cur = mysql.connection.cursor()
    cur.execute(
        "select ssb.tid, ssb.sid, t.name, t.description, ssb.submission_text from (SELECT * FROM submit s join submission sb on s.sid=sb.id where cid = %s) as ssb join tasks t on ssb.tid=t.number", (cid,))
    objAssess = cur.fetchall()

    for obj in objAssess:
        arrayAssess.append(obj)

    # if a course has no submissions then shows this error
    if not arrayAssess:
        abort(404, description="This course has no submissions yet.")

    objRandom = random.choice(arrayAssess)

    cur.execute("select submission, user from canrate")
    subUser = cur.fetchall()

    cur.execute("select sid, user from submit where cid = %s", (cid,))
    sidUser = cur.fetchall()


# inorder to avoid the rate option for the tasks which is done by user self.
    if (objRandom[1], user) in sidUser:
        cur.execute(
            "select ssb.tid, ssb.sid, t.name, t.description, ssb.submission_text from (SELECT * FROM submit s join submission sb on s.sid=sb.id where cid = %s and sid != %s and user != %s) as ssb join tasks t on ssb.tid=t.number",
            (cid, objRandom[1], user))
        objAssess = cur.fetchall()

        # if a course has no submissions then shows this error
        for obj in objAssess:
            arrayAssess2.append(obj)

        if not arrayAssess2:
            abort(404, description="This course has no submissions yet.")

        objRandom = random.choice(arrayAssess2)

    # this querry for autocomplete the search field
    cur.execute("select name from course")
    nameData = cur.fetchall()

    cur.close()

    try:
        if request.method == "POST":

            grade = int(request.form.get("gd"))
            comment = request.form["cmt"]
            subId = int(request.form["sb"])

            if (subId, user) in subUser:
                abort(404, description="You have already rated for the course")

            cur = mysql.connection.cursor()
            cur.execute("insert into canrate values(%s, %s, %s, %s)", (grade, comment, subId, user))
            mysql.connection.commit()
            cur.close()
            flash("Successfully graded for the task", "success")
            return redirect(url_for("view_course_detail", cid=cid))
    except Exception as e:
        raise e

    return render_template("assess.html", objRandom=objRandom, nameData=nameData)


@app.route('/new_task/<int:cid>', methods=['GET', 'POST'])
def new_task(cid):
    # for checking whether there is user in session (logged in user)
    if "user" in session:
        user = session["user"]
    else:
        flash("Log In first", "danger")
        return redirect(url_for("login"))

    cur = mysql.connection.cursor()
    cur.execute("select name from course where ID = %s", (cid,))
    objCourse = cur.fetchall()

    # this querry for autocomplete the search field
    cur.execute("select name from course")
    nameData = cur.fetchall()

    cur.close()
    try:
        if request.method == "POST":
            task = request.form["tsk"]
            description = request.form["des"]

            if task and description:
                cur = mysql.connection.cursor()
                cur.execute("insert into tasks(name, description, nr) values(%s, %s, %s)", (task, description, cid))
                mysql.connection.commit()

                cur.close()
                flash("Task created successfully", "success")
                return redirect(url_for("view_course_detail", cid=cid))
            else:
                raise Exception
    except Exception as e:
        raise e
    return render_template("task.html", objCourse=objCourse, nameData=nameData)


@app.route('/search', methods=['GET', 'POST'])
def search():
    if request.method == "POST":
        cur = mysql.connection.cursor()
        searchedName = request.form.get("srch")
        sname = "%"+searchedName.lower()+"%"
        cur.execute("SELECT * FROM searchedcourse WHERE lower(cname) like %s", (sname,))
        nameobj = cur.fetchall()

        # this querry for autocomplete the search field
        cur.execute("select name from course")
        nameData=cur.fetchall()

        cur.close()
        return render_template("search.html", nameobj=nameobj, nameData=nameData)


if __name__ == '__main__':
    app.run()
