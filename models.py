from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

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
