from flask import Flask, render_template, request, redirect, url_for
from clients import get_genre_list, GetRandomMovie

app = Flask(__name__)


@app.route('/')
def index():
    genre_list = get_genre_list()
    return render_template("index.html", genre_list=genre_list)


@app.route('/movie', methods=['POST', 'GET'])
def get_movie():
    if request.method == "POST":
        genre_codes = request.form.getlist("my_checkbox")
        raiting = float(request.form.get("my_raiting"))

        get_random_movie = GetRandomMovie(genre_codes, raiting)
        data = get_random_movie()
        # print(data)

        if data['title'] == get_random_movie.SORRY_MESSAGE:
            return redirect(url_for("sorry"))

        return render_template("movie.html", data=data)


@app.route('/sorry')
def sorry():
    return render_template("sorry.html")


if __name__ == "__main__":
    app.run(debug=True)
