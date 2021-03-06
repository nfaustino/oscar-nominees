import sqlite3 as lite
import pandas as pd
pd.set_option('display.width', 2000)
pd.set_option('display.max_rows', 500)


def main_menu():
    menu = ["movie title", "release year", "person", "genre", "award category"]
    while True:
        choice = shortcuts("\nWhat can I find for you? (enter 'q' any time to quit and 'm' to see this menu)\n\n"
                           "I can search by:\n 1) Movie title\n 2) Release year\n 3) Person\n 4) Genre\n "
                           "5) Award category \n\n>>> ")
        if choice in ["1", menu[0]]:
            title_search()
        elif choice in ["2", menu[1]]:
            year_search("null")
        elif choice in ["3", menu[2]]:
            person_search()
        elif choice in ["4", menu[3]]:
            genre_search()
        elif choice in ["5", menu[4]]:
            award_search()
        else:
            print("\nLet's try that again...\n")
            continue


# checks if input is empty
# checks if user wants to quit or to see main menu
def shortcuts(prompt):
    while True:
        try:
            value = input(prompt)
        except (ValueError, TypeError):
            print("Sorry, that's not a valid input.")
            continue
        if value.lower() == 'q':
            print("\nUntil next time!")
            raise SystemExit
        elif value.lower() == 'm':
            main_menu()
        elif not value:
            print("\nLet's try this again...\n")
            continue
        break
    return value


# checks if menu selection is valid
def valid_selection(df, i):
    if i > len(df) - 1:
        print("\nOops, that's not a valid selection.\n\n")
        return False
    return True


#  grabs data from sqlite database according to SQL statement
#  returns pandas data frame
def get_df(sql, connection):
    df = pd.read_sql(sql, connection)
    df.columns = map(str.upper, df.columns)
    return df


# returns movie metadata
# user can then select to see 1 of the movie's 3 top billed actors
def get_film_info(df):
    con = lite.connect('oscars.db')
    while True:
        try:
            print("\n", df)
            index = int(shortcuts("\n Enter a number to learn more about the movie: \n\n>>> "))
        except (ValueError, TypeError):
            print("\nOops, that's not a valid input.\n")
            continue
        if not valid_selection(df, index):
            continue
        movie = df.iat[index, 1]
        break
    print("\n" + movie + "\n")
    award_df = get_df(("""SELECT award, nominee, result
                          FROM nominees
                          WHERE film = '%s'""" % movie), con)
    info_df = get_df(("""SELECT year, director, genre, rated, writer, metascore, imdbRating as imdb_rating
                         FROM films
                         WHERE film = '%s'""" % movie), con)
    actors_df = get_df(("""SELECT DISTINCT name
                           FROM people
                           WHERE film = '%s'
                            AND role = 'actor'""" % movie), con)
    print(info_df, "\n\n\nAcademy Awards\n", award_df, "\n\n\nTop billed actors")
    get_person_info(actors_df)


# returns actor filmography and award history
def get_person_info(df):
    con = lite.connect("oscars.db")
    while True:
        try:
            print(df)
            index = int(shortcuts("\nEnter a number to learn more about the actor's filmography: \n\n>>> "))
        except (ValueError, TypeError):
            print("Oops, that's not a valid input.\n")
            continue
        if not valid_selection(df, index):
            continue
        person = df.iat[index, 0]
        break
    print("\n" + person)
    film_df = get_df(("""SELECT films.year, people.film, people.role, nominees.award, nominees.result
                         FROM people
                         INNER JOIN films ON people.film = films.film
                         LEFT JOIN nominees ON (nominees.nominee = people.name AND nominees.film = people.film)
                         WHERE people.name = '%s'
                         ORDER BY films.year""" % person), con)
    get_film_info(film_df)


# returns films according to year parameter and possibly award nominations
def get_year_info(start_year, end_year, params):
    con = lite.connect("oscars.db")
    if params == "null":
        film_df = get_df(("SELECT year, film FROM films WHERE year BETWEEN %04d AND %04d ORDER BY year"
                          % (start_year, end_year)), con)
    else:
        stmt = """SELECT films.year as release_year, nominees.film, nominees.award, nominees.nominee, nominees.result
                  FROM nominees
                  JOIN films ON nominees.film = films.film
                  WHERE (nominees.award = '%s'"""
        cats = (params[0][0],)
        if len(params[0]) > 1:
            for c in range(1, len(params[0])):
                stmt += " OR nominees.award = '%s'"
                cats += (params[0][c],)
        if params[1] == 1:
            stmt += ") AND nominees.result = 'Won'"
        elif params[1] == 2:
            stmt += ") AND nominees.result = 'Nominated'"
        else:
            stmt += ")"
        cats += (start_year, end_year)
        stmt += " AND films.year BETWEEN %04d AND %04d ORDER BY films.year"
        film_df = get_df((stmt % cats), con)
    get_film_info(film_df)


# prompts user for year parameter
def year_search(params):
    while True:
        try:
            yr_range = \
                shortcuts("\nEnter a year or year range between 2000 and 2015 (eg: 2005-2010):\n\n>>> ").split("-")
            start = int(yr_range[0].strip())
            if len(yr_range) == 2:
                end = int(yr_range[1].strip())
        except (TypeError, ValueError):
            print("\nOops, that's not a valid input.")
            continue
        if start < 2000 or start > 2015:
            print("\nOops, that's not a valid year input.")
            continue
        elif "end" in locals():
            if end < 2000 or end > 2015:
                print("\nOops, that's not a valid year range")
                continue
            elif end < start:
                start, end = end, start
                break
        else:
            end = start
            break
        break
    get_year_info(start, end, params)


# searches for user provided name
def person_search():
    con = lite.connect("oscars.db")
    while True:
        name = shortcuts("\nEnter the name of an actor or director: \n\n>>> ")
        people_df = get_df(("""SELECT DISTINCT name
                               FROM people
                               WHERE normal_name LIKE '%s'
                               ORDER BY name""" % ("%" + name + "%")), con)
        if len(people_df) == 0:
            print("\nSorry, I can't find that name. Try someone else.")
            continue
        break
    get_person_info(people_df)


# searches for user provided film title
def title_search():
    con = lite.connect("oscars.db")
    while True:
        title = shortcuts("\nEnter a word or phrase: \n\n>>> ")
        movie_df = get_df(("""SELECT year, film
                             FROM films
                             WHERE film LIKE '%s'
                             ORDER BY year""" % ("%" + title + "%")), con)
        if len(movie_df) == 0:
            print("\nSorry, I can't find that title. Try another one.")
            continue
        break
    get_film_info(movie_df)


# searches for films according to provided genre(s)
def genre_search():
    con = lite.connect("oscars.db")
    while True:
        genre = shortcuts("\nEnter a genre or several genres (eg: biography, drama, sport): \n\n>>> ")
        genre_list = [genre.strip().replace(",", "") for genre in genre.split(" ")]
        genres = ("%" + genre_list[0] + "%",)
        stmt = "(genre LIKE '%s'"
        if len(genre_list) > 1:
            for i in range(1, len(genre_list)):
                stmt += " AND genre LIKE '%s'"
                genres += ("%" + genre_list[i] + "%",)
        stmt = "SELECT year, film, genre FROM films WHERE " + stmt + ")"
        movie_df = get_df((stmt % genres), con)
        if len(movie_df) == 0:
            print("\nSorry, no movies match that genre search. Try something else.")
            continue
        break
    get_film_info(movie_df)


# user can search for films nominated for select award categories
# returns winners, losers, or both
def award_search():
    menu = ["Best Picture", "Best Director", "Best Actor", "Best Actress", "Best Supporting Actor",
            "Best Supporting Actress"]
    while True:
        valid = True;
        award = shortcuts("\nWhich category or categories do you want to search in? (eg: 3, 4, 5)\n\n"
                          "1) "+menu[0]+"\n"
                          "2) "+menu[1]+"\n"
                          "3) "+menu[2]+"\n"
                          "4) "+menu[3]+"\n"
                          "5) "+menu[4]+"\n"
                          "6) "+menu[5]+"\n\n>>> ")

        award_list = [award.strip().replace(",", "") for award in award.split(" ")]
        for i in range(len(award_list)):
            try:
                award = int(award_list[i]) - 1
            except ValueError:
                print("\nSorry, that's not a valid selection.")
                continue
            if award > 5 or award < 0:
                print("\nSorry, that's not a valid selection.")
                valid = False
                break
            award_list[i] = menu[award]
        if not valid:
            continue
        break
    while True:
        result = int(shortcuts("\nDo you want to search for: \n\n"
                               "1) Only award winners\n"
                               "2) Only award nominees\n"
                               "3) Both\n\n>>> "))
        if result not in [1,  2, 3]:
            print("\nSorry, that's not a valid selection.")
            continue
        break
    year_search([award_list, result])


# begin by prompting user with main menu
def main():
    main_menu()
main()
