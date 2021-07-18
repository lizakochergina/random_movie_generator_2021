from tmdbv3api import TMDb
from tmdbv3api import Genre
from tmdbv3api import Discover
import random
import requests
import matplotlib.pyplot as plt
import seaborn as sns
import matplotlib.ticker as ticker

tmdb = TMDb()
tmdb.language = 'ru'
tmdb.api_key = '20b507326d205b1a15c70d92ceb7a749'


def get_genre_list():
    genre = Genre()
    genre_list = genre.movie_list()
    return genre_list


def get_genre_dict(genre_list):
    genre_dict = {}
    for item in genre_list:
        genre_dict[item['id']] = item['name']
    return genre_dict


class GetRandomMovie:
    MAX_NUM_PAGES = 250
    SORRY_MESSAGE = 'error'

    def __init__(self, genre_codes, raiting):
        self.genre_codes = genre_codes
        self.raiting = raiting
        self.folder_id = 'b1ghm8nsvtpqj2nql4n9'
        self.iam_token = 't1.9euelZrJjI-TlsySlZ3Nj5iQxsuLkO3rnpWako2KkZOWlcjNyMeWzZ7MyYzl8_dMODB4-e9KUV9c_t3z9wxnLXj570pRX1z-.rXJqyN-w-Lwpt2YgsvyUOpCjUlUpskZjah_1c00dQmYd7lfMuu7jhMcUxxzyqmLJLfasy7SV5sT2t5S_4MeFCQ'

    def __call__(self):
        movies = self.discover_movies_with_genres_and_raiting()
        # print(movies)

        if len(movies) == 0:
            movie_description = {'title': GetRandomMovie.SORRY_MESSAGE, 'raiting': 0, 'overview': '',
                                 'id': '', 'img': '', 'genres': []}
            return movie_description

        random.shuffle(movies)

        movie_num = -1
        for i in range(len(movies)):
            print(i, "overview: ", movies[i]['overview'], "  end overview")
            if movies[i]['overview'] != '':
                movie_num = i
                break

        if movie_num == -1:
            movie_description = {'title': GetRandomMovie.SORRY_MESSAGE, 'raiting': 1, 'overview': '',
                                 'id': '', 'img': '', 'genres': []}
            return movie_description

        movie = movies[movie_num]
        movie_title = movie['title'] + ' (' + movie['release_date'][: 4] + ')'
        movie_poster_path = movie['poster_path']
        movie_img = f'https://www.themoviedb.org/t/p/w1280{movie_poster_path}'
        movie_genres = []
        genre_dict = get_genre_dict(get_genre_list())
        for genre_id in movie['genre_ids']:
            movie_genres.append(genre_dict[genre_id])

        self.synthesize(movie['overview'])

        movies_avr = self.get_average_raiting(movies)
        popular_movies = self.get_most_popular_movies_in_year(movies)
        self.get_pic_of_cnt_of_movies(movies)

        movie_description = {'title': movie_title, 'raiting': movie['vote_average'],
                             'overview': movie['overview'], 'id': movie['id'], 'img': movie_img,
                             'genres': movie_genres, 'avr': movies_avr, 'popular_movies': popular_movies}
        return movie_description

    def discover_movies_with_genres_and_raiting(self):
        discover = Discover()
        str_genre_codes = self.genre_codes_to_str()
        movies = []
        for page_num in range(1, GetRandomMovie.MAX_NUM_PAGES):
            tmp = discover.discover_movies({
                'primary_release_date.gte': '1900-01-01',  # смотрю фильмы, которые вышли после этой даты
                'primary_release_date.lte': '2021-07-17',  # смотрю фильмы, которые вышли до этой даты
                'with_genres': str_genre_codes,
                'page': page_num,
                'vote_average.gte': self.raiting,
                'vote_count.gte': 10,  # чтобы рейтинг имел какой-то смысл,
                # рассматриваю только те фильмы, которым поставили
                # оценку больше 10 людей
                'with_runtime.gte': 60  # длительность фильма больше 60мин
            })
            if len(tmp) == 0:
                break
            movies.extend(tmp)
        return movies

    def genre_codes_to_str(self):
        str_genre_codes = ''
        for code in self.genre_codes:
            str_genre_codes += str(code) + ', '
        return str_genre_codes[: -2]

    @staticmethod
    def get_pic_of_cnt_of_movies(movies):
        data = {}
        for movie in movies:
            if movie['release_date'] != '':
                key = int(movie['release_date'][: 4])
                if key in data:
                    data[key] += 1
                else:
                    data[key] = 1
        keys = sorted(data.keys())
        vals = [data[key] for key in keys]

        fig, ax = plt.subplots(figsize=(15, 12))
        ax.yaxis.set_major_locator(ticker.MultipleLocator(1))
        ax.set_xlabel('year', fontsize=18)
        ax.set_ylabel('number of films', fontsize=18)
        plt.xticks(rotation=80)
        sns.barplot(x=keys, y=vals, palette="rocket")
        plt.savefig('static/imgs/plot.png')

    @staticmethod
    def get_average_raiting(movies):
        avr = 0
        for movie in movies:
            avr += movie['vote_average']
        return float("{0:.3f}".format(avr / len(movies)))

    @staticmethod
    def get_most_popular_movies_in_year(movies):
        data = {}
        for movie in movies:
            if movie['release_date'] != '':
                key = int(movie['release_date'][: 4])
                if key not in data:
                    data[key] = movie['title']
        sorted_data = {}
        for key in sorted(data.keys(), reverse=True):
            sorted_data[key] = data[key]

        return sorted_data

    def synthesize(self, text):
        url = 'https://tts.api.cloud.yandex.net/speech/v1/tts:synthesize'
        headers = {
            'Authorization': 'Bearer ' + self.iam_token,
        }

        data = {
            'text': text,
            'lang': 'ru-RU',
            'folderId': self.folder_id,
            'sampleRateHertz': 48000,
            "emotion": "good"
        }

        f = open('static/audios/audio.ogg', 'wb')

        with requests.post(url, headers=headers, data=data, stream=True) as resp:
            if resp.status_code != 200:
                raise RuntimeError("Invalid response received: code: %d, message: %s" % (resp.status_code, resp.text))

            for chunk in resp.iter_content(chunk_size=None):
                f.write(chunk)

        f.close()
