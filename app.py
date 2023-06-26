# Модули для установки:
# pip install flask
# pip install psycopg2

import psycopg2
import psycopg2.extras
from flask import Flask, render_template, request, redirect, url_for


app = Flask(__name__)

conn = psycopg2.connect(host="localhost", database="practice1", user="postgres", password="admin")

# conn.commit() - Использование данной конструкции поможет сохранять изменения в БД.


def sql_one(query):
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cur.execute(query)
    res = cur.fetchone()
    cur.close()
    conn.commit()
    return res


def sql_all(query):
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cur.execute(query)
    res = cur.fetchall()
    cur.close()
    return res


@app.route("/",  methods=['GET', 'POST'])
def start_page():
    out = sql_one("select count(id_pass) as count_pass, count(id_log) as count_logs from passes, logs")
    if request.method == "POST":
        id_pass = request.form["id"]
        if id_pass.isdigit():
            out2 = sql_one(f"select * from passes where id_pass = {id_pass}")
        else:
            out2 = None
        return render_template("main.html", out=out, res=True, out2=out2, old_id=id_pass)
    return render_template("main.html", out=out, res=False)


@app.route("/work")
def work_page():
    return render_template("work.html")


if __name__ == "__main__":
    #app.host = '0.0.0.0'
    app.debug = True
    #app.run(host='0.0.0.0')
    app.run()
