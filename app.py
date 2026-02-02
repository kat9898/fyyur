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
    jsonify,
    render_template,
    request,
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

    for venue in venues_data:
        key = (venue.city, venue.state)
        if key not in areas:
            areas[key] = {"city": venue.city, "state": venue.state, "venues": []}

        num_upcoming_shows = (
            db.session.query(shows_list)
            .filter(shows_list.c.venue_id == venue.id)
            .count()
        )

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
    search_term = request.form.get("search_term", "")
    venues = Venue.query.filter(Venue.name.ilike(f"%{search_term}%")).all()
    data = []
    for venue in venues:
        data.append(
            {
                "id": venue.id,
                "name": venue.name,
                "num_upcoming_shows": (
                    db.session.query(shows_list)
                    .filter(shows_list.c.venue_id == venue.id)
                    .count()
                ),
            }
        )
    response = {
        "count": len(venues),
        "data": data,
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
    return render_template("pages/home.html")


@app.route("/venues/<venue_id>", methods=["DELETE"])
def delete_venue(venue_id):
    error = False
    try:
        venue = Venue.query.get(venue_id)
        db.session.delete(venue)
        db.session.commit()
    except Exception as e:
        error = True
        db.session.rollback()
        print(f"Error occurred: {e}")
    finally:
        db.session.close()
    if error:
        flash(
            "An error occurred. Venue "
            + request.form["name"]
            + " could not be deleted."
        )
        abort(400)
    else:
        flash("Venue " + venue_id + " was successfully deleted!")
    return jsonify({"success": True})


#  Artists
#  ----------------------------------------------------------------
@app.route("/artists")
def artists():
    artists = Artist.query.all()
    return render_template("pages/artists.html", artists=artists)


@app.route("/artists/search", methods=["POST"])
def search_artists():
    search_term = request.form.get("search_term", "")
    artists = Artist.query.filter(Artist.name.ilike(f"%{search_term}%")).all()
    data = []
    for artist in artists:
        data.append(
            {
                "id": artist.id,
                "name": artist.name,
                "num_upcoming_shows": (
                    db.session.query(shows_list)
                    .filter(shows_list.c.artist_id == artist.id)
                    .count()
                ),
            }
        )
    response = {
        "count": len(artists),
        "data": data,
    }
    return render_template(
        "pages/search_artists.html",
        results=response,
        search_term=request.form.get("search_term", ""),
    )


@app.route("/artists/<int:artist_id>")
def show_artist(artist_id):
    artist_display = Artist.query.get(artist_id)
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
    artist = Artist.query.get(artist_id)
    form = ArtistForm(obj=artist)
    form.genres.data = artist.genres.split(", ")
    form.seeking_venue.data = artist.is_looking_for_venues
    return render_template("forms/edit_artist.html", form=form, artist=artist)


@app.route("/artists/<int:artist_id>/edit", methods=["POST"])
def edit_artist_submission(artist_id):
    error = False
    try:
        artist = Artist.query.get(artist_id)
        artist.name = request.form["name"]
        artist.city = request.form["city"]
        artist.state = request.form["state"]
        artist.phone = request.form["phone"]
        artist.genres = ", ".join(request.form.getlist("genres"))
        artist.facebook_link = request.form["facebook_link"]
        artist.image_link = request.form["image_link"]
        artist.website_link = request.form["website_link"]
        artist.is_looking_for_venues = (
            True if "seeking_venue" in request.form else False
        )
        artist.seeking_description = request.form["seeking_description"]

        db.session.commit()
    except Exception as e:
        error = True
        db.session.rollback()
        print(f"Error occurred: {e}")
    finally:
        db.session.close()
    if error:
        flash("An error occurred. Artist could not be updated.")
        abort(400)
    return redirect(url_for("show_artist", artist_id=artist_id))


@app.route("/venues/<int:venue_id>/edit", methods=["GET"])
def edit_venue(venue_id):
    venue = Venue.query.get(venue_id)
    form = VenueForm(obj=venue)
    form.genres.data = venue.genres.split(", ")
    form.seeking_talent.data = venue.is_looking_for_talent
    return render_template("forms/edit_venue.html", form=form, venue=venue)


@app.route("/venues/<int:venue_id>/edit", methods=["POST"])
def edit_venue_submission(venue_id):
    error = False
    try:
        venue = Venue.query.get(venue_id)
        venue.name = request.form["name"]
        venue.city = request.form["city"]
        venue.state = request.form["state"]
        venue.phone = request.form["phone"]
        venue.genres = ", ".join(request.form.getlist("genres"))
        venue.facebook_link = request.form["facebook_link"]
        venue.image_link = request.form["image_link"]
        venue.website_link = request.form["website_link"]
        venue.is_looking_for_talent = (
            True if "seeking_talent" in request.form else False
        )
        venue.seeking_description = request.form["seeking_description"]

        db.session.commit()
    except Exception as e:
        error = True
        db.session.rollback()
        print(f"Error occurred: {e}")
    finally:
        db.session.close()
    if error:
        flash("An error occurred. Venue could not be updated.")
        abort(400)
    return redirect(url_for("show_venue", venue_id=venue_id))


#  Create Artist
#  ----------------------------------------------------------------


@app.route("/artists/create", methods=["GET"])
def create_artist_form():
    form = ArtistForm()
    return render_template("forms/new_artist.html", form=form)


@app.route("/artists/create", methods=["POST"])
def create_artist_submission():
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
    flash("Artist " + request.form["name"] + " was successfully listed!")
    return render_template("pages/home.html")


#  Shows
#  ----------------------------------------------------------------


@app.route("/shows")
def shows():
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
    return render_template("pages/shows.html", shows=data)


@app.route("/shows/create")
def create_shows():
    # renders form. do not touch.
    form = ShowForm()
    return render_template("forms/new_show.html", form=form)


@app.route("/shows/create", methods=["POST"])
def create_show_submission():
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
