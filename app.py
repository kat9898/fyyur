# ----------------------------------------------------------------------------#
# Imports
# ----------------------------------------------------------------------------#

import json
import dateutil.parser
import babel
from datetime import datetime
from flask import (
    Flask,
    abort,
    render_template,
    request,
    Response,
    flash,
    redirect,
    url_for,
)
from flask_moment import Moment
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
import logging
from logging import Formatter, FileHandler
from flask_wtf import Form
from forms import *
from sqlalchemy import func

# ----------------------------------------------------------------------------#
# App Config.
# ----------------------------------------------------------------------------#

app = Flask(__name__)
moment = Moment(app)
app.config.from_object("config")
db = SQLAlchemy(app)
migrate = Migrate(app, db)

# ----------------------------------------------------------------------------#
# Models.
# ----------------------------------------------------------------------------#

shows_list = db.Table(
    "shows",
    db.Column("venue_id", db.Integer, db.ForeignKey("Venue.id"), primary_key=True),
    db.Column("artist_id", db.Integer, db.ForeignKey("Artist.id"), primary_key=True),
    db.Column("start_time", db.DateTime, nullable=False),
)


class Venue(db.Model):
    __tablename__ = "Venue"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False)
    city = db.Column(db.String(120), nullable=False)
    state = db.Column(db.String(120), nullable=False)
    address = db.Column(db.String(120), nullable=False)
    phone = db.Column(db.String(120))
    genres = db.Column(db.String(120), nullable=False)
    image_link = db.Column(db.String(500))
    facebook_link = db.Column(db.String(120))
    website_link = db.Column(db.String(120))
    is_looking_for_talent = db.Column(db.Boolean, default=False)
    seeking_description = db.Column(db.String(300))
    artists = db.relationship(
        "Artist", secondary=shows_list, backref=db.backref("venues", lazy=True)
    )


class Artist(db.Model):
    __tablename__ = "Artist"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False)
    city = db.Column(db.String(120), nullable=False)
    state = db.Column(db.String(120), nullable=False)
    phone = db.Column(db.String(120))
    genres = db.Column(db.String(120), nullable=False)
    image_link = db.Column(db.String(500))
    facebook_link = db.Column(db.String(120))
    website_link = db.Column(db.String(120))
    is_looking_for_venues = db.Column(db.Boolean, default=False)
    seeking_description = db.Column(db.String(300))


# ----------------------------------------------------------------------------#
# Filters.
# ----------------------------------------------------------------------------#


def format_datetime(value, format="medium"):
    date = dateutil.parser.parse(value)
    if format == "full":
        format = "EEEE MMMM, d, y 'at' h:mma"
    elif format == "medium":
        format = "EE MM, dd, y h:mma"
    return babel.dates.format_datetime(date, format, locale="en")


app.jinja_env.filters["datetime"] = format_datetime

# ----------------------------------------------------------------------------#
# Controllers.
# ----------------------------------------------------------------------------#


@app.route("/")
def index():
    return render_template("pages/home.html")


#  Venues
#  ----------------------------------------------------------------


@app.route("/venues")
def venues():
    venues_data = Venue.query.all()
    areas = {}
    print("VENUES:", venues_data)

    for venue in venues_data:
        key = (venue.city, venue.state)
        if key not in areas:
            areas[key] = {"city": venue.city, "state": venue.state, "venues": []}

        num_upcoming_shows = (
            db.session.query(shows_list)
            .filter(shows_list.c.venue_id == venue.id)
            .count()
        )
        print("VENUE SHOWS NUMBER:", num_upcoming_shows)

        areas[key]["venues"].append(
            {
                "id": venue.id,
                "name": venue.name,
                "num_upcoming_shows": num_upcoming_shows,
            }
        )
    return render_template("pages/venues.html", areas=list(areas.values()))


@app.route("/venues/search", methods=["POST"])
def search_venues():
    # TODO: implement search on artists with partial string search. Ensure it is case-insensitive.
    # seach for Hop should return "The Musical Hop".
    # search for "Music" should return "The Musical Hop" and "Park Square Live Music & Coffee"
    response = {
        "count": 1,
        "data": [
            {
                "id": 2,
                "name": "The Dueling Pianos Bar",
                "num_upcoming_shows": 0,
            }
        ],
    }
    return render_template(
        "pages/search_venues.html",
        results=response,
        search_term=request.form.get("search_term", ""),
    )


@app.route("/venues/<int:venue_id>")
def show_venue(venue_id):
    display_venue = Venue.query.get(venue_id)
    past_shows = (
        db.session.query(
            Artist.id.label("artist_id"),
            Artist.name.label("artist_name"),
            Artist.image_link.label("artist_image_link"),
            shows_list.c.start_time,
        )
        .join(shows_list, Artist.id == shows_list.c.artist_id)
        .filter(
            shows_list.c.venue_id == venue_id, shows_list.c.start_time < datetime.now()
        )
        .all()
    )
    upcoming_shows = (
        db.session.query(
            Artist.id.label("artist_id"),
            Artist.name.label("artist_name"),
            Artist.image_link.label("artist_image_link"),
            shows_list.c.start_time,
        )
        .join(shows_list, Artist.id == shows_list.c.artist_id)
        .filter(
            shows_list.c.venue_id == venue_id, shows_list.c.start_time >= datetime.now()
        )
        .all()
    )
    print(display_venue.genres)

    data = {
        "id": display_venue.id,
        "name": display_venue.name,
        "genres": display_venue.genres.split(", "),
        "address": display_venue.address,
        "city": display_venue.city,
        "state": display_venue.state,
        "phone": display_venue.phone,
        "website": display_venue.website_link,
        "facebook_link": display_venue.facebook_link,
        "seeking_talent": display_venue.is_looking_for_talent,
        "seeking_description": display_venue.seeking_description,
        "image_link": display_venue.image_link,
        "past_shows": [
            {
                "artist_id": show.artist_id,
                "artist_name": show.artist_name,
                "artist_image_link": show.artist_image_link,
                "start_time": show.start_time.isoformat(),
            }
            for show in past_shows
        ],
        "upcoming_shows": [
            {
                "artist_id": show.artist_id,
                "artist_name": show.artist_name,
                "artist_image_link": show.artist_image_link,
                "start_time": show.start_time.isoformat(),
            }
            for show in upcoming_shows
        ],
        "past_shows_count": len(past_shows),
        "upcoming_shows_count": len(upcoming_shows),
    }

    return render_template("pages/show_venue.html", venue=data)


#  Create Venue
#  ----------------------------------------------------------------


@app.route("/venues/create", methods=["GET"])
def create_venue_form():
    form = VenueForm()
    return render_template("forms/new_venue.html", form=form)


@app.route("/venues/create", methods=["POST"])
def create_venue_submission():
    print(request.form)
    error = False
    try:
        venue = Venue(
            name=request.form["name"],
            city=request.form["city"],
            state=request.form["state"],
            address=request.form["address"],
            phone=request.form["phone"],
            genres=", ".join(request.form.getlist("genres")),
            facebook_link=request.form["facebook_link"],
            image_link=request.form["image_link"],
            website_link=request.form["website_link"],
            is_looking_for_talent=True if "seeking_talent" in request.form else False,
            seeking_description=request.form["seeking_description"],
        )
        db.session.add(venue)
        db.session.commit()
    except Exception as e:
        error = True
        db.session.rollback()
        print(f"Error occurred: {e}")
    finally:
        db.session.close()
    if error:
        flash(
            "An error occurred. Venue " + request.form["name"] + " could not be listed."
        )
        abort(400)
    else:
        flash("Venue " + request.form["name"] + " was successfully listed!")
    # TODO: on unsuccessful db insert, flash an error instead.
    # e.g., flash('An error occurred. Venue ' + data.name + ' could not be listed.')
    # see: http://flask.pocoo.org/docs/1.0/patterns/flashing/
    return render_template("pages/home.html")


@app.route("/venues/<venue_id>", methods=["DELETE"])
def delete_venue(venue_id):
    # TODO: Complete this endpoint for taking a venue_id, and using
    # SQLAlchemy ORM to delete a record. Handle cases where the session commit could fail.

    # BONUS CHALLENGE: Implement a button to delete a Venue on a Venue Page, have it so that
    # clicking that button delete it from the db then redirect the user to the homepage
    return None


#  Artists
#  ----------------------------------------------------------------
@app.route("/artists")
def artists():
    artists = Artist.query.all()
    return render_template("pages/artists.html", artists=artists)


@app.route("/artists/search", methods=["POST"])
def search_artists():
    # TODO: implement search on artists with partial string search. Ensure it is case-insensitive.
    # seach for "A" should return "Guns N Petals", "Matt Quevado", and "The Wild Sax Band".
    # search for "band" should return "The Wild Sax Band".
    response = {
        "count": 1,
        "data": [
            {
                "id": 4,
                "name": "Guns N Petals",
                "num_upcoming_shows": 0,
            }
        ],
    }
    return render_template(
        "pages/search_artists.html",
        results=response,
        search_term=request.form.get("search_term", ""),
    )


@app.route("/artists/<int:artist_id>")
def show_artist(artist_id):
    print("ARTIST ID:", artist_id)
    artist_display = Artist.query.get(artist_id)
    print("ARTIST DISPLAY:", artist_display.genres)
    upcoming_shows = (
        db.session.query(
            Venue.id.label("venue_id"),
            Venue.name.label("venue_name"),
            Venue.image_link.label("venue_image_link"),
            shows_list.c.start_time,
        )
        .join(shows_list, Venue.id == shows_list.c.venue_id)
        .filter(
            shows_list.c.artist_id == artist_id,
            shows_list.c.start_time >= datetime.now(),
        )
        .all()
    )
    past_shows = (
        db.session.query(
            Venue.id.label("venue_id"),
            Venue.name.label("venue_name"),
            Venue.image_link.label("venue_image_link"),
            shows_list.c.start_time,
        )
        .join(shows_list, Venue.id == shows_list.c.venue_id)
        .filter(
            shows_list.c.artist_id == artist_id,
            shows_list.c.start_time < datetime.now(),
        )
        .all()
    )
    data = {
        "id": artist_display.id,
        "name": artist_display.name,
        "genres": artist_display.genres.split(", "),
        "city": artist_display.city,
        "state": artist_display.state,
        "phone": artist_display.phone,
        "website": artist_display.website_link,
        "facebook_link": artist_display.facebook_link,
        "seeking_venue": artist_display.is_looking_for_venues,
        "seeking_description": artist_display.seeking_description,
        "image_link": artist_display.image_link,
        "past_shows": [
            {
                "venue_id": show.venue_id,
                "venue_name": show.venue_name,
                "venue_image_link": show.venue_image_link,
                "start_time": show.start_time.isoformat(),
            }
            for show in past_shows
        ],
        "upcoming_shows": [
            {
                "venue_id": show.venue_id,
                "venue_name": show.venue_name,
                "venue_image_link": show.venue_image_link,
                "start_time": show.start_time.isoformat(),
            }
            for show in upcoming_shows
        ],
        "past_shows_count": len(past_shows),
        "upcoming_shows_count": len(upcoming_shows),
    }

    return render_template("pages/show_artist.html", artist=data)


#  Update
#  ----------------------------------------------------------------
@app.route("/artists/<int:artist_id>/edit", methods=["GET"])
def edit_artist(artist_id):
    form = ArtistForm()
    artist = {
        "id": 4,
        "name": "Guns N Petals",
        "genres": ["Rock n Roll"],
        "city": "San Francisco",
        "state": "CA",
        "phone": "326-123-5000",
        "website": "https://www.gunsnpetalsband.com",
        "facebook_link": "https://www.facebook.com/GunsNPetals",
        "seeking_venue": True,
        "seeking_description": "Looking for shows to perform at in the San Francisco Bay Area!",
        "image_link": "https://images.unsplash.com/photo-1549213783-8284d0336c4f?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=300&q=80",
    }
    # TODO: populate form with fields from artist with ID <artist_id>
    return render_template("forms/edit_artist.html", form=form, artist=artist)


@app.route("/artists/<int:artist_id>/edit", methods=["POST"])
def edit_artist_submission(artist_id):
    # TODO: take values from the form submitted, and update existing
    # artist record with ID <artist_id> using the new attributes

    return redirect(url_for("show_artist", artist_id=artist_id))


@app.route("/venues/<int:venue_id>/edit", methods=["GET"])
def edit_venue(venue_id):
    form = VenueForm()
    venue = {
        "id": 1,
        "name": "The Musical Hop",
        "genres": ["Jazz", "Reggae", "Swing", "Classical", "Folk"],
        "address": "1015 Folsom Street",
        "city": "San Francisco",
        "state": "CA",
        "phone": "123-123-1234",
        "website": "https://www.themusicalhop.com",
        "facebook_link": "https://www.facebook.com/TheMusicalHop",
        "seeking_talent": True,
        "seeking_description": "We are on the lookout for a local artist to play every two weeks. Please call us.",
        "image_link": "https://images.unsplash.com/photo-1543900694-133f37abaaa5?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=400&q=60",
    }
    # TODO: populate form with values from venue with ID <venue_id>
    return render_template("forms/edit_venue.html", form=form, venue=venue)


@app.route("/venues/<int:venue_id>/edit", methods=["POST"])
def edit_venue_submission(venue_id):
    # TODO: take values from the form submitted, and update existing
    # venue record with ID <venue_id> using the new attributes
    return redirect(url_for("show_venue", venue_id=venue_id))


#  Create Artist
#  ----------------------------------------------------------------


@app.route("/artists/create", methods=["GET"])
def create_artist_form():
    form = ArtistForm()
    return render_template("forms/new_artist.html", form=form)


@app.route("/artists/create", methods=["POST"])
def create_artist_submission():
    print(request.form)
    error = False
    try:
        artist = Artist(
            name=request.form["name"],
            city=request.form["city"],
            state=request.form["state"],
            phone=request.form["phone"],
            genres=", ".join(request.form.getlist("genres")),
            facebook_link=request.form["facebook_link"],
            image_link=request.form["image_link"],
            website_link=request.form["website_link"],
            is_looking_for_venues=True if "seeking_venue" in request.form else False,
            seeking_description=request.form["seeking_description"],
        )
        db.session.add(artist)
        db.session.commit()
    except Exception as e:
        error = True
        db.session.rollback()
        print(f"Error occurred: {e}")
    finally:
        db.session.close()
    if error:
        flash(
            "An error occurred. Artist "
            + request.form["name"]
            + " could not be listed."
        )
        abort(400)
    # called upon submitting the new artist listing form
    # TODO: insert form data as a new Venue record in the db, instead
    # TODO: modify data to be the data object returned from db insertion

    # on successful db insert, flash success
    flash("Artist " + request.form["name"] + " was successfully listed!")
    # TODO: on unsuccessful db insert, flash an error instead.
    # e.g., flash('An error occurred. Artist ' + data.name + ' could not be listed.')
    return render_template("pages/home.html")


#  Shows
#  ----------------------------------------------------------------


@app.route("/shows")
def shows():
    # displays list of shows at /shows
    # TODO: replace with real venues data.
    shows = (
        db.session.query(
            Venue.id.label("venue_id"),
            Venue.name.label("venue_name"),
            Artist.id.label("artist_id"),
            Artist.name.label("artist_name"),
            Artist.image_link.label("artist_image_link"),
            shows_list.c.start_time,
        )
        .join(shows_list, Venue.id == shows_list.c.venue_id)
        .join(Artist, Artist.id == shows_list.c.artist_id)
        .all()
    )

    data = []
    for show in shows:
        data.append(
            {
                "venue_id": show.venue_id,
                "venue_name": show.venue_name,
                "artist_id": show.artist_id,
                "artist_name": show.artist_name,
                "artist_image_link": show.artist_image_link,
                "start_time": show.start_time.isoformat(),
            }
        )

    # data=[{
    #   "venue_id": 1,
    #   "venue_name": "The Musical Hop",
    #   "artist_id": 4,
    #   "artist_name": "Guns N Petals",
    #   "artist_image_link": "https://images.unsplash.com/photo-1549213783-8284d0336c4f?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=300&q=80",
    #   "start_time": "2019-05-21T21:30:00.000Z"
    # }, {
    #   "venue_id": 3,
    #   "venue_name": "Park Square Live Music & Coffee",
    #   "artist_id": 5,
    #   "artist_name": "Matt Quevedo",
    #   "artist_image_link": "https://images.unsplash.com/photo-1495223153807-b916f75de8c5?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=334&q=80",
    #   "start_time": "2019-06-15T23:00:00.000Z"
    # }, {
    #   "venue_id": 3,
    #   "venue_name": "Park Square Live Music & Coffee",
    #   "artist_id": 6,
    #   "artist_name": "The Wild Sax Band",
    #   "artist_image_link": "https://images.unsplash.com/photo-1558369981-f9ca78462e61?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=794&q=80",
    #   "start_time": "2035-04-01T20:00:00.000Z"
    # }, {
    #   "venue_id": 3,
    #   "venue_name": "Park Square Live Music & Coffee",
    #   "artist_id": 6,
    #   "artist_name": "The Wild Sax Band",
    #   "artist_image_link": "https://images.unsplash.com/photo-1558369981-f9ca78462e61?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=794&q=80",
    #   "start_time": "2035-04-08T20:00:00.000Z"
    # }, {
    #   "venue_id": 3,
    #   "venue_name": "Park Square Live Music & Coffee",
    #   "artist_id": 6,
    #   "artist_name": "The Wild Sax Band",
    #   "artist_image_link": "https://images.unsplash.com/photo-1558369981-f9ca78462e61?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=794&q=80",
    #   "start_time": "2035-04-15T20:00:00.000Z"
    # }]
    return render_template("pages/shows.html", shows=data)


@app.route("/shows/create")
def create_shows():
    # renders form. do not touch.
    form = ShowForm()
    return render_template("forms/new_show.html", form=form)


@app.route("/shows/create", methods=["POST"])
def create_show_submission():
    print(request.form)
    error = False
    try:
        show = shows_list.insert().values(
            venue_id=request.form["venue_id"],
            artist_id=request.form["artist_id"],
            start_time=request.form["start_time"],
        )
        db.session.execute(show)
        db.session.commit()
    except Exception as e:
        error = True
        db.session.rollback()
        print(f"Error occurred: {e}")
    finally:
        db.session.close()
    if error:
        flash("An error occurred. Show could not be listed.")
        abort(400)
    flash("Show was successfully listed!")
    return render_template("pages/home.html")


@app.errorhandler(404)
def not_found_error(error):
    return render_template("errors/404.html"), 404


@app.errorhandler(500)
def server_error(error):
    return render_template("errors/500.html"), 500


if not app.debug:
    file_handler = FileHandler("error.log")
    file_handler.setFormatter(
        Formatter("%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]")
    )
    app.logger.setLevel(logging.INFO)
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.info("errors")

# ----------------------------------------------------------------------------#
# Launch.
# ----------------------------------------------------------------------------#

# Default port:
if __name__ == "__main__":
    app.run()

# Or specify port manually:
"""
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
"""
